from typing import List, Optional, Union

from pydantic import BaseModel, Field


class Address(BaseModel):
    street: str = Field(..., description="Street address, e.g. '1 Ohio University'")
    city: str = Field(..., description="City name, e.g. 'Athens'")
    state: str = Field(..., description="State or province, e.g. 'OH'")
    zip_code: Optional[str] = Field(None, description="Postal code, e.g. '45701'")
    country: str = Field(..., description="Country, e.g. 'United States'")


class ContactInfo(BaseModel):
    phone: str = Field(..., description="Main phone number, e.g. '740-593-1000'")
    fax: Optional[str] = Field(None, description="Fax number, if present")
    email: Optional[str] = Field(None, description="Contact e-mail address, if present")
    name: Optional[str] = Field(None, description="Contact person's name, if present")
    title: Optional[str] = Field(None, description="Contact person's title, if present")


class LocationContact(BaseModel):
    address: Address
    contact: ContactInfo


class MajorProgram(BaseModel):
    name: str = Field(..., description="Program or major name")
    offers_associate: bool = Field(
        ...,
        description="True if an Associate degree is offered",
    )
    offers_bachelors: bool = Field(
        ...,
        description="True if a Bachelor's degree is offered",
    )


class MajorCategory(BaseModel):
    category: str = Field(
        ...,
        description="Top-level grouping, e.g. 'Biological And Biomedical Sciences'",
    )
    programs: List[MajorProgram]


class AdmissionStats(BaseModel):
    applied: int = Field(..., description="Total number of applications received")
    accepted: int = Field(..., description="Total number of offers made")
    enrolled: int = Field(..., description="Total number of students who enrolled")
    acceptance_rate: float = Field(
        ..., description="Overall acceptance rate as a percentage, e.g. 85.0"
    )


class GenderAdmissionStats(BaseModel):
    applied: int = Field(..., description="Applications from this gender")
    accepted: int = Field(..., description="Offers made to this gender")
    acceptance_rate: float = Field(
        ...,
        description="Acceptance rate for this gender as a percentage, e.g. 87.0",
    )


class GenderBreakdown(BaseModel):
    female: GenderAdmissionStats
    male: GenderAdmissionStats


class ApplicationInfo(BaseModel):
    application_fee: Optional[float] = Field(
        None,
        description="Application fee in USD, e.g. 50.0",
    )
    avg_high_school_gpa: Optional[float] = Field(
        None,
        description="Average entering GPA, e.g. 3.65",
    )


class AdmissionRequirement(BaseModel):
    category: str = Field(
        ...,
        description="Requirement type, e.g. 'Required', 'Recommended', etc.",
    )
    items: List[str] = Field(
        ...,
        description="List of requirement details, e.g. ['Transcript of high school record', 'Essay']",
    )


class ApplicationDeadline(BaseModel):
    type: str = Field(
        ...,
        description="Admission cycle, e.g. 'Fall freshmen', 'Transfer', etc.",
    )
    application_closing: Optional[str] = Field(
        None,
        description="Closing date or 'Not reported', e.g. 'February 1st'",
    )
    notification_date: Optional[str] = Field(
        None,
        description="Decision date or 'Not reported', e.g. 'September 15th'",
    )
    rolling_admissions: bool = Field(
        ...,
        description="True if rolling admissions applies",
    )


class TestScoreAccepted(BaseModel):
    test: str = Field(..., description="Test name, e.g. 'SAT Math'")
    avg_score: float = Field(..., description="Average score, e.g. 582")
    percentile_25: float = Field(..., description="25th percentile score")
    percentile_75: float = Field(..., description="75th percentile score")


class Admissions(BaseModel):
    overall: AdmissionStats
    by_gender: GenderBreakdown
    applying: ApplicationInfo
    requirements: List[AdmissionRequirement]
    application_deadlines: List[ApplicationDeadline]
    test_scores_accepted: List[TestScoreAccepted]


class TuitionFee(BaseModel):
    category: str = Field(
        ...,
        description="Label for the tuition line, e.g. 'In-state', 'Out-of-state', 'Private'",
    )
    amount: float = Field(..., description="Dollar amount, e.g. 12518.00")


class FeeItem(BaseModel):
    category: str = Field(
        ...,
        description="Label for the fee line, e.g. 'Room & board', 'Full-time student fees', etc.",
    )
    amount: float = Field(..., description="Dollar amount, e.g. 14162.00")


class OtherPaymentConsideration(BaseModel):
    name: str = Field(
        ...,
        description="What the row describes, e.g. 'Guaranteed tuition plan offered'",
    )
    value: Union[bool, List[str]] = Field(
        ...,
        description=(
            "Either a boolean (Yes/No) or a list of strings "
            "(e.g. ['Senior Citizens','Employees']) for waiver-groups"
        ),
    )


class TuitionAndFees(BaseModel):
    tuition: List[TuitionFee] = Field(
        ...,
        description="All the tuition lines under the Tuition icon",
    )
    fees: List[FeeItem] = Field(
        ...,
        description="All the line items under the Fees icon",
    )
    other_payment_considerations: Optional[List[OtherPaymentConsideration]] = Field(
        None,
        description=(
            'The "Other Payment Considerations" table, if present; '
            "each row becomes one object"
        ),
    )


class FinancialAidPackageStats(BaseModel):
    avg_financial_aid_package: float = Field(
        ...,
        description="Average total financial aid package, e.g. 11853.00",
    )
    avg_freshman_financial_aid_package: float = Field(
        ...,
        description="Average freshman financial aid package, e.g. 12735.00",
    )
    avg_international_financial_aid_package: Optional[float] = Field(
        None,
        description="Avg. international student package (if shown), e.g. 7228.00",
    )


class FinancialAidAmounts(BaseModel):
    avg_loan_aid: float = Field(..., description="Average loan aid, e.g. 3829.00")
    avg_grant_aid: float = Field(..., description="Average grant aid, e.g. 6404.00")
    avg_scholarship_and_grant_aid_awarded: float = Field(
        ...,
        description="Avg. scholarship/grant aid awarded, e.g. 9699.00",
    )


class FinancialAidCoverageStats(BaseModel):
    percentage_need_receive_financial_aid: float = Field(
        ...,
        description="% of students with need who receive aid, e.g. 100.0",
    )
    avg_percentage_of_financial_need_met: float = Field(
        ...,
        description="Avg. % of financial need met, e.g. 62.7",
    )
    percentage_students_need_fully_met: float = Field(
        ...,
        description="% of students whose need was fully met, e.g. 16.0",
    )


class FinancialAid(BaseModel):
    package_stats: FinancialAidPackageStats
    amounts: FinancialAidAmounts
    coverage_stats: FinancialAidCoverageStats


class SportOffering(BaseModel):
    sport: str = Field(..., description="Name of the sport, e.g. 'Basketball'")
    intramural: bool = Field(
        ...,
        description="True if offered intramurally, False otherwise",
    )
    intercollegiate: Optional[str] = Field(
        None,
        description=(
            "If offered intercollegiately, the level (e.g. 'Division 1'); "
            "nil or None if not offered"
        ),
    )
    scholarship: bool = Field(
        ...,
        description="True if athletic scholarships are available, False otherwise",
    )


class Athletics(BaseModel):
    mens_sports: List[SportOffering] = Field(
        ...,
        alias="Men's Sports",
        description="All men's sports offerings",
    )
    womens_sports: List[SportOffering] = Field(
        ...,
        alias="Women's Sports",
        description="All women's sports offerings",
    )


class Housing(BaseModel):
    college_owned_housing: Optional[bool] = Field(
        None,
        description=(
            "True if the school provides college-owned housing, "
            "False if explicitly No, or null if Not reported"
        ),
    )
    housing_requirements: Optional[bool] = Field(
        None,
        description=(
            "True if there are housing requirements, "
            "False if none, or null if Not reported"
        ),
    )
    housing_options: List[str] = Field(
        default_factory=list,
        description="List of available housing options, e.g. ['Co-ed housing','Disabled housing','Women-only housing']",
    )
    percent_undergrads_in_college_housing: Optional[float] = Field(
        None,
        description="Percentage of undergrad students living in college housing, as a number 0-100",
    )


class CampusLife(BaseModel):
    housing: Housing


class EmploymentStats(BaseModel):
    full_time: int = Field(..., description="Number of full-time faculty, e.g. 851")
    part_time: int = Field(..., description="Number of part-time faculty, e.g. 304")


class GenderFacultyStats(BaseModel):
    male: int = Field(..., description="Number of male faculty, e.g. 586")
    female: int = Field(..., description="Number of female faculty, e.g. 569")


class Faculty(BaseModel):
    total_faculty: int = Field(..., description="Total number of faculty, e.g. 1155")
    student_faculty_ratio: str = Field(
        ...,
        description="Student-to-faculty ratio, as shown e.g. '18:1'",
    )
    employment: EmploymentStats
    gender: GenderFacultyStats


class ExtractSchema(BaseModel):
    university_name: str = Field(
        ...,
        description="Name of the university, e.g. 'Harvard University', 'Ohio University', 'Georgia Institute of Technology'",
    )
    location_contact: LocationContact
    majors_and_degrees: List[MajorCategory]
    admissions: Admissions
    tuition_and_fees: TuitionAndFees
    financial_aid: FinancialAid
    athletics: Athletics
    campus_life: CampusLife
    faculty: Faculty
