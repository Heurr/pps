from app import crud
from app.crud.product import CRUDProduct
from app.schemas.product import ProductDBSchema
from .base import BaseService


class ProductService(BaseService[CRUDProduct, ProductDBSchema]):
    def __init__(self):
        super().__init__(crud.product, "product", __name__)
