from typing import Literal
from pydantic import BaseModel, Field

Paper = Literal["auto", "A4", "Legal"]
Edge = Literal["auto", "long", "short"]
SortOrder = Literal["name", "modified", "created"]
Duplex = bool | Literal["auto"]

class PrintIntent(BaseModel):
    action: Literal["print"] = "print"
    folder: str
    extensions: list[str] = Field(default_factory=lambda: [".pdf"])
    exclude_contains: list[str] = Field(default_factory=list)
    recursive: bool = True
    sort_order: SortOrder = "name"
    paper: Paper = "auto"
    duplex: Duplex = "auto"
    edge: Edge = "auto"
    copies: int = Field(default=1, ge=1, le=20)
    confirmation_required: bool = False
