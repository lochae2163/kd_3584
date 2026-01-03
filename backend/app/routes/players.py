from fastapi import APIRouter, HTTPException, Query
from app.services.ml_service import ml_service

router = APIRouter(prefix="/api", tags=["Public API"])


@router.get("/leaderboard")
async def get_leaderboard(
    kvk_season_id: str = Query(default="season_1"),
    sort_by: str = Query(default="kill_points_gained"),
    limit: int = Query(default=100, le=500)
):
    """
    Get leaderboard with deltas from baseline.

    - sort_by: kill_points_gained, deads_gained, kill_points, power, t5_kills, t4_kills, deads
    - limit: max number of players to return (default: ranked by kill_points_gained)
    """
    result = await ml_service.get_leaderboard(
        kvk_season_id=kvk_season_id,
        sort_by=sort_by,
        limit=limit
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))
    
    return result


@router.get("/player/{governor_id}")
async def get_player(
    governor_id: str,
    kvk_season_id: str = Query(default="season_1")
):
    """Get individual player stats with deltas."""
    result = await ml_service.get_player_stats(kvk_season_id, governor_id)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))
    
    return result


@router.get("/stats/summary")
async def get_summary(
    kvk_season_id: str = Query(default="season_1")
):
    """Get kingdom summary statistics."""
    result = await ml_service.get_leaderboard(kvk_season_id, limit=500)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))
    
    return {
        "kvk_season_id": kvk_season_id,
        "player_count": result.get('player_count', 0),
        "baseline_date": result.get('baseline_date'),
        "current_date": result.get('current_date'),
        "summary": result.get('summary', {}),
        "top_players": result.get('summary', {}).get('top_players', {})
    }