import serial
import time
import json
import requests
import os
import logging
import asyncio
import websockets
import threading
from heading_calc import calculate_heading
from gps_logger import save_gps_log

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RETRY_FILE = "/mdt/home/navbox/retry_queue.json"
latest_data = {}
connected_clients = set()

def validate_config(config):
    required = ['gps_port_a', 'gps_port_b', 'baudrate', 'server_url', 'websocket_port']
    for key in required:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    return config

def read_gpgga_line(ser):
    try:
        while True:
            line = ser.readline().decode('ascii', errors='ignore')
            if line.startswith("$GPGGA"):
                return line.strip()
    except Exception as e:
        logger.error(f"Error reading GPGGA line: {e}")
        return None

def parse_gpgga(gpgga):
    try:
        parts = gpgga.split(',')
        if len(parts) > 5 and parts[2] and parts[4]:
            raw_lat = float(parts[2])
            lat = int(raw_lat / 100) + (raw_lat % 100) / 60
            if parts[3] == 'S':
                lat *= -1

            raw_lon = float(parts[4])
            lon = int(raw_lon / 100) + (raw_lon % 100) / 60
            if parts[5] == 'W':
                lon *= -1

            return lat, lon
        return None, None
    except Exception as e:
        logger.error(f"Error parsing GPGGA: {e}")
        return None, None

def send_to_server(url, lat, lon, heading, device_id):
    data = {"device_id": device_id, "lat": lat, "lon": lon, "heading": heading}
    try:
        response = requests.post(url, json=data, timeout=5)
        logger.info(f"Server send success: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Server send failed: {e}")
        save_retry(data)
        return False

def save_retry(data):
    try:
        with threading.Lock():
            queue = []
            if os.path.exists(RETRY_FILE):
                with open(RETRY_FILE, 'r') as f:
                    queue = json.load(f)
            queue.append(data)
            with open(RETRY_FILE, 'w') as f:
                json.dump(queue, f)
            logger.info(f"Saved to retry queue: {data}")
    except Exception as e:
        logger.error(f"Error saving to retry queue: {e}")

def resend_retry_queue(url):
    try:
        if not os.path.exists(RETRY_FILE):
            return
        with threading.Lock():
            with open(RETRY_FILE, 'r') as f:
                queue = json.load(f)
            success = []
            for item in queue:
                try:
                    res = requests.post(url, json=item, timeout=5)
                    if res.ok:
                        success.append(item)
                except:
                    pass
            if len(success) < len(queue):
                with open(RETRY_FILE, 'w') as f:
                    json.dump(queue[len(success):], f)
            else:
                os.remove(RETRY_FILE)
            logger.info(f"Retry queue processed: {len(success)} succeeded")
    except Exception as e:
        logger.error(f"Error processing retry queue: {e}")

def get_device_id():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.strip().split(":")[1].strip()
    except:
        logger.warning("Failed to read device ID, using default")
        return "UNKNOWN"

async def websocket_handler(websocket, path):
    global connected_clients
    connected_clients.add(websocket)
    logger.info(f"New WebSocket client connected: {websocket.remote_address}")
    try:
        # Send latest data immediately upon connection
        if latest_data:
            await websocket.send(json.dumps(latest_data))
        async for message in websocket:
            # Handle incoming messages if needed (not used in this case)
            pass
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket client disconnected: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)

async def broadcast_data():
    global latest_data
    while True:
        if connected_clients and latest_data:
            message = json.dumps(latest_data)
            await asyncio.gather(*(client.send(message) for client in connected_clients))
        await asyncio.sleep(5)

def start_websocket_server(port):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(websocket_handler, "0.0.0.0", port)
    loop.run_until_complete(server)
    # Start broadcasting task
    loop.create_task(broadcast_data())
    logger.info(f"Started WebSocket server on ws://0.0.0.0:{port}/api/position")
    loop.run_forever()

def main():
    global latest_data
    device_id = get_device_id()
    logger.info(f"Device ID: {device_id}")

    try:
        with open('/mdt/home/navbox/config.json', 'r') as f:
            config = validate_config(json.load(f))
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    # Start WebSocket server in a separate thread
    ws_thread = threading.Thread(target=start_websocket_server, args=(config['websocket_port'],), daemon=True)
    ws_thread.start()

    while True:
        try:
            ser_a = serial.Serial(config['gps_port_a'], config['baudrate'], timeout=1)
            ser_b = serial.Serial(config['gps_port_b'], config['baudrate'], timeout=1)
            logger.info("Serial ports opened successfully")
            break
        except Exception as e:
            logger.error(f"Failed to open serial ports: {e}")
            time.sleep(5)

    while True:
        try:
            gga_a = read_gpgga_line(ser_a)
            gga_b = read_gpgga_line(ser_b)

            lat_a, lon_a = parse_gpgga(gga_a)
            lat_b, lon_b = parse_gpgga(gga_b)

            if lat_a and lat_b:
                heading = calculate_heading(lat_b, lon_b, lat_a, lon_a)
                logger.info(f"Position A: ({lat_a:.6f}, {lon_a:.6f}) / Heading: {heading:.2f}°")
                latest_data = {
                    "device_id": device_id,
                    "lat": lat_a,
                    "lon": lon_a,
                    "heading": heading
                }
                save_gps_log(lat_a, lon_a, lat_b, lon_b, heading)
                send_to_server(config['server_url'], lat_a, lon_a, heading, device_id)
                resend_retry_queue(config['server_url'])
            else:
                logger.warning("Insufficient GPS signal or parsing failed")

            time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Program interrupted")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()