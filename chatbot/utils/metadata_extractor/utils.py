"""
Utility functions for metadata extraction.

This module contains helper functions used across different metadata extraction sections.
"""

from typing import List


def derive_region_from_state(state: str) -> str:
    """Derive US region from state name."""
    region_mapping = {
        # Pacific
        "California": "Pacific",
        "Oregon": "Pacific",
        "Washington": "Pacific",
        "Alaska": "Pacific",
        "Hawaii": "Pacific",
        # Mountain
        "Arizona": "Mountain",
        "Colorado": "Mountain",
        "Idaho": "Mountain",
        "Montana": "Mountain",
        "Nevada": "Mountain",
        "New Mexico": "Mountain",
        "Utah": "Mountain",
        "Wyoming": "Mountain",
        # West North Central
        "Iowa": "West North Central",
        "Kansas": "West North Central",
        "Minnesota": "West North Central",
        "Missouri": "West North Central",
        "Nebraska": "West North Central",
        "North Dakota": "West North Central",
        "South Dakota": "West North Central",
        # West South Central
        "Arkansas": "West South Central",
        "Louisiana": "West South Central",
        "Oklahoma": "West South Central",
        "Texas": "West South Central",
        # East North Central
        "Illinois": "East North Central",
        "Indiana": "East North Central",
        "Michigan": "East North Central",
        "Ohio": "East North Central",
        "Wisconsin": "East North Central",
        # East South Central
        "Alabama": "East South Central",
        "Kentucky": "East South Central",
        "Mississippi": "East South Central",
        "Tennessee": "East South Central",
        # South Atlantic
        "Delaware": "South Atlantic",
        "Florida": "South Atlantic",
        "Georgia": "South Atlantic",
        "Maryland": "South Atlantic",
        "North Carolina": "South Atlantic",
        "South Carolina": "South Atlantic",
        "Virginia": "South Atlantic",
        "West Virginia": "South Atlantic",
        "Washington DC": "South Atlantic",
        # Mid-Atlantic
        "New Jersey": "Mid-Atlantic",
        "New York": "Mid-Atlantic",
        "Pennsylvania": "Mid-Atlantic",
        # New England
        "Connecticut": "New England",
        "Maine": "New England",
        "Massachusetts": "New England",
        "New Hampshire": "New England",
        "Rhode Island": "New England",
        "Vermont": "New England",
    }

    return region_mapping.get(state, "Other")


def get_sport_variations(sport: str) -> List[str]:
    """Get various name variations for a sport."""
    variations = {
        # Top tier sports (>80% coverage)
        "basketball": ["Basketball"],
        "volleyball": ["Volleyball"],
        "soccer": ["Soccer"],
        "softball": ["Softball"],
        "cross_country": ["Cross-country Running", "Cross Country"],
        # High coverage sports (70-80%)
        "baseball": ["Baseball"],
        "golf": ["Golf"],
        "tennis": ["Tennis"],
        "track": ["Track And Field", "Track and Field"],
        "football": ["Football"],
        # Medium coverage sports (45-70%)
        "indoor_track": ["Indoor Track"],
        "lacrosse": ["Lacrosse"],
        "cheerleading": ["Cheerleading"],
        "ultimate_frisbee": ["Ultimate Frisbee"],
        "swimming": ["Swimming And Diving", "Swimming"],
        # Lower but significant coverage sports (30-45%)
        "table_tennis": ["Table Tennis"],
        "rugby": ["Rugby"],
        "bowling": ["Bowling"],
        "ice_hockey": ["Ice Hockey"],
        "badminton": ["Badminton"],
    }

    return variations.get(sport, [sport.title()])
