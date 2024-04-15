from datetime import date
from uuid import UUID

from app.constants import CountryCode

IdCountryPk = tuple[UUID, CountryCode]
IdCountryDatePk = tuple[UUID, CountryCode, date]
