import swisseph as swe
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from .houses import calculate_planetary_positions, get_zodiac_sign, format_degree

# Define standard aspects and their orbs
ASPECTS = {
    'conjunction': {'angle': 0, 'orb': 8},
    'opposition': {'angle': 180, 'orb': 8},
    'trine': {'angle': 120, 'orb': 8},
    'square': {'angle': 90, 'orb': 8},
    'sextile': {'angle': 60, 'orb': 6},
    'quincunx': {'angle': 150, 'orb': 3},
    'semisextile': {'angle': 30, 'orb': 3},
    'semisquare': {'angle': 45, 'orb': 2},
    'sesquisquare': {'angle': 135, 'orb': 2},
}

def calculate_aspect_orb(angle1: float, angle2: float, aspect_angle: float) -> float:
    """
    Calculate the orb between two angles for a specific aspect.
    
    Args:
        angle1 (float): First angle in degrees
        angle2 (float): Second angle in degrees
        aspect_angle (float): The aspect angle to check against
    
    Returns:
        float: The orb (distance from exact aspect)
    """
    diff = abs(angle1 - angle2)
    orb = min(diff, 360 - diff)
    return abs(orb - aspect_angle)

def is_retrograde(planet_data: Dict) -> bool:
    """
    Determine if a planet is retrograde based on its speed.
    
    Args:
        planet_data (dict): Dictionary containing planetary data including longitude_speed
    
    Returns:
        bool: True if planet is retrograde, False otherwise
    """
    return planet_data['longitude_speed'] < 0

def find_aspects(positions1: Dict, positions2: Dict, max_orb: float = None) -> List[Dict]:
    """
    Find all aspects between two sets of planetary positions.
    
    Args:
        positions1 (dict): First set of planetary positions
        positions2 (dict): Second set of planetary positions
        max_orb (float, optional): Maximum orb to consider for aspects
    
    Returns:
        list: List of dictionaries containing aspect information
    """
    aspects = []
    
    for planet1, pos1 in positions1.items():
        for planet2, pos2 in positions2.items():
            for aspect_name, aspect_data in ASPECTS.items():
                orb = calculate_aspect_orb(pos1['longitude'], pos2['longitude'], aspect_data['angle'])
                
                # Skip if orb is too large
                if max_orb is not None and orb > max_orb:
                    continue
                
                if orb <= aspect_data['orb']:
                    aspects.append({
                        'planet1': planet1,
                        'planet2': planet2,
                        'aspect': aspect_name,
                        'orb': orb,
                        'exact_angle': aspect_data['angle'],
                        'planet1_retrograde': is_retrograde(pos1),
                        'planet2_retrograde': is_retrograde(pos2)
                    })
    
    return aspects

def find_exact_aspect_time(
    natal_positions: Dict,
    start_time: datetime,
    end_time: datetime,
    planet1: str,
    planet2: str,
    aspect_name: str,
    timezone: float = 0
) -> Optional[datetime]:
    """
    Find the exact time when an aspect becomes exact between two planets.
    
    Args:
        natal_positions (dict): Natal planetary positions
        start_time (datetime): Start time to search from
        end_time (datetime): End time to search until
        planet1 (str): First planet name
        planet2 (str): Second planet name
        aspect_name (str): Name of the aspect to find
        timezone (float): Timezone offset in hours
    
    Returns:
        datetime: The exact time of the aspect, or None if not found
    """
    from .houses import compute_julian_day
    
    aspect_data = ASPECTS[aspect_name]
    time_step = timedelta(hours=1)  # Start with 1-hour steps
    current_time = start_time
    
    while current_time <= end_time:
        jd = compute_julian_day(current_time, timezone)
        transit_positions = calculate_planetary_positions(jd)
        
        # Calculate orb for this time
        orb = calculate_aspect_orb(
            natal_positions[planet1]['longitude'],
            transit_positions[planet2]['longitude'],
            aspect_data['angle']
        )
        
        # If we're very close to exact, do a finer search
        if orb < 0.1:  # Less than 6 minutes of arc
            # Search in smaller time steps around this point
            fine_start = current_time - timedelta(hours=1)
            fine_end = current_time + timedelta(hours=1)
            fine_step = timedelta(minutes=1)
            
            best_time = None
            best_orb = float('inf')
            
            while fine_start <= fine_end:
                jd = compute_julian_day(fine_start, timezone)
                transit_positions = calculate_planetary_positions(jd)
                orb = calculate_aspect_orb(
                    natal_positions[planet1]['longitude'],
                    transit_positions[planet2]['longitude'],
                    aspect_data['angle']
                )
                
                if orb < best_orb:
                    best_orb = orb
                    best_time = fine_start
                
                fine_start += fine_step
            
            return best_time
        
        current_time += time_step
    
    return None

def calculate_transits(
    natal_positions: Dict,
    transit_date: datetime,
    timezone: float = 0
) -> Dict:
    """
    Calculate transiting planets and their aspects to natal planets.
    
    Args:
        natal_positions (dict): Natal planetary positions
        transit_date (datetime): Date to calculate transits for
        timezone (float): Timezone offset in hours
    
    Returns:
        dict: Dictionary containing transit information
    """
    from .houses import compute_julian_day
    
    jd = compute_julian_day(transit_date, timezone)
    transit_positions = calculate_planetary_positions(jd)
    
    # Find all aspects between natal and transiting planets
    aspects = find_aspects(natal_positions, transit_positions)
    
    return {
        'date': transit_date,
        'transit_positions': transit_positions,
        'aspects': aspects
    }

def format_transit_report(transit_data: Dict) -> str:
    """
    Format transit data into a readable report.
    
    Args:
        transit_data (dict): Transit data from calculate_transits
    
    Returns:
        str: Formatted transit report
    """
    output = []
    
    # Header
    output.append(f"Transit Report for {transit_data['date'].strftime('%Y-%m-%d %H:%M')}")
    output.append("=" * 50)
    
    # Transit Positions
    output.append("\nTransiting Planets:")
    output.append("-" * 20)
    for planet, pos in transit_data['transit_positions'].items():
        sign, degree = get_zodiac_sign(pos['longitude'])
        retrograde = "R" if is_retrograde(pos) else ""
        output.append(f"{planet:8} {format_degree(pos['longitude'])} ({sign} {format_degree(degree)}) {retrograde}")
    
    # Aspects
    output.append("\nAspects to Natal Planets:")
    output.append("-" * 20)
    for aspect in transit_data['aspects']:
        output.append(
            f"{aspect['planet1']} {aspect['aspect']} {aspect['planet2']} "
            f"(orb: {aspect['orb']:.2f}°) "
            f"{'R' if aspect['planet1_retrograde'] else ''} "
            f"{'R' if aspect['planet2_retrograde'] else ''}"
        )
    
    return "\n".join(output) 