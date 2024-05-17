import datetime as dt
from uuid import UUID

from pydantic import ConfigDict, Field

from app.constants import Action, CountryCode, CurrencyCode, ProductPriceType
from app.schemas.base import BaseModel


class ProductPriceCreateSchema(BaseModel):
    day: dt.date
    product_id: UUID
    country_code: CountryCode
    price_type: ProductPriceType
    min_price: float
    max_price: float
    currency_code: CurrencyCode
    updated_at: dt.datetime


class ProductPriceDBSchema(ProductPriceCreateSchema):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ProductPricePricesDropRabbitSchema(BaseModel):
    percentage: int = Field(
        ...,
        title="Percentage",
        description="The percentage drop in price",
        examples=[10, 20, 30],
    )

    baseline_price: float = Field(
        ...,
        title="Baseline Price",
        description="The original baseline price before the drop",
        examples=[100.0, 150.5, 200.75],
    )

    shop_count: int = Field(
        ...,
        title="Shop Count",
        description="Number of shops participating in the price drop",
        examples=[5, 10, 15],
    )


class ProductPricePricesRabbitSchema(BaseModel):
    min: float = Field(
        ...,
        title="Minimum Price",
        description="The minimum price for the product",
        examples=[19.99, 24.99, 29.99],
    )

    max: float = Field(
        ...,
        title="Maximum Price",
        description="The maximum price for the product",
        examples=[39.99, 44.99, 49.99],
    )

    price_drop: ProductPricePricesDropRabbitSchema | None = Field(
        default=None,
        title="Price Drop",
        description="Details of the price drop, if applicable",
    )
    type: ProductPriceType = Field(
        ...,
        title="Price Type",
        description="Type of price",
        examples=[ProductPriceType.MARKETPLACE.value, ProductPriceType.IN_STOCK.value],
    )


class ProductPriceRabbitSchema(BaseModel):
    product_id: UUID = Field(
        ...,
        title="Product ID",
        alias="productId",
        description="Product ID to which the price belongs to",
        examples=[
            [
                "bdc18828-bbda-483b-8a92-c1c6f587072f",
                "c5748761-0131-470e-b7c9-6767894149ff",
            ]
        ],
    )
    currency_code: CurrencyCode = Field(
        title="Currency Code",
        alias="currencyCode",
        description="Currency of price, e.g. USD, EUR",
        examples=[CurrencyCode.EUR.value, CurrencyCode.HUF.value],
    )
    country_code: CountryCode = Field(
        title="Country Code",
        alias="countryCode",
        description="Country of price, e.g. HU, CZ",
        examples=[CountryCode.HU.value, CountryCode.CZ.value],
    )
    prices: list[ProductPricePricesRabbitSchema] = Field(
        ...,
        title="Prices",
        description="List of prices for the product in each price type",
    )
    version: int = Field(
        ...,
        title="Version",
        description="Version number of the pricing schema, UNIX timestamp",
        examples=[1674655837, 1709192024, 1723129456],
    )

    action: Action = Field(
        ...,
        title="Action",
        description="Action to be performed, e.g. update",
        examples=[Action.UPDATE.value],
    )
