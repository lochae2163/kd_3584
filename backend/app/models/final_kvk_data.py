"""
Final KvK Data Models

Models for comprehensive end-of-KvK data upload.
"""
from pydantic import BaseModel, Field
from typing import Optional


class FinalKvKDataRow(BaseModel):
    """Single row from final KvK data Excel upload."""
    governor_id: str = Field(..., description="Player governor ID")
    account_type: str = Field(default="main", description="Account type: main, farm, or vacation")
    linked_to_main: Optional[str] = Field(default=None, description="Main account ID if this is a farm")
    t4_deaths: int = Field(ge=0, description="Verified T4 deaths")
    t5_deaths: int = Field(ge=0, description="Verified T5 deaths")
    notes: Optional[str] = Field(default=None, description="Admin notes")


class FinalKvKUploadResult(BaseModel):
    """Result of final KvK data upload."""
    success: bool
    message: str
    total_rows: int
    players_processed: int
    classifications_updated: int
    farms_linked: int
    deaths_verified: int
    errors: list[dict] = []
    warnings: list[dict] = []
