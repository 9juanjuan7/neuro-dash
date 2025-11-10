"""
EEG Backend - BrainFlow integration and demo mode
Handles real-time EEG data streaming and beta wave extraction.
"""

from typing import Optional, Tuple
import csv
import numpy as np
from scipy import signal
from collections import deque
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# Try to import BrainFlow
try:
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
    BRAINFLOW_AVAILABLE = True
except ImportError:
    BRAINFLOW_AVAILABLE = False
    print("BrainFlow not available. Using demo mode only.")

# -------------------------------
# EEGNet 4-Channel Model Definition
# -------------------------------

class EEGNet4Ch(nn.Module):
    def __init__(self, n_channels=4, n_timepoints=250):
        super(EEGNet4Ch, self).__init__()
        self.n_channels = n_channels
        self.n_timepoints = n_timepoints

        # Temporal Convolution
        self.conv1 = nn.Conv2d(1, 16, (1, 64), padding=(0, 32), bias=False)
        self.batchnorm1 = nn.BatchNorm2d(16)

        # Depthwise Convolution
        self.depthwise = nn.Conv2d(16, 32, (n_channels, 1), groups=16, bias=False)
        self.batchnorm2 = nn.BatchNorm2d(32)
        self.pooling2 = nn.AvgPool2d((1, 4))
        self.dropout2 = nn.Dropout(0.5)

        # Separable Convolution
        self.separable = nn.Conv2d(32, 32, (1, 16), padding=(0, 8), bias=False)
        self.batchnorm3 = nn.BatchNorm2d(32)
        self.pooling3 = nn.AvgPool2d((1, 8))
        self.dropout3 = nn.Dropout(0.5)

        # Fully Connected (output)
        # This depends on timepoints and pooling size
        self.output_size = self._get_output_size()
        self.fc1 = nn.Linear(self.output_size, 1)

    def _get_output_size(self):
        # Simulate forward pass to compute flattened size
        x = torch.zeros(1, 1, self.n_channels, self.n_timepoints)
        x = self.conv1(x)
        x = self.batchnorm1(x)
        x = F.elu(x)
        x = self.depthwise(x)
        x = self.batchnorm2(x)
        x = F.elu(x)
        x = self.pooling2(x)
        x = self.dropout2(x)
        x = self.separable(x)
        x = self.batchnorm3(x)
        x = F.elu(x)
        x = self.pooling3(x)
        x = self.dropout3(x)
        return x.view(1, -1).shape[1]

    def forward(self, x):
        x = F.elu(self.batchnorm1(self.conv1(x)))
        x = F.elu(self.batchnorm2(self.depthwise(x)))
        x = self.pooling2(x)
        x = self.dropout2(x)
        x = F.elu(self.batchnorm3(self.separable(x)))
        x = self.pooling3(x)
        x = self.dropout3(x)
        x = x.view(x.size(0), -1)
        x = torch.sigmoid(self.fc1(x))
        return x


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
        self.n_channels = 4
        
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
        # Don't set a default board_id - it must be provided when connecting
        self.board_id = None
    
    def connect(self, serial_port: Optional[str] = None, mac_address: Optional[str] = None, board_id: Optional[int] = None) -> bool:
        """
        Connect to OpenBCI hardware.
        
        Args:
            serial_port: Serial port for OpenBCI device (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            mac_address: MAC address for Ganglion BLE connection (e.g., 'XX:XX:XX:XX:XX:XX')
            board_id: BrainFlow board ID (required for hardware connection)
            
        Returns:
            True if connection successful
        """
        if self.use_demo or not BRAINFLOW_AVAILABLE:
            print("Cannot connect: use_demo=True or BrainFlow not available")
            return False
        
        # Validate board_id is provided
        if board_id is None:
            print("Error: board_id must be provided for hardware connection")
            return False
        
        # Validate that either serial_port or mac_address is provided
        if not serial_port and not mac_address:
            print("Error: Either serial_port or mac_address must be provided")
            return False
        
        # Validate that we don't have both (ambiguous)
        if serial_port and mac_address:
            print("Warning: Both serial_port and mac_address provided. Using serial_port.")
            mac_address = None
        
        # Clean up any existing board connection first
        if self.board is not None:
            try:
                self.stop_streaming()
                self.board.release_session()
            except:
                pass
            self.board = None
        
        try:
            # Set board ID
            self.board_id = board_id
            
            # Initialize fresh params for each connection attempt
            self.params = BrainFlowInputParams()
            
            # Set connection parameters
            if serial_port:
                self.params.serial_port = serial_port
                print(f"Connecting via serial port: {serial_port}")
            if mac_address:
                self.params.mac_address = mac_address
                print(f"Connecting via MAC address: {mac_address}")
            
            # Get board name for logging
            board_names = {
                BoardIds.CYTON_BOARD.value: "Cyton",
                BoardIds.CYTON_DAISY_BOARD.value: "Cyton + Daisy",
                BoardIds.GANGLION_BOARD.value: "Ganglion",
            }
            board_name = board_names.get(self.board_id, f"Board {self.board_id}")
            print(f"Attempting to connect to {board_name} (board_id={self.board_id})")
            
            # Create board instance
            self.board = BoardShim(self.board_id, self.params)
            
            # Prepare session (this is where the actual connection happens)
            print("Preparing session...")
            self.board.prepare_session()
            
            # Get board info
            self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
            eeg_channels = BoardShim.get_eeg_channels(self.board_id)
            self.n_channels = len(eeg_channels)
            
            print(f" Successfully connected to {board_name}!")
            print(f"   Sampling rate: {self.sampling_rate} Hz")
            print(f"   EEG channels: {self.n_channels}")
            
            return True
        except Exception as e:
            print(f" Connection failed: {e}")
            print(f"   Attempted: board_id={self.board_id}, serial_port={serial_port}, mac_address={mac_address}")
            
            # Clean up on failure
            if self.board is not None:
                try:
                    self.board.release_session()
                except:
                    pass
                self.board = None
            
            import traceback
            print("Full traceback:")
            traceback.print_exc()
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


# -------------------------------
# BetaWaveProcessor with Model
# -------------------------------
class BetaWaveProcessor:
    def __init__(self, sampling_rate: int = 250, beta_band: tuple = (13.0, 30.0), model_path="focus_eegnet_4ch.pth"):
        # model_path parameter kept for compatibility but model is disabled
        self.sampling_rate = sampling_rate
        self.beta_band = beta_band
        self.buffer = deque(maxlen=sampling_rate)  # 1-second buffer
        
        # Design beta bandpass filter
        nyquist = sampling_rate / 2.0
        low = max(0.01, min(beta_band[0] / nyquist, 0.99))
        high = max(0.01, min(beta_band[1] / nyquist, 0.99))
        if low < high:
            self.b, self.a = signal.butter(4, [low, high], btype='band')
        else:
            self.b, self.a = None, None
        
        # History
        self.beta_history = deque(maxlen=1000)
        self.focus_scores = deque(maxlen=1000)
        self.timestamps = deque(maxlen=1000)
        
        # Dynamic baseline for relative power calculation (DISABLED - using absolute power)
        # self.baseline_beta_power = None
        # self.baseline_samples = deque(maxlen=200)
        # self.baseline_update_rate = 0.005
        # self.baseline_initialized = False
        
        # Smoothing for focus scores (exponential moving average)
        self.smoothed_focus = None
        self.smoothing_alpha = 0.25  # 0.0 = no smoothing (instant), 1.0 = no change (fully smoothed)
        # Lower alpha = more smoothing (less responsive), higher alpha = less smoothing (more responsive)
        # 0.25 = 25% new value, 75% old value (more smoothing to prevent spikes)
        
        # Spike detection - track recent values to detect sudden jumps
        self.recent_scores = deque(maxlen=10)  # Track last 10 scores
        
        # MODEL DISABLED - Using threshold method only
        # # Load model
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.model = EEGNet4Ch(n_channels=4, n_timepoints=250).to(self.device)
        # try:
        #     self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        #     self.model.eval()
        #     print("✅ EEGNet focus model loaded")
        #     self.model_loaded = True
        # except Exception as e:
        #     print(f"❌ Failed to load model: {e}")
        #     self.model_loaded = False
        self.model_loaded = False  # Always use threshold method

    # Add EEG data to buffer
    def add_data(self, data: np.ndarray):
        if data is None or data.size == 0:
            return
        for i in range(data.shape[1]):
            self.buffer.append(data[:, i])

    # Compute beta power (optional, still available)
    def get_beta_power(self) -> float:
        if len(self.buffer) < 50 or self.b is None or self.a is None:
            return 0.0
        data = np.array(list(self.buffer)).T  # n_channels x n_samples
        total_power = 0.0
        for ch in range(data.shape[0]):
            try:
                filtered = signal.filtfilt(self.b, self.a, data[ch, :].astype(np.float64))
                total_power += np.var(filtered)
            except:
                continue
        beta_power = total_power / data.shape[0] if data.shape[0] > 0 else 0.0
        
        # Baseline tracking disabled - using absolute power approach for stability
        # self.baseline_samples.append(beta_power)
        # ... baseline update code removed ...
        
        self.beta_history.append(beta_power)
        self.timestamps.append(time.time())
        return beta_power

    # Predict focus score using threshold method (model disabled)
    def get_focus_score(self, beta_power: float = None, threshold: float = None) -> float:
        # MODEL DISABLED - Always use threshold method
        # This is the original implementation before the model was added
        return self._threshold_focus(beta_power, threshold)
        
        # MODEL CODE (COMMENTED OUT):
        # if not self.model_loaded:
        #     return self._threshold_focus(beta_power, threshold)
        # 
        # if len(self.buffer) == 0:
        #     return 0.0
        # 
        # data = np.array(list(self.buffer)).T  # n_channels x n_samples
        # if data.shape[0] != 4:
        #     return 0.0
        # if data.shape[1] > 250:
        #     data = data[:, -250:]
        # elif data.shape[1] < 250:
        #     padding = np.zeros((4, 250 - data.shape[1]))
        #     data = np.concatenate([padding, data], axis=1)
        # 
        # data_normalized = np.zeros_like(data)
        # for ch in range(data.shape[0]):
        #     channel_data = data[ch, :]
        #     channel_mean = np.mean(channel_data)
        #     channel_std = np.std(channel_data)
        #     if channel_std > 1e-6:
        #         data_normalized[ch, :] = (channel_data - channel_mean) / channel_std
        #     else:
        #         data_normalized[ch, :] = channel_data - channel_mean
        # 
        # data = data_normalized
        # data_tensor = torch.tensor(data, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
        # 
        # try:
        #     with torch.no_grad():
        #         pred = self.model(data_tensor)
        #         raw_score = pred.item()
        #         score = max(0.0, min(1.0, raw_score))
        # except Exception as e:
        #     print(f"⚠️  Model inference error: {e}, falling back to threshold method")
        #     return self._threshold_focus(beta_power, threshold)
        # 
        # self.focus_scores.append(score)
        # return score

    # Old threshold-based fallback
    def _threshold_focus(self, beta_power: float, threshold: float) -> float:
        if threshold is None or threshold <= 0 or beta_power is None:
            return 0.0
        
        # Use absolute power approach (more stable, no baseline drift issues)
        max_power = threshold * 10.0  # Increased from 8.0 to 10.0 - much less sensitive
        raw_score = min(beta_power / max_power, 1.0)
        
        # Apply a much steeper curve to make it less sensitive
        # Lower exponent = steeper curve = harder to reach high focus
        score = raw_score ** 0.4  # Changed from 0.5 to 0.4 - even less sensitive
        
        # Map the score to allow full range 0-100%, with clearer response to changes
        # Make it easier to see the relationship between focusing and speed
        if raw_score > 0.7:
            # For high values, allow reaching 100% with a steeper curve
            excess = (raw_score - 0.7) / 0.3  # Normalize 0.7-1.0 to 0-1
            # Apply a steeper curve to make it harder to reach 100%
            curved_excess = excess ** 1.5
            score = 0.7 ** 0.4 + curved_excess * (1.0 - 0.7 ** 0.4)
        else:
            # For lower values, use the power curve
            score = raw_score ** 0.4
        
        score = max(0.0, min(1.0, score))
        
        # Spike detection - prevent sudden jumps
        if len(self.recent_scores) > 0:
            recent_avg = np.mean(list(self.recent_scores))
            # If current score is more than 0.4 above recent average, it's likely a spike
            if score > recent_avg + 0.4:
                # Cap the increase to prevent spikes
                score = recent_avg + 0.2  # Limit increase to 0.2 per step
                score = min(score, 1.0)
        
        self.recent_scores.append(score)
        
        # Apply exponential moving average smoothing to reduce noise and spikes
        if self.smoothed_focus is None:
            self.smoothed_focus = score
        else:
            # Exponential moving average: new = alpha * current + (1 - alpha) * previous
            # Lower alpha = more smoothing (less responsive, prevents spikes)
            self.smoothed_focus = self.smoothing_alpha * score + (1 - self.smoothing_alpha) * self.smoothed_focus
        
        # Use smoothed value
        smoothed_score = self.smoothed_focus
        
        # Debug: Print occasionally to verify EEG data is being processed
        if not hasattr(self, '_last_threshold_debug_time'):
            self._last_threshold_debug_time = time.time()
        if time.time() - self._last_threshold_debug_time > 5.0:
            print(f"[Threshold] Beta power: {beta_power:.2f}, Threshold: {threshold:.2f}, Max power: {max_power:.2f}, Raw score: {raw_score:.3f}, Before smooth: {score:.3f}, Final: {smoothed_score:.3f}")
            self._last_threshold_debug_time = time.time()
        
        self.focus_scores.append(smoothed_score)
        return smoothed_score

    def get_history(self):
        if len(self.timestamps) == 0:
            return (np.array([]), np.array([]), np.array([]))
        return (np.array(self.timestamps), np.array(self.beta_history), np.array(self.focus_scores))
    
    def reset(self):
        self.buffer.clear()
        self.beta_history.clear()
        self.focus_scores.clear()
        self.timestamps.clear()
