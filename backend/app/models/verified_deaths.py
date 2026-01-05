"""
Verified Deaths Models

Models for manual T4/T5 death data upload and verification.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VerifiedDeathsData(BaseModel):
    """Verified T4/T5 death data for a player."""
    t4_deaths: int = Field(ge=0, description="Verified T4 deaths")
    t5_deaths: int = Field(ge=0, description="Verified T5 deaths")
    verified: bool = Field(default=True, description="Whether data has been verified")
    verified_at: datetime = Field(default_factory=datetime.utcnow, description="When data was verified")
    notes: Optional[str] = Field(default=None, description="Admin notes about verification")


class UploadVerifiedDeathsRequest(BaseModel):
    """Request model for uploading verified deaths."""
    kvk_season_id: str = Field(..., description="KvK season ID")


class VerifiedDeathRow(BaseModel):
    """Single row from verified deaths Excel upload."""
    governor_id: str = Field(..., description="Player governor ID")
    t4_deaths: int = Field(ge=0, description="T4 deaths count")
    t5_deaths: int = Field(ge=0, description="T5 deaths count")
    notes: Optional[str] = Field(default=None, description="Optional notes")


class VerifiedDeathsUploadPreview(BaseModel):
    """Preview of verified deaths upload before processing."""
    total_rows: int
    players_found: int
    players_not_found: int
    preview_rows: list[dict]


class ContributionScore(BaseModel):
    """Player's calculated contribution score using verified deaths."""
    governor_id: str
    governor_name: str
    rank: int = Field(default=0, description="Rank by contribution score")

    # Kill scores
    t4_kill_score: int = Field(default=0, description="T4 kills × 1")
    t5_kill_score: int = Field(default=0, description="T5 kills × 2")

    # Death scores
    t4_death_score: int = Field(default=0, description="T4 deaths × 4")
    t5_death_score: int = Field(default=0, description="T5 deaths × 8")

    # Totals
    total_kill_score: int = Field(default=0, description="Sum of kill scores")
    total_death_score: int = Field(default=0, description="Sum of death scores")
    total_contribution_score: int = Field(default=0, description="Total DKP score")

    # Flags
    has_verified_deaths: bool = Field(default=False, description="Whether verified death data exists")
    using_estimated_deaths: bool = Field(default=False, description="Using total deaths fallback")
