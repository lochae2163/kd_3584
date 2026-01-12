"""
Season management service

Handles KvK season lifecycle: creation, activation, completion, archiving
"""
from app.database import Database
from app.cache import CacheService, CacheKeys
from app.models.season import KvKSeason, SeasonStatus
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class SeasonService:
    """Service for managing KvK seasons"""

    async def create_season(self, season_name: str, description: Optional[str] = None,
                          start_date: Optional[datetime] = None, kingdom_id: str = "3584") -> Dict:
        """
        Create a new KvK season

        Args:
            season_name: Human-readable name
            description: Optional description
            start_date: KvK start date
            kingdom_id: Kingdom identifier

        Returns:
            Dict with success status and season data
        """
        try:
            seasons_col = Database.get_collection("kvk_seasons")

            # Get next season number
            latest_season = await seasons_col.find_one(
                sort=[("season_number", -1)]
            )
            next_number = (latest_season['season_number'] + 1) if latest_season else 1

            # Generate season_id
            season_id = f"season_{next_number}"

            # Check if season_id already exists
            existing = await seasons_col.find_one({"season_id": season_id})
            if existing:
                return {
                    "success": False,
                    "error": f"Season {season_id} already exists"
                }

            # Create season document
            season = KvKSeason(
                season_id=season_id,
                season_name=season_name,
                season_number=next_number,
                status=SeasonStatus.PREPARING,
                is_active=False,
                is_archived=False,
                start_date=start_date,
                description=description,
                kingdom_id=kingdom_id,
                created_at=datetime.utcnow()
            )

            # Insert to database
            await seasons_col.insert_one(season.model_dump())

            logger.info(f"Created season: {season_id} - {season_name}")

            return {
                "success": True,
                "message": f"Season {season_id} created successfully",
                "season": season.model_dump()
            }

        except Exception as e:
            logger.error(f"Failed to create season: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_active_season(self) -> Optional[Dict]:
        """
        Get the currently active season (with caching)

        Cache TTL: 5 minutes (active season changes infrequently)

        Returns:
            Active season dict or None
        """
        # Try cache first
        cache_key = CacheKeys.active_season()
        cached = await CacheService.get(cache_key)
        if cached is not None:
            return cached

        # Cache miss - fetch from database
        seasons_col = Database.get_collection("kvk_seasons")
        active_season = await seasons_col.find_one({"is_active": True})

        if active_season:
            # Remove MongoDB _id
            active_season.pop('_id', None)

        # Cache result (even if None)
        await CacheService.set(cache_key, active_season, ttl=300)  # 5 minutes

        return active_season

    async def get_all_seasons(self) -> List[Dict]:
        """
        Get all seasons, sorted by season_number descending

        Returns:
            List of season dicts
        """
        seasons_col = Database.get_collection("kvk_seasons")

        cursor = seasons_col.find().sort("season_number", -1)
        seasons = await cursor.to_list(length=None)

        # Remove MongoDB _id
        for season in seasons:
            season.pop('_id', None)

        return seasons

    async def get_season(self, season_id: str) -> Optional[Dict]:
        """
        Get a specific season by ID

        Args:
            season_id: Season identifier

        Returns:
            Season dict or None
        """
        seasons_col = Database.get_collection("kvk_seasons")
        season = await seasons_col.find_one({"season_id": season_id})

        if season:
            season.pop('_id', None)

        return season

    async def activate_season(self, season_id: str) -> Dict:
        """
        Activate a season (deactivate all others)

        Args:
            season_id: Season to activate

        Returns:
            Dict with success status
        """
        try:
            seasons_col = Database.get_collection("kvk_seasons")

            # Check if season exists
            season = await seasons_col.find_one({"season_id": season_id})
            if not season:
                return {
                    "success": False,
                    "error": f"Season {season_id} not found"
                }

            # Check if already archived
            if season.get('is_archived'):
                return {
                    "success": False,
                    "error": f"Cannot activate archived season {season_id}"
                }

            # Deactivate all other seasons
            await seasons_col.update_many(
                {},
                {"$set": {"is_active": False}}
            )

            # Activate this season
            await seasons_col.update_one(
                {"season_id": season_id},
                {
                    "$set": {
                        "is_active": True,
                        "status": SeasonStatus.ACTIVE.value,
                        "activated_at": datetime.utcnow()
                    }
                }
            )

            # Invalidate active season cache
            await CacheService.delete(CacheKeys.active_season())

            logger.info(f"Activated season: {season_id}")

            return {
                "success": True,
                "message": f"Season {season_id} activated successfully",
                "season_id": season_id
            }

        except Exception as e:
            logger.error(f"Failed to activate season: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def archive_season(self, season_id: str) -> Dict:
        """
        Archive a season (mark as read-only)

        Args:
            season_id: Season to archive

        Returns:
            Dict with success status
        """
        try:
            seasons_col = Database.get_collection("kvk_seasons")

            # Check if season exists
            season = await seasons_col.find_one({"season_id": season_id})
            if not season:
                return {
                    "success": False,
                    "error": f"Season {season_id} not found"
                }

            # Check if already archived
            if season.get('is_archived'):
                return {
                    "success": False,
                    "error": f"Season {season_id} is already archived"
                }

            # Verify final data uploaded
            if not season.get('final_data_uploaded'):
                logger.warning(f"Archiving season {season_id} without final data")

            # Archive the season
            await seasons_col.update_one(
                {"season_id": season_id},
                {
                    "$set": {
                        "is_archived": True,
                        "is_active": False,
                        "status": SeasonStatus.ARCHIVED.value,
                        "archived_at": datetime.utcnow()
                    }
                }
            )

            logger.info(f"Archived season: {season_id}")

            return {
                "success": True,
                "message": f"Season {season_id} archived successfully",
                "season_id": season_id
            }

        except Exception as e:
            logger.error(f"Failed to archive season: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def update_season_stats(self, season_id: str) -> Dict:
        """
        Update season statistics (upload count, player count, data flags)

        Args:
            season_id: Season to update

        Returns:
            Dict with success status
        """
        try:
            # Get baseline
            baseline_col = Database.get_collection("baselines")
            baseline = await baseline_col.find_one({"kvk_season_id": season_id})

            # Get upload history count
            history_col = Database.get_collection("upload_history")
            upload_count = await history_col.count_documents({"kvk_season_id": season_id})

            # Get current data
            current_col = Database.get_collection("current_data")
            current = await current_col.find_one({"kvk_season_id": season_id})

            # Update season
            seasons_col = Database.get_collection("kvk_seasons")
            await seasons_col.update_one(
                {"season_id": season_id},
                {
                    "$set": {
                        "has_baseline": baseline is not None,
                        "has_current_data": current is not None,
                        "total_uploads": upload_count,
                        "player_count": baseline.get('player_count', 0) if baseline else 0
                    }
                }
            )

            logger.info(f"Updated stats for season {season_id}: {upload_count} uploads")

            return {
                "success": True,
                "message": "Season stats updated"
            }

        except Exception as e:
            logger.error(f"Failed to update season stats: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def is_season_archived(self, season_id: str) -> bool:
        """
        Check if a season is archived (read-only)

        Args:
            season_id: Season to check

        Returns:
            True if archived, False otherwise
        """
        seasons_col = Database.get_collection("kvk_seasons")
        season = await seasons_col.find_one({"season_id": season_id})

        if not season:
            return False

        return season.get('is_archived', False)

    async def mark_final_data_uploaded(self, season_id: str) -> Dict:
        """
        Mark that final comprehensive data has been uploaded

        Args:
            season_id: Season ID

        Returns:
            Dict with success status
        """
        try:
            seasons_col = Database.get_collection("kvk_seasons")

            await seasons_col.update_one(
                {"season_id": season_id},
                {
                    "$set": {
                        "final_data_uploaded": True,
                        "completed_at": datetime.utcnow(),
                        "status": SeasonStatus.COMPLETED.value
                    }
                }
            )

            logger.info(f"Marked final data uploaded for season {season_id}")

            return {
                "success": True,
                "message": "Final data marked as uploaded"
            }

        except Exception as e:
            logger.error(f"Failed to mark final data: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def update_season_dates(self, season_id: str, start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict:
        """
        Update season start and end dates

        Args:
            season_id: Season ID
            start_date: ISO format date string (optional)
            end_date: ISO format date string (optional)

        Returns:
            Dict with success status
        """
        try:
            seasons_col = Database.get_collection("kvk_seasons")

            # Verify season exists
            season = await seasons_col.find_one({"season_id": season_id})
            if not season:
                return {
                    "success": False,
                    "error": f"Season {season_id} not found"
                }

            # Prepare update
            update_fields = {}

            if start_date is not None:
                # Parse and validate date
                if start_date:  # Non-empty string
                    try:
                        parsed_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        update_fields["start_date"] = parsed_date
                    except ValueError as e:
                        return {
                            "success": False,
                            "error": f"Invalid start_date format: {e}"
                        }
                else:
                    update_fields["start_date"] = None

            if end_date is not None:
                # Parse and validate date
                if end_date:  # Non-empty string
                    try:
                        parsed_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        update_fields["end_date"] = parsed_date
                    except ValueError as e:
                        return {
                            "success": False,
                            "error": f"Invalid end_date format: {e}"
                        }
                else:
                    update_fields["end_date"] = None

            if not update_fields:
                return {
                    "success": False,
                    "error": "No dates provided to update"
                }

            # Update season
            await seasons_col.update_one(
                {"season_id": season_id},
                {"$set": update_fields}
            )

            logger.info(f"Updated dates for season {season_id}: {update_fields}")

            return {
                "success": True,
                "message": "Season dates updated successfully",
                "updated_fields": {k: v.isoformat() if isinstance(v, datetime) else v
                                  for k, v in update_fields.items()}
            }

        except Exception as e:
            logger.error(f"Failed to update season dates: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Create singleton instance
season_service = SeasonService()
