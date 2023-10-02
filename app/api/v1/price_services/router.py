from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from app.api.deps import get_db_conn
from app.api.response import ORJsonResponse
from app.api.v1.price_services.schemas import PriceServiceRequest, PriceServiceResponse
from app.exceptions import EntityNotFoundError
from app.services.product import ProductService

router = APIRouter(prefix="/v1", default_response_class=ORJsonResponse)
product_service = ProductService()


@router.post(
    "/product-price-history",
    description="Example price service endpoint that gets product name "
    "and legacy id from product one platform id",
)
async def product_detail(
    request: PriceServiceRequest, db_conn: AsyncConnection = Depends(get_db_conn)  # noqa
) -> PriceServiceResponse:
    product = await product_service.get(db_conn, request.product_id)
    if product is None:
        raise EntityNotFoundError()
    return PriceServiceResponse(
        product_name=product.name, product_local_id=product.local_product_id
    )
