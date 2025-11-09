"""
EEG Backend - BrainFlow integration and demo mode
Handles real-time EEG data streaming and beta wave extraction.
"""

import numpy as np
from scipy import signal
from typing import Optional, Tuple
from collections import deque
import time

# Try to import BrainFlow
try:
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
    BRAINFLOW_AVAILABLE = True
except ImportError:
    BRAINFLOW_AVAILABLE = False
    print("BrainFlow not available. Using demo mode only.")


class EEGStreamer:
    """
    Manages EEG data streaming from OpenBCI hardware or demo mode.
    """
    
    def __init__(self, use_demo: bool = True):
        """
        Initialize EEG streamer.
        
        Args:
            use_demo: If True, use demo mode with synthetic data
        """
        self.use_demo = use_demo
        self.board = None
        self.is_streaming = False
        self.sampling_rate = 250
        self.n_channels = 8
        
        if use_demo:
            self._init_demo()
        elif BRAINFLOW_AVAILABLE:
            self._init_brainflow()
        else:
            print("BrainFlow not available. Falling back to demo mode.")
            self.use_demo = True
            self._init_demo()
    
    def _init_demo(self):
        """Initialize demo mode with synthetic EEG data."""
        self.demo_phase = 0.0
        self.demo_start_time = None  # Will be set when streaming starts
    
    def _init_brainflow(self):
        """Initialize BrainFlow for hardware connection."""
        self.params = BrainFlowInputParams()
        self.board_id = BoardIds.SYNTHETIC_BOARD.value  # Default to synthetic for testing
    
    def connect(self, serial_port: Optional[str] = None, mac_address: Optional[str] = None, board_id: Optional[int] = None) -> bool:
        """
        Connect to OpenBCI hardware.
        
        Args:
            serial_port: Serial port for OpenBCI device (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            mac_address: MAC address for Ganglion BLE connection (e.g., 'XX:XX:XX:XX:XX:XX')
            board_id: BrainFlow board ID (optional, uses default if not provided)
            
        Returns:
            True if connection successful
        """
        if self.use_demo or not BRAINFLOW_AVAILABLE:
            return False
        
        try:
            # Set board ID if provided
            if board_id is not None:
                self.board_id = board_id
            
            # Set connection parameters
            if serial_port:
                self.params.serial_port = serial_port
            if mac_address:
                self.params.mac_address = mac_address
            
            self.board = BoardShim(self.board_id, self.params)
            self.board.prepare_session()
            self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
            eeg_channels = BoardShim.get_eeg_channels(self.board_id)
            self.n_channels = len(eeg_channels)
            print(f"Connected to board. Sampling rate: {self.sampling_rate} Hz, Channels: {self.n_channels}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            print(f"Tried: board_id={self.board_id}, serial_port={serial_port}, mac_address={mac_address}")
            return False
    
    def start_streaming(self) -> bool:
        """Start streaming EEG data."""
        if self.use_demo:
            if self.demo_start_time is None:
                self.demo_start_time = time.time()
            self.is_streaming = True
            return True
        
        if self.board is None:
            return False
        
        try:
            self.board.start_stream()
            self.is_streaming = True
            return True
        except Exception as e:
            print(f"Failed to start streaming: {e}")
            return False
    
    def stop_streaming(self):
        """Stop streaming EEG data."""
        self.is_streaming = False
        if not self.use_demo and self.board is not None:
            try:
                self.board.stop_stream()
            except:
                pass
    
    def get_data(self, n_samples: int = 250) -> Optional[np.ndarray]:
        """
        Get EEG data samples.
        
        Args:
            n_samples: Number of samples to retrieve
            
        Returns:
            EEG data array (n_channels, n_samples) or None
        """
        if not self.is_streaming:
            return None
        
        if self.use_demo:
            return self._get_demo_data(n_samples)
        else:
            return self._get_hardware_data(n_samples)
    
    def _get_demo_data(self, n_samples: int) -> np.ndarray:
        """Generate synthetic EEG data for demo mode."""
        if self.demo_start_time is None:
            self.demo_start_time = time.time()
        
        current_time = time.time()
        elapsed = current_time - self.demo_start_time
        
        # Simulate focus levels (beta waves)
        # Create varying focus patterns for gameplay
        focus_level = 0.5 + 0.3 * np.sin(elapsed / 5.0)  # Slow variation
        focus_level += 0.2 * np.sin(elapsed / 1.0)  # Faster variation
        focus_level = np.clip(focus_level, 0.2, 1.0)
        
        # Generate beta waves (13-30 Hz) proportional to focus
        beta_freq = 20.0  # 20 Hz center frequency
        beta_amplitude = focus_level * 15.0
        
        # Generate data for each channel
        data = np.zeros((self.n_channels, n_samples))
        for ch in range(self.n_channels):
            # Time array
            t = np.arange(n_samples) / self.sampling_rate + elapsed
            
            # Beta component (focus)
            beta_wave = beta_amplitude * np.sin(2 * np.pi * beta_freq * t + self.demo_phase)
            
            # Alpha component (relaxation) - inverse of focus
            alpha_wave = (1 - focus_level) * 10.0 * np.sin(2 * np.pi * 10.0 * t)
            
            # Noise
            noise = np.random.normal(0, 2.0, n_samples)
            
            # Combine
            data[ch, :] = beta_wave + alpha_wave + noise
        
        self.demo_phase += 2 * np.pi * beta_freq * n_samples / self.sampling_rate
        return data
    
    def _get_hardware_data(self, n_samples: int) -> Optional[np.ndarray]:
        """Get EEG data from hardware."""
        if self.board is None:
            return None
        
        try:
            data = self.board.get_board_data()
            if data is None or data.size == 0:
                return None
            
            eeg_channels = BoardShim.get_eeg_channels(self.board_id)
            eeg_data = data[eeg_channels, :]
            
            if eeg_data.shape[1] > n_samples:
                eeg_data = eeg_data[:, -n_samples:]
            
            return eeg_data
        except Exception as e:
            print(f"Error getting data: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from hardware."""
        self.stop_streaming()
        if not self.use_demo and self.board is not None:
            try:
                self.board.release_session()
                self.board = None
            except:
                pass


class BetaWaveProcessor:
    """
    Processes EEG data to extract beta wave power (focus/concentration).
    """
    
    def __init__(self, sampling_rate: int = 250, beta_band: Tuple[float, float] = (13.0, 30.0)):
        """
        Initialize beta wave processor.
        
        Args:
            sampling_rate: Sampling rate in Hz
            beta_band: Beta wave frequency range (default 13-30 Hz)
        """
        self.sampling_rate = sampling_rate
        self.beta_band = beta_band
        self.buffer = deque(maxlen=sampling_rate)  # 1 second buffer
        
        # Design beta bandpass filter
        nyquist = sampling_rate / 2.0
        low = beta_band[0] / nyquist
        high = beta_band[1] / nyquist
        low = max(0.01, min(low, 0.99))
        high = max(0.01, min(high, 0.99))
        
        if low < high:
            self.b, self.a = signal.butter(4, [low, high], btype='band')
        else:
            self.b, self.a = None, None
        
        # History for tracking
        self.beta_history = deque(maxlen=1000)
        self.focus_scores = deque(maxlen=1000)
        self.timestamps = deque(maxlen=1000)
    
    def add_data(self, data: np.ndarray):
        """
        Add EEG data to buffer.
        
        Args:
            data: EEG data array (n_channels, n_samples)
        """
        if data is None or data.size == 0:
            return
        
        # Add to buffer (transpose to samples x channels)
        for i in range(data.shape[1]):
            self.buffer.append(data[:, i])
    
    def get_beta_power(self) -> float:
        """
        Extract beta wave power from buffered data.
        
        Returns:
            Beta wave power (average across channels)
        """
        if len(self.buffer) < 50:  # Need minimum samples
            return 0.0
        
        # Convert buffer to array
        data = np.array(list(self.buffer)).T  # (n_channels, n_samples)
        
        if self.b is None or self.a is None:
            return 0.0
        
        # Compute beta power for each channel
        total_power = 0.0
        for ch in range(data.shape[0]):
            try:
                filtered = signal.filtfilt(self.b, self.a, data[ch, :].astype(np.float64))
                power = np.var(filtered)
                total_power += power
            except:
                continue
        
        beta_power = total_power / data.shape[0] if data.shape[0] > 0 else 0.0
        
        # Store in history
        self.beta_history.append(beta_power)
        self.timestamps.append(time.time())
        
        return beta_power
    
    def get_focus_score(self, beta_power: float, threshold: float) -> float:
        """
        Compute focus score (0.0 to 1.0) based on beta power.
        
        Args:
            beta_power: Beta wave power
            threshold: Threshold for focus detection
            
        Returns:
            Focus score from 0.0 (unfocused) to 1.0 (highly focused)
        """
        if threshold <= 0:
            return 0.0
        
        # Normalize power relative to threshold
        score = min(beta_power / threshold, 2.0) / 2.0
        score = max(0.0, min(1.0, score))
        
        self.focus_scores.append(score)
        return score
    
    def get_history(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get historical data.
        
        Returns:
            Tuple of (timestamps, beta_power_history, focus_scores)
        """
        if len(self.timestamps) == 0:
            return (np.array([]), np.array([]), np.array([]))
        
        timestamps = np.array(self.timestamps)
        beta = np.array(self.beta_history)
        focus = np.array(self.focus_scores)
        
        return (timestamps, beta, focus)
    
    def reset(self):
        """Reset processor buffers."""
        self.buffer.clear()
        self.beta_history.clear()
        self.focus_scores.clear()
        self.timestamps.clear()
