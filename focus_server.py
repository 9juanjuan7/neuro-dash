"""
Focus Server - Processes OpenBCI EEG data and sends focus scores to the game.
Uses the same EEG backend as app.py for OpenBCI hardware integration.
"""

import socket
import time
import argparse
import sys
from eeg_backend import EEGStreamer, BetaWaveProcessor
import eeg_backend
import numpy as np
import csv

# Check if BrainFlow is available
BRAINFLOW_AVAILABLE = getattr(eeg_backend, 'BRAINFLOW_AVAILABLE', False)

# UDP socket to send focus to game and dashboard
UDP_IP = "127.0.0.1"
UDP_PORT_GAME = 5005  # game listens here
UDP_PORT_DASHBOARD = 5006  # dashboard listens here

sock_out_game = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_out_dashboard = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Default focus threshold (beta power threshold, not normalized focus score)
DEFAULT_FOCUS_THRESHOLD = 70


lister = []

def main():
    """Main server loop."""
    parser = argparse.ArgumentParser(description='Focus Server for EEG Car Race Game')
    parser.add_argument('--demo', action='store_true', help='Use demo mode (no hardware)')
    parser.add_argument('--board-type', choices=['Cyton', 'Ganglion', 'Cyton + Daisy'], 
                       default='Cyton', help='OpenBCI board type (hardware mode only)')
    parser.add_argument('--serial-port', type=str, default=None,
                       help='Serial port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux/Mac)')
    parser.add_argument('--mac-address', type=str, default=None,
                       help='MAC address for Bluetooth connection (Ganglion only)')
    parser.add_argument('--threshold', type=float, default=DEFAULT_FOCUS_THRESHOLD,
                       help='Focus threshold (beta power threshold)')
    parser.add_argument('--update-rate', type=float, default=0.016,
                       help='Update rate in seconds (default: 0.016 = ~60 Hz to match game FPS)')
    
    args = parser.parse_args()
    
    # Initialize EEG streamer
    use_demo = args.demo
    if not use_demo and not BRAINFLOW_AVAILABLE:
        print(" BrainFlow not available. Falling back to demo mode.")
        use_demo = True
    
    print("=" * 60)
    print("Focus Server - EEG Car Race")
    print("=" * 60)
    
    if use_demo:
        print(" Mode: DEMO (synthetic EEG data)")
        eeg_streamer = EEGStreamer(use_demo=True)
    else:
        print(" Mode: HARDWARE (OpenBCI)")
        print(f"   Board Type: {args.board_type}")
        if args.serial_port:
            print(f"   Serial Port: {args.serial_port}")
        elif args.mac_address:
            print(f"   MAC Address: {args.mac_address}")
        else:
            print("    No connection method specified. Using default COM3")
            args.serial_port = "COM3"
        
        # Map board type to BrainFlow ID
        if not BRAINFLOW_AVAILABLE:
            print(" BrainFlow not installed! Install with: pip install brainflow")
            sys.exit(1)
        
        from brainflow.board_shim import BoardIds
        board_id_map = {
            "Cyton": BoardIds.CYTON_BOARD.value,
            "Ganglion": BoardIds.GANGLION_BOARD.value,
            "Cyton + Daisy": BoardIds.CYTON_DAISY_BOARD.value,
        }
        board_id = board_id_map.get(args.board_type)
        if board_id is None:
            print(f" Invalid board type: {args.board_type}")
            sys.exit(1)
        
        # Initialize streamer
        eeg_streamer = EEGStreamer(use_demo=False)
        
        # Connect to hardware
        print("   Connecting to OpenBCI...")
        if eeg_streamer.connect(
            serial_port=args.serial_port,
            mac_address=args.mac_address,
            board_id=board_id
        ):
            print("   Connected!")
        else:
            print("    Connection failed!")
            print("   Common issues:")
            print("   1. Device not connected or powered on")
            print("   2. Serial port/MAC address is incorrect")
            print("   3. Board type doesn't match your device")
            print("   4. Another application is using the device")
            print("   5. Drivers not installed (Windows)")
            sys.exit(1)
    
    # Start streaming
    print("   Starting EEG streaming...")
    if eeg_streamer.start_streaming():
        print("   Streaming started!")
    else:
        print("    Failed to start streaming!")
        eeg_streamer.disconnect()
        sys.exit(1)
    
    # Initialize processor
    processor = BetaWaveProcessor()
    focus_threshold = args.threshold
    
    print(f"   Focus Threshold: {focus_threshold}")
    print(f"   Update Rate: {args.update_rate * 1000:.0f} ms ({1/args.update_rate:.1f} Hz)")
    print(f"   Sending focus to game: {UDP_IP}:{UDP_PORT_GAME}")
    print(f"   Sending focus to dashboard: {UDP_IP}:{UDP_PORT_DASHBOARD}")
    print("=" * 60)
    print(" Server running! Start the game to see focus data.")
    print("   Press Ctrl+C to stop.")
    print("=" * 60)
    
    try:
        while True:
            # Get EEG data
            data = eeg_streamer.get_data(n_samples=250)
            if data is not None:
                processor.add_data(data)
                
            
            # Get beta power and compute focus score
            beta_power = processor.get_beta_power()
            focus_score = processor.get_focus_score(beta_power, focus_threshold)
            if data is not None and len(list(np.mean(data, axis=0))) == 4:
                lister.append([*[float(x) for x in list(np.mean(data, axis=0))], beta_power, focus_score, 1 if focus_score >= 0.99 else 0])
            # Send focus score to game and dashboard (0.0 to 1.0)
            # The game/dashboard will multiply by 100 to get 0-100%
            msg = str(focus_score).encode()
            sock_out_game.sendto(msg, (UDP_IP, UDP_PORT_GAME))
            sock_out_dashboard.sendto(msg, (UDP_IP, UDP_PORT_DASHBOARD))
            
            # Print status
            # print(f"Focus: {focus_score:.3f} (Beta Power: {beta_power:.2f})", end='\r')
            # print(beta_power, focus_score, 1 if focus_score > 0.5 else 0, np.mean(data, axis=0))
            # print(np.mean(data, axis=0))
            # print(data.shape)
            
            # Sleep to control update rate
            time.sleep(args.update_rate)
    
    except KeyboardInterrupt:
        print("\n\nStopping server...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("   Disconnecting...")
        eeg_streamer.disconnect()
        sock_out_game.close()
        sock_out_dashboard.close()
        print("   Server stopped.")

        # print(processor.get_history())
        with open("outputer.txt", 'w', newline='\n') as file:
            writer = csv.writer(file)

            writer.writerow("channel_1,channel_2,channel_3,channel_4,beta_power,focus_score,focused_classification".split(","))

            # Write multiple rows at once
            writer.writerows(lister)


if __name__ == "__main__":
    main()
