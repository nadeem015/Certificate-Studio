from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr

class JobCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    recipients: list[RecipientInput] = Field(min_length=1, max_length=500)

class RecipientResult(BaseModel):
    id: int
    name: str
    email: str
    status: str
    error_message: str | None = None
    download_url: str | None = None

class JobResult(BaseModel):
    id: int
    event_name: str
    status: str
    total_count: int
    success_count: int
    failure_count: int
    recipients: list[RecipientResult]

class JobAccepted(BaseModel):
    job_id: int
    status: str
    message: str
