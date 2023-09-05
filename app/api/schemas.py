from pydantic import BaseModel


class HealthcheckStatus(BaseModel):
    status: str
    description: str
    connections: dict = {}
