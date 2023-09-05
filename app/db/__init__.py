from app.config.settings import base_settings
from .pg import DBAdapter

db_adapter = DBAdapter(dsn=base_settings.postgres_db_dsn)

__all__ = ["db_adapter", "DBAdapter"]
