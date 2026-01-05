"""
Contribution Scoring Service

Calculates player contribution scores using DKP formula:
- T4 kills × 1
- T5 kills × 2
- T4 deaths × 4
- T5 deaths × 8
"""
from app.database import Database
from app.models.verified_deaths import ContributionScore, VerifiedDeathsData
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ContributionService:
    """Service for calculating player contribution scores."""

    # DKP Weights
    T4_KILL_WEIGHT = 1
    T5_KILL_WEIGHT = 2
    T4_DEATH_WEIGHT = 4
    T5_DEATH_WEIGHT = 8
    ESTIMATED_DEATH_WEIGHT = 5  # Average of 4 and 8 for fallback

    def calculate_player_contribution(
        self,
        player: Dict,
        use_verified_deaths: bool = True
    ) -> ContributionScore:
        """
        Calculate contribution score for a single player.

        Args:
            player: Player data dict with stats and optional verified_deaths
            use_verified_deaths: Whether to use verified death data if available

        Returns:
            ContributionScore with all calculations
        """
        stats = player.get('stats', {})
        governor_id = player.get('governor_id', '')
        governor_name = player.get('governor_name', '')

        # Kill scores (from auto-detected data)
        t4_kills = stats.get('t4_kills', 0)
        t5_kills = stats.get('t5_kills', 0)

        t4_kill_score = t4_kills * self.T4_KILL_WEIGHT
        t5_kill_score = t5_kills * self.T5_KILL_WEIGHT
        total_kill_score = t4_kill_score + t5_kill_score

        # Death scores (only from verified data)
        verified_deaths = player.get('verified_deaths')
        has_verified = False
        t4_death_score = 0
        t5_death_score = 0

        if use_verified_deaths and verified_deaths and verified_deaths.get('verified'):
            # Use verified T4/T5 death breakdown
            t4_deaths = verified_deaths.get('t4_deaths', 0)
            t5_deaths = verified_deaths.get('t5_deaths', 0)

            t4_death_score = t4_deaths * self.T4_DEATH_WEIGHT
            t5_death_score = t5_deaths * self.T5_DEATH_WEIGHT
            has_verified = True
        else:
            # No verified data - death scores remain 0
            # Contribution score will only include kills until deaths are verified
            t4_death_score = 0
            t5_death_score = 0

        total_death_score = t4_death_score + t5_death_score
        total_contribution = total_kill_score + total_death_score

        return ContributionScore(
            governor_id=governor_id,
            governor_name=governor_name,
            t4_kill_score=t4_kill_score,
            t5_kill_score=t5_kill_score,
            t4_death_score=t4_death_score,
            t5_death_score=t5_death_score,
            total_kill_score=total_kill_score,
            total_death_score=total_death_score,
            total_contribution_score=total_contribution,
            has_verified_deaths=has_verified,
            using_estimated_deaths=False  # No longer using estimates
        )

    async def calculate_all_contributions(
        self,
        kvk_season_id: str,
        use_verified_deaths: bool = True
    ) -> List[ContributionScore]:
        """
        Calculate contribution scores for all players in a season.

        Args:
            kvk_season_id: Season ID
            use_verified_deaths: Whether to use verified death data

        Returns:
            List of ContributionScore sorted by total_contribution_score
        """
        current_col = Database.get_collection("current_data")
        current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

        if not current_data:
            return []

        players = current_data.get('players', [])
        contributions = []

        for player in players:
            contribution = self.calculate_player_contribution(player, use_verified_deaths)
            contributions.append(contribution)

        # Sort by total contribution score (descending)
        contributions.sort(key=lambda x: x.total_contribution_score, reverse=True)

        return contributions

    async def update_verified_deaths(
        self,
        kvk_season_id: str,
        governor_id: str,
        t4_deaths: int,
        t5_deaths: int,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Update verified death data for a player.

        Args:
            kvk_season_id: Season ID
            governor_id: Player's governor ID
            t4_deaths: Verified T4 deaths
            t5_deaths: Verified T5 deaths
            notes: Optional admin notes

        Returns:
            Dict with success status
        """
        try:
            from datetime import datetime

            current_col = Database.get_collection("current_data")
            current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

            if not current_data:
                return {
                    "success": False,
                    "error": f"No data found for season {kvk_season_id}"
                }

            # Find player
            player = None
            for p in current_data.get('players', []):
                if p['governor_id'] == governor_id:
                    player = p
                    break

            if not player:
                return {
                    "success": False,
                    "error": f"Player {governor_id} not found in season {kvk_season_id}"
                }

            # Create verified deaths data
            verified_deaths = {
                "t4_deaths": t4_deaths,
                "t5_deaths": t5_deaths,
                "verified": True,
                "verified_at": datetime.utcnow(),
                "notes": notes
            }

            # Update player document
            await current_col.update_one(
                {
                    "kvk_season_id": kvk_season_id,
                    "players.governor_id": governor_id
                },
                {
                    "$set": {
                        "players.$[player].verified_deaths": verified_deaths
                    }
                },
                array_filters=[{"player.governor_id": governor_id}]
            )

            logger.info(f"Updated verified deaths for {governor_id} in {kvk_season_id}: T4={t4_deaths}, T5={t5_deaths}")

            return {
                "success": True,
                "message": f"Verified deaths updated for {governor_id}",
                "governor_id": governor_id,
                "t4_deaths": t4_deaths,
                "t5_deaths": t5_deaths
            }

        except Exception as e:
            logger.error(f"Failed to update verified deaths: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_verification_status(
        self,
        kvk_season_id: str
    ) -> Dict:
        """
        Get verification status for a season.

        Returns:
            Dict with verification statistics
        """
        current_col = Database.get_collection("current_data")
        current_data = await current_col.find_one({"kvk_season_id": kvk_season_id})

        if not current_data:
            return {
                "success": False,
                "error": f"No data found for season {kvk_season_id}"
            }

        players = current_data.get('players', [])
        total_players = len(players)
        verified_count = sum(
            1 for p in players
            if p.get('verified_deaths', {}).get('verified', False)
        )
        unverified_count = total_players - verified_count

        verification_percentage = (verified_count / total_players * 100) if total_players > 0 else 0

        return {
            "success": True,
            "kvk_season_id": kvk_season_id,
            "total_players": total_players,
            "verified_count": verified_count,
            "unverified_count": unverified_count,
            "verification_percentage": round(verification_percentage, 2)
        }


# Create singleton instance
contribution_service = ContributionService()
