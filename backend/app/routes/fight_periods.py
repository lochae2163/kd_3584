"""
Fight Period API Routes

Admin endpoints for managing fight periods to track real combat KP vs trade KP.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.services.fight_period_service import fight_period_service
from app.services.auth_service import get_current_admin
from app.models.fight_period import (
    CreateFightPeriodRequest, UpdateFightPeriodRequest, EndFightPeriodRequest
)
from typing import List, Dict

# Admin-only fight period management routes
admin_router = APIRouter(prefix="/admin/fight-periods", tags=["Fight Period Management"])

# Public fight period info routes (read-only)
public_router = APIRouter(prefix="/api/fight-periods", tags=["Fight Periods"])


# ============== PUBLIC ROUTES (No Auth Required) ==============

@public_router.get("/{season_id}")
async def get_fight_periods(season_id: str):
    """
    Get all fight periods for a season

    Returns list of fight periods sorted by fight_number
    """
    fight_periods = await fight_period_service.get_fight_periods(season_id)

    return {
        "success": True,
        "season_id": season_id,
        "count": len(fight_periods),
        "fight_periods": fight_periods
    }


@public_router.get("/{season_id}/{fight_number}")
async def get_fight_period(season_id: str, fight_number: int):
    """
    Get a specific fight period

    Args:
        season_id: KvK season ID
        fight_number: Fight sequence number
    """
    fight_period = await fight_period_service.get_fight_period(season_id, fight_number)

    if not fight_period:
        raise HTTPException(
            status_code=404,
            detail=f"Fight period not found: {season_id} - Fight {fight_number}"
        )

    return {
        "success": True,
        "fight_period": fight_period
    }


# ============== ADMIN ROUTES (Auth Required) ==============

@admin_router.post("")
async def create_fight_period(
    request: CreateFightPeriodRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Create a new fight period

    Requires admin authentication.

    Example:
    ```json
    {
        "season_id": "season_6",
        "fight_number": 1,
        "fight_name": "Pass 1 - Kingdom 1234",
        "start_time": "2025-12-25T10:00:00",
        "end_time": "2025-12-28T23:59:59",
        "description": "First major battle of KvK 6"
    }
    ```
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Create fight period request received: {request}")

    result = await fight_period_service.create_fight_period(
        request,
        admin_username=current_admin
    )

    if not result['success']:
        logger.warning(f"Create fight period failed: {result['error']}")
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@admin_router.put("/{season_id}/{fight_number}")
async def update_fight_period(
    season_id: str,
    fight_number: int,
    request: UpdateFightPeriodRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Update an existing fight period

    Requires admin authentication.
    Only updates fields that are provided in the request.
    """
    result = await fight_period_service.update_fight_period(
        season_id,
        fight_number,
        request
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@admin_router.post("/{season_id}/{fight_number}/end")
async def end_fight_period(
    season_id: str,
    fight_number: int,
    request: EndFightPeriodRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Mark a fight period as completed

    Requires admin authentication.

    Example:
    ```json
    {
        "end_time": "2025-12-28T23:59:59",
        "description": "Final stats recorded"
    }
    ```
    """
    result = await fight_period_service.end_fight_period(
        season_id,
        fight_number,
        request
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@admin_router.delete("/{season_id}/{fight_number}")
async def delete_fight_period(
    season_id: str,
    fight_number: int,
    current_admin: str = Depends(get_current_admin)
):
    """
    Delete a fight period

    Requires admin authentication.
    Use with caution - this will affect KP calculations!
    """
    result = await fight_period_service.delete_fight_period(season_id, fight_number)

    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])

    return result
