from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Union

class ChatRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    question: str
    url: Optional[Union[HttpUrl, List[HttpUrl]]] = None

class ChatResponse(BaseModel):
    answer: str
    source: str
