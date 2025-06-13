"""
Athletics metadata extraction for Peterson university data.
"""

from typing import Any, Dict

from ..utils import get_sport_variations


def extract_athletics_metadata(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract athletics metadata fields.

    Fields extracted:
    - sport_[sport_name]: Boolean flags for 21 major sports
    - scholarship_sports_available: Whether any sports offer scholarships

    Sports tracked (based on Peterson data coverage analysis):
    - Top tier (>80%): basketball, volleyball, soccer, softball, cross_country
    - High coverage (70-80%): baseball, golf, tennis, track, football
    - Medium coverage (45-70%): indoor_track, lacrosse, cheerleading, ultimate_frisbee, swimming
    - Lower but significant (30-45%): table_tennis, rugby, bowling, ice_hockey, badminton

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with athletics metadata
    """
    metadata = {}

    athletics = json_record.get("athletics", {})

    # Major sports as boolean flags (based on Peterson data coverage analysis)
    sports_to_check = [
        # Top tier sports (>80% coverage)
        "basketball",
        "volleyball",
        "soccer",
        "softball",
        "cross_country",
        # High coverage sports (70-80%)
        "baseball",
        "golf",
        "tennis",
        "track",
        "football",
        # Medium coverage sports (45-70%)
        "indoor_track",
        "lacrosse",
        "cheerleading",
        "ultimate_frisbee",
        "swimming",
        # Lower but significant coverage sports (30-45%)
        "table_tennis",
        "rugby",
        "bowling",
        "ice_hockey",
        "badminton",
    ]

    # Check both men's and women's sports (they are lists of sport objects)
    mens_sports = athletics.get("Men's Sports", [])
    womens_sports = athletics.get("Women's Sports", [])

    for sport in sports_to_check:
        # Check if sport exists in either men's or women's athletics
        has_sport = False

        # Check various sport name variations
        sport_variations = get_sport_variations(sport)

        # Check in men's sports list
        for sport_obj in mens_sports:
            if (
                isinstance(sport_obj, dict)
                and sport_obj.get("sport") in sport_variations
            ):
                has_sport = True
                break

        # Check in women's sports list if not found in men's
        if not has_sport:
            for sport_obj in womens_sports:
                if (
                    isinstance(sport_obj, dict)
                    and sport_obj.get("sport") in sport_variations
                ):
                    has_sport = True
                    break

        metadata[f"sport_{sport}"] = has_sport

    # Check if any sports offer scholarships
    scholarship_available = False
    for sports_list in [mens_sports, womens_sports]:
        for sport_obj in sports_list:
            if isinstance(sport_obj, dict) and sport_obj.get("scholarship") is True:
                scholarship_available = True
                break
        if scholarship_available:
            break

    metadata["scholarship_sports_available"] = scholarship_available

    return metadata
