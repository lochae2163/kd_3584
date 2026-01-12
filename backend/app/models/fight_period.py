"""
Fight Period Models

Tracks time periods when real KvK fights occur vs trading periods.
Admins can mark fight start/end times to calculate real combat KP.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class FightPeriodStatus(str, Enum):
    """Fight period status"""
    UPCOMING = "upcoming"     # Fight hasn't started yet
    ACTIVE = "active"         # Fight is currently happening
    COMPLETED = "completed"   # Fight has ended


class CreateFightPeriodRequest(BaseModel):
    """Request to create a new fight period"""
    season_id: str = Field(..., description="KvK season ID (e.g., season_6)")
    fight_number: int = Field(..., ge=1, description="Fight sequence number (1, 2, 3, ...)")
    fight_name: str = Field(..., min_length=1, max_length=100, description="Descriptive name (e.g., 'Pass 1 - Kingdom 1234')")
    start_time: datetime = Field(..., description="When the fight started")
    end_time: Optional[datetime] = Field(None, description="When the fight ended (optional for ongoing fights)")
    description: Optional[str] = Field(None, max_length=500, description="Additional notes about this fight")


class UpdateFightPeriodRequest(BaseModel):
    """Request to update an existing fight period"""
    fight_name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[FightPeriodStatus] = None


class EndFightPeriodRequest(BaseModel):
    """Request to end a fight period"""
    end_time: datetime = Field(..., description="When the fight ended")
    description: Optional[str] = Field(None, max_length=500, description="Final notes about the fight")


class FightPeriod(BaseModel):
    """Fight period document structure"""
    season_id: str
    fight_number: int
    fight_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: FightPeriodStatus
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None  # Admin username who created this

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
