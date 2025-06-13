"""
Metadata attribute definitions for Peterson university data.

This module contains the comprehensive AttributeInfo definitions used by
the SelfQueryRetriever to understand and filter Peterson university data.
"""

from langchain.chains.query_constructor.schema import AttributeInfo

# Define comprehensive metadata fields for SelfQueryRetriever
PETERSON_METADATA_FIELDS = [
    # Identity & Location (100% coverage)
    AttributeInfo(
        name="university_name",
        type="string",
        description="Name of the university",
    ),
    AttributeInfo(
        name="state",
        type="string",
        description="US state where university is located",
    ),
    AttributeInfo(
        name="city",
        type="string",
        description="City where university is located",
    ),
    AttributeInfo(
        name="region",
        type="string",
        description="US census region (Pacific, Mountain, West North Central, West South Central, East North Central, East South Central, South Atlantic, Mid-Atlantic, New England)",
    ),
    AttributeInfo(
        name="zip_code",
        type="string",
        description="ZIP code of university location",
    ),
    # Admissions & Selectivity (99%+ coverage)
    AttributeInfo(
        name="accept_rate",
        type="number",
        description="Acceptance rate as decimal 0-1 (e.g., 0.25 = 25%)",
    ),
    AttributeInfo(
        name="avg_high_school_gpa",
        type="number",
        description="Average high school GPA of admitted students",
    ),
    AttributeInfo(
        name="application_fee",
        type="integer",
        description="Application fee in dollars",
    ),
    # SAT Score Ranges (71%+ coverage)
    AttributeInfo(
        name="sat_verbal_25",
        type="integer",
        description="25th percentile SAT Critical Reading score",
    ),
    AttributeInfo(
        name="sat_verbal_75",
        type="integer",
        description="75th percentile SAT Critical Reading score",
    ),
    AttributeInfo(
        name="sat_verbal_avg",
        type="integer",
        description="Average SAT Critical Reading score",
    ),
    AttributeInfo(
        name="sat_math_25",
        type="integer",
        description="25th percentile SAT Math score",
    ),
    AttributeInfo(
        name="sat_math_75",
        type="integer",
        description="75th percentile SAT Math score",
    ),
    AttributeInfo(
        name="sat_math_avg",
        type="integer",
        description="Average SAT Math score",
    ),
    # ACT Score Ranges (71%+ coverage)
    AttributeInfo(
        name="act_composite_25",
        type="integer",
        description="25th percentile ACT Composite score",
    ),
    AttributeInfo(
        name="act_composite_75",
        type="integer",
        description="75th percentile ACT Composite score",
    ),
    AttributeInfo(
        name="act_composite_avg",
        type="integer",
        description="Average ACT Composite score",
    ),
    # Cost & Financial Aid (98%+ coverage)
    AttributeInfo(
        name="tuition_private",
        type="integer",
        description="Private tuition cost in dollars",
    ),
    AttributeInfo(
        name="tuition_in_state",
        type="integer",
        description="In-state tuition cost in dollars",
    ),
    AttributeInfo(
        name="tuition_out_of_state",
        type="integer",
        description="Out-of-state tuition cost in dollars",
    ),
    AttributeInfo(
        name="room_and_board",
        type="integer",
        description="Room and board cost in dollars",
    ),
    AttributeInfo(
        name="avg_financial_aid_package",
        type="integer",
        description="Average financial aid package in dollars",
    ),
    AttributeInfo(
        name="avg_grant_aid",
        type="integer",
        description="Average grant aid amount in dollars",
    ),
    AttributeInfo(
        name="percentage_need_receive_financial_aid",
        type="number",
        description="Percentage of students receiving financial aid as decimal 0-1",
    ),
    # Academic Environment (90%+ coverage)
    AttributeInfo(
        name="total_faculty",
        type="integer",
        description="Total number of faculty members",
    ),
    AttributeInfo(
        name="student_faculty_ratio",
        type="number",
        description="Student to faculty ratio (e.g., 15.0 means 15:1 ratio)",
    ),
    # Campus Housing (90%+ coverage)
    AttributeInfo(
        name="college_owned_housing",
        type="boolean",
        description="Whether college owns housing facilities",
    ),
    AttributeInfo(
        name="housing_required_first_year",
        type="boolean",
        description="Whether housing is required for first-year students",
    ),
    AttributeInfo(
        name="percent_students_on_campus",
        type="number",
        description="Percentage of students living on campus as decimal 0-1",
    ),
    # Student Demographics
    AttributeInfo(
        name="percent_women",
        type="number",
        description="Percentage of women students as decimal 0-1",
    ),
    # Athletics - Top Tier Sports (80%+ coverage)
    AttributeInfo(
        name="sport_basketball",
        type="boolean",
        description="Whether university offers basketball",
    ),
    AttributeInfo(
        name="sport_volleyball",
        type="boolean",
        description="Whether university offers volleyball",
    ),
    AttributeInfo(
        name="sport_soccer",
        type="boolean",
        description="Whether university offers soccer",
    ),
    AttributeInfo(
        name="sport_softball",
        type="boolean",
        description="Whether university offers softball",
    ),
    AttributeInfo(
        name="sport_cross_country",
        type="boolean",
        description="Whether university offers cross country running",
    ),
    # Athletics - High Coverage Sports (70-80% coverage)
    AttributeInfo(
        name="sport_baseball",
        type="boolean",
        description="Whether university offers baseball",
    ),
    AttributeInfo(
        name="sport_golf", type="boolean", description="Whether university offers golf"
    ),
    AttributeInfo(
        name="sport_tennis",
        type="boolean",
        description="Whether university offers tennis",
    ),
    AttributeInfo(
        name="sport_track",
        type="boolean",
        description="Whether university offers track and field",
    ),
    AttributeInfo(
        name="sport_football",
        type="boolean",
        description="Whether university offers football",
    ),
    # Athletics - Medium Coverage Sports (45-70% coverage)
    AttributeInfo(
        name="sport_lacrosse",
        type="boolean",
        description="Whether university offers lacrosse",
    ),
    AttributeInfo(
        name="sport_swimming",
        type="boolean",
        description="Whether university offers swimming and diving",
    ),
    AttributeInfo(
        name="sport_ice_hockey",
        type="boolean",
        description="Whether university offers ice hockey",
    ),
    # Athletics - General
    AttributeInfo(
        name="scholarship_sports_available",
        type="boolean",
        description="Whether any sports offer athletic scholarships",
    ),
]
