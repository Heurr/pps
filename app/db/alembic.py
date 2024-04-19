# Import all the tables. The sa_metadata import has to be first.
# It is helper file for "autogenerate" migration by Alembic


from .pg import sa_metadata  # noqa
from .tables.shop import shop_table  # noqa
from .tables.offer import offer_table  # noqa
