
import math
from collections import deque

heading_buffer = deque(maxlen=5)

def calculate_heading(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)

    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) -         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)

    initial_bearing = math.atan2(x, y)
    compass_bearing = (math.degrees(initial_bearing) + 360) % 360

    heading_buffer.append(compass_bearing)
    average_heading = sum(heading_buffer) / len(heading_buffer)

    return round(average_heading, 2)
