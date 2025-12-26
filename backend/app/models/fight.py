from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FightType(str, Enum):
    PASS_4 = "pass4"
    PASS_7 = "pass7"
    ALTAR = "altar"
    OTHER = "other"


class FightStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"


class Fight(BaseModel):
    """Individual fight during KvK."""
    fight_id: str = Field(..., description="Unique fight identifier")
    kvk_season_id: str
    fight_name: str
    fight_type: FightType
    start_datetime: datetime
    end_datetime: datetime
    duration_hours: float
    before_snapshot_id: Optional[str] = None
    after_snapshot_id: Optional[str] = None
    status: FightStatus = FightStatus.UPCOMING
    created_at: datetime = Field(default_factory=datetime.utcnow)