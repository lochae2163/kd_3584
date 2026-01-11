"""
Player classification API routes
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from app.services.player_classification_service import player_classification_service
from app.services.auth_service import get_current_admin
from app.models.player_classification import (
    ClassifyPlayerRequest,
    LinkFarmAccountRequest,
    UnlinkFarmAccountRequest,
    AccountType
)
from typing import List, Dict

router = APIRouter(prefix="/admin/players", tags=["Player Classification"])


@router.post("/classify")
async def classify_player(
    request: ClassifyPlayerRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Classify a player's account type

    - Mark as main, farm, or vacation account
    - Flag as dead weight if inactive
    - Add admin notes
    """
    result = await player_classification_service.classify_player(
        governor_id=request.governor_id,
        kvk_season_id=request.kvk_season_id,
        account_type=request.account_type,
        is_dead_weight=request.is_dead_weight,
        classification_notes=request.classification_notes
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.post("/link-farm")
async def link_farm_account(
    request: LinkFarmAccountRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Link a farm account to a main account

    - Farm must be classified as "farm" type
    - Main cannot be a farm account
    - Farm can only be linked to one main at a time
    """
    result = await player_classification_service.link_farm_to_main(
        farm_governor_id=request.farm_governor_id,
        main_governor_id=request.main_governor_id,
        kvk_season_id=request.kvk_season_id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.post("/unlink-farm")
async def unlink_farm_account(
    request: UnlinkFarmAccountRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Unlink a farm account from a main account

    - Removes farm from main's farm_accounts list
    - Clears linked_to_main on farm account
    """
    result = await player_classification_service.unlink_farm_from_main(
        farm_governor_id=request.farm_governor_id,
        main_governor_id=request.main_governor_id,
        kvk_season_id=request.kvk_season_id
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.get("/classification/{kvk_season_id}/{governor_id}")
async def get_player_classification(kvk_season_id: str, governor_id: str):
    """
    Get classification data for a specific player

    Returns account type, dead weight status, and farm linking info
    """
    classification = await player_classification_service.get_player_classification(
        governor_id=governor_id,
        kvk_season_id=kvk_season_id
    )

    if not classification:
        raise HTTPException(
            status_code=404,
            detail=f"Player {governor_id} not found in season {kvk_season_id}"
        )

    return {
        "success": True,
        "classification": classification
    }


@router.get("/all-with-classification/{kvk_season_id}")
async def get_all_players_with_classification(kvk_season_id: str):
    """
    Get all players with their classification data

    Returns list of all players with:
    - Basic stats (power, kill points, etc.)
    - Account type classification
    - Farm linking information
    - Dead weight status
    """
    players = await player_classification_service.get_all_players_with_classification(
        kvk_season_id=kvk_season_id
    )

    return {
        "success": True,
        "kvk_season_id": kvk_season_id,
        "player_count": len(players),
        "players": players
    }


@router.get("/stats/classification-summary/{kvk_season_id}")
async def get_classification_summary(kvk_season_id: str):
    """
    Get summary statistics of player classifications

    Returns counts of:
    - Main accounts
    - Farm accounts
    - Vacation accounts
    - Dead weight players
    - Unclassified players
    """
    players = await player_classification_service.get_all_players_with_classification(
        kvk_season_id=kvk_season_id
    )

    summary = {
        "total_players": len(players),
        "main_accounts": sum(1 for p in players if p["account_type"] == "main"),
        "farm_accounts": sum(1 for p in players if p["account_type"] == "farm"),
        "vacation_accounts": sum(1 for p in players if p["account_type"] == "vacation"),
        "dead_weight": sum(1 for p in players if p["is_dead_weight"]),
        "farms_linked": sum(1 for p in players if p.get("linked_to_main")),
        "mains_with_farms": sum(1 for p in players if len(p.get("farm_accounts", [])) > 0),
        "total_farm_links": sum(len(p.get("farm_accounts", [])) for p in players)
    }

    return {
        "success": True,
        "kvk_season_id": kvk_season_id,
        "summary": summary
    }
