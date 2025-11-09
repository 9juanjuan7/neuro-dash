"""
Simple EEG Car Race Game
Car moves forward based on EEG focus (beta waves).
Timed race - compete for fastest time.
"""

import time
from dataclasses import dataclass
from enum import Enum


class GameState(Enum):
    """Game states."""
    MENU = "menu"
    CALIBRATING = "calibrating"
    RACING = "racing"
    FINISHED = "finished"


@dataclass
class Car:
    """Car object."""
    x: float = 50.0  # Horizontal position (starts at left)
    y: float = 300.0  # Vertical position (center)
    speed: float = 0.0  # Current speed
    max_speed: float = 8.0  # Maximum speed


class CarRaceGame:
    """
    Simple EEG-controlled car race.
    Car moves forward when focus (beta waves) exceeds threshold.
    Goal: Finish the race as fast as possible.
    """
    
    def __init__(self, screen_width: int = 800, screen_height: int = 600):
        """
        Initialize game.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Game state
        self.state = GameState.MENU
        self.start_time = None
        self.finish_time = None
        self.race_time = 0.0
        self.distance_traveled = 0.0
        self.race_length = 1000.0  # Race length in pixels
        
        # Car
        self.car = Car()
        
        # EEG control - Made MUCH harder!
        self.focus_threshold = 0.80  # Default threshold (0-1) - Increased to 80% for much harder difficulty
        self.current_focus = 0.0
        self.focus_streak = 0
        self.max_focus_streak = 0
        self.min_focus_to_move = 0.75  # Minimum focus required to start moving (increased from 70%)
        
        # Calibration
        self.calibration_samples = []
        self.calibration_start_time = None
        self.calibration_duration = 10.0  # 10 seconds calibration
        
        # Game timing
        self.last_update = time.time()
    
    def start_calibration(self):
        """Start calibration phase."""
        self.state = GameState.CALIBRATING
        self.calibration_samples = []
        self.calibration_start_time = time.time()
        self.last_update = time.time()
    
    def add_calibration_sample(self, beta_power: float):
        """Add a calibration sample."""
        if self.state == GameState.CALIBRATING:
            self.calibration_samples.append(beta_power)
    
    def finish_calibration(self) -> float:
        """
        Finish calibration and compute threshold.
        
        Returns:
            Recommended focus threshold
        """
        if len(self.calibration_samples) < 10:
            return 30.0  # Default threshold
        
        # Use median + margin as threshold
        import numpy as np
        median_power = np.median(self.calibration_samples)
        threshold = median_power * 1.2  # 20% above median
        
        return max(threshold, 20.0)  # Minimum threshold
    
    def is_calibration_complete(self) -> bool:
        """Check if calibration is complete."""
        if self.calibration_start_time is None:
            return False
        elapsed = time.time() - self.calibration_start_time
        return elapsed >= self.calibration_duration
    
    def start_race(self):
        """Start a new race."""
        self.state = GameState.RACING
        self.start_time = time.time()
        self.finish_time = None
        self.race_time = 0.0
        self.distance_traveled = 0.0
        # Reset car to starting position (left side)
        # Slightly reduced max speed for harder difficulty
        self.car = Car(x=50.0, y=300.0, speed=0.0, max_speed=7.0)
        self.focus_streak = 0
        self.max_focus_streak = 0
        self.current_focus = 0.0
        # Ensure min_focus_to_move is set (should be just below threshold)
        if not hasattr(self, 'min_focus_to_move') or self.min_focus_to_move is None:
            self.min_focus_to_move = max(0.75, self.focus_threshold - 0.05)
        self.last_update = time.time()
    
    def update_focus(self, focus_score: float):
        """
        Update current focus level.
        
        Args:
            focus_score: Focus score from 0.0 to 1.0
        """
        self.current_focus = focus_score
        
        # Track focus streak
        if focus_score >= self.focus_threshold:
            self.focus_streak += 1
            if self.focus_streak > self.max_focus_streak:
                self.max_focus_streak = self.focus_streak
        else:
            self.focus_streak = 0
    
    def update(self, delta_time: float):
        """
        Update game state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if self.state != GameState.RACING:
            return
        
        # Update race time
        if self.start_time:
            self.race_time = time.time() - self.start_time
        
        # Update car movement based on focus - Made harder!
        # Require higher focus to move, and make speed scaling more strict
        if self.current_focus >= self.min_focus_to_move:
            # Move forward - but speed is much more dependent on focus level
            # Need to be well above threshold to get decent speed
            if self.current_focus >= self.focus_threshold:
                # Above threshold - speed scales more strictly
                # Focus needs to be quite high (0.85+) to get good speed
                if self.focus_threshold < 1.0:
                    # More strict scaling: need focus > 0.85 to get > 50% speed
                    excess_focus = self.current_focus - self.focus_threshold
                    available_range = 1.0 - self.focus_threshold
                    # Square the focus factor to make it harder (non-linear)
                    focus_factor = (excess_focus / available_range) ** 1.5
                else:
                    focus_factor = 1.0
                focus_factor = max(0.0, min(1.0, focus_factor))  # Clamp to 0-1
                # Even with focus_factor, require minimum focus to get any speed
                if self.current_focus < 0.85:
                    focus_factor *= 0.2  # EXTREMELY slow if just above threshold (was 0.3)
                elif self.current_focus < 0.90:
                    focus_factor *= 0.5  # Still slow below 90%
                self.car.speed = self.car.max_speed * focus_factor
            else:
                # Between min_focus_to_move and threshold - very slow movement
                # This creates a "crawl" zone where you move but very slowly
                crawl_factor = (self.current_focus - self.min_focus_to_move) / (self.focus_threshold - self.min_focus_to_move)
                crawl_factor = max(0.0, min(1.0, crawl_factor))
                self.car.speed = self.car.max_speed * 0.15 * crawl_factor  # Max 15% speed in crawl zone
        else:
            # Below minimum focus - decelerate quickly and stop
            self.car.speed *= 0.75  # Faster deceleration (was 0.85)
            if self.car.speed < 0.05:
                self.car.speed = 0.0
        
        # Move car forward (right across the screen)
        self.car.x += self.car.speed * delta_time * 60
        
        # Update distance traveled
        self.distance_traveled += self.car.speed * delta_time * 60
        
        # Check if race is finished
        if self.distance_traveled >= self.race_length:
            if self.finish_time is None:
                self.finish_time = time.time()
                self.state = GameState.FINISHED
                self.race_time = self.finish_time - self.start_time
        
        # Keep car in bounds horizontally (left to right)
        self.car.x = max(50, min(self.screen_width - 50, self.car.x))
    
    def get_game_data(self) -> dict:
        """
        Get current game state data.
        
        Returns:
            Dictionary with game state data
        """
        progress = min(100.0, (self.distance_traveled / self.race_length) * 100.0)
        
        return {
            'state': self.state.value,
            'car_x': self.car.x,
            'car_y': self.car.y,
            'car_speed': self.car.speed,
            'current_focus': self.current_focus,
            'focus_threshold': self.focus_threshold,
            'focus_streak': self.focus_streak,
            'max_focus_streak': self.max_focus_streak,
            'race_time': self.race_time,
            'distance_traveled': self.distance_traveled,
            'race_length': self.race_length,
            'progress': progress
        }