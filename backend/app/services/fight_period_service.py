"""
Fight Period Service

Manages fight periods for tracking real combat KP vs trade KP.
Provides CRUD operations and validation for fight periods.
"""
from app.database import Database
from app.cache import CacheService, CacheKeys
from app.models.fight_period import (
    FightPeriod, FightPeriodStatus,
    CreateFightPeriodRequest, UpdateFightPeriodRequest, EndFightPeriodRequest
)
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class FightPeriodService:
    """Service for managing fight periods"""

    async def create_fight_period(
        self,
        request: CreateFightPeriodRequest,
        admin_username: str
    ) -> Dict:
        """
        Create a new fight period

        Args:
            request: Fight period creation request
            admin_username: Username of admin creating the period

        Returns:
            Dict with success status and fight period data
        """
        try:
            collection = Database.get_collection("fight_periods")

            # Validate: check if fight number already exists for this season
            existing = await collection.find_one({
                "season_id": request.season_id,
                "fight_number": request.fight_number
            })

            if existing:
                return {
                    "success": False,
                    "error": f"Fight {request.fight_number} already exists for season {request.season_id}"
                }

            # Validate: start_time < end_time (if end_time provided)
            if request.end_time and request.start_time >= request.end_time:
                return {
                    "success": False,
                    "error": "start_time must be before end_time"
                }

            # Determine status
            now = datetime.utcnow()
            if request.end_time and request.end_time < now:
                status = FightPeriodStatus.COMPLETED
            elif request.start_time > now:
                status = FightPeriodStatus.UPCOMING
            else:
                status = FightPeriodStatus.ACTIVE

            # Create fight period document
            fight_period = {
                "season_id": request.season_id,
                "fight_number": request.fight_number,
                "fight_name": request.fight_name,
                "start_time": request.start_time,
                "end_time": request.end_time,
                "status": status.value,
                "description": request.description,
                "created_at": now,
                "updated_at": now,
                "created_by": admin_username
            }

            result = await collection.insert_one(fight_period)

            # Invalidate cache
            await self._invalidate_cache(request.season_id)

            logger.info(f"Created fight period: {request.season_id} - Fight {request.fight_number}")

            return {
                "success": True,
                "message": f"Fight period created: {request.fight_name}",
                "fight_period": {
                    **fight_period,
                    "_id": str(result.inserted_id)
                }
            }

        except Exception as e:
            logger.error(f"Failed to create fight period: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_fight_periods(self, season_id: str) -> List[Dict]:
        """
        Get all fight periods for a season, sorted by fight_number

        Args:
            season_id: KvK season ID

        Returns:
            List of fight period dicts
        """
        try:
            # Try cache first
            cache_key = CacheKeys.fight_periods(season_id)
            cached = await CacheService.get(cache_key)
            if cached is not None:
                return cached

            collection = Database.get_collection("fight_periods")
            cursor = collection.find({"season_id": season_id}).sort("fight_number", 1)
            fight_periods = await cursor.to_list(length=100)

            # Remove MongoDB _id
            for period in fight_periods:
                period.pop('_id', None)

            # Cache result
            await CacheService.set(cache_key, fight_periods, ttl=300)  # 5 minutes

            return fight_periods

        except Exception as e:
            logger.error(f"Failed to get fight periods: {e}", exc_info=True)
            return []

    async def get_fight_period(self, season_id: str, fight_number: int) -> Optional[Dict]:
        """
        Get a specific fight period

        Args:
            season_id: KvK season ID
            fight_number: Fight sequence number

        Returns:
            Fight period dict or None
        """
        try:
            collection = Database.get_collection("fight_periods")
            period = await collection.find_one({
                "season_id": season_id,
                "fight_number": fight_number
            })

            if period:
                period.pop('_id', None)

            return period

        except Exception as e:
            logger.error(f"Failed to get fight period: {e}", exc_info=True)
            return None

    async def update_fight_period(
        self,
        season_id: str,
        fight_number: int,
        request: UpdateFightPeriodRequest
    ) -> Dict:
        """
        Update an existing fight period

        Args:
            season_id: KvK season ID
            fight_number: Fight sequence number
            request: Update request with new values

        Returns:
            Dict with success status
        """
        try:
            collection = Database.get_collection("fight_periods")

            # Build update document (only include fields that are provided)
            update_doc = {"updated_at": datetime.utcnow()}

            if request.fight_name is not None:
                update_doc["fight_name"] = request.fight_name
            if request.start_time is not None:
                update_doc["start_time"] = request.start_time
            if request.end_time is not None:
                update_doc["end_time"] = request.end_time
            if request.description is not None:
                update_doc["description"] = request.description
            if request.status is not None:
                update_doc["status"] = request.status.value

            # Validate: start_time < end_time (if both present)
            existing = await self.get_fight_period(season_id, fight_number)
            if not existing:
                return {
                    "success": False,
                    "error": f"Fight period not found: {season_id} - Fight {fight_number}"
                }

            start_time = request.start_time or existing.get("start_time")
            end_time = request.end_time or existing.get("end_time")
            if start_time and end_time and start_time >= end_time:
                return {
                    "success": False,
                    "error": "start_time must be before end_time"
                }

            result = await collection.update_one(
                {"season_id": season_id, "fight_number": fight_number},
                {"$set": update_doc}
            )

            if result.modified_count == 0:
                return {
                    "success": False,
                    "error": "Fight period not found or no changes made"
                }

            # Invalidate cache
            await self._invalidate_cache(season_id)

            logger.info(f"Updated fight period: {season_id} - Fight {fight_number}")

            return {
                "success": True,
                "message": f"Fight period updated successfully",
                "modified_count": result.modified_count
            }

        except Exception as e:
            logger.error(f"Failed to update fight period: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def end_fight_period(
        self,
        season_id: str,
        fight_number: int,
        request: EndFightPeriodRequest
    ) -> Dict:
        """
        Mark a fight period as completed

        Args:
            season_id: KvK season ID
            fight_number: Fight sequence number
            request: End request with end_time

        Returns:
            Dict with success status
        """
        try:
            collection = Database.get_collection("fight_periods")

            # Validate fight exists
            existing = await self.get_fight_period(season_id, fight_number)
            if not existing:
                return {
                    "success": False,
                    "error": f"Fight period not found: {season_id} - Fight {fight_number}"
                }

            # Validate end_time > start_time
            if request.end_time <= existing["start_time"]:
                return {
                    "success": False,
                    "error": "end_time must be after start_time"
                }

            update_doc = {
                "end_time": request.end_time,
                "status": FightPeriodStatus.COMPLETED.value,
                "updated_at": datetime.utcnow()
            }

            if request.description:
                update_doc["description"] = request.description

            result = await collection.update_one(
                {"season_id": season_id, "fight_number": fight_number},
                {"$set": update_doc}
            )

            # Invalidate cache
            await self._invalidate_cache(season_id)

            logger.info(f"Ended fight period: {season_id} - Fight {fight_number}")

            return {
                "success": True,
                "message": f"Fight period ended successfully",
                "end_time": request.end_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to end fight period: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_fight_period(
        self,
        season_id: str,
        fight_number: int
    ) -> Dict:
        """
        Delete a fight period

        Args:
            season_id: KvK season ID
            fight_number: Fight sequence number

        Returns:
            Dict with success status
        """
        try:
            collection = Database.get_collection("fight_periods")

            result = await collection.delete_one({
                "season_id": season_id,
                "fight_number": fight_number
            })

            if result.deleted_count == 0:
                return {
                    "success": False,
                    "error": "Fight period not found"
                }

            # Invalidate cache
            await self._invalidate_cache(season_id)

            logger.info(f"Deleted fight period: {season_id} - Fight {fight_number}")

            return {
                "success": True,
                "message": "Fight period deleted successfully",
                "deleted_count": result.deleted_count
            }

        except Exception as e:
            logger.error(f"Failed to delete fight period: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def _invalidate_cache(self, season_id: str):
        """Invalidate all caches related to fight periods"""
        await CacheService.delete(CacheKeys.fight_periods(season_id))
        # Also invalidate leaderboard cache since fight periods affect KP calculations
        await CacheService.delete(CacheKeys.leaderboard(season_id, "kill_points_gained"))
        await CacheService.delete(CacheKeys.combined_leaderboard(season_id))


# Singleton instance
fight_period_service = FightPeriodService()
