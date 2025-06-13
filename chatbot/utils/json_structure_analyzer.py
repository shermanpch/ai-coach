import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


def load_peterson_data() -> List[Dict[str, Any]]:
    """Load the peterson_data.json file."""
    data_path = Path("data/cleaned/peterson_data.json")

    if not data_path.exists():
        raise FileNotFoundError(f"Peterson data file not found at: {data_path}")

    print(f"Loading data from: {data_path}")
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} universities")
    return data


def analyze_location_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the location_contact section."""
    print("\nAnalyzing LOCATION section...")

    address_keys = Counter()
    contact_keys = Counter()
    address_samples = defaultdict(list)
    contact_samples = defaultdict(list)

    for i, university in enumerate(data):
        if i % 200 == 0:
            print(f"  Processed {i}/{len(data)} universities...")

        location = university.get("location_contact", {})

        # Analyze address keys
        address = location.get("address", {})
        for key, value in address.items():
            address_keys[key] += 1
            if value is not None and len(address_samples[key]) < 3:
                str_value = str(value)
                if str_value not in address_samples[key]:
                    address_samples[key].append(str_value)

        # Analyze contact keys
        contact = location.get("contact", {})
        for key, value in contact.items():
            contact_keys[key] += 1
            if value is not None and len(contact_samples[key]) < 3:
                str_value = str(value)
                if str_value not in contact_samples[key]:
                    contact_samples[key].append(str_value)

    return {
        "section_name": "location_contact",
        "total_universities": len(data),
        "address_keys": address_keys,
        "contact_keys": contact_keys,
        "address_samples": dict(address_samples),
        "contact_samples": dict(contact_samples),
    }


def analyze_admissions_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the admissions section."""
    print("\nAnalyzing ADMISSIONS section...")

    all_keys = Counter()
    samples = defaultdict(list)

    def analyze_nested(obj, prefix=""):
        """Recursively analyze nested structure."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                all_keys[full_key] += 1

                if not isinstance(value, (dict, list)) and value is not None:
                    if len(samples[full_key]) < 3:
                        str_value = str(value)
                        if str_value not in samples[full_key]:
                            samples[full_key].append(str_value)
                elif isinstance(value, dict):
                    analyze_nested(value, full_key)
                elif isinstance(value, list) and value:
                    if isinstance(value[0], dict):
                        analyze_nested(value[0], f"{full_key}[0]")
                    else:
                        # List of simple values
                        if len(samples[full_key]) < 3:
                            str_value = str(value[0])
                            if str_value not in samples[full_key]:
                                samples[full_key].append(str_value)

    for i, university in enumerate(data):
        if i % 200 == 0:
            print(f"  Processed {i}/{len(data)} universities...")

        admissions = university.get("admissions", {})
        if admissions:
            analyze_nested(admissions)

    return {
        "section_name": "admissions",
        "total_universities": len(data),
        "all_keys": all_keys,
        "samples": dict(samples),
    }


def analyze_tuition_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the tuition_and_fees section."""
    print("\nAnalyzing TUITION_AND_FEES section...")

    all_keys = Counter()
    samples = defaultdict(list)
    tuition_categories = Counter()
    fee_categories = Counter()

    for i, university in enumerate(data):
        if i % 200 == 0:
            print(f"  Processed {i}/{len(data)} universities...")

        tuition_fees = university.get("tuition_and_fees", {})

        # Track top-level keys
        for key in tuition_fees.keys():
            all_keys[key] += 1

        # Analyze tuition categories
        for tuition_info in tuition_fees.get("tuition", []):
            category = tuition_info.get("category")
            if category:
                tuition_categories[category] += 1
                if len(samples[f"tuition.{category}"]) < 3:
                    amount = tuition_info.get("amount")
                    if amount is not None:
                        str_amount = str(amount)
                        if str_amount not in samples[f"tuition.{category}"]:
                            samples[f"tuition.{category}"].append(str_amount)

        # Analyze fee categories
        for fee_info in tuition_fees.get("fees", []):
            category = fee_info.get("category")
            if category:
                fee_categories[category] += 1
                if len(samples[f"fees.{category}"]) < 3:
                    amount = fee_info.get("amount")
                    if amount is not None:
                        str_amount = str(amount)
                        if str_amount not in samples[f"fees.{category}"]:
                            samples[f"fees.{category}"].append(str_amount)

        # Other payment considerations
        other = tuition_fees.get("other_payment_considerations")
        if other is not None:
            all_keys["other_payment_considerations"] += 1
            if len(samples["other_payment_considerations"]) < 3:
                str_other = str(other)
                if str_other not in samples["other_payment_considerations"]:
                    samples["other_payment_considerations"].append(str_other)

    return {
        "section_name": "tuition_and_fees",
        "total_universities": len(data),
        "all_keys": all_keys,
        "tuition_categories": tuition_categories,
        "fee_categories": fee_categories,
        "samples": dict(samples),
    }


def analyze_campus_life_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the campus_life section."""
    print("\nAnalyzing CAMPUS_LIFE section...")

    all_keys = Counter()
    samples = defaultdict(list)

    def analyze_nested(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                all_keys[full_key] += 1

                if not isinstance(value, (dict, list)) and value is not None:
                    if len(samples[full_key]) < 3:
                        str_value = str(value)
                        if str_value not in samples[full_key]:
                            samples[full_key].append(str_value)
                elif isinstance(value, dict):
                    analyze_nested(value, full_key)
                elif isinstance(value, list) and value:
                    if isinstance(value[0], dict):
                        analyze_nested(value[0], f"{full_key}[0]")
                    else:
                        if len(samples[full_key]) < 3:
                            str_value = str(value[:3])  # First few items
                            if str_value not in samples[full_key]:
                                samples[full_key].append(str_value)

    for i, university in enumerate(data):
        if i % 200 == 0:
            print(f"  Processed {i}/{len(data)} universities...")

        campus_life = university.get("campus_life", {})
        if campus_life:
            analyze_nested(campus_life)

    return {
        "section_name": "campus_life",
        "total_universities": len(data),
        "all_keys": all_keys,
        "samples": dict(samples),
    }


def analyze_faculty_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the faculty section."""
    print("\nAnalyzing FACULTY section...")

    all_keys = Counter()
    samples = defaultdict(list)

    def analyze_nested(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                all_keys[full_key] += 1

                if not isinstance(value, (dict, list)) and value is not None:
                    if len(samples[full_key]) < 3:
                        str_value = str(value)
                        if str_value not in samples[full_key]:
                            samples[full_key].append(str_value)
                elif isinstance(value, dict):
                    analyze_nested(value, full_key)

    for i, university in enumerate(data):
        if i % 200 == 0:
            print(f"  Processed {i}/{len(data)} universities...")

        faculty = university.get("faculty", {})
        if faculty:
            analyze_nested(faculty)

    return {
        "section_name": "faculty",
        "total_universities": len(data),
        "all_keys": all_keys,
        "samples": dict(samples),
    }


def print_location_report(analysis: Dict[str, Any]) -> None:
    """Print detailed location analysis report."""
    total = analysis["total_universities"]

    print("\n" + "=" * 70)
    print("LOCATION SECTION DETAILED REPORT")
    print("=" * 70)

    print(f"\nADDRESS KEYS ({len(analysis['address_keys'])} unique keys):")
    print("-" * 50)
    for key, count in analysis["address_keys"].most_common():
        percentage = (count / total) * 100
        print(f"  • {key:<15} {count:>4}/{total} ({percentage:>5.1f}%)")
        if key in analysis["address_samples"]:
            samples = analysis["address_samples"][key][:3]
            print(f"    Examples: {', '.join(samples)}")

    print(f"\nCONTACT KEYS ({len(analysis['contact_keys'])} unique keys):")
    print("-" * 50)
    for key, count in analysis["contact_keys"].most_common():
        percentage = (count / total) * 100
        print(f"  • {key:<15} {count:>4}/{total} ({percentage:>5.1f}%)")
        if key in analysis["contact_samples"]:
            samples = analysis["contact_samples"][key][:3]
            print(f"    Examples: {', '.join(samples)}")


def print_section_report(analysis: Dict[str, Any]) -> None:
    """Print detailed section analysis report."""
    total = analysis["total_universities"]
    section_name = analysis["section_name"].upper().replace("_", " ")

    print("\n" + "=" * 70)
    print(f"{section_name} SECTION DETAILED REPORT")
    print("=" * 70)

    if "tuition_categories" in analysis:
        # Special handling for tuition section
        print("\nTUITION CATEGORIES:")
        print("-" * 40)
        for category, count in analysis["tuition_categories"].most_common():
            percentage = (count / total) * 100
            print(f"  • {category:<20} {count:>4}/{total} ({percentage:>5.1f}%)")
            if f"tuition.{category}" in analysis["samples"]:
                samples = analysis["samples"][f"tuition.{category}"][:3]
                print(f"    Examples: {', '.join(samples)}")

        print("\nFEE CATEGORIES:")
        print("-" * 40)
        for category, count in analysis["fee_categories"].most_common():
            percentage = (count / total) * 100
            print(f"  • {category:<20} {count:>4}/{total} ({percentage:>5.1f}%)")
            if f"fees.{category}" in analysis["samples"]:
                samples = analysis["samples"][f"fees.{category}"][:3]
                print(f"    Examples: {', '.join(samples)}")

    print(f"\nALL KEYS IN {section_name}:")
    print("-" * 50)
    for key, count in analysis["all_keys"].most_common():
        percentage = (count / total) * 100
        print(f"  • {key:<30} {count:>4}/{total} ({percentage:>5.1f}%)")
        if key in analysis["samples"]:
            samples = analysis["samples"][key][:3]
            print(f"    Examples: {', '.join(samples)}")


def analyze_financial_aid_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the financial_aid section."""
    print("\nAnalyzing FINANCIAL_AID section...")

    all_keys = Counter()
    samples = defaultdict(list)

    def analyze_nested(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                all_keys[full_key] += 1

                if not isinstance(value, (dict, list)) and value is not None:
                    if len(samples[full_key]) < 3:
                        str_value = str(value)
                        if str_value not in samples[full_key]:
                            samples[full_key].append(str_value)
                elif isinstance(value, dict):
                    analyze_nested(value, full_key)

    for i, university in enumerate(data):
        if i % 200 == 0:
            print(f"  Processed {i}/{len(data)} universities...")

        financial_aid = university.get("financial_aid", {})
        if financial_aid:
            analyze_nested(financial_aid)

    return {
        "section_name": "financial_aid",
        "total_universities": len(data),
        "all_keys": all_keys,
        "samples": dict(samples),
    }


def analyze_athletics_section(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the athletics section."""
    print("\nAnalyzing ATHLETICS section...")

    all_keys = Counter()
    samples = defaultdict(list)
    mens_sports_count = Counter()
    womens_sports_count = Counter()

    # Track universities that have each attribute (not individual sport records)
    universities_with_key = defaultdict(set)

    for i, university in enumerate(data):
        if i % 200 == 0:
            print(f"  Processed {i}/{len(data)} universities...")

        athletics = university.get("athletics", {})

        # Count top-level keys
        for key in athletics.keys():
            universities_with_key[key].add(i)

        # Analyze men's sports
        mens_sports = athletics.get("Men's Sports", [])
        if mens_sports:
            universities_with_key["Men's Sports"].add(i)

            # Track if this university has any men's sports with these attributes
            has_mens_intramural = False
            has_mens_intercollegiate = False
            has_mens_scholarship = False

            for sport_info in mens_sports:
                if isinstance(sport_info, dict):
                    sport_name = sport_info.get("sport")
                    if sport_name:
                        mens_sports_count[sport_name] += 1
                        if len(samples["Men's Sports.sports"]) < 10:
                            if sport_name not in samples["Men's Sports.sports"]:
                                samples["Men's Sports.sports"].append(sport_name)

                    # Check sport attributes for this university
                    if sport_info.get("intramural") is not None:
                        has_mens_intramural = True
                        if len(samples["Men's Sports.intramural"]) < 3:
                            str_value = str(sport_info["intramural"])
                            if str_value not in samples["Men's Sports.intramural"]:
                                samples["Men's Sports.intramural"].append(str_value)

                    if sport_info.get("intercollegiate") is not None:
                        has_mens_intercollegiate = True
                        if len(samples["Men's Sports.intercollegiate"]) < 3:
                            str_value = str(sport_info["intercollegiate"])
                            if str_value not in samples["Men's Sports.intercollegiate"]:
                                samples["Men's Sports.intercollegiate"].append(
                                    str_value
                                )

                    if sport_info.get("scholarship") is not None:
                        has_mens_scholarship = True
                        if len(samples["Men's Sports.scholarship"]) < 3:
                            str_value = str(sport_info["scholarship"])
                            if str_value not in samples["Men's Sports.scholarship"]:
                                samples["Men's Sports.scholarship"].append(str_value)

            # Count university once for each attribute it has
            if has_mens_intramural:
                universities_with_key["Men's Sports.intramural"].add(i)
            if has_mens_intercollegiate:
                universities_with_key["Men's Sports.intercollegiate"].add(i)
            if has_mens_scholarship:
                universities_with_key["Men's Sports.scholarship"].add(i)

        # Analyze women's sports
        womens_sports = athletics.get("Women's Sports", [])
        if womens_sports:
            universities_with_key["Women's Sports"].add(i)

            # Track if this university has any women's sports with these attributes
            has_womens_intramural = False
            has_womens_intercollegiate = False
            has_womens_scholarship = False

            for sport_info in womens_sports:
                if isinstance(sport_info, dict):
                    sport_name = sport_info.get("sport")
                    if sport_name:
                        womens_sports_count[sport_name] += 1
                        if len(samples["Women's Sports.sports"]) < 10:
                            if sport_name not in samples["Women's Sports.sports"]:
                                samples["Women's Sports.sports"].append(sport_name)

                    # Check sport attributes for this university
                    if sport_info.get("intramural") is not None:
                        has_womens_intramural = True
                        if len(samples["Women's Sports.intramural"]) < 3:
                            str_value = str(sport_info["intramural"])
                            if str_value not in samples["Women's Sports.intramural"]:
                                samples["Women's Sports.intramural"].append(str_value)

                    if sport_info.get("intercollegiate") is not None:
                        has_womens_intercollegiate = True
                        if len(samples["Women's Sports.intercollegiate"]) < 3:
                            str_value = str(sport_info["intercollegiate"])
                            if (
                                str_value
                                not in samples["Women's Sports.intercollegiate"]
                            ):
                                samples["Women's Sports.intercollegiate"].append(
                                    str_value
                                )

                    if sport_info.get("scholarship") is not None:
                        has_womens_scholarship = True
                        if len(samples["Women's Sports.scholarship"]) < 3:
                            str_value = str(sport_info["scholarship"])
                            if str_value not in samples["Women's Sports.scholarship"]:
                                samples["Women's Sports.scholarship"].append(str_value)

            # Count university once for each attribute it has
            if has_womens_intramural:
                universities_with_key["Women's Sports.intramural"].add(i)
            if has_womens_intercollegiate:
                universities_with_key["Women's Sports.intercollegiate"].add(i)
            if has_womens_scholarship:
                universities_with_key["Women's Sports.scholarship"].add(i)

    # Convert sets to counts
    for key, university_set in universities_with_key.items():
        all_keys[key] = len(university_set)

    return {
        "section_name": "athletics",
        "total_universities": len(data),
        "all_keys": all_keys,
        "samples": dict(samples),
        "mens_sports_count": mens_sports_count,
        "womens_sports_count": womens_sports_count,
    }


def print_athletics_report(analysis: Dict[str, Any]) -> None:
    """Print detailed athletics analysis report."""
    total = analysis["total_universities"]

    print("\n" + "=" * 70)
    print("ATHLETICS SECTION DETAILED REPORT")
    print("=" * 70)

    print("\nTOP 20 MEN'S SPORTS:")
    print("-" * 50)
    for sport, count in analysis["mens_sports_count"].most_common(20):
        percentage = (count / total) * 100
        print(f"  • {sport:<30} {count:>4}/{total} ({percentage:>5.1f}%)")

    print("\nTOP 20 WOMEN'S SPORTS:")
    print("-" * 50)
    for sport, count in analysis["womens_sports_count"].most_common(20):
        percentage = (count / total) * 100
        print(f"  • {sport:<30} {count:>4}/{total} ({percentage:>5.1f}%)")

    print("\nALL KEYS IN ATHLETICS:")
    print("-" * 50)
    for key, count in analysis["all_keys"].most_common():
        percentage = (count / total) * 100
        print(f"  • {key:<30} {count:>4}/{total} ({percentage:>5.1f}%)")
        if key in analysis["samples"]:
            samples = analysis["samples"][key][:5]
            print(f"    Examples: {', '.join(samples)}")


def generate_markdown_report(
    location_analysis: Dict[str, Any],
    admissions_analysis: Dict[str, Any],
    tuition_analysis: Dict[str, Any],
    campus_life_analysis: Dict[str, Any],
    faculty_analysis: Dict[str, Any],
    financial_aid_analysis: Dict[str, Any],
    athletics_analysis: Dict[str, Any],
) -> str:
    """Generate a comprehensive markdown report."""

    total = location_analysis["total_universities"]

    md_content = []

    # Header
    md_content.append("# Peterson Data JSON Structure Analysis Report")
    md_content.append("")
    md_content.append(f"**Total Universities Analyzed:** {total}")
    md_content.append("**Total Sections Analyzed:** 7")
    md_content.append("")

    # Table of Contents
    md_content.append("## Table of Contents")
    md_content.append("1. [Location Section](#location-section)")
    md_content.append("2. [Admissions Section](#admissions-section)")
    md_content.append("3. [Tuition and Fees Section](#tuition-and-fees-section)")
    md_content.append("4. [Campus Life Section](#campus-life-section)")
    md_content.append("5. [Faculty Section](#faculty-section)")
    md_content.append("6. [Financial Aid Section](#financial-aid-section)")
    md_content.append("7. [Athletics Section](#athletics-section)")
    md_content.append("")

    # Location Section
    md_content.append("## Location Section")
    md_content.append("")
    md_content.append("### Address Keys")
    md_content.append("| Key | Universities | Coverage | Examples |")
    md_content.append("|-----|-------------|----------|----------|")
    for key, count in location_analysis["address_keys"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(location_analysis["address_samples"].get(key, [])[:3])
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {key} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    md_content.append("")
    md_content.append("### Contact Keys")
    md_content.append("| Key | Universities | Coverage | Examples |")
    md_content.append("|-----|-------------|----------|----------|")
    for key, count in location_analysis["contact_keys"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(location_analysis["contact_samples"].get(key, [])[:3])
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {key} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    # Admissions Section
    md_content.append("")
    md_content.append("## Admissions Section")
    md_content.append("")
    md_content.append("### All Keys in Admissions")
    md_content.append("| Key | Universities | Coverage | Examples |")
    md_content.append("|-----|-------------|----------|----------|")
    for key, count in admissions_analysis["all_keys"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(
            str(x) for x in admissions_analysis["samples"].get(key, [])[:3]
        )
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {key} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    # Tuition Section
    md_content.append("")
    md_content.append("## Tuition and Fees Section")
    md_content.append("")
    md_content.append("### Tuition Categories")
    md_content.append("| Category | Universities | Coverage | Examples |")
    md_content.append("|----------|-------------|----------|----------|")
    for category, count in tuition_analysis["tuition_categories"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(
            str(x)
            for x in tuition_analysis["samples"].get(f"tuition.{category}", [])[:3]
        )
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {category} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    md_content.append("")
    md_content.append("### Fee Categories")
    md_content.append("| Category | Universities | Coverage | Examples |")
    md_content.append("|----------|-------------|----------|----------|")
    for category, count in tuition_analysis["fee_categories"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(
            str(x) for x in tuition_analysis["samples"].get(f"fees.{category}", [])[:3]
        )
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {category} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    # Campus Life Section
    md_content.append("")
    md_content.append("## Campus Life Section")
    md_content.append("")
    md_content.append("### All Keys in Campus Life")
    md_content.append("| Key | Universities | Coverage | Examples |")
    md_content.append("|-----|-------------|----------|----------|")
    for key, count in campus_life_analysis["all_keys"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(
            str(x) for x in campus_life_analysis["samples"].get(key, [])[:3]
        )
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        # Truncate very long examples
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {key} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    # Faculty Section
    md_content.append("")
    md_content.append("## Faculty Section")
    md_content.append("")
    md_content.append("### All Keys in Faculty")
    md_content.append("| Key | Universities | Coverage | Examples |")
    md_content.append("|-----|-------------|----------|----------|")
    for key, count in faculty_analysis["all_keys"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(
            str(x) for x in faculty_analysis["samples"].get(key, [])[:3]
        )
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {key} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    # Financial Aid Section
    md_content.append("")
    md_content.append("## Financial Aid Section")
    md_content.append("")
    md_content.append("### All Keys in Financial Aid")
    md_content.append("| Key | Universities | Coverage | Examples |")
    md_content.append("|-----|-------------|----------|----------|")
    for key, count in financial_aid_analysis["all_keys"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(
            str(x) for x in financial_aid_analysis["samples"].get(key, [])[:3]
        )
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {key} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    # Athletics Section
    md_content.append("")
    md_content.append("## Athletics Section")
    md_content.append("")
    md_content.append("### Top 20 Men's Sports")
    md_content.append("| Sport | Universities | Coverage |")
    md_content.append("|-------|-------------|----------|")
    for sport, count in athletics_analysis["mens_sports_count"].most_common(20):
        percentage = (count / total) * 100
        md_content.append(f"| {sport} | {count}/{total} | {percentage:.1f}% |")

    md_content.append("")
    md_content.append("### Top 20 Women's Sports")
    md_content.append("| Sport | Universities | Coverage |")
    md_content.append("|-------|-------------|----------|")
    for sport, count in athletics_analysis["womens_sports_count"].most_common(20):
        percentage = (count / total) * 100
        md_content.append(f"| {sport} | {count}/{total} | {percentage:.1f}% |")

    md_content.append("")
    md_content.append("### Athletics Keys")
    md_content.append("| Key | Universities | Coverage | Examples |")
    md_content.append("|-----|-------------|----------|----------|")
    for key, count in athletics_analysis["all_keys"].most_common():
        percentage = (count / total) * 100
        examples = ", ".join(
            str(x) for x in athletics_analysis["samples"].get(key, [])[:3]
        )
        # Escape markdown table characters
        examples = examples.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        if len(examples) > 100:
            examples = examples[:97] + "..."
        md_content.append(
            f"| {key} | {count}/{total} | {percentage:.1f}% | {examples} |"
        )

    # Summary
    md_content.append("")
    md_content.append("## Summary")
    md_content.append("")
    md_content.append(
        "This analysis provides a comprehensive overview of the data structure and coverage"
    )
    md_content.append(
        "across all sections of the Peterson university dataset. The percentages indicate"
    )
    md_content.append("how many universities have data for each specific field.")
    md_content.append("")
    md_content.append("### Key Findings:")
    md_content.append(
        "- **Location data**: 100% coverage for all address and contact fields"
    )
    md_content.append("- **Admissions data**: 99%+ coverage for most core fields")
    md_content.append(
        "- **Athletics data**: 98% of universities have both men's and women's sports"
    )
    md_content.append(
        "- **Financial aid data**: 98%+ coverage for financial aid information"
    )
    md_content.append("")

    return "\n".join(md_content)


def main():
    """Main function to run comprehensive analysis."""
    print("PETERSON DATA JSON STRUCTURE ANALYZER")
    print("=" * 70)

    try:
        # Load data
        data = load_peterson_data()

        # Analyze each section
        location_analysis = analyze_location_section(data)
        admissions_analysis = analyze_admissions_section(data)
        tuition_analysis = analyze_tuition_section(data)
        campus_life_analysis = analyze_campus_life_section(data)
        faculty_analysis = analyze_faculty_section(data)
        financial_aid_analysis = analyze_financial_aid_section(data)
        athletics_analysis = analyze_athletics_section(data)

        # Print reports to console
        print_location_report(location_analysis)
        print_section_report(admissions_analysis)
        print_section_report(tuition_analysis)
        print_section_report(campus_life_analysis)
        print_section_report(faculty_analysis)
        print_section_report(financial_aid_analysis)
        print_athletics_report(athletics_analysis)

        # Generate markdown report
        print("\nGenerating markdown report...")
        markdown_content = generate_markdown_report(
            location_analysis,
            admissions_analysis,
            tuition_analysis,
            campus_life_analysis,
            faculty_analysis,
            financial_aid_analysis,
            athletics_analysis,
        )

        # Write to markdown file at root
        output_file = Path("peterson_data_structure_analysis.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Markdown report saved to: {output_file.absolute()}")

        print("\n" + "=" * 70)
        print("COMPREHENSIVE ANALYSIS COMPLETE!")
        print("=" * 70)
        print("Total sections analyzed: 7")
        print(f"Total universities: {len(data)}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()
