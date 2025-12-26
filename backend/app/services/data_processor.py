from typing import List, Dict
from app.models.player import PlayerStats, PlayerDelta
from app.models.snapshot import SnapshotPlayer

class DataProcessor:
    """Process snapshots and calculate deltas."""
    
    @staticmethod
    def calculate_delta(before: PlayerStats, after: PlayerStats) -> PlayerStats:
        """
        Calculate the difference between two snapshots.
        Delta = After - Before
        """
        return PlayerStats(
            power=after.power - before.power,
            kill_points=after.kill_points - before.kill_points,
            deads=after.deads - before.deads,
            t4_kills=after.t4_kills - before.t4_kills,
            t5_kills=after.t5_kills - before.t5_kills
        )
    
    @classmethod
    def calculate_fight_contributions(
        cls,
        before_players: List[SnapshotPlayer],
        after_players: List[SnapshotPlayer]
    ) -> List[PlayerDelta]:
        """
        Calculate each player's contribution in a fight.
        
        Args:
            before_players: Snapshot before fight
            after_players: Snapshot after fight
            
        Returns:
            List of PlayerDelta objects with stat changes
        """
        # Create lookup dict for before snapshot
        before_dict = {p.governor_id: p for p in before_players}
        
        deltas = []
        
        for after_player in after_players:
            governor_id = after_player.governor_id
            
            # Find matching player in before snapshot
            if governor_id in before_dict:
                before_player = before_dict[governor_id]
                
                # Calculate delta
                delta_stats = cls.calculate_delta(
                    before_player.stats,
                    after_player.stats
                )
                
                deltas.append(PlayerDelta(
                    governor_id=governor_id,
                    governor_name=after_player.governor_name,
                    delta_stats=delta_stats
                ))
            else:
                # Player joined during fight - count all their stats
                deltas.append(PlayerDelta(
                    governor_id=governor_id,
                    governor_name=after_player.governor_name,
                    delta_stats=after_player.stats
                ))
        
        return deltas
    
    @staticmethod
    def calculate_kd_ratio(kill_points: int, deads: int) -> float:
        """Calculate KD ratio. Returns 0 if no deaths."""
        if deads == 0:
            return 0.0
        return round(kill_points / deads, 2)