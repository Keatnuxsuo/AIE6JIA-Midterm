import swisseph as swe
from datetime import datetime
import math

def compute_julian_day(birth_datetime, timezone=0):
    """
    Compute Julian Day for a birth datetime.
    
    Args:
        birth_datetime (datetime): Birth date and time
        timezone (float): Timezone offset in hours (default: 0 for UTC)
            Positive for east of UTC, negative for west of UTC
            Example: -5 for EST, +1 for CET
    
    Returns:
        float: Julian Day number
    """
    # Convert to UTC by subtracting timezone offset
    utc_hour = birth_datetime.hour - timezone
    
    # Calculate Julian Day directly using swe.julday
    return swe.julday(
        birth_datetime.year,
        birth_datetime.month,
        birth_datetime.day,
        utc_hour + birth_datetime.minute/60.0
    )

def calculate_planetary_positions(julian_day):
    """
    Calculate positions of all planets for a given Julian Day.
    
    Args:
        julian_day (float): Julian Day number
    
    Returns:
        dict: Dictionary containing planetary positions
    """
    # Planets to calculate
    PLANETS = {
        'Sun':    swe.SUN,
        'Moon':   swe.MOON,
        'Mercury':swe.MERCURY,
        'Venus':  swe.VENUS,
        'Mars':   swe.MARS,
        'Jupiter':swe.JUPITER,
        'Saturn': swe.SATURN,
        'Uranus': swe.URANUS,
        'Neptune':swe.NEPTUNE,
        'Pluto':  swe.PLUTO,
    }
    
    positions = {}
    for name, code in PLANETS.items():
        result = swe.calc_ut(julian_day, code)
        # Get the values from the first tuple
        lon = result[0][0]  # actual longitude
        lat = result[0][1]  # latitude
        dist = result[0][2]  # distance
        lon_speed = result[0][3]  # longitude speed
        lat_speed = result[0][4]  # latitude speed
        dist_speed = result[0][5]  # distance speed
        
        positions[name] = {
            'longitude': lon,
            'latitude': lat,
            'distance': dist,
            'longitude_speed': lon_speed,
            'latitude_speed': lat_speed,
            'distance_speed': dist_speed,
            'julian_day': julian_day
        }
    
    return positions

def calculate_ascendant_and_houses(julian_day, latitude, longitude, house_system='P'):
    """
    Calculate the Ascendant and house cusps.
    
    Args:
        julian_day (float): Julian day number
        latitude (float): Geographic latitude in degrees
        longitude (float): Geographic longitude in degrees
        house_system (str): House system to use
            'P' = Placidus (default)
            'K' = Koch
            'O' = Porphyrius
            'R' = Regiomontanus
            'C' = Campanus
            'A' = Equal
            'V' = Vehlow equal
            'W' = Whole sign
    
    Returns:
        dict: Dictionary containing ascendant and house cusps
    """
    # Set geographic location
    swe.set_topo(latitude, longitude, 0)
    
    # Calculate houses
    cusps, ascmc = swe.houses(julian_day, latitude, longitude, house_system)
    
    # Get the Ascendant (first house cusp)
    ascendant = cusps[0]
    
    # Create result dictionary
    result = {
        'ascendant': ascendant,
        'house_cusps': {
            'house_1': cusps[0],
            'house_2': cusps[1],
            'house_3': cusps[2],
            'house_4': cusps[3],
            'house_5': cusps[4],
            'house_6': cusps[5],
            'house_7': cusps[6],
            'house_8': cusps[7],
            'house_9': cusps[8],
            'house_10': cusps[9],
            'house_11': cusps[10],
            'house_12': cusps[11]
        },
        'angles': {
            'ascendant': ascmc[0],
            'midheaven': ascmc[1],
            'armc': ascmc[2],
            'vertex': ascmc[3]
        }
    }
    
    return result

def render_chart_wheel(positions, houses, latitude, longitude, birth_datetime):
    """
    Render the astrological chart wheel.
    
    Args:
        positions (dict): Planetary positions
        houses (dict): House cusps and angles
        latitude (float): Geographic latitude
        longitude (float): Geographic longitude
        birth_datetime (datetime): Birth date and time
    
    Returns:
        str: Formatted chart wheel representation
    """
    # Create the chart wheel header
    chart = f"""
Birth Chart
===========
Date: {birth_datetime.strftime('%Y-%m-%d %H:%M')}
Location: {latitude}°N, {longitude}°E

Ascendant: {format_degree(houses['ascendant'])} ({get_zodiac_sign(houses['ascendant'])[0]})
Midheaven: {format_degree(houses['angles']['midheaven'])} ({get_zodiac_sign(houses['angles']['midheaven'])[0]})

Planetary Positions:
------------------"""

    # Add planetary positions
    for name, pos in positions.items():
        sign, degree = get_zodiac_sign(pos['longitude'])
        chart += f"\n{name:8} {format_degree(pos['longitude'])} ({sign} {format_degree(degree)})"

    # Add house cusps
    chart += "\n\nHouse Cusps:"
    for house, cusp in houses['house_cusps'].items():
        sign, degree = get_zodiac_sign(cusp)
        chart += f"\n{house:8} {format_degree(cusp)} ({sign} {format_degree(degree)})"

    return chart

def get_zodiac_sign(degree):
    """
    Convert a degree to its corresponding zodiac sign.
    
    Args:
        degree (float): Degree in the zodiac (0-360)
    
    Returns:
        tuple: (sign_name, degree_in_sign)
    """
    signs = [
        'Aries', 'Taurus', 'Gemini', 'Cancer',
        'Leo', 'Virgo', 'Libra', 'Scorpio',
        'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]
    
    sign_num = int(degree / 30)
    degree_in_sign = degree % 30
    
    return signs[sign_num], degree_in_sign

def format_degree(degree):
    """
    Format a degree into degrees, minutes, and seconds.
    
    Args:
        degree (float): Degree in decimal format
    
    Returns:
        str: Formatted degree string (e.g., "15°30'45\"")
    """
    degrees = int(degree)
    minutes = int((degree - degrees) * 60)
    seconds = int(((degree - degrees) * 60 - minutes) * 60)
    
    return f"{degrees}°{minutes}'{seconds}\""

def calculate_houses_for_positions(positions, latitude, longitude, house_system='P'):
    """
    Calculate houses for multiple planetary positions.
    
    Args:
        positions (dict): Dictionary of planetary positions with Julian day numbers
        latitude (float): Geographic latitude in degrees
        longitude (float): Geographic longitude in degrees
        house_system (str): House system to use (default: Placidus)
    
    Returns:
        dict: Dictionary containing houses for each position
    """
    results = {}
    
    for name, pos in positions.items():
        # Extract Julian day from position data
        jd = pos.get('julian_day')
        if jd is None:
            print(f"Warning: No Julian day found for {name}, skipping...")
            continue
            
        # Calculate houses for this position
        house_data = calculate_ascendant_and_houses(jd, latitude, longitude, house_system)
        
        # Store results with planet name as key
        results[name] = {
            'ascendant': house_data['ascendant'],
            'house_cusps': house_data['house_cusps'],
            'angles': house_data['angles']
        }
    
    return results

def print_houses_for_positions(results):
    """
    Print house calculations for multiple positions in a readable format.
    
    Args:
        results (dict): Dictionary of house calculations from calculate_houses_for_positions
    """
    for name, data in results.items():
        print(f"\n=== Houses for {name} ===")
        
        # Print Ascendant
        sign, degree = get_zodiac_sign(data['ascendant'])
        print(f"Ascendant: {format_degree(data['ascendant'])} ({sign} {format_degree(degree)})")
        
        # Print House Cusps
        print("\nHouse Cusps:")
        for house, cusp in data['house_cusps'].items():
            sign, degree = get_zodiac_sign(cusp)
            print(f"{house}: {format_degree(cusp)} ({sign} {format_degree(degree)})")
        
        # Print Angles
        print("\nAngles:")
        for angle, value in data['angles'].items():
            sign, degree = get_zodiac_sign(value)
            print(f"{angle}: {format_degree(value)} ({sign} {format_degree(degree)})")

# Example usage
if __name__ == "__main__":
    # 1. Compute Julian Day for birth datetime
    birth_time = datetime(1990, 1, 1, 12, 0)  # January 1, 1990, 12:00 PM
    jd = compute_julian_day(birth_time, timezone=-5)  # EST timezone
    
    # 2. Calculate planetary positions
    positions = calculate_planetary_positions(jd)
    
    # 3. Compute the Ascendant and houses
    geo_lat = 40.7128  # New York City latitude
    geo_lon = -74.0060  # New York City longitude
    houses = calculate_ascendant_and_houses(jd, geo_lat, geo_lon)
    
    # 4. Render the chart wheel
    chart = render_chart_wheel(positions, houses, geo_lat, geo_lon, birth_time)
    print(chart) 