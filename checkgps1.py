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
                if line and line.startswith(("$GPGGA", "$GNGGA")) and parse_gpgga(line):
                    logger.info(f"GNSS module on {port} responded with valid GPGGA/GNGGA")
                    return True
                elif line and line.startswith("$GNGSA") and parse_gngsa(line):
                    logger.info(f"GNSS module on {port} responded with valid GNGSA")
                    return True
            logger.error(f"No valid GPGGA/GNGGA or GNGSA data received from {port}")
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
        logger.info("All GNSS modules are connected and responding.")
        sys.exit(0)
    else:
        logger.error("One or more GNSS modules failed to respond. Please check connections and ensure modules are powered on.")
        sys.exit(1)

if __name__ == "__main__":
    main()