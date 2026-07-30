from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    question: str

class ChatResponse(BaseModel):
    answer: str
    source: str
