"""
Re-process current data to fix negative deltas for migrated players
Run this directly on Railway or local with proper MongoDB connection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "kvk_tracker"
SEASON_ID = "season_6"

class DataModel:
    """Simplified data model for delta calculation"""
    NUMERIC_COLUMNS = ['power', 'deads', 'kill_points', 't4_kills', 't5_kills']
    
    def calculate_player_delta(self, baseline_stats, current_stats):
        """Calculate delta between baseline and current stats"""
        delta = {}
        for field in self.NUMERIC_COLUMNS:
            baseline_val = baseline_stats.get(field, 0)
            current_val = current_stats.get(field, 0)
            delta[field] = current_val - baseline_val
        return delta
    
    def calculate_all_deltas(self, baseline_players, current_players):
        """Calculate deltas for all players with migrated player handling"""
        # Create baseline lookup
        baseline_lookup = {}
        for player in baseline_players:
            gov_id = player.get('governor_id')
            baseline_lookup[gov_id] = player.get('stats', {})
        
        results = []
        new_players_added = []
        
        for player in current_players:
            gov_id = player.get('governor_id')
            current_stats = player.get('stats', {})
            
            # Check if player has any KvK-relevant stats
            kvk_stats_fields = ['kill_points', 'deads', 't4_kills', 't5_kills']
            has_any_stats = any(current_stats.get(field, 0) > 0 for field in kvk_stats_fields)
            
            # Check if player exists in baseline
            if gov_id in baseline_lookup and has_any_stats:
                # Existing player with stats - calculate delta normally
                baseline_stats = baseline_lookup[gov_id]
                delta = self.calculate_player_delta(baseline_stats, current_stats)
                in_baseline = True
                newly_added = False
            else:
                # New player OR migrated out/back player - use current stats as new baseline
                baseline_stats = current_stats
                delta = {field: 0 for field in self.NUMERIC_COLUMNS}
                in_baseline = gov_id in baseline_lookup
                newly_added = True
                
                new_players_added.append({
                    "governor_id": gov_id,
                    "governor_name": player.get('governor_name'),
                    "stats": current_stats
                })
                
                if gov_id not in baseline_lookup:
                    logger.info(f"New player: {player.get('governor_name')} (ID: {gov_id})")
                else:
                    logger.info(f"Player migrated back/reset: {player.get('governor_name')} (ID: {gov_id})")
            
            # Build result with all original fields preserved
            result = {
                "governor_id": gov_id,
                "governor_name": player.get('governor_name'),
                "stats": current_stats,
                "delta": delta,
                "in_baseline": in_baseline,
                "newly_added_to_baseline": newly_added
            }
            
            # Preserve classification fields if they exist
            for field in ['account_type', 'is_dead_weight', 'classification_notes', 
                         'farm_accounts', 'linked_to_main', 'rank']:
                if field in player:
                    result[field] = player[field]
            
            results.append(result)
        
        if new_players_added:
            logger.info(f"Added/reset {len(new_players_added)} players")
        
        return results

async def reprocess_current_data():
    """Re-calculate deltas for current data"""
    client = None
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        
        # Get baseline
        baseline = await db.baselines.find_one({"kvk_season_id": SEASON_ID})
        if not baseline:
            logger.error(f"No baseline found for {SEASON_ID}")
            return
        
        # Get current data
        current_data = await db.current_data.find_one({"kvk_season_id": SEASON_ID})
        if not current_data:
            logger.error(f"No current data found for {SEASON_ID}")
            return
        
        logger.info(f"Baseline: {len(baseline['players'])} players")
        logger.info(f"Current: {len(current_data['players'])} players")
        
        # Re-calculate deltas
        model = DataModel()
        players_with_deltas = model.calculate_all_deltas(
            baseline['players'],
            current_data['players']
        )
        
        logger.info(f"Re-calculated deltas for {len(players_with_deltas)} players")
        
        # Update current_data
        result = await db.current_data.update_one(
            {"kvk_season_id": SEASON_ID},
            {"$set": {"players": players_with_deltas}}
        )
        
        logger.info(f"✅ Updated current data (modified: {result.modified_count})")
        
        # Check specific player
        player_148964283 = next((p for p in players_with_deltas if p['governor_id'] == '148964283'), None)
        if player_148964283:
            logger.info(f"\n📊 Player 148964283 (Hii V):")
            logger.info(f"   Stats: power={player_148964283['stats']['power']:,}, kp={player_148964283['stats']['kill_points']:,}")
            logger.info(f"   Delta: kp={player_148964283['delta']['kill_points']:,}, deaths={player_148964283['delta']['deads']:,}")
            logger.info(f"   Newly added: {player_148964283.get('newly_added_to_baseline')}")
        
        # Update baseline with new/reset players
        new_players = [p for p in players_with_deltas if p.get('newly_added_to_baseline')]
        if new_players:
            baseline_players = baseline.get('players', [])
            
            for new_player in new_players:
                # Check if already in baseline
                existing_idx = next((i for i, p in enumerate(baseline_players) 
                                   if p['governor_id'] == new_player['governor_id']), None)
                
                baseline_entry = {
                    "governor_id": new_player['governor_id'],
                    "governor_name": new_player['governor_name'],
                    "stats": new_player['stats']
                }
                
                if existing_idx is not None:
                    # Update existing entry
                    baseline_players[existing_idx] = baseline_entry
                else:
                    # Add new entry
                    baseline_players.append(baseline_entry)
            
            await db.baselines.update_one(
                {"kvk_season_id": SEASON_ID},
                {"$set": {"players": baseline_players}}
            )
            logger.info(f"✅ Updated baseline with {len(new_players)} new/reset players")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(reprocess_current_data())
