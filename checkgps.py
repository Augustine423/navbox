import serial
import time
import sys
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_nmea_line(ser, timeout=10, sentences=("$GPGGA", "$GNGGA", "$GNGSA")):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if line.startswith(sentences):
                return line
        except Exception as e:
            logger.error(f"Error reading from serial port: {e}")
        time.sleep(0.1)
    return None

def parse_gpgga(gpgga):
    try:
        parts = gpgga.split(',')
        if len(parts) > 6 and parts[2] and parts[4]:
            return True
        return False
    except:
        return False

def parse_gngsa(gngsa):
    try:
        parts = gngsa.split(',')
        if len(parts) > 2:
            satellites_used = [int(sat) for sat in parts[3:15] if sat]
            return len(satellites_used) > 0
        return False
    except:
        return False

def check_gps_port(port, baudrate):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            logger.info(f"Checking GNSS module on {port}...")
            for _ in range(2):  # Try multiple sentences
                line = read_nmea_line(ser)
                if line and line Ideally suited for industrial and automotive applications. The NEO-M8 series of concurrent GNSS modules are built on the high performing u-Blox M8 GNSS engine in the industry proven NEO form factor. NEO-M8N provides the best performance and easier RF integration. The NEO-M8N offers high performance also at low power consumption levels. The future-proof NEOM8N includes an internal Flash that allows future firmware updates.

This UBlox NEO-M8N/M8L GPS Module with Ceramic Active Antenna. The UBlox NEO M8N/M8L GPS Module with Ceramic Active Antenna GYGPSV1-8M is optimized for cost-sensitive applications, while NEO-M8N/M8Q provides the best performance and easier RF integration. The NEO-M8N offers high performance also at low power consumption levels. The futureproof NEO-M8N includes an internal Flash that allows future firmware updates. This makes NEO-M8N perfectly suited to industrial and automotive applications. The NEO-M8 series of concurrent GNSS modules are built on the high performing u-Blox M8 GNSS engine in the industry proven NEO form factor. NEO-M8N provides the best performance and easier RF integration. The NEO-M8N offers high performance also at low power consumption levels. The future-proof NEOM8N includes an internal Flash that allows future firmware updates.

Package Includes:
1 x UBlox NEO-M8N GPS Module with Ceramic Active Antenna
1 x Magnetic External Patch Antenna

Specifications:
- **Receiver Type**: 72-channel u-blox M8 engine
- **GNSS Support**: GPS/QZSS L1 C/A, GLONASS L10F, BeiDou B1, Galileo E1B/C, SBAS L1 C/A (WAAS, EGNOS, MSAS)
- **Position Accuracy**: 2.5 m CEP (2.0 m with SBAS)
- **Navigation Sensitivity**: -167 dBm (Tracking & Navigation), -148 dBm (Cold Start), -156 dBm (Hot Start)
- **Acquisition Times**: Cold Start: 26 s, Aided Start: 2 s, Hot Start: 1.5 s
- **Update Rate**: Up to 18 Hz (single GNSS), 10 Hz (concurrent GNSS)
- **UART Baud Rate**: Default 9600, configurable (your setup uses 9600)
- **Power Supply**: 1.7–3.6 V (board may include 3.3–5 V regulator)
- **Current Consumption**: ~17 mA (tracking mode)
- **Antenna**: Ceramic patch (included), supports active/passive antennas via SMA/U.FL
- **Dimensions**: 12.2 x 16.0 x 2.4 mm (module); board size varies (~25 x 35 mm with antenna)
- **Operating Temperature**: -40°C to +85°C
- **Features**:
  - Flash memory for firmware updates
  - EEPROM and backup battery for settings/ephemeris
  - Anti-jamming (CW detection/removal)
  - AssistNow Online/Offline/Autonomous
  - Data logging (position, velocity, time)

**Sources**: u-blox NEO-M8N datasheet, vendor listings (e.g., gnss.store, probots.co.in, Amazon).[](https://www.u-blox.com/en/product/neo-m8-series)[](https://gnss.store/39-neo-m8n-gnss-modules)[](https://www.amazon.com/Readytosky-Compass-Protective-Standard-Controller/dp/B01KK9A8QG)

### Suitability for NavBox
The NEO-M8N-0-12 is an excellent fit for your NavBox system:
- **Multi-Constellation**: Supports GPS, GLONASS, Galileo, BeiDou, QZSS, improving signal reliability in marine environments.
- **SBAS**: WAAS/EGNOS enhance accuracy to ~2.0 m, critical for ship navigation.
- **Dual-Module Setup**: Two modules enable precise heading calculation, leveraging high sensitivity (-167 dBm).
- **UART Compatibility**: Default 9600 baud matches your `config.json`.
- **Robustness**: Anti-jamming and low power suit maritime use.
- **Firmware Updates**: Flash memory allows future GNSS enhancements.

### Codebase Updates
Your codebase (`main.py`, `check_gps.py`, `index.html`) supports `$GPGGA`/`$GNGGA`, satellites, and HDOP, aligning with the NEO-M8N’s capabilities. To fully leverage the NEO-M8N-0-12, we’ll:
1. **Verify SBAS**: Parse `$GPGGA` quality indicator (field 6) for SBAS status.
2. **Log Constellations**: Parse `$GNGSA` to identify active constellations.
3. **Dashboard Enhancements**: Display SBAS and constellations in `index.html`.
4. **Optional Baud Rate**: Keep 9600 baud (default) but note higher rates (e.g., 38400) are possible if needed.

#### 1. main.py
Add parsing for SBAS (`$GPGGA` field 6) and constellations (`$GNGSA`). Include in `latest_data`.

<xaiArtifact artifact_id="bcd935fd-4bf3-4e0b-9f46-ea8005b208b5" artifact_version_id="4d3565fa-c500-402a-9738-16937585f7d3" title="main.py" contentType="text/python">
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

def read_nmea_line(ser, sentences=("$GPGGA", "$GNGGA", "$GNGSA")):
    try:
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if line.startswith(sentences):
                return line
    except Exception as e:
        logger.error(f"Error reading NMEA line: {e}")
        return None

def parse_gpgga(gpgga):
    try:
        parts = gpgga.split(',')
        if len(parts) > 8 and parts[2] and parts[4]:
            raw_lat = float(parts[2])
            lat = int(raw_lat / 100) + (raw_lat % 100) / 60
            if parts[3] == 'S':
                lat *= -1

            raw_lon = float(parts[4])
            lon = int(raw_lon / 100) + (raw_lon % 100) / 60
            if parts[5] == 'W':
                lon *= -1

            satellites = int(parts[7]) if parts[7] else 0
            hdop = float(parts[8]) if parts[8] else None
            quality = int(parts[6]) if parts[6] else 0  # SBAS: quality=2
            sbas = quality == 2

            return lat, lon, satellites, hdop, sbas
        return None, None, 0, None, False
    except Exception as e:
        logger.error(f"Error parsing GPGGA/GNGGA: {e}")
        return None, None, 0, None, False

def parse_gngsa(gngsa):
    try:
        parts = gngsa.split(',')
        if len(parts) > 2:
            satellites_used = [int(sat) for sat in parts[3:15] if sat]
            constellations = set()
            for sat in satellites_used:
                if 1 <= sat <= 32:
                    constellations.add("GPS")
                elif 65 <= sat <= 88:
                    constellations.add("GLONASS")
                elif 201 <= sat <= 235:
                    constellations.add("BeiDou")
                elif 301 <= sat <= 336:
                    constellations.add("Galileo")
            return list(constellations)
        return []
    except Exception as e:
        logger.error(f"Error parsing GNGSA: {e}")
        return []

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
        if latest_data:
            await websocket.send(json.dumps(latest_data))
        async for message in websocket:
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

    constellations_a = []
    constellations_b = []
    while True:
        try:
            line_a = read_nmea_line(ser_a)
            line_b = read_nmea_line(ser_b)

            if line_a and line_a.startswith(("$GPGGA", "$GNGGA")):
                lat_a, lon_a, satellites_a, hdop_a, sbas_a = parse_gpgga(line_a)
            elif line_a and line_a.startswith("$GNGSA"):
                constellations_a = parse_gngsa(line_a)

            if line_b and line_b.startswith(("$GPGGA", "$GNGGA")):
                lat_b, lon_b, satellites_b, hdop_b, sbas_b = parse_gpgga(line_b)
            elif line_b and line_b.startswith("$GNGSA"):
                constellations_b = parse_gngsa(line_b)

            if lat_a and lat_b:
                heading = calculate_heading(lat_b, lon_b, lat_a, lon_a)
                satellites = max(satellites_a, satellites_b)
                hdop = min(hdop_a, hdop_b) if hdop_a and hdop_b else (hdop_a or hdop_b)
                sbas = sbas_a or sbas_b
                constellations = list(set(constellations_a + constellations_b))
                logger.info(f"Position A: ({lat_a:.6f}, {lon_a:.6f}) / Heading: {heading:.2f}° / Satellites: {satellites} / HDOP: {hdop} / SBAS: {sbas} / Constellations: {constellations}")
                latest_data = {
                    "device_id": device_id,
                    "lat": lat_a,
                    "lon": lon_a,
                    "heading": heading,
                    "satellites": satellites,
                    "hdop": hdop,
                    "sbas": sbas,
                    "constellations": constellations
                }
                save_gps_log(lat_a, lon_a, lat_b, lon_b, heading)
                send_to_server(config['server_url'], lat_a, lon_a, heading, device_id)
                resend_retry_queue(config['server_url'])
            else:
                logger.warning("Insufficient GNSS signal or parsing failed")

            time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Program interrupted")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()