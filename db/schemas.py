from pydantic import BaseModel


class RoutSchema(BaseModel):
    id: int
    rout_name: str
    rout_description: str
    base_price: int
    is_displayed: bool


