import pandas as pd
from typing import List, Dict
from io import StringIO
from app.models.player import PlayerStats
from app.models.snapshot import SnapshotPlayer


class CSVParser:
    """Parse and clean KvK stats CSV files."""
    
    REQUIRED_COLUMNS = [
        'governor_id',
        'governor_name',
        'power',
        'deads',
        'kill_points',
        't4_kills',
        't5_kills'
    ]
    
    @staticmethod
    def clean_number(value) -> int:
        """
        Remove commas from numbers and convert to int.
        Handles: "230,639,240" or 230639240 or "230639240"
        """
        if pd.isna(value):
            return 0
        
        if isinstance(value, (int, float)):
            return int(value)
        
        # Convert to string and remove ALL commas, quotes, spaces
        cleaned = str(value).replace(',', '').replace('"', '').replace("'", "").strip()
        
        # Handle empty string
        if not cleaned:
            return 0
        
        try:
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0
    
    @classmethod
    def parse_csv(cls, csv_content: str) -> List[SnapshotPlayer]:
        """Parse CSV content and return list of SnapshotPlayer objects."""
        try:
            df = pd.read_csv(StringIO(csv_content))
            
            # Check for required columns
            missing_cols = set(cls.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Clean numeric columns
            numeric_columns = ['power', 'deads', 'kill_points', 't4_kills', 't5_kills']
            for col in numeric_columns:
                df[col] = df[col].apply(cls.clean_number)
            
            # Convert governor_id to string
            df['governor_id'] = df['governor_id'].astype(str)
            
            # Build player list
            players = []
            for _, row in df.iterrows():
                player = SnapshotPlayer(
                    governor_id=str(row['governor_id']),
                    governor_name=str(row['governor_name']),
                    stats=PlayerStats(
                        power=int(row['power']),
                        kill_points=int(row['kill_points']),
                        deads=int(row['deads']),
                        t4_kills=int(row['t4_kills']),
                        t5_kills=int(row['t5_kills'])
                    )
                )
                players.append(player)
            
            return players
            
        except Exception as e:
            raise ValueError(f"CSV parsing error: {str(e)}")
    
    @classmethod
    def validate_csv_format(cls, csv_content: str) -> Dict[str, any]:
        """Validate CSV format and return summary."""
        try:
            df = pd.read_csv(StringIO(csv_content))
            
            missing_cols = set(cls.REQUIRED_COLUMNS) - set(df.columns)
            extra_cols = set(df.columns) - set(cls.REQUIRED_COLUMNS)
            
            return {
                "valid": len(missing_cols) == 0,
                "row_count": len(df),
                "columns_found": list(df.columns),
                "missing_columns": list(missing_cols),
                "extra_columns": list(extra_cols),
                "preview": df.head(3).to_dict('records')
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }