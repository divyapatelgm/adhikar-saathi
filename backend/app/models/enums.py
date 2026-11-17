from enum import Enum

class TierType(str, Enum):
    VERIFIED = "verified"
    EXTRACTED = "extracted"

class SchemeStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"

class LevelType(str, Enum):
    CENTRAL = "central"
    STATE = "state"

class RuleOperator(str, Enum):
    EQ = "eq"
    NE = "ne"
    IN = "in"
    NOT_IN = "not_in"
    GTE = "gte"
    LTE = "lte"
    BETWEEN = "between"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"

class RuleField(str, Enum):
    AGE = "age"
    ANNUAL_INCOME = "annual_income"
    OCCUPATION = "occupation"
    CATEGORY = "category"
    GENDER = "gender"
    STATE = "state"
    DISTRICT = "district"
    OWNS_LAND = "owns_land"
    LAND_ACRES = "land_acres"
    IS_STUDENT = "is_student"
    EDUCATION_LEVEL = "education_level"
    DISABILITY = "disability"
    MARITAL_STATUS = "marital_status"
    BPL = "bpl"
    OTHER = "other"

class VerdictType(str, Enum):
    ELIGIBLE = "Eligible"
    LIKELY = "Likely"
    NOT_ELIGIBLE = "Not eligible"
    MAYBE = "Maybe"

class BenefitType(str, Enum):
    CASH = "cash"
    SUBSIDY = "subsidy"
    LOAN = "loan"
    INSURANCE = "insurance"
    SERVICE = "service"
    SCHOLARSHIP = "scholarship"
    OTHER = "other"

class ApplicationMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BOTH = "both"
