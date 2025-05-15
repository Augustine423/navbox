import csv
import os
import logging
from datetime import datetime, timedelta
import zipfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LOG_DIR = "/mdt/home/navbox/logs"

def save_gps_log(lat1, lon1, lat2, lon2, heading):
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
            logger.info(f"Created log directory: {LOG_DIR}")

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        filename = os.path.join(LOG_DIR, f"gps_{date_str}.csv")
        write_header = not os.path.exists(filename)

        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['timestamp', 'lat1', 'lon1', 'lat2', 'lon2', 'heading'])
                logger.info(f"Created new log file: {filename}")

            writer.writerow([
                now.isoformat(timespec='seconds'),
                lat1, lon1, lat2, lon2, heading
            ])
            logger.debug(f"Logged GPS data: {lat1}, {lon1}, {lat2}, {lon2}, {heading}")

        compress_old_logs()
    except Exception as e:
        logger.error(f"Error saving GPS log: {e}")

def compress_old_logs():
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        log_path = os.path.join(LOG_DIR, f"gps_{yesterday}.csv")
        zip_path = os.path.join(LOG_DIR, f"gps_{yesterday}.zip")

        if os.path.exists(log_path) and not os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(log_path, arcname=os.path.basename(log_path))
            os.remove(log_path)
            logger.info(f"Compressed and removed old log: {log_path}")
    except Exception as e:
        logger.error(f"Error compressing old logs: {e}")