from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SeasonStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"


class KvKSeason(BaseModel):
    """KvK Season information."""
    season_id: str = Field(..., description="Unique season identifier")
    season_name: str
    kingdom: str = "3584"
    start_date: datetime
    end_date: datetime
    duration_days: int = 40
    baseline_snapshot_id: Optional[str] = None
    status: SeasonStatus = SeasonStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)