import serial
import time
import sys
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_gpgga_line(ser, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if line.startswith("$GPGGA"):
                return line
        except Exception as e:
            logger.error(f"Error reading from serial port: {e}")
        time.sleep(0.1)
    return None

def check_gps_port(port, baudrate):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            logger.info(f"Checking GPS module on {port}...")
            gpgga_line = read_gpgga_line(ser)
            if gpgga_line:
                logger.info(f"GPS module on {port} responded with: {gpgga_line}")
                return True
            else:
                logger.error(f"No valid GPGGA data received from {port}")
                return False
    except Exception as e:
        logger.error(f"Failed to open {port}: {e}")
        return False

def main():
    try:
        with open('/mdt/home/navbox/config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}")
        sys.exit(1)

    ports = [config.get('gps_port_a'), config.get('gps_port_b')]
    baudrate = config.get('baudrate', 9600)

    all_ports_ok = True
    for port in ports:
        if not port:
            logger.error("Missing port configuration in config.json")
            sys.exit(1)
        if not check_gps_port(port, baudrate):
            all_ports_ok = False

    if all_ports_ok:
        logger.info("All GPS modules are connected and responding.")
        sys.exit(0)
    else:
        logger.error("One or more GPS modules failed to respond. Please check connections and ensure modules are powered on.")
        sys.exit(1)

if __name__ == "__main__":
    main()