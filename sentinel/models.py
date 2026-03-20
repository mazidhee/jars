from pydantic import BaseModel, Field
from typing import List

class Signal(BaseModel):
    symbol: str
    side: str
    order_type: str = Field(alias="orderType")
    qty: float 
    price: float
    timestamp: int = Field(alias="updatedTime")
    order_id: str = Field(alias="orderId")
    order_status: str = Field(alias="orderStatus")

class OrderWebsocketMessage(BaseModel):
    topic: str
    data: List[Signal]