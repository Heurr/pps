from enum import StrEnum


class LogFormatType(StrEnum):
    DEFAULT = "default"
    JSON_LOGGER = "jsonlogger"


class PriceType(StrEnum):
    REGULAR = "REGULAR"
    DISCOUNT = "DISCOUNT"
    MEMBERSHIP = "MEMBERSHIP"


class CountryCode(StrEnum):
    BOSNIA_AND_HERZEGOVINA = "BA"
    BULGARIA = "BG"
    CROATIA = "HR"
    CZECH = "CZ"
    HUNGARY = "HU"
    ROMANIA = "RO"
    SERBIA = "RS"
    SLOVENIA = "SI"
    SLOVAKIA = "SK"


class PlatformCode(StrEnum):
    HEUREKA = "heu"
    OCS = "ocs"
    CENEJE = "cen"


class StockInfo(StrEnum):
    IN_STOCK = "IN_STOCK"
    PREORDER = "PREORDER"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class ShopCertificate(StrEnum):
    BLUE = "BLUE"
    GOLD = "GOLD"


class CurrencyCode(StrEnum):
    BAM = "BAM"  # Bosnia and Herzegovina
    EUR = "EUR"  # Slovenia, Slovakia
    BGN = "BGN"  # Bulgaria
    HRK = "HRK"  # Croatia
    CZK = "CZK"  # Czech
    HUF = "HUF"  # Hungary
    RON = "RON"  # Romania
    RSD = "RSD"  # Serbia


class ProductStatus(StrEnum):
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
