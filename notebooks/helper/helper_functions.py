import pandas as pd

# Define mapping dictionaries
withdrawal_reason_map = {
    # Graduated / Academic Completion
    "Year End": "Graduated/Completed",
    "High School Graduation": "Graduated/Completed",
    "Advanced to another school in district": "Graduated/Completed",
    # Transfers
    "SB10 Public Schools Transfer": "Transfer",
    "SB10 Private Schools Tranfer": "Transfer",
    "SB10 State Schools Transfer": "Transfer",
    "School Choice Transfer": "Transfer",
    "USCO": "Transfer",
    "Transfer to Another Public GA School": "Transfer",
    "Transferred Out of State": "Transfer",
    "Transferred Out of Country": "Transfer",
    "Transferred to Private School": "Transfer",
    "Transferred to a Dept of Defense School": "Transfer",
    "Transferred Under the Jurisdiction of DJJ": "Transfer",
    "Transferred to another school in district": "Transfer",
    "Department of Defense": "Transfer",
    # Legal / Disciplinary
    "Court Order or Legal Requirement": "Legal/Disciplinary",
    "Expelled": "Legal/Disciplinary",
    "Incarcerated": "Legal/Disciplinary",
    "Removed for Lack of Attendance": "Legal/Disciplinary",
    # Personal / Family Reasons
    "Marriage": "Personal/Family",
    "Pregnant/Parent": "Personal/Family",
    "Financial Hardship/Job-Related": "Personal/Family",
    "Low Grades/School Failure": "Personal/Family",
    "Serious Illness/Accident": "Personal/Family",
    "Displaced Due to Natural Disaster": "Personal/Family",
    # Other Education Paths
    "Adult Education/Post Secondary": "Alternative Education",
    "Attend Home School": "Alternative Education",
    "Withdrew to TCSG Dual Achieve Program": "Alternative Education",
    "No Longer Participating in Dexter Mosely": "Alternative Education",
    "Youth Challenge": "Alternative Education",
    "Summer Semester": "Alternative Education",
    # Other
    "Unknown": "Other",
    "Military": "Other",
    "Death": "Other",
    "Under the Age of Compulsory School Attendance": "Other",
}

enrollment_reason_map = {
    # New Students
    "Never attended school before": "New Enrollment",
    "Admitted from home school": "New Enrollment",
    # Re-Entries
    "Re-entered after withdrawal, this school this year": "Re-entry",
    "Re-entered - Other": "Re-entry",
    "Re-entered after illness": "Re-entry",
    "Re-entered after incarceration": "Re-entry",
    # Transfers In
    "Entered from a Department of Defense School": "Transfer",
    "Entered From Another State or U.S. Territory": "Transfer",
    "Entered From Another Country": "Transfer",
    "Transferred from another state or country": "Transfer",
    "Transferred from another GA district": "Transfer",
    "Transferred from private school": "Transfer",
    "Transfered/promoted within the same school system": "Transfer",
    # School Choice Programs
    "Admitted under SB10": "School Choice",
    "Admitted under School Choice": "School Choice",
    "Admitted under USCO": "School Choice",
    # Continuing Students
    "Continuing in same school": "Continuing",
}


# Function to apply groupings
def classify_reasons(df):
    df["EnrollmentGroup"] = (
        df["EnrollmentReasonDesc"].map(enrollment_reason_map).fillna("Unclassified")
    )
    df["WithdrawalGroup"] = (
        df["WithDrawalReasonDesc"].map(withdrawal_reason_map).fillna("Unclassified")
    )
    return df


# Function to join enrollment and withdrawal data
def join_enrollment_withdrawal(enrollment, enrollment_reason, withdrawal_reason):
    """
    Joins enrollment and withdrawal dataframes with reason descriptions and classifications.
    """
    # get the enrollment reason description
    enrol_reasons = pd.merge(
        enrollment,
        enrollment_reason[["EnrollmentReasonId", "EnrollmentReasonDesc"]],
        on="EnrollmentReasonId",
        how="left",
    )
    # get the withdrawal reason description
    registration = pd.merge(
        enrol_reasons,
        withdrawal_reason[["WithdrawalReasonId", "WithDrawalReasonDesc"]],
        on="WithdrawalReasonId",
        how="left",
    )
    # classify the reasons
    registration_reasons = classify_reasons(registration)
    # drop the columns that are not needed
    # registration_reasons = registration_reasons.drop(columns=['EnrollmentReasonDesc', 'WithDrawalReasonDesc'])
    # drop 'GradeLevel' column if it exists
    # GradeLevel is the same as 'GradeLevelId' but consist of both numeric and string values for some grades, complicating analysis
    if "GradeLevel" in registration_reasons.columns:
        registration_reasons = registration_reasons.drop(columns=["GradeLevel"])
    return registration_reasons


def get_school_info(df, school):
    """
    Joins school information with the enrollment dataframe.
    Args:
        df (DataFrame): The enrollment dataframe.
        school (DataFrame): The school information dataframe.
    """
    # Join school information
    df = pd.merge(df, school, on="SchoolId", how="left")
    return df
