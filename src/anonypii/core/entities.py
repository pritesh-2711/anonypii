"""
Entity taxonomy for anonypii.

Defines all 82 entity types from the PIIBench paper (Appendix A) with their
coarse group membership.  The EntityType enum is the single source of truth;
the coarse group lookup is derived from ENTITY_COARSE_MAP.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CoarseGroup(str, Enum):
    """Ten coarse entity categories from the PIIBench taxonomy."""

    FINANCIAL_ID = "FINANCIAL_ID"
    LOCATION = "LOCATION"
    PERSON_GROUP = "PERSON_GROUP"
    ORG_ROLE = "ORG_ROLE"
    TEMPORAL = "TEMPORAL"
    NETWORK = "NETWORK"
    MISC = "MISC"
    CONTACT = "CONTACT"
    CREDENTIAL = "CREDENTIAL"
    FINANCIAL_NER = "FINANCIAL_NER"


class EntityType(str, Enum):
    """
    All 82 fine-grained PII entity types retained in the corrected PIIBench
    preparation (Table A1 of the accompanying paper).
    """

    # FINANCIAL_ID
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"
    BBAN = "BBAN"
    BIC = "BIC"
    CREDIT_CARD = "CREDIT_CARD"
    CREDIT_CARD_NUMBER = "CREDIT_CARD_NUMBER"
    CREDIT_DEBIT_CARD = "CREDIT_DEBIT_CARD"
    CVV = "CVV"
    IBAN = "IBAN"
    SWIFT_BIC = "SWIFT_BIC"
    SWIFT_BIC_CODE = "SWIFT_BIC_CODE"
    BANK_ROUTING_NUMBER = "BANK_ROUTING_NUMBER"

    # LOCATION
    ADDRESS = "ADDRESS"
    CITY = "CITY"
    COORDINATE = "COORDINATE"
    COUNTRY = "COUNTRY"
    COUNTY = "COUNTY"
    LOC = "LOC"
    LOCAL_LATLNG = "LOCAL_LATLNG"
    POSTCODE = "POSTCODE"
    STATE = "STATE"
    STREET_ADDRESS = "STREET_ADDRESS"

    # PERSON_GROUP
    AGE = "AGE"
    FIRST_NAME = "FIRST_NAME"
    GENDER = "GENDER"
    LAST_NAME = "LAST_NAME"
    NAME = "NAME"
    PERSON = "PERSON"

    # ORG_ROLE
    COMPANY = "COMPANY"
    COMPANY_NAME = "COMPANY_NAME"
    JOB = "JOB"
    OCCUPATION = "OCCUPATION"
    ORG = "ORG"

    # TEMPORAL
    DATE = "DATE"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    DATE_TIME = "DATE_TIME"
    TIME = "TIME"

    # NETWORK
    DEVICE_IDENTIFIER = "DEVICE_IDENTIFIER"
    HTTP_COOKIE = "HTTP_COOKIE"
    IP_ADDRESS = "IP_ADDRESS"
    IPV4 = "IPV4"
    IPV6 = "IPV6"
    MAC_ADDRESS = "MAC_ADDRESS"
    URL = "URL"
    USERNAME = "USERNAME"
    USER_NAME = "USER_NAME"

    # MISC
    AMOUNT = "AMOUNT"
    BLOOD_TYPE = "BLOOD_TYPE"
    CC_SECURITY_CODE = "CC_SECURITY_CODE"
    CRYPTO_ADDRESS = "CRYPTO_ADDRESS"
    CURRENCY = "CURRENCY"
    EDUCATION_LEVEL = "EDUCATION_LEVEL"
    EMPLOYMENT_STATUS = "EMPLOYMENT_STATUS"
    LANGUAGE = "LANGUAGE"
    LICENSE_PLATE = "LICENSE_PLATE"
    MISC = "MISC"
    POLITICAL_VIEW = "POLITICAL_VIEW"
    RACE_ETHNICITY = "RACE_ETHNICITY"
    RELIGIOUS_BELIEF = "RELIGIOUS_BELIEF"
    SEXUALITY = "SEXUALITY"
    VEHICLE = "VEHICLE"
    VEHICLE_IDENTIFIER = "VEHICLE_IDENTIFIER"

    # CONTACT
    EMAIL = "EMAIL"
    FAX_NUMBER = "FAX_NUMBER"
    PHONE = "PHONE"
    PHONE_NUMBER = "PHONE_NUMBER"

    # CREDENTIAL
    ACCOUNT_PIN = "ACCOUNT_PIN"
    API_KEY = "API_KEY"
    BIOMETRIC_ID = "BIOMETRIC_ID"
    CERT_LICENSE_NUM = "CERT_LICENSE_NUM"
    CUSTOMER_ID = "CUSTOMER_ID"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    EMPLOYEE_ID = "EMPLOYEE_ID"
    HP_BENEF_NUMBER = "HP_BENEF_NUMBER"
    MEDICAL_RECORD = "MEDICAL_RECORD"
    NATIONAL_ID = "NATIONAL_ID"
    PASSPORT_NUMBER = "PASSPORT_NUMBER"
    PASSWORD = "PASSWORD"
    PIN = "PIN"
    SSN = "SSN"
    TAX_ID = "TAX_ID"
    UNIQUE_ID = "UNIQUE_ID"

    # FINANCIAL_NER
    FINANCIAL_ENTITY = "FINANCIAL_ENTITY"


# ---------------------------------------------------------------------------
# Coarse group membership map
# ---------------------------------------------------------------------------

ENTITY_COARSE_MAP: dict[EntityType, CoarseGroup] = {
    # FINANCIAL_ID
    EntityType.ACCOUNT_NUMBER: CoarseGroup.FINANCIAL_ID,
    EntityType.BBAN: CoarseGroup.FINANCIAL_ID,
    EntityType.BIC: CoarseGroup.FINANCIAL_ID,
    EntityType.CREDIT_CARD: CoarseGroup.FINANCIAL_ID,
    EntityType.CREDIT_CARD_NUMBER: CoarseGroup.FINANCIAL_ID,
    EntityType.CREDIT_DEBIT_CARD: CoarseGroup.FINANCIAL_ID,
    EntityType.CVV: CoarseGroup.FINANCIAL_ID,
    EntityType.IBAN: CoarseGroup.FINANCIAL_ID,
    EntityType.SWIFT_BIC: CoarseGroup.FINANCIAL_ID,
    EntityType.SWIFT_BIC_CODE: CoarseGroup.FINANCIAL_ID,
    EntityType.BANK_ROUTING_NUMBER: CoarseGroup.FINANCIAL_ID,
    # LOCATION
    EntityType.ADDRESS: CoarseGroup.LOCATION,
    EntityType.CITY: CoarseGroup.LOCATION,
    EntityType.COORDINATE: CoarseGroup.LOCATION,
    EntityType.COUNTRY: CoarseGroup.LOCATION,
    EntityType.COUNTY: CoarseGroup.LOCATION,
    EntityType.LOC: CoarseGroup.LOCATION,
    EntityType.LOCAL_LATLNG: CoarseGroup.LOCATION,
    EntityType.POSTCODE: CoarseGroup.LOCATION,
    EntityType.STATE: CoarseGroup.LOCATION,
    EntityType.STREET_ADDRESS: CoarseGroup.LOCATION,
    # PERSON_GROUP
    EntityType.AGE: CoarseGroup.PERSON_GROUP,
    EntityType.FIRST_NAME: CoarseGroup.PERSON_GROUP,
    EntityType.GENDER: CoarseGroup.PERSON_GROUP,
    EntityType.LAST_NAME: CoarseGroup.PERSON_GROUP,
    EntityType.NAME: CoarseGroup.PERSON_GROUP,
    EntityType.PERSON: CoarseGroup.PERSON_GROUP,
    # ORG_ROLE
    EntityType.COMPANY: CoarseGroup.ORG_ROLE,
    EntityType.COMPANY_NAME: CoarseGroup.ORG_ROLE,
    EntityType.JOB: CoarseGroup.ORG_ROLE,
    EntityType.OCCUPATION: CoarseGroup.ORG_ROLE,
    EntityType.ORG: CoarseGroup.ORG_ROLE,
    # TEMPORAL
    EntityType.DATE: CoarseGroup.TEMPORAL,
    EntityType.DATE_OF_BIRTH: CoarseGroup.TEMPORAL,
    EntityType.DATE_TIME: CoarseGroup.TEMPORAL,
    EntityType.TIME: CoarseGroup.TEMPORAL,
    # NETWORK
    EntityType.DEVICE_IDENTIFIER: CoarseGroup.NETWORK,
    EntityType.HTTP_COOKIE: CoarseGroup.NETWORK,
    EntityType.IP_ADDRESS: CoarseGroup.NETWORK,
    EntityType.IPV4: CoarseGroup.NETWORK,
    EntityType.IPV6: CoarseGroup.NETWORK,
    EntityType.MAC_ADDRESS: CoarseGroup.NETWORK,
    EntityType.URL: CoarseGroup.NETWORK,
    EntityType.USERNAME: CoarseGroup.NETWORK,
    EntityType.USER_NAME: CoarseGroup.NETWORK,
    # MISC
    EntityType.AMOUNT: CoarseGroup.MISC,
    EntityType.BLOOD_TYPE: CoarseGroup.MISC,
    EntityType.CC_SECURITY_CODE: CoarseGroup.MISC,
    EntityType.CRYPTO_ADDRESS: CoarseGroup.MISC,
    EntityType.CURRENCY: CoarseGroup.MISC,
    EntityType.EDUCATION_LEVEL: CoarseGroup.MISC,
    EntityType.EMPLOYMENT_STATUS: CoarseGroup.MISC,
    EntityType.LANGUAGE: CoarseGroup.MISC,
    EntityType.LICENSE_PLATE: CoarseGroup.MISC,
    EntityType.MISC: CoarseGroup.MISC,
    EntityType.POLITICAL_VIEW: CoarseGroup.MISC,
    EntityType.RACE_ETHNICITY: CoarseGroup.MISC,
    EntityType.RELIGIOUS_BELIEF: CoarseGroup.MISC,
    EntityType.SEXUALITY: CoarseGroup.MISC,
    EntityType.VEHICLE: CoarseGroup.MISC,
    EntityType.VEHICLE_IDENTIFIER: CoarseGroup.MISC,
    # CONTACT
    EntityType.EMAIL: CoarseGroup.CONTACT,
    EntityType.FAX_NUMBER: CoarseGroup.CONTACT,
    EntityType.PHONE: CoarseGroup.CONTACT,
    EntityType.PHONE_NUMBER: CoarseGroup.CONTACT,
    # CREDENTIAL
    EntityType.ACCOUNT_PIN: CoarseGroup.CREDENTIAL,
    EntityType.API_KEY: CoarseGroup.CREDENTIAL,
    EntityType.BIOMETRIC_ID: CoarseGroup.CREDENTIAL,
    EntityType.CERT_LICENSE_NUM: CoarseGroup.CREDENTIAL,
    EntityType.CUSTOMER_ID: CoarseGroup.CREDENTIAL,
    EntityType.DRIVER_LICENSE: CoarseGroup.CREDENTIAL,
    EntityType.EMPLOYEE_ID: CoarseGroup.CREDENTIAL,
    EntityType.HP_BENEF_NUMBER: CoarseGroup.CREDENTIAL,
    EntityType.MEDICAL_RECORD: CoarseGroup.CREDENTIAL,
    EntityType.NATIONAL_ID: CoarseGroup.CREDENTIAL,
    EntityType.PASSPORT_NUMBER: CoarseGroup.CREDENTIAL,
    EntityType.PASSWORD: CoarseGroup.CREDENTIAL,
    EntityType.PIN: CoarseGroup.CREDENTIAL,
    EntityType.SSN: CoarseGroup.CREDENTIAL,
    EntityType.TAX_ID: CoarseGroup.CREDENTIAL,
    EntityType.UNIQUE_ID: CoarseGroup.CREDENTIAL,
    # FINANCIAL_NER
    EntityType.FINANCIAL_ENTITY: CoarseGroup.FINANCIAL_NER,
}

ALL_ENTITY_TYPES: frozenset[EntityType] = frozenset(EntityType)


def coarse_group_of(entity_type: EntityType) -> CoarseGroup:
    return ENTITY_COARSE_MAP[entity_type]


def entity_types_for_group(group: CoarseGroup) -> frozenset[EntityType]:
    return frozenset(et for et, g in ENTITY_COARSE_MAP.items() if g == group)


# ---------------------------------------------------------------------------
# Entity dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Entity:
    """
    A single detected PII span.

    Attributes:
        text:       The raw text of the detected span.
        type:       The fine-grained EntityType.
        start:      Character offset of the span start (inclusive).
        end:        Character offset of the span end (exclusive).
        confidence: Model confidence score in [0.0, 1.0].
                    Always 1.0 for regex-based detectors.
    """

    text: str
    type: EntityType
    start: int
    end: int
    confidence: float

    @property
    def coarse_group(self) -> CoarseGroup:
        return ENTITY_COARSE_MAP[self.type]

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "type": self.type.value,
            "coarse_group": self.coarse_group.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }

    def __repr__(self) -> str:
        return (
            f"Entity(type={self.type.value!r}, text={self.text!r}, "
            f"[{self.start}:{self.end}], conf={self.confidence:.3f})"
        )
