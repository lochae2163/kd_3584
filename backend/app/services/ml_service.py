"""
ML Service - High-level interface for ML operations
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.ml.data_model import kvk_model, KvKDataModel
from app.database import Database
import logging

logger = logging.getLogger(__name__)


class MLService:
    """
    Service class that interfaces between API routes and ML model.
    Handles database operations and model calls.
    """
    
    def __init__(self):
        self.model = kvk_model
    
    async def process_and_save_baseline(
        self,
        csv_content: str,
        kvk_season_id: str,
        file_name: str
    ) -> Dict:
        """
        Process baseline CSV and save to database.
        """
        # Process through ML model
        result = self.model.process_csv(csv_content)

        if not result['success']:
            return result

        # Create baseline document
        baseline_doc = {
            "type": "baseline",
            "kvk_season_id": kvk_season_id,
            "file_name": file_name,
            "timestamp": datetime.utcnow(),
            "player_count": result['player_count'],
            "players": result['players'],
            "processing_stats": result['processing_stats']
        }

        # Save to database (replace existing baseline for this season)
        collection = Database.get_collection("baselines")

        # Use upsert for atomic operation (prevents race conditions)
        update_result = await collection.update_one(
            {"kvk_season_id": kvk_season_id},
            {"$set": baseline_doc},
            upsert=True
        )

        return {
            "success": True,
            "message": f"Baseline saved with {result['player_count']} players",
            "player_count": result['player_count'],
            "kvk_season_id": kvk_season_id,
            "upserted": update_result.upserted_id is not None,
            "modified": update_result.modified_count > 0
        }

    async def process_and_save_baseline_excel(
        self,
        excel_bytes: bytes,
        kvk_season_id: str,
        file_name: str,
        kingdom_id: str = "3584"
    ) -> Dict:
        """
        Process baseline Excel file and save to database.
        Uses file date from Excel Summary sheet instead of upload time.
        """
        # Process through ML model
        result = self.model.process_excel(excel_bytes, kingdom_id)

        if not result['success']:
            return result

        # Use file_date from Excel if available, otherwise use upload time
        timestamp = result.get('file_date')
        if timestamp:
            # Convert ISO string back to datetime
            timestamp = datetime.fromisoformat(timestamp)
            logger.info(f"Using file date from Excel: {timestamp}")
        else:
            timestamp = datetime.utcnow()
            logger.warning("File date not found in Excel, using upload time")

        # Create baseline document
        baseline_doc = {
            "type": "baseline",
            "kvk_season_id": kvk_season_id,
            "file_name": file_name,
            "timestamp": timestamp,  # Use file date from Excel
            "player_count": result['player_count'],
            "players": result['players'],
            "processing_stats": result['processing_stats']
        }

        # Save to database (replace existing baseline for this season)
        collection = Database.get_collection("baselines")

        # Use upsert for atomic operation (prevents race conditions)
        update_result = await collection.update_one(
            {"kvk_season_id": kvk_season_id},
            {"$set": baseline_doc},
            upsert=True
        )

        return {
            "success": True,
            "message": f"Baseline saved with {result['player_count']} players from Excel",
            "player_count": result['player_count'],
            "kvk_season_id": kvk_season_id,
            "upserted": update_result.upserted_id is not None,
            "modified": update_result.modified_count > 0,
            "sheet_used": result['processing_stats'].get('sheet_used')
        }
    
    async def process_and_save_current(
        self,
        csv_content: str,
        kvk_season_id: str,
        file_name: str,
        description: str = ""
    ) -> Dict:
        """
        Process current data CSV, calculate deltas, save, and add to history.
        New players are automatically added to baseline with zero deltas.
        """
        # Process through ML model
        result = self.model.process_csv(csv_content)

        if not result['success']:
            return result

        # Get baseline for this season
        baselines = Database.get_collection("baselines")
        baseline = await baselines.find_one({"kvk_season_id": kvk_season_id})

        if not baseline:
            return {
                "success": False,
                "error": f"No baseline found for season {kvk_season_id}. Please upload baseline first."
            }

        # Calculate deltas
        players_with_deltas = self.model.calculate_all_deltas(
            baseline.get('players', []),
            result['players']
        )

        # Check if any new players were added and update baseline
        new_players = [p for p in players_with_deltas if p.get('newly_added_to_baseline', False)]
        if new_players:
            # Add new players to baseline
            baseline_players = baseline.get('players', [])
            for new_player in new_players:
                baseline_players.append({
                    "governor_id": new_player['governor_id'],
                    "governor_name": new_player['governor_name'],
                    "stats": new_player['stats']
                })

            # Update baseline in database
            await baselines.update_one(
                {"kvk_season_id": kvk_season_id},
                {
                    "$set": {
                        "players": baseline_players,
                        "player_count": len(baseline_players),
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated baseline with {len(new_players)} new players for season {kvk_season_id}")

        # Rank players by kill_points_gained (delta)
        ranked_players = self.model.rank_players(players_with_deltas, "kill_points_gained")

        # Calculate summary (using players_with_deltas to include delta info)
        summary = self.model.calculate_summary_stats(players_with_deltas)

        timestamp = datetime.utcnow()

        # Create current data document
        current_doc = {
            "type": "current",
            "kvk_season_id": kvk_season_id,
            "file_name": file_name,
            "description": description,
            "timestamp": timestamp,
            "player_count": result['player_count'],
            "players": ranked_players,
            "summary": summary,
            "processing_stats": result['processing_stats']
        }

        # Save to current_data (replace existing)
        current_collection = Database.get_collection("current_data")
        # Use upsert for atomic operation (prevents race conditions)
        await current_collection.update_one(
            {"kvk_season_id": kvk_season_id},
            {"$set": current_doc},
            upsert=True
        )

        # Also save to history (append, don't replace)
        # Include full player snapshots for historical tracking (Phase 2A)
        history_doc = {
            "kvk_season_id": kvk_season_id,
            "file_name": file_name,
            "description": description,
            "timestamp": timestamp,
            "player_count": result['player_count'],
            "players": ranked_players,  # Store full player snapshots with ranks and deltas
            "summary": summary
        }

        history_collection = Database.get_collection("upload_history")
        await history_collection.insert_one(history_doc)

        return {
            "success": True,
            "message": f"Current data saved with {result['player_count']} players",
            "player_count": result['player_count'],
            "kvk_season_id": kvk_season_id,
            "description": description,
            "summary": summary
        }

    async def process_and_save_current_excel(
        self,
        excel_bytes: bytes,
        kvk_season_id: str,
        file_name: str,
        description: str = "",
        kingdom_id: str = "3584"
    ) -> Dict:
        """
        Process current data Excel file, calculate deltas, save, and add to history.
        New players are automatically added to baseline with zero deltas.
        Uses file date from Excel Summary sheet instead of upload time.
        """
        # Process through ML model
        result = self.model.process_excel(excel_bytes, kingdom_id)

        if not result['success']:
            return result

        # Get baseline for this season
        baselines = Database.get_collection("baselines")
        baseline = await baselines.find_one({"kvk_season_id": kvk_season_id})

        if not baseline:
            return {
                "success": False,
                "error": f"No baseline found for season {kvk_season_id}. Please upload baseline first."
            }

        # Calculate deltas
        players_with_deltas = self.model.calculate_all_deltas(
            baseline.get('players', []),
            result['players']
        )

        # Check if any new players were added and update baseline
        new_players = [p for p in players_with_deltas if p.get('newly_added_to_baseline', False)]
        if new_players:
            # Add new players to baseline
            baseline_players = baseline.get('players', [])
            for new_player in new_players:
                baseline_players.append({
                    "governor_id": new_player['governor_id'],
                    "governor_name": new_player['governor_name'],
                    "stats": new_player['stats']
                })

            # Update baseline in database
            await baselines.update_one(
                {"kvk_season_id": kvk_season_id},
                {
                    "$set": {
                        "players": baseline_players,
                        "player_count": len(baseline_players),
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated baseline with {len(new_players)} new players for season {kvk_season_id}")

        # Rank players by kill_points_gained (delta)
        ranked_players = self.model.rank_players(players_with_deltas, "kill_points_gained")

        # Calculate summary (using players_with_deltas to include delta info)
        summary = self.model.calculate_summary_stats(players_with_deltas)

        # Use file_date from Excel if available, otherwise use upload time
        timestamp = result.get('file_date')
        if timestamp:
            # Convert ISO string back to datetime
            timestamp = datetime.fromisoformat(timestamp)
            logger.info(f"Using file date from Excel: {timestamp}")
        else:
            timestamp = datetime.utcnow()
            logger.warning("File date not found in Excel, using upload time")

        # Create current data document
        current_doc = {
            "type": "current",
            "kvk_season_id": kvk_season_id,
            "file_name": file_name,
            "description": description,
            "timestamp": timestamp,  # Use file date from Excel
            "player_count": result['player_count'],
            "players": ranked_players,
            "summary": summary,
            "processing_stats": result['processing_stats']
        }

        # Save to current_data (replace existing)
        current_collection = Database.get_collection("current_data")
        # Use upsert for atomic operation (prevents race conditions)
        await current_collection.update_one(
            {"kvk_season_id": kvk_season_id},
            {"$set": current_doc},
            upsert=True
        )

        # Also save to history (append, don't replace)
        # Include full player snapshots for historical tracking (Phase 2A)
        history_doc = {
            "kvk_season_id": kvk_season_id,
            "file_name": file_name,
            "description": description,
            "timestamp": timestamp,
            "player_count": result['player_count'],
            "players": ranked_players,  # Store full player snapshots with ranks and deltas
            "summary": summary
        }

        history_collection = Database.get_collection("upload_history")
        await history_collection.insert_one(history_doc)

        return {
            "success": True,
            "message": f"Current data saved with {result['player_count']} players from Excel",
            "player_count": result['player_count'],
            "kvk_season_id": kvk_season_id,
            "description": description,
            "summary": summary,
            "sheet_used": result['processing_stats'].get('sheet_used')
        }
    
    async def get_leaderboard(
        self, 
        kvk_season_id: str,
        sort_by: str = "kill_points",
        limit: int = 100
    ) -> Dict:
        """
        Get current leaderboard with deltas from baseline.
        """
        # Get current data
        current_collection = Database.get_collection("current_data")
        current = await current_collection.find_one({"kvk_season_id": kvk_season_id})
        
        # Get baseline for comparison info
        baseline_collection = Database.get_collection("baselines")
        baseline = await baseline_collection.find_one({"kvk_season_id": kvk_season_id})
        
        if not current:
            # If no current data, try to return baseline
            if baseline:
                players = baseline.get('players', [])
                # Add empty deltas
                for p in players:
                    p['delta'] = {
                        "power": 0,
                        "kill_points": 0,
                        "deads": 0,
                        "t4_kills": 0,
                        "t5_kills": 0
                    }
                ranked = self.model.rank_players(players, sort_by)[:limit]

                # Convert datetime to ISO string for JSON serialization
                baseline_ts = baseline.get('timestamp')
                if baseline_ts and hasattr(baseline_ts, 'isoformat'):
                    baseline_ts = baseline_ts.isoformat()

                return {
                    "success": True,
                    "kvk_season_id": kvk_season_id,
                    "baseline_date": baseline_ts,
                    "current_date": baseline_ts,
                    "is_baseline_only": True,
                    "player_count": len(ranked),
                    "leaderboard": ranked
                }
            return {
                "success": False,
                "error": "No data found for this season"
            }
        
        # Re-rank by requested field
        players = current.get('players', [])
        ranked = self.model.rank_players(players, sort_by)[:limit]
        
        # Convert datetime objects to ISO strings for JSON serialization
        baseline_date = baseline.get('timestamp') if baseline else None
        if baseline_date and hasattr(baseline_date, 'isoformat'):
            baseline_date = baseline_date.isoformat()

        current_date = current.get('timestamp')
        if current_date and hasattr(current_date, 'isoformat'):
            current_date = current_date.isoformat()

        return {
            "success": True,
            "kvk_season_id": kvk_season_id,
            "baseline_date": baseline_date,
            "current_date": current_date,
            "description": current.get('description', ''),
            "is_baseline_only": False,
            "player_count": len(ranked),
            "leaderboard": ranked,
            "summary": current.get('summary', {})
        }
    
    async def get_player_stats(
        self, 
        kvk_season_id: str, 
        governor_id: str
    ) -> Dict:
        """
        Get individual player stats with deltas and rank.
        """
        current_collection = Database.get_collection("current_data")
        current = await current_collection.find_one({"kvk_season_id": kvk_season_id})
        
        if not current:
            # Try baseline if no current data
            baseline_collection = Database.get_collection("baselines")
            baseline = await baseline_collection.find_one({"kvk_season_id": kvk_season_id})
            
            if not baseline:
                return {"success": False, "error": "No data found"}
            
            players = baseline.get('players', [])
            player = next(
                (p for p in players if p.get('governor_id') == governor_id),
                None
            )
            
            if not player:
                return {"success": False, "error": "Player not found"}
            
            # Add empty deltas
            player_copy = player.copy()
            player_copy['delta'] = {
                "power": 0,
                "kill_points": 0,
                "deads": 0,
                "t4_kills": 0,
                "t5_kills": 0
            }
            
            # Calculate rank by kill_points_gained (delta)
            ranked = self.model.rank_players(players, "kill_points_gained")
            for p in ranked:
                if p.get('governor_id') == governor_id:
                    player_copy['rank'] = p.get('rank', 0)
                    break
            
            return {"success": True, "player": player_copy}
        
        players = current.get('players', [])

        # Re-rank all players by kill_points_gained to get correct current rank
        ranked_players = self.model.rank_players(players, "kill_points_gained")

        # Find player in ranked list
        player = next(
            (p for p in ranked_players if p.get('governor_id') == governor_id),
            None
        )

        if not player:
            return {"success": False, "error": "Player not found"}

        return {
            "success": True,
            "player": player
        }

    async def get_upload_history(
        self,
        kvk_season_id: str,
        limit: int = 50
    ) -> Dict:
        """
        Get upload history for a season (Phase 2A: Historical Tracking).
        Returns list of all uploads with summary data, ordered by timestamp (newest first).
        """
        history_collection = Database.get_collection("upload_history")

        # Fetch history, sorted by timestamp descending (newest first)
        cursor = history_collection.find(
            {"kvk_season_id": kvk_season_id}
        ).sort("timestamp", -1).limit(limit)

        history = await cursor.to_list(length=limit)

        if not history:
            return {
                "success": False,
                "error": f"No upload history found for season {kvk_season_id}"
            }

        # Convert MongoDB _id to string and format response
        formatted_history = []
        for upload in history:
            formatted_history.append({
                "upload_id": str(upload['_id']),
                "file_name": upload.get('file_name', 'Unknown'),
                "description": upload.get('description', ''),
                "timestamp": upload.get('timestamp'),
                "player_count": upload.get('player_count', 0),
                "summary": upload.get('summary', {})
            })

        return {
            "success": True,
            "kvk_season_id": kvk_season_id,
            "upload_count": len(formatted_history),
            "uploads": formatted_history
        }

    async def get_player_timeline(
        self,
        kvk_season_id: str,
        governor_id: str
    ) -> Dict:
        """
        Get player progress timeline across all uploads (Phase 2A: Historical Tracking).
        Shows how a player's stats evolved over time.
        """
        history_collection = Database.get_collection("upload_history")

        # Fetch all uploads for this season, sorted by timestamp
        cursor = history_collection.find(
            {"kvk_season_id": kvk_season_id}
        ).sort("timestamp", 1)  # Ascending order (oldest first)

        all_uploads = await cursor.to_list(length=None)

        if not all_uploads:
            return {
                "success": False,
                "error": f"No upload history found for season {kvk_season_id}"
            }

        # Extract this player's data from each upload
        timeline = []
        for upload in all_uploads:
            players = upload.get('players', [])

            # Find this player in this upload
            player_data = next(
                (p for p in players if p.get('governor_id') == governor_id),
                None
            )

            if player_data:
                timeline.append({
                    "upload_id": str(upload['_id']),
                    "file_name": upload.get('file_name', 'Unknown'),
                    "description": upload.get('description', ''),
                    "timestamp": upload.get('timestamp'),
                    "rank": player_data.get('rank', 0),
                    "stats": player_data.get('stats', {}),
                    "delta": player_data.get('delta', {})
                })

        if not timeline:
            return {
                "success": False,
                "error": f"Player {governor_id} not found in any uploads for season {kvk_season_id}"
            }

        # Get baseline for comparison
        baseline_collection = Database.get_collection("baselines")
        baseline = await baseline_collection.find_one({"kvk_season_id": kvk_season_id})

        baseline_data = None
        if baseline:
            baseline_players = baseline.get('players', [])
            baseline_player = next(
                (p for p in baseline_players if p.get('governor_id') == governor_id),
                None
            )
            if baseline_player:
                baseline_data = {
                    "timestamp": baseline.get('timestamp'),
                    "stats": baseline_player.get('stats', {})
                }

        return {
            "success": True,
            "kvk_season_id": kvk_season_id,
            "governor_id": governor_id,
            "governor_name": timeline[0].get('stats', {}).get('governor_name', 'Unknown') if timeline else 'Unknown',
            "baseline": baseline_data,
            "timeline_count": len(timeline),
            "timeline": timeline
        }


# Create singleton instance
ml_service = MLService()