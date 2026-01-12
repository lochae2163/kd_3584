from fastapi import APIRouter, HTTPException, Query
from app.services.ml_service import ml_service
from app.services.player_classification_service import player_classification_service
from app.cache import CacheService, CacheKeys

router = APIRouter(prefix="/api", tags=["Public API"])


@router.get("/leaderboard")
async def get_leaderboard(
    kvk_season_id: str = Query(default="season_1"),
    sort_by: str = Query(default="kill_points_gained"),
    limit: int = Query(default=100, le=500)
):
    """
    Get leaderboard with deltas from baseline (with caching).

    Cache TTL: 1 minute (data updates frequently during KvK)

    - sort_by: kill_points_gained, fight_kp_gained, deads_gained, kill_points, power, t5_kills, t4_kills, deads
    - limit: max number of players to return (default: ranked by kill_points_gained)

    New fields (when fight periods are defined):
    - fight_kp_gained: Real combat KP (gained during marked fight periods only)
    - fight_kp_percentage: % of total KP from actual fighting
    """
    # Try cache first
    cache_key = CacheKeys.leaderboard(kvk_season_id, sort_by)
    cached = await CacheService.get(cache_key)
    if cached is not None:
        return cached

    # Cache miss - fetch from service
    result = await ml_service.get_leaderboard(
        kvk_season_id=kvk_season_id,
        sort_by=sort_by,
        limit=limit
    )

    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))

    # Cache successful result
    await CacheService.set(cache_key, result, ttl=60)  # 1 minute

    return result


@router.get("/player/{governor_id}")
async def get_player(
    governor_id: str,
    kvk_season_id: str = Query(default="season_1")
):
    """
    Get individual player stats with deltas (with caching).

    Cache TTL: 2 minutes (player stats update less frequently than leaderboard)
    """
    # Try cache first
    cache_key = CacheKeys.player(kvk_season_id, governor_id)
    cached = await CacheService.get(cache_key)
    if cached is not None:
        return cached

    # Cache miss - fetch from service
    result = await ml_service.get_player_stats(kvk_season_id, governor_id)

    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))

    # Cache successful result
    await CacheService.set(cache_key, result, ttl=120)  # 2 minutes

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


@router.get("/history")
async def get_upload_history(
    kvk_season_id: str = Query(default="season_1"),
    limit: int = Query(default=50, le=100)
):
    """
    Get upload history for a season (Phase 2A: Historical Tracking).
    Returns list of all uploads with summary data.
    """
    result = await ml_service.get_upload_history(kvk_season_id, limit)

    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))

    return result


@router.get("/player/{governor_id}/timeline")
async def get_player_timeline(
    governor_id: str,
    kvk_season_id: str = Query(default="season_1")
):
    """
    Get player progress timeline across all uploads (Phase 2A: Historical Tracking).
    Shows how a player's stats evolved over time.
    """
    result = await ml_service.get_player_timeline(kvk_season_id, governor_id)

    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))

    return result


@router.get("/leaderboard/combined")
async def get_combined_leaderboard(
    kvk_season_id: str = Query(default="season_1"),
    sort_by: str = Query(default="kill_points_gained"),
    limit: int = Query(default=100, le=500),
    include_farms: bool = Query(default=True)
):
    """
    Get combined leaderboard with main + farm account stats merged (with caching).

    Cache TTL: 1 minute (same as regular leaderboard)

    - Main accounts show combined stats (main + all linked farms)
    - Farm accounts are hidden (merged into their main)
    - Vacation accounts are excluded
    - Dead weight players can be optionally excluded

    Response includes farm details for expandable view
    """
    # Try cache first
    cache_key = CacheKeys.combined_leaderboard(kvk_season_id)
    cached = await CacheService.get(cache_key)
    if cached is not None:
        return cached

    # Cache miss - compute combined leaderboard
    # Get regular leaderboard
    leaderboard_result = await ml_service.get_leaderboard(
        kvk_season_id=kvk_season_id,
        sort_by=sort_by,
        limit=1000  # Get all players first
    )

    if not leaderboard_result.get('success'):
        raise HTTPException(status_code=404, detail=leaderboard_result.get('error'))

    players = leaderboard_result.get('leaderboard', [])

    # Get all players with classification
    all_classified = await player_classification_service.get_all_players_with_classification(kvk_season_id)

    # Create O(1) lookups for classification and players
    classification_map = {p['governor_id']: p for p in all_classified}
    player_lookup = {p['governor_id']: p for p in players}

    # Combine main + farms
    combined_players = []
    processed_farms = set()

    for player in players:
        gov_id = player['governor_id']
        classification = classification_map.get(gov_id, {})

        account_type = classification.get('account_type', 'main')
        is_dead_weight = classification.get('is_dead_weight', False)

        # Skip farm accounts (they're merged into main)
        if account_type == 'farm':
            continue

        # Skip vacation accounts
        if account_type == 'vacation':
            continue

        # Start with main account stats
        combined = {
            'governor_id': player['governor_id'],
            'governor_name': player['governor_name'],
            'account_type': account_type,
            'is_dead_weight': is_dead_weight,

            # Main stats
            'main_power': player['stats']['power'],
            'main_kill_points': player['stats']['kill_points'],
            'main_kill_points_gained': player['delta']['kill_points'],

            # Combined stats (start with main)
            'combined_power': player['stats']['power'],
            'combined_kill_points': player['stats']['kill_points'],
            'combined_deads': player['stats']['deads'],
            'combined_t4_kills': player['stats']['t4_kills'],
            'combined_t5_kills': player['stats']['t5_kills'],

            # Combined deltas
            'combined_power_gained': player['delta']['power'],
            'combined_kill_points_gained': player['delta']['kill_points'],
            'combined_deads_gained': player['delta']['deads'],
            'combined_t4_kills_gained': player['delta']['t4_kills'],
            'combined_t5_kills_gained': player['delta']['t5_kills'],

            'farm_count': 0,
            'farm_details': [],
            'rank': player.get('rank', 0)
        }

        # Add linked farms if this is a main account
        farm_ids = classification.get('farm_accounts', [])
        if farm_ids and include_farms:
            for farm_id in farm_ids:
                # Find farm using O(1) lookup instead of O(n) search
                farm_player = player_lookup.get(farm_id)
                if farm_player:
                    # Add farm stats to combined
                    combined['combined_power'] += farm_player['stats']['power']
                    combined['combined_kill_points'] += farm_player['stats']['kill_points']
                    combined['combined_deads'] += farm_player['stats']['deads']
                    combined['combined_t4_kills'] += farm_player['stats']['t4_kills']
                    combined['combined_t5_kills'] += farm_player['stats']['t5_kills']

                    combined['combined_power_gained'] += farm_player['delta']['power']
                    combined['combined_kill_points_gained'] += farm_player['delta']['kill_points']
                    combined['combined_deads_gained'] += farm_player['delta']['deads']
                    combined['combined_t4_kills_gained'] += farm_player['delta']['t4_kills']
                    combined['combined_t5_kills_gained'] += farm_player['delta']['t5_kills']

                    # Add to farm details
                    combined['farm_details'].append({
                        'governor_id': farm_player['governor_id'],
                        'governor_name': farm_player['governor_name'],
                        'power': farm_player['stats']['power'],
                        'kill_points': farm_player['stats']['kill_points'],
                        'kill_points_gained': farm_player['delta']['kill_points'],
                        't4_kills': farm_player['stats']['t4_kills'],
                        't5_kills': farm_player['stats']['t5_kills']
                    })

                    combined['farm_count'] = len(combined['farm_details'])
                    processed_farms.add(farm_id)

        combined_players.append(combined)

    # Sort by requested field
    sort_field_map = {
        'kill_points_gained': 'combined_kill_points_gained',
        'power': 'combined_power',
        'kill_points': 'combined_kill_points',
        't4_kills': 'combined_t4_kills',
        't5_kills': 'combined_t5_kills',
        'deads': 'combined_deads'
    }

    sort_field = sort_field_map.get(sort_by, 'combined_kill_points_gained')
    combined_players.sort(key=lambda x: x.get(sort_field, 0), reverse=True)

    # Re-rank
    for idx, player in enumerate(combined_players, 1):
        player['rank'] = idx

    # Apply limit
    combined_players = combined_players[:limit]

    result = {
        'success': True,
        'kvk_season_id': kvk_season_id,
        'player_count': len(combined_players),
        'total_farms_merged': len(processed_farms),
        'sort_by': sort_by,
        'players': combined_players,
        'baseline_date': leaderboard_result.get('baseline_date'),
        'current_date': leaderboard_result.get('current_date')
    }

    # Cache result
    await CacheService.set(cache_key, result, ttl=60)  # 1 minute

    return result