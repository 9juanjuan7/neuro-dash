"""
Focus Server - Processes OpenBCI EEG data and sends focus scores to the game using a trained EEGNet model.
"""

import socket
import time
import argparse
import sys
from eeg_backend import EEGStreamer, BetaWaveProcessor
import eeg_backend
import numpy as np
import torch

# Check if BrainFlow is available
BRAINFLOW_AVAILABLE = getattr(eeg_backend, 'BRAINFLOW_AVAILABLE', False)

# UDP socket to send focus to game
UDP_IP = "127.0.0.1"
UDP_PORT_OUT = 5005  # game listens here

sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Load trained EEGNet model
MODEL_PATH = "focus_eegnet_4ch.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.load(MODEL_PATH, map_location=device)
model.eval()


def predict_focus(model, data: np.ndarray) -> float:
    """
    Predict focus score from EEG data using trained model.

    Args:
        model: Trained PyTorch model
        data: EEG data array (n_channels, n_samples)

    Returns:
        focus score (0.0 to 1.0)
    """
    if data is None or data.size == 0:
        return 0.0

    # EEGNet usually expects shape (batch, channels, samples)
    x = torch.tensor(data, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(x)
        # Assuming output is single sigmoid or softmax for binary focus
        if output.shape[-1] == 1:
            score = output.item()  # sigmoid output
        else:
            # If softmax, take probability of "focused" class
            score = torch.softmax(output, dim=1)[0, 1].item()
    return float(np.clip(score, 0.0, 1.0))


def main():
    parser = argparse.ArgumentParser(description='Focus Server for EEG Car Race Game')
    parser.add_argument('--demo', action='store_true', help='Use demo mode (no hardware)')
    parser.add_argument('--board-type', choices=['Cyton', 'Ganglion', 'Cyton + Daisy'],
                        default='Cyton', help='OpenBCI board type (hardware mode only)')
    parser.add_argument('--serial-port', type=str, default=None,
                        help='Serial port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux/Mac)')
    parser.add_argument('--mac-address', type=str, default=None,
                        help='MAC address for Bluetooth connection (Ganglion only)')
    parser.add_argument('--update-rate', type=float, default=0.016,
                        help='Update rate in seconds (default: 0.016 = ~60 Hz)')
    
    args = parser.parse_args()
    
    # Initialize EEG streamer
    use_demo = args.demo
    if not use_demo and not BRAINFLOW_AVAILABLE:
        print("BrainFlow not available. Falling back to demo mode.")
        use_demo = True
    
    print("=" * 60)
    print("Focus Server - EEG Car Race")
    print("=" * 60)
    
    eeg_streamer = EEGStreamer(use_demo=use_demo)
    
    if not use_demo:
        # connect to hardware
        from brainflow.board_shim import BoardIds
        board_id_map = {
            "Cyton": BoardIds.CYTON_BOARD.value,
            "Ganglion": BoardIds.GANGLION_BOARD.value,
            "Cyton + Daisy": BoardIds.CYTON_DAISY_BOARD.value,
        }
        board_id = board_id_map.get(args.board_type)
        if not eeg_streamer.connect(board_id=board_id, serial_port=args.serial_port, mac_address=args.mac_address):
            print("Failed to connect to hardware. Exiting.")
            sys.exit(1)
    
    if not eeg_streamer.start_streaming():
        print("Failed to start EEG streaming. Exiting.")
        sys.exit(1)
    
    print(f"Sending focus predictions to: {UDP_IP}:{UDP_PORT_OUT}")
    print("=" * 60)
    
    try:
        while True:
            data = eeg_streamer.get_data(n_samples=250)
            focus_score = predict_focus(model, data)
            
            # Send focus score to game
            msg = str(focus_score).encode()
            sock_out.sendto(msg, (UDP_IP, UDP_PORT_OUT))
            
            # Optional: print for debugging
            print(f"Focus Score: {focus_score:.3f}", end='\r')
            
            time.sleep(args.update_rate)
    
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        eeg_streamer.disconnect()
        sock_out.close()
        print("Server stopped.")


if __name__ == "__main__":
    main()
