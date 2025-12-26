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
        
        # Delete existing baseline for this season
        await collection.delete_many({"kvk_season_id": kvk_season_id})
        
        # Insert new baseline
        insert_result = await collection.insert_one(baseline_doc)
        
        return {
            "success": True,
            "message": f"Baseline saved with {result['player_count']} players",
            "player_count": result['player_count'],
            "kvk_season_id": kvk_season_id,
            "mongo_id": str(insert_result.inserted_id)
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
        
        # Rank players by kill_points
        ranked_players = self.model.rank_players(players_with_deltas, "kill_points")
        
        # Calculate summary
        summary = self.model.calculate_summary_stats(result['players'])
        
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
        await current_collection.delete_many({"kvk_season_id": kvk_season_id})
        await current_collection.insert_one(current_doc)
        
        # Also save to history (append, don't replace)
        history_doc = {
            "kvk_season_id": kvk_season_id,
            "file_name": file_name,
            "description": description,
            "timestamp": timestamp,
            "player_count": result['player_count'],
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
                return {
                    "success": True,
                    "kvk_season_id": kvk_season_id,
                    "baseline_date": baseline.get('timestamp'),
                    "current_date": baseline.get('timestamp'),
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
        
        return {
            "success": True,
            "kvk_season_id": kvk_season_id,
            "baseline_date": baseline.get('timestamp') if baseline else None,
            "current_date": current.get('timestamp'),
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
            
            # Calculate rank
            ranked = self.model.rank_players(players, "kill_points")
            for p in ranked:
                if p.get('governor_id') == governor_id:
                    player_copy['rank'] = p.get('rank', 0)
                    break
            
            return {"success": True, "player": player_copy}
        
        players = current.get('players', [])
        
        # Find player
        player = next(
            (p for p in players if p.get('governor_id') == governor_id),
            None
        )
        
        if not player:
            return {"success": False, "error": "Player not found"}
        
        return {
            "success": True,
            "player": player
        }


# Create singleton instance
ml_service = MLService()