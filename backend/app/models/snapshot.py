from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.player import PlayerStats


class SnapshotPlayer(BaseModel):
    """Player data in a snapshot."""
    governor_id: str
    governor_name: str
    stats: PlayerStats


class Snapshot(BaseModel):
    """Data snapshot from CSV upload."""
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    kvk_season_id: str
    fight_id: Optional[str] = None
    snapshot_type: str = Field(..., description="baseline, pre_fight, or post_fight")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_name: str
    player_count: int
    players: List[SnapshotPlayer]
    processed: bool = False
    uploaded_by: str = "admin"