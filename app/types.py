from uuid import UUID

from pendulum import Date

from app.constants import CountryCode

IdCountryPk = tuple[UUID, CountryCode]
IdCountryDatePk = tuple[UUID, CountryCode, Date]
