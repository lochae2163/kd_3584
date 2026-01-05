"""
Player classification service

Handles account type classification and farm linking
"""
from app.database import Database
from app.models.player_classification import (
    AccountType,
    PlayerClassification,
    PlayerWithClassification,
    CombinedPlayerStats
)
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class PlayerClassificationService:
    """Service for managing player account classification"""

    async def classify_player(
        self,
        governor_id: str,
        kvk_season_id: str,
        account_type: AccountType,
        is_dead_weight: bool = False,
        classification_notes: Optional[str] = None
    ) -> Dict:
        """
        Classify a player account type

        Args:
            governor_id: Player's governor ID
            kvk_season_id: Season ID
            account_type: Account type (main, farm, vacation)
            is_dead_weight: Flag as dead weight (inactive)
            classification_notes: Admin notes

        Returns:
            Dict with success status
        """
        try:
            # Get player from current_data to verify they exist
            current_col = Database.get_collection("current_data")
            current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

            if not current_data:
                return {
                    "success": False,
                    "error": f"No data found for season {kvk_season_id}"
                }

            # Find player in current data
            player = None
            for p in current_data.get("players", []):
                if p["governor_id"] == governor_id:
                    player = p
                    break

            if not player:
                return {
                    "success": False,
                    "error": f"Player {governor_id} not found in season {kvk_season_id}"
                }

            # Update player classification in current_data
            # Handle both AccountType enum and string values
            account_type_str = account_type.value if hasattr(account_type, 'value') else account_type

            classification = {
                "account_type": account_type_str,
                "is_dead_weight": is_dead_weight,
                "classification_notes": classification_notes
            }

            # If changing to farm and previously had farm_accounts, clear them
            if account_type_str == "farm":
                classification["farm_accounts"] = []
                classification["linked_to_main"] = None  # Will be set when linking

            # If changing from farm to main/vacation, unlink from any main account
            if account_type != AccountType.FARM and player.get("linked_to_main"):
                # Find and update the main account
                main_gov_id = player["linked_to_main"]
                await self._remove_farm_from_main(main_gov_id, governor_id, kvk_season_id)
                classification["linked_to_main"] = None

            # Update the player document
            await current_col.update_one(
                {
                    "kvk_season_id": kvk_season_id,
                    "players.governor_id": governor_id
                },
                {
                    "$set": {
                        f"players.$[player].account_type": classification["account_type"],
                        f"players.$[player].is_dead_weight": classification["is_dead_weight"],
                        f"players.$[player].classification_notes": classification["classification_notes"],
                        f"players.$[player].farm_accounts": classification.get("farm_accounts", []),
                        f"players.$[player].linked_to_main": classification.get("linked_to_main")
                    }
                },
                array_filters=[{"player.governor_id": governor_id}]
            )

            logger.info(f"Classified player {governor_id} as {account_type.value} in {kvk_season_id}")

            return {
                "success": True,
                "message": f"Player {governor_id} classified as {account_type.value}",
                "governor_id": governor_id,
                "account_type": account_type.value,
                "is_dead_weight": is_dead_weight
            }

        except Exception as e:
            logger.error(f"Failed to classify player: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def link_farm_to_main(
        self,
        farm_governor_id: str,
        main_governor_id: str,
        kvk_season_id: str
    ) -> Dict:
        """
        Link a farm account to a main account

        Args:
            farm_governor_id: Farm account governor ID
            main_governor_id: Main account governor ID
            kvk_season_id: Season ID

        Returns:
            Dict with success status
        """
        try:
            current_col = Database.get_collection("current_data")
            current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

            if not current_data:
                return {
                    "success": False,
                    "error": f"No data found for season {kvk_season_id}"
                }

            # Verify both players exist
            farm_player = None
            main_player = None
            for p in current_data.get("players", []):
                if p["governor_id"] == farm_governor_id:
                    farm_player = p
                if p["governor_id"] == main_governor_id:
                    main_player = p

            if not farm_player:
                return {
                    "success": False,
                    "error": f"Farm account {farm_governor_id} not found"
                }

            if not main_player:
                return {
                    "success": False,
                    "error": f"Main account {main_governor_id} not found"
                }

            # Verify farm is classified as farm
            if farm_player.get("account_type") != "farm":
                return {
                    "success": False,
                    "error": f"Account {farm_governor_id} is not classified as a farm account"
                }

            # Verify main is not a farm
            if main_player.get("account_type") == "farm":
                return {
                    "success": False,
                    "error": f"Cannot link to {main_governor_id} because it is a farm account"
                }

            # If farm was previously linked to another main, unlink it
            if farm_player.get("linked_to_main") and farm_player["linked_to_main"] != main_governor_id:
                old_main_id = farm_player["linked_to_main"]
                await self._remove_farm_from_main(old_main_id, farm_governor_id, kvk_season_id)

            # Link farm to main
            await current_col.update_one(
                {
                    "kvk_season_id": kvk_season_id,
                    "players.governor_id": farm_governor_id
                },
                {
                    "$set": {
                        "players.$[player].linked_to_main": main_governor_id
                    }
                },
                array_filters=[{"player.governor_id": farm_governor_id}]
            )

            # Add farm to main's farm_accounts list
            await current_col.update_one(
                {
                    "kvk_season_id": kvk_season_id,
                    "players.governor_id": main_governor_id
                },
                {
                    "$addToSet": {
                        "players.$[player].farm_accounts": farm_governor_id
                    }
                },
                array_filters=[{"player.governor_id": main_governor_id}]
            )

            logger.info(f"Linked farm {farm_governor_id} to main {main_governor_id} in {kvk_season_id}")

            return {
                "success": True,
                "message": f"Farm {farm_governor_id} linked to main {main_governor_id}",
                "farm_governor_id": farm_governor_id,
                "main_governor_id": main_governor_id
            }

        except Exception as e:
            logger.error(f"Failed to link farm account: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def unlink_farm_from_main(
        self,
        farm_governor_id: str,
        main_governor_id: str,
        kvk_season_id: str
    ) -> Dict:
        """
        Unlink a farm account from a main account

        Args:
            farm_governor_id: Farm account governor ID
            main_governor_id: Main account governor ID
            kvk_season_id: Season ID

        Returns:
            Dict with success status
        """
        try:
            await self._remove_farm_from_main(main_governor_id, farm_governor_id, kvk_season_id)

            # Remove linked_to_main from farm
            current_col = Database.get_collection("current_data")
            await current_col.update_one(
                {
                    "kvk_season_id": kvk_season_id,
                    "players.governor_id": farm_governor_id
                },
                {
                    "$set": {
                        "players.$[player].linked_to_main": None
                    }
                },
                array_filters=[{"player.governor_id": farm_governor_id}]
            )

            logger.info(f"Unlinked farm {farm_governor_id} from main {main_governor_id} in {kvk_season_id}")

            return {
                "success": True,
                "message": f"Farm {farm_governor_id} unlinked from main {main_governor_id}",
                "farm_governor_id": farm_governor_id,
                "main_governor_id": main_governor_id
            }

        except Exception as e:
            logger.error(f"Failed to unlink farm account: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def _remove_farm_from_main(
        self,
        main_governor_id: str,
        farm_governor_id: str,
        kvk_season_id: str
    ):
        """Helper: Remove farm from main's farm_accounts list"""
        current_col = Database.get_collection("current_data")
        await current_col.update_one(
            {
                "kvk_season_id": kvk_season_id,
                "players.governor_id": main_governor_id
            },
            {
                "$pull": {
                    "players.$[player].farm_accounts": farm_governor_id
                }
            },
            array_filters=[{"player.governor_id": main_governor_id}]
        )

    async def get_player_classification(
        self,
        governor_id: str,
        kvk_season_id: str
    ) -> Optional[Dict]:
        """
        Get player classification data

        Args:
            governor_id: Player's governor ID
            kvk_season_id: Season ID

        Returns:
            Player classification dict or None
        """
        try:
            current_col = Database.get_collection("current_data")
            current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

            if not current_data:
                return None

            for p in current_data.get("players", []):
                if p["governor_id"] == governor_id:
                    return {
                        "governor_id": p["governor_id"],
                        "governor_name": p["governor_name"],
                        "account_type": p.get("account_type", "main"),
                        "is_dead_weight": p.get("is_dead_weight", False),
                        "linked_to_main": p.get("linked_to_main"),
                        "farm_accounts": p.get("farm_accounts", []),
                        "classification_notes": p.get("classification_notes")
                    }

            return None

        except Exception as e:
            logger.error(f"Failed to get player classification: {e}", exc_info=True)
            return None

    async def get_all_players_with_classification(
        self,
        kvk_season_id: str
    ) -> List[Dict]:
        """
        Get all players with their classification data

        Args:
            kvk_season_id: Season ID

        Returns:
            List of players with classification
        """
        try:
            current_col = Database.get_collection("current_data")
            current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

            if not current_data:
                return []

            players = []
            for p in current_data.get("players", []):
                players.append({
                    "governor_id": p["governor_id"],
                    "governor_name": p["governor_name"],
                    "power": p["stats"]["power"],
                    "kill_points": p["stats"]["kill_points"],
                    "kill_points_gained": p["delta"]["kill_points"],
                    "account_type": p.get("account_type", "main"),
                    "is_dead_weight": p.get("is_dead_weight", False),
                    "linked_to_main": p.get("linked_to_main"),
                    "farm_accounts": p.get("farm_accounts", []),
                    "classification_notes": p.get("classification_notes"),
                    "rank": p.get("rank", 0)
                })

            return players

        except Exception as e:
            logger.error(f"Failed to get players with classification: {e}", exc_info=True)
            return []


# Create singleton instance
player_classification_service = PlayerClassificationService()
