# Import all the tables. The sa_metadata import has to be first.
# It is helper file for "autogenerate" migration by Alembic


from .pg import sa_metadata  # noqa
from .tables.shop import shop_table  # noqa
from .tables.offer import offer_table  # noqa
from .tables.availability import availability_table  # noqa
from .tables.buyable import buyable_table  # noqa
from .tables.product_price import product_price_table  # noqa
from .tables.product_discount import product_discount_table  # noqa
from .tables.prodcut_price_history import product_price_history_table  # noqa
