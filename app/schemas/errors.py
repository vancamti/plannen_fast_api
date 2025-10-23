from typing import Optional

from pydantic import BaseModel


class NotFoundResponse(BaseModel):
    message: str
    details: Optional[str] = None