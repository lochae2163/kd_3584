"""
Verified Deaths API Routes

Endpoints for uploading and managing verified T4/T5 death data.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from app.services.contribution_service import contribution_service
from app.services.auth_service import get_current_admin
from app.database import Database
from typing import List
import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/verified-deaths", tags=["Verified Deaths"])


@router.post("/upload/{kvk_season_id}")
async def upload_verified_deaths(
    kvk_season_id: str,
    file: UploadFile = File(...),
    current_admin: str = Depends(get_current_admin)
):
    """
    Upload Excel file with verified T4/T5 death data.

    Excel format:
    - Column 1: governor_id (required)
    - Column 2: t4_deaths (required)
    - Column 3: t5_deaths (required)
    - Column 4: notes (optional)

    The endpoint will:
    1. Parse the Excel file
    2. Validate all governor IDs exist
    3. Preview the data
    4. Update verified_deaths for each player
    5. Recalculate contribution scores
    """
    try:
        # Validate file is Excel
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls) are allowed"
            )

        # Read Excel file
        content = await file.read()
        excel_data = pd.read_excel(io.BytesIO(content))

        # Map common alternative column names to expected names
        column_mapping = {
            'Governor ID': 'governor_id',
            'governor_id': 'governor_id',
            'T4 Deaths': 't4_deaths',
            't4_deaths': 't4_deaths',
            'T5 Deaths': 't5_deaths',
            't5_deaths': 't5_deaths',
            'Notes': 'notes',
            'notes': 'notes',
        }
        excel_data.rename(
            columns={col: column_mapping[col] for col in excel_data.columns if col in column_mapping},
            inplace=True
        )

        # Validate required columns
        required_cols = ['governor_id', 't4_deaths', 't5_deaths']
        missing_cols = [col for col in required_cols if col not in excel_data.columns]

        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}. Expected: governor_id, t4_deaths, t5_deaths"
            )

        # Get current data to validate governor IDs
        current_col = Database.get_collection("current_data")
        current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

        if not current_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for season {kvk_season_id}"
            )

        # Create lookup of existing players
        existing_players = {p['governor_id']: p for p in current_data.get('players', [])}

        # Process each row
        results = {
            "total_rows": len(excel_data),
            "success_count": 0,
            "not_found_count": 0,
            "error_count": 0,
            "players_updated": [],
            "players_not_found": [],
            "errors": []
        }

        for idx, row in excel_data.iterrows():
            try:
                gov_id = str(row['governor_id']).strip()
                t4_deaths = int(row['t4_deaths'])
                t5_deaths = int(row['t5_deaths'])
                notes = str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else None

                # Skip players with 0/0 deaths - not verified
                if t4_deaths == 0 and t5_deaths == 0:
                    results['skipped_count'] = results.get('skipped_count', 0) + 1
                    continue

                # Validate player exists
                if gov_id not in existing_players:
                    results['not_found_count'] += 1
                    results['players_not_found'].append({
                        "governor_id": gov_id,
                        "row": idx + 2  # Excel row (header is row 1)
                    })
                    continue

                # Validate death counts
                if t4_deaths < 0 or t5_deaths < 0:
                    results['error_count'] += 1
                    results['errors'].append({
                        "governor_id": gov_id,
                        "row": idx + 2,
                        "error": "Death counts cannot be negative"
                    })
                    continue

                # Update verified deaths
                update_result = await contribution_service.update_verified_deaths(
                    kvk_season_id=kvk_season_id,
                    governor_id=gov_id,
                    t4_deaths=t4_deaths,
                    t5_deaths=t5_deaths,
                    notes=notes
                )

                if update_result.get('success'):
                    results['success_count'] += 1
                    player = existing_players[gov_id]
                    results['players_updated'].append({
                        "governor_id": gov_id,
                        "governor_name": player.get('governor_name', 'Unknown'),
                        "t4_deaths": t4_deaths,
                        "t5_deaths": t5_deaths,
                        "notes": notes
                    })
                else:
                    results['error_count'] += 1
                    results['errors'].append({
                        "governor_id": gov_id,
                        "row": idx + 2,
                        "error": update_result.get('error', 'Unknown error')
                    })

            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    "row": idx + 2,
                    "error": str(e)
                })

        # Get updated verification status
        status = await contribution_service.get_verification_status(kvk_season_id)

        return {
            "success": True,
            "message": f"Processed {results['total_rows']} rows: {results['success_count']} updated, {results.get('skipped_count', 0)} skipped (0/0 deaths), {results['not_found_count']} not found, {results['error_count']} errors",
            "kvk_season_id": kvk_season_id,
            "file_name": file.filename,
            "results": results,
            "verification_status": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload verified deaths: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@router.get("/unverified/{kvk_season_id}")
async def get_unverified_players(kvk_season_id: str):
    """Get list of players without verified death data."""
    current_col = Database.get_collection("current_data")
    current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

    if not current_data:
        raise HTTPException(status_code=404, detail=f"No data found for season {kvk_season_id}")

    players = current_data.get('players', [])
    unverified = [
        {
            "governor_id": p.get('governor_id'),
            "governor_name": p.get('governor_name', 'Unknown'),
            "power": p.get('power', 0),
        }
        for p in players
        if not p.get('verified_deaths', {}).get('verified', False)
    ]
    # Sort by power descending so highest power unverified show first
    unverified.sort(key=lambda x: x['power'], reverse=True)

    return {
        "success": True,
        "kvk_season_id": kvk_season_id,
        "unverified_count": len(unverified),
        "total_players": len(players),
        "players": unverified
    }


@router.get("/status/{kvk_season_id}")
async def get_verification_status(kvk_season_id: str):
    """
    Get verification status for a season.

    Returns:
    - Total players
    - Verified count
    - Unverified count
    - Verification percentage
    """
    result = await contribution_service.get_verification_status(kvk_season_id)

    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))

    return result


@router.get("/contribution-scores/{kvk_season_id}")
async def get_contribution_scores(
    kvk_season_id: str,
    use_verified_deaths: bool = Query(default=True),
    limit: int = Query(default=100, le=500)
):
    """
    Get contribution scores for all players.

    DKP Formula (based on GAINED/DELTA kills, not total):
    - T4 kills gained × 1
    - T5 kills gained × 2
    - T4 deaths × 4 (only when verified data exists)
    - T5 deaths × 8 (only when verified data exists)

    Note: Death scores are 0 for unverified players.
    Upload verified deaths to get complete contribution scores.

    Args:
        use_verified_deaths: Use verified death data if available
        limit: Max number of players to return

    Returns:
        List of players sorted by total_contribution_score
    """
    contributions = await contribution_service.calculate_all_contributions(
        kvk_season_id=kvk_season_id,
        use_verified_deaths=use_verified_deaths
    )

    # Limit results
    contributions = contributions[:limit]

    # Add ranks
    for idx, contribution in enumerate(contributions, 1):
        contribution.rank = idx

    return {
        "success": True,
        "kvk_season_id": kvk_season_id,
        "player_count": len(contributions),
        "use_verified_deaths": use_verified_deaths,
        "contributions": [c.dict() for c in contributions]
    }


@router.get("/player/{kvk_season_id}/{governor_id}")
async def get_player_verified_deaths(
    kvk_season_id: str,
    governor_id: str
):
    """
    Get verified death data for a specific player.

    Returns:
    - Verified death data if exists
    - Contribution score breakdown
    """
    current_col = Database.get_collection("current_data")
    current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

    if not current_data:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for season {kvk_season_id}"
        )

    # Find player
    player = None
    for p in current_data.get('players', []):
        if p['governor_id'] == governor_id:
            player = p
            break

    if not player:
        raise HTTPException(
            status_code=404,
            detail=f"Player {governor_id} not found"
        )

    # Calculate contribution
    contribution = contribution_service.calculate_player_contribution(player, use_verified_deaths=True)

    return {
        "success": True,
        "governor_id": governor_id,
        "governor_name": player.get('governor_name'),
        "verified_deaths": player.get('verified_deaths'),
        "contribution": contribution.dict()
    }


@router.delete("/{kvk_season_id}/{governor_id}")
async def delete_verified_deaths(
    kvk_season_id: str,
    governor_id: str,
    current_admin: str = Depends(get_current_admin)
):
    """
    Remove verified death data for a player.

    This will cause the player to fall back to estimated death scoring.
    """
    try:
        current_col = Database.get_collection("current_data")

        # Remove verified_deaths field
        result = await current_col.update_one(
            {
                "kvk_season_id": kvk_season_id,
                "players.governor_id": governor_id
            },
            {
                "$unset": {
                    "players.$[player].verified_deaths": ""
                }
            },
            array_filters=[{"player.governor_id": governor_id}]
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Player {governor_id} not found or no verified deaths to remove"
            )

        return {
            "success": True,
            "message": f"Verified deaths removed for {governor_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete verified deaths: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete verified deaths: {str(e)}"
        )
