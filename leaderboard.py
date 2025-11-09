"""
Leaderboard management for EEG Car Race Game.
"""

import json
import os
from typing import List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RaceRecord:
    """Race record entry."""
    player_name: str
    race_time: float  # Time in seconds (lower is better)
    max_focus_streak: int
    timestamp: str


class Leaderboard:
    """Manages race leaderboard."""
    
    def __init__(self, filename: str = "leaderboard.json"):
        """
        Initialize leaderboard.
        
        Args:
            filename: JSON file to store leaderboard data
        """
        self.filename = filename
        self.records: List[RaceRecord] = []
        self.load()
    
    def load(self):
        """Load leaderboard from file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.records = [RaceRecord(**entry) for entry in data]
                    # Sort by race time (fastest first)
                    self.records.sort(key=lambda x: x.race_time)
            except Exception as e:
                print(f"Error loading leaderboard: {e}")
                self.records = []
    
    def save(self):
        """Save leaderboard to file."""
        try:
            with open(self.filename, 'w') as f:
                data = [asdict(record) for record in self.records]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
    
    def add_record(self, player_name: str, race_time: float, max_focus_streak: int):
        """
        Add a race record to the leaderboard.
        
        Args:
            player_name: Player's name
            race_time: Race completion time in seconds
            max_focus_streak: Maximum focus streak during race
        """
        new_record = RaceRecord(
            player_name=player_name,
            race_time=race_time,
            max_focus_streak=max_focus_streak,
            timestamp=datetime.now().isoformat()
        )
        
        self.records.append(new_record)
        # Sort by race time (fastest first)
        self.records.sort(key=lambda x: x.race_time)
        
        # Keep top 50 records
        if len(self.records) > 50:
            self.records = self.records[:50]
        
        self.save()
    
    def get_top_records(self, n: int = 10) -> List[RaceRecord]:
        """
        Get top N fastest records.
        
        Args:
            n: Number of records to return
            
        Returns:
            List of top N fastest records
        """
        return self.records[:n]
    
    def get_best_time(self) -> float:
        """Get the best (fastest) race time."""
        if len(self.records) == 0:
            return 0.0
        return self.records[0].race_time
    
    def get_best_streak(self) -> int:
        """Get the best focus streak."""
        if len(self.records) == 0:
            return 0
        return max(record.max_focus_streak for record in self.records)