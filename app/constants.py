import enum


class LogFormatType(str, enum.Enum):
    DEFAULT = "default"
    JSON_LOGGER = "jsonlogger"


class CountryCode(str, enum.Enum):
    BOSNIA_AND_HERZEGOVINA = "BA"
    BULGARIA = "BG"
    CROATIA = "HR"
    CZECH = "CZ"
    HUNGARY = "HU"
    ROMANIA = "RO"
    SERBIA = "RS"
    SLOVENIA = "SI"
    SLOVAKIA = "SK"


class PlatformCode(str, enum.Enum):
    HEUREKA = "heu"
    OCS = "ocs"
    CENEJE = "cen"


class CurrencyCode(str, enum.Enum):
    BAM = "BAM"  # Bosnia and Herzegovina
    EUR = "EUR"  # Slovenia, Slovakia
    BGN = "BGN"  # Bulgaria
    HRK = "HRK"  # Croatia
    CZK = "CZK"  # Czech
    HUF = "HUF"  # Hungary
    RON = "RON"  # Romania
    RSD = "RSD"  # Serbia


class ProductStatus(str, enum.Enum):
    ENABLED = "ENABLED"
    VISIBLE = "VISIBLE"
    DISABLED = "DISABLED"


PLATFORM_COUNTRY_MAP = {
    PlatformCode.HEUREKA: [CountryCode.CZECH, CountryCode.SLOVAKIA],
    PlatformCode.OCS: [CountryCode.BULGARIA, CountryCode.HUNGARY, CountryCode.ROMANIA],
    PlatformCode.CENEJE: [
        CountryCode.BOSNIA_AND_HERZEGOVINA,
        CountryCode.CROATIA,
        CountryCode.SERBIA,
        CountryCode.SLOVENIA,
    ],
}
COUNTRY_PLATFORM_MAP = {
    country: platform
    for platform, countries in PLATFORM_COUNTRY_MAP.items()
    for country in countries
}


COUNTRY_CODE_STRING_LENGTH = 2
LOCAL_PRODUCT_ID_STRING_LENGTH = 32
