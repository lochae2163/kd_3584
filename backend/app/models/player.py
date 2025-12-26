from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PlayerStats(BaseModel):
    """Player statistics - matching CSV columns exactly."""
    power: int = 0
    kill_points: int = 0
    deads: int = 0
    t4_kills: int = 0
    t5_kills: int = 0


class Player(BaseModel):
    """Player profile."""
    governor_id: str = Field(..., description="Unique player ID")
    governor_name: str
    current_stats: PlayerStats
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PlayerDelta(BaseModel):
    """Change in stats between two snapshots."""
    governor_id: str
    governor_name: str
    delta_stats: PlayerStats


class PlayerKvKSummary(BaseModel):
    """Player's KvK contribution summary."""
    governor_id: str
    governor_name: str
    baseline_stats: PlayerStats
    current_stats: PlayerStats
    kvk_contribution: PlayerStats
    fights_participated: int = 0
    total_fights: int = 0
    kd_ratio: float = 0.0
    avg_kp_per_fight: float = 0.0