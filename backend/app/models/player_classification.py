"""
Player classification models for account types and farm linking
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class AccountType(str, Enum):
    """Player account type classification"""
    MAIN = "main"
    FARM = "farm"
    VACATION = "vacation"  # Vacation ticket holder - excluded from contribution


class PlayerClassification(BaseModel):
    """Player account classification and linking metadata"""
    governor_id: str
    governor_name: str

    # Classification
    account_type: AccountType = AccountType.MAIN
    is_dead_weight: bool = False  # Manually flagged as inactive/dead weight

    # Farm linking
    linked_to_main: Optional[str] = None  # For farm accounts: main account governor_id
    farm_accounts: List[str] = Field(default_factory=list)  # For main accounts: list of farm governor_ids

    # Notes
    classification_notes: Optional[str] = None  # Admin notes about this player

    class Config:
        use_enum_values = True


class ClassifyPlayerRequest(BaseModel):
    """Request to classify a player account"""
    governor_id: str
    kvk_season_id: str
    account_type: AccountType
    is_dead_weight: bool = False
    classification_notes: Optional[str] = None

    class Config:
        use_enum_values = True


class LinkFarmAccountRequest(BaseModel):
    """Request to link a farm account to a main account"""
    farm_governor_id: str
    main_governor_id: str
    kvk_season_id: str


class UnlinkFarmAccountRequest(BaseModel):
    """Request to unlink a farm account from a main account"""
    farm_governor_id: str
    main_governor_id: str
    kvk_season_id: str


class PlayerWithClassification(BaseModel):
    """Player data combined with classification metadata"""
    governor_id: str
    governor_name: str

    # Stats
    power: int
    kill_points: int
    deads: int
    t4_kills: int
    t5_kills: int

    # Deltas (gains)
    power_gained: int = 0
    kill_points_gained: int = 0
    deads_gained: int = 0
    t4_kills_gained: int = 0
    t5_kills_gained: int = 0

    # Classification
    account_type: AccountType = AccountType.MAIN
    is_dead_weight: bool = False
    linked_to_main: Optional[str] = None
    farm_accounts: List[str] = Field(default_factory=list)
    classification_notes: Optional[str] = None

    class Config:
        use_enum_values = True


class CombinedPlayerStats(BaseModel):
    """Main account stats combined with all linked farms"""
    # Main account info
    governor_id: str
    governor_name: str
    account_type: AccountType = AccountType.MAIN

    # Combined stats (main + all farms)
    combined_power: int
    combined_kill_points: int
    combined_deads: int
    combined_t4_kills: int
    combined_t5_kills: int

    # Combined gains
    combined_power_gained: int
    combined_kill_points_gained: int
    combined_deads_gained: int
    combined_t4_kills_gained: int
    combined_t5_kills_gained: int

    # Main account individual stats
    main_power: int
    main_kill_points: int
    main_kill_points_gained: int

    # Farm details
    farm_count: int = 0
    farm_details: List[dict] = Field(default_factory=list)

    # Ranking (based on combined stats)
    rank: Optional[int] = None
    contribution_percentage: Optional[float] = None

    class Config:
        use_enum_values = True
