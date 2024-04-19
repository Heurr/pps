from enum import StrEnum


class LogFormatType(StrEnum):
    DEFAULT = "default"
    JSON_LOGGER = "jsonlogger"


class PriceType(StrEnum):
    REGULAR = "regular"
    DISCOUNT = "discount"
    MEMBERSHIP = "membership"


class CountryCode(StrEnum):
    BA = "BA"  # BOSNIA_AND_HERZEGOVINA
    BG = "BG"  # BULGARIA
    HR = "HR"  # CROATIA
    CZ = "CZ"  # CZECH
    HU = "HU"  # HUNGARY
    RO = "RO"  # ROMANIA
    RS = "RS"  # SERBIA
    SI = "SI"  # SLOVENIA
    SK = "SK"  # SLOVAKIA


class PlatformCode(StrEnum):
    HEUREKA = "heu"
    OCS = "ocs"
    CENEJE = "cen"


class StockInfo(StrEnum):
    IN_STOCK = "IN_STOCK"
    PREORDER = "PREORDER"
    OUT_OF_STOCK = "OUT_OF_STOCK"


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


class ProductPriceType(StrEnum):
    ALL_OFFERS = "ALL_OFFERS"
    MARKETPLACE = "MARKETPLACE"
    IN_STOCK = "IN_STOCK"
    IN_STOCK_CERTIFIED = "IN_STOCK_CERTIFIED"


class Entity(StrEnum):
    SHOP = "shop"
    OFFER = "offer"
    BUYABLE = "buyable"
    AVAILABILITY = "availability"


class Action(StrEnum):
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"


PLATFORM_COUNTRY_MAP = {
    PlatformCode.HEUREKA: [CountryCode.CZ, CountryCode.SK],
    PlatformCode.OCS: [CountryCode.BG, CountryCode.HU, CountryCode.RO],
    PlatformCode.CENEJE: [CountryCode.BA, CountryCode.HR, CountryCode.RS, CountryCode.SI],
}
COUNTRY_PLATFORM_MAP = {
    country: platform
    for platform, countries in PLATFORM_COUNTRY_MAP.items()
    for country in countries
}


PRICE_PRECISION = 12
PRICE_SCALE = 2
DISCOUNT_PRECISION = 5
DISCOUNT_SCALE = 2
