from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import swisseph as swe
from datetime import datetime
import sys
import os
from typing import Dict, Tuple, Optional, Any

from .houses import (
    compute_julian_day,
    calculate_ascendant_and_houses,
    calculate_planetary_positions,
    get_zodiac_sign,
    format_degree
)

class LocationGeocoder:
    """Handles location name to coordinates conversion."""
    
    def __init__(self, user_agent: str = "my_astrology_app"):
        self.geolocator = Nominatim(user_agent=user_agent)
    
    def get_coordinates(self, location_name: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Convert a location name to latitude and longitude coordinates.
        
        Args:
            location_name (str): Name of the location (e.g., "Beijing, China")
        
        Returns:
            tuple: (latitude, longitude) in degrees
        """
        try:
            location = self.geolocator.geocode(location_name)
            if location:
                return location.latitude, location.longitude
            print(f"Location '{location_name}' not found")
            return None, None
        except GeocoderTimedOut:
            print("Geocoding service timed out. Please try again.")
            return None, None

class AstrologicalChart:
    """Handles astrological chart calculations and formatting."""
    
    def __init__(self, geocoder: LocationGeocoder):
        self.geocoder = geocoder
    
    def calculate(self, location_name: str, birth_datetime: datetime, timezone: float) -> Optional[Dict[str, Any]]:
        """
        Calculate astrological chart for a given location and time.
        
        Args:
            location_name (str): Name of the location
            birth_datetime (datetime): Birth date and time
            timezone (float): Timezone offset in hours
        
        Returns:
            dict: Chart data including houses, angles, and planetary positions
        """
        latitude, longitude = self.geocoder.get_coordinates(location_name)
        if latitude is None or longitude is None:
            return None
        
        julian_day = compute_julian_day(birth_datetime, timezone)
        houses = calculate_ascendant_and_houses(julian_day, latitude, longitude, b'P')
        planets = calculate_planetary_positions(julian_day)
        
        return {
            'location': {
                'name': location_name,
                'latitude': latitude,
                'longitude': longitude
            },
            'time': {
                'datetime': birth_datetime,
                'timezone': timezone,
                'julian_day': julian_day
            },
            'houses': houses,
            'planets': planets
        }
    
    def format_chart(self, chart: Dict[str, Any]) -> str:
        """
        Format the chart data into a readable string.
        
        Args:
            chart (dict): Chart data from calculate method
        
        Returns:
            str: Formatted chart information
        """
        if not chart:
            return "No chart data available"
        
        output = []
        
        # Location information
        output.append(f"Location: {chart['location']['name']}")
        output.append(f"Latitude: {chart['location']['latitude']}°N")
        output.append(f"Longitude: {chart['location']['longitude']}°E")
        
        # Time information
        timezone = chart['time']['timezone']
        output.append(f"Time: {chart['time']['datetime'].strftime('%Y-%m-%d %H:%M')} "
                     f"(UTC{'+' if timezone >= 0 else ''}{timezone})")
        output.append(f"Julian Day: {chart['time']['julian_day']}")
        
        # Planetary Positions
        output.append("\nPlanetary Positions:")
        output.append("------------------")
        for planet, pos in chart['planets'].items():
            sign, degree = get_zodiac_sign(pos['longitude'])
            output.append(f"{planet:8} {format_degree(pos['longitude'])} ({sign} {format_degree(degree)})")
        
        # Ascendant
        houses = chart['houses']
        ascendant = houses['ascendant']
        sign, degree = get_zodiac_sign(ascendant)
        output.append(f"\nAscendant (Rising Sign):")
        output.append(f"Position: {format_degree(ascendant)} ({sign} {format_degree(degree)})")
        
        # House Cusps
        output.append("\nHouse Cusps:")
        output.append("------------")
        for house, cusp in houses['house_cusps'].items():
            sign, degree = get_zodiac_sign(cusp)
            output.append(f"{house:8} {format_degree(cusp)} ({sign} {format_degree(degree)})")
        
        # Angles
        output.append("\nAngles:")
        output.append("-------")
        for angle, value in houses['angles'].items():
            sign, degree = get_zodiac_sign(value)
            output.append(f"{angle:10} {format_degree(value)} ({sign} {format_degree(degree)})")
        
        return "\n".join(output) 