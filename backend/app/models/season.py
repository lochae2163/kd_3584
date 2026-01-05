"""
KvK Season model for managing multiple KvK seasons
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SeasonStatus(str, Enum):
    """Season lifecycle status"""
    PREPARING = "preparing"      # New season, setting up baseline
    ACTIVE = "active"            # KvK in progress, accepting uploads
    COMPLETED = "completed"      # KvK ended, final data uploaded
    ARCHIVED = "archived"        # Locked, read-only, historical


class KvKSeason(BaseModel):
    """
    KvK Season model

    Manages different Kingdom vs Kingdom events with complete data isolation
    """
    season_id: str = Field(..., description="Unique season identifier (e.g., 'season_1', 'season_2')")
    season_name: str = Field(..., description="Human-readable name (e.g., 'KvK 1 - Season of Conquest')")
    season_number: int = Field(..., description="Sequential number (1, 2, 3, etc.)")

    status: SeasonStatus = Field(default=SeasonStatus.PREPARING, description="Current season status")

    # Activation flags
    is_active: bool = Field(default=False, description="Currently active season (only ONE can be active)")
    is_archived: bool = Field(default=False, description="Locked for editing when True")

    # Dates
    start_date: Optional[datetime] = Field(default=None, description="KvK start date")
    end_date: Optional[datetime] = Field(default=None, description="KvK end date")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Season created timestamp")
    activated_at: Optional[datetime] = Field(default=None, description="When season became active")
    completed_at: Optional[datetime] = Field(default=None, description="When final data was uploaded")
    archived_at: Optional[datetime] = Field(default=None, description="When season was archived")

    # Data status flags
    has_baseline: bool = Field(default=False, description="Baseline data uploaded")
    has_current_data: bool = Field(default=False, description="At least one current data uploaded")
    final_data_uploaded: bool = Field(default=False, description="Final comprehensive data uploaded")

    # Metadata
    description: Optional[str] = Field(default=None, description="Season description or notes")
    kingdom_id: Optional[str] = Field(default=None, description="Kingdom identifier")
    enemy_kingdoms: list[str] = Field(default_factory=list, description="Enemy kingdom IDs")

    # Statistics
    total_uploads: int = Field(default=0, description="Number of current data uploads")
    player_count: int = Field(default=0, description="Total unique players")

    class Config:
        json_schema_extra = {
            "example": {
                "season_id": "season_1",
                "season_name": "KvK 1 - Season of Conquest",
                "season_number": 1,
                "status": "active",
                "is_active": True,
                "is_archived": False,
                "description": "First Kingdom vs Kingdom event",
                "kingdom_id": "3584"
            }
        }


class CreateSeasonRequest(BaseModel):
    """Request model for creating a new season"""
    season_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(default=None, description="Optional description")
    start_date: Optional[datetime] = Field(default=None, description="KvK start date")
    kingdom_id: Optional[str] = Field(default="3584", description="Kingdom identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "season_name": "KvK 2 - Season of Valor",
                "description": "Second KvK event against Kingdom 3585",
                "start_date": "2026-02-01T00:00:00Z",
                "kingdom_id": "3584"
            }
        }


class ActivateSeasonRequest(BaseModel):
    """Request model for activating a season"""
    season_id: str = Field(..., description="Season ID to activate")


class ArchiveSeasonRequest(BaseModel):
    """Request model for archiving a season"""
    season_id: str = Field(..., description="Season ID to archive")
    confirm: bool = Field(..., description="Confirmation flag (must be True)")
