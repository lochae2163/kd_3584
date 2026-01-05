"""
Final KvK Data Upload Routes

Comprehensive end-of-KvK data processing endpoint.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.player_classification_service import player_classification_service
from app.services.contribution_service import contribution_service
from app.services.season_service import season_service
from app.database import Database
import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/final-kvk", tags=["Final KvK"])


@router.post("/upload/{kvk_season_id}")
async def upload_final_kvk_data(
    kvk_season_id: str,
    file: UploadFile = File(...)
):
    """
    Upload comprehensive final KvK data (all-in-one).

    This endpoint processes:
    1. Account classification (main/farm/vacation)
    2. Farm linking to main accounts
    3. Verified T4/T5 death data
    4. Marks season as completed

    Excel format (required columns):
    - governor_id (required)
    - account_type (required: main, farm, or vacation)
    - linked_to_main (optional: governor_id of main account if farm)
    - t4_deaths (required: verified T4 deaths)
    - t5_deaths (required: verified T5 deaths)
    - notes (optional: admin notes)

    Use this at the END of KvK to finalize all data at once.
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

        # Validate required columns
        required_cols = ['governor_id', 'account_type', 't4_deaths', 't5_deaths']
        missing_cols = [col for col in required_cols if col not in excel_data.columns]

        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )

        # Get current data
        current_col = Database.get_collection("current_data")
        current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

        if not current_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for season {kvk_season_id}"
            )

        # Create lookup of existing players
        existing_players = {p['governor_id']: p for p in current_data.get('players', [])}

        # Track results
        results = {
            "total_rows": len(excel_data),
            "players_processed": 0,
            "classifications_updated": 0,
            "farms_linked": 0,
            "deaths_verified": 0,
            "errors": [],
            "warnings": []
        }

        # Phase 1: Process each row - classify accounts and update deaths
        for idx, row in excel_data.iterrows():
            try:
                gov_id = str(row['governor_id']).strip()
                account_type = str(row['account_type']).strip().lower()
                t4_deaths = int(row['t4_deaths'])
                t5_deaths = int(row['t5_deaths'])
                notes = str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else None

                # Validate player exists
                if gov_id not in existing_players:
                    results['warnings'].append({
                        "row": idx + 2,
                        "governor_id": gov_id,
                        "warning": "Player not found in current data - skipped"
                    })
                    continue

                # Validate account type
                if account_type not in ['main', 'farm', 'vacation']:
                    results['errors'].append({
                        "row": idx + 2,
                        "governor_id": gov_id,
                        "error": f"Invalid account_type: {account_type}. Must be main, farm, or vacation"
                    })
                    continue

                # Classify account
                classify_result = await player_classification_service.classify_player(
                    governor_id=gov_id,
                    kvk_season_id=kvk_season_id,
                    account_type=account_type,
                    is_dead_weight=False,
                    classification_notes=notes
                )

                if classify_result.get('success'):
                    results['classifications_updated'] += 1

                # Update verified deaths
                deaths_result = await contribution_service.update_verified_deaths(
                    kvk_season_id=kvk_season_id,
                    governor_id=gov_id,
                    t4_deaths=t4_deaths,
                    t5_deaths=t5_deaths,
                    notes=notes
                )

                if deaths_result.get('success'):
                    results['deaths_verified'] += 1

                results['players_processed'] += 1

            except Exception as e:
                results['errors'].append({
                    "row": idx + 2,
                    "error": str(e)
                })

        # Phase 2: Process farm linking (must be after classification)
        for idx, row in excel_data.iterrows():
            try:
                gov_id = str(row['governor_id']).strip()
                account_type = str(row['account_type']).strip().lower()

                # Skip if not a farm or player not found
                if account_type != 'farm' or gov_id not in existing_players:
                    continue

                # Check if linked_to_main is provided
                if 'linked_to_main' not in excel_data.columns or pd.isna(row.get('linked_to_main')):
                    results['warnings'].append({
                        "row": idx + 2,
                        "governor_id": gov_id,
                        "warning": "Farm account but no linked_to_main specified"
                    })
                    continue

                main_id = str(row['linked_to_main']).strip()

                # Link farm to main
                link_result = await player_classification_service.link_farm_to_main(
                    farm_governor_id=gov_id,
                    main_governor_id=main_id,
                    kvk_season_id=kvk_season_id
                )

                if link_result.get('success'):
                    results['farms_linked'] += 1
                else:
                    results['warnings'].append({
                        "row": idx + 2,
                        "governor_id": gov_id,
                        "warning": link_result.get('error', 'Farm linking failed')
                    })

            except Exception as e:
                results['warnings'].append({
                    "row": idx + 2,
                    "error": f"Farm linking error: {str(e)}"
                })

        # Get final statistics
        verification_status = await contribution_service.get_verification_status(kvk_season_id)
        classification_summary = await player_classification_service.get_all_players_with_classification(kvk_season_id)

        return {
            "success": True,
            "message": f"Final KvK data processed: {results['players_processed']} players updated",
            "kvk_season_id": kvk_season_id,
            "file_name": file.filename,
            "results": results,
            "verification_status": verification_status,
            "final_stats": {
                "total_players": len(classification_summary),
                "main_accounts": sum(1 for p in classification_summary if p.get('account_type') == 'main'),
                "farm_accounts": sum(1 for p in classification_summary if p.get('account_type') == 'farm'),
                "vacation_accounts": sum(1 for p in classification_summary if p.get('account_type') == 'vacation'),
                "farms_linked": results['farms_linked'],
                "deaths_verified": verification_status.get('verified_count', 0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload final KvK data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@router.post("/mark-complete/{kvk_season_id}")
async def mark_season_complete(kvk_season_id: str):
    """
    Mark season as completed (final data uploaded).

    This sets the season status to 'completed' which indicates:
    - All final data has been uploaded
    - Season is ready to be archived
    - No more regular uploads should occur

    Note: Season can still be edited until archived.
    """
    try:
        # Verify season exists
        season = await season_service.get_season(kvk_season_id)

        if not season:
            raise HTTPException(
                status_code=404,
                detail=f"Season {kvk_season_id} not found"
            )

        # Update season status
        seasons_col = Database.get_collection("seasons")
        result = await seasons_col.update_one(
            {"season_id": kvk_season_id},
            {
                "$set": {
                    "status": "completed",
                    "final_data_uploaded": True
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Season status not updated"
            )

        return {
            "success": True,
            "message": f"Season {kvk_season_id} marked as completed",
            "kvk_season_id": kvk_season_id,
            "status": "completed",
            "can_archive": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark season complete: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark season complete: {str(e)}"
        )
