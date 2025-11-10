"""
LSL Forwarder - Runs on laptop with OpenBCI GUI
Connects to LSL stream locally, processes EEG data, and forwards focus scores
to Raspberry Pi via UDP over Tailscale.
"""

import time
import argparse
import socket
import sys
from eeg_backend import LSLReader, BetaWaveProcessor
import eeg_backend

# Check if pylsl is available
PYLSL_AVAILABLE = getattr(eeg_backend, 'PYLSL_AVAILABLE', False)

# Default focus threshold
DEFAULT_FOCUS_THRESHOLD = 70.0

# Ready flag parameters
READY_THRESHOLD = 0.7  # Attention score threshold for ready state
READY_DURATION = 3.0   # Seconds of sustained focus to become ready


def compute_ready_flag(attention_score: float, ready_timer: float, dt: float) -> tuple:
    """
    Compute ready flag based on attention score.
    
    Args:
        attention_score: Current attention score (0.0 to 1.0)
        ready_timer: Current ready timer value
        dt: Time delta since last update
        
    Returns:
        Tuple of (ready_flag: bool, new_ready_timer: float)
    """
    if attention_score >= READY_THRESHOLD:
        # Increment timer when above threshold
        new_timer = ready_timer + dt
        if new_timer >= READY_DURATION:
            return (True, new_timer)
        else:
            return (False, new_timer)
    else:
        # Reset timer when below threshold
        return (False, 0.0)


def main():
    """Main forwarder loop."""
    parser = argparse.ArgumentParser(description='LSL Forwarder - Forwards EEG focus scores to Raspberry Pi over Tailscale')
    parser.add_argument('--stream-name', type=str, default='eegstream',
                       help='Name of LSL stream to connect to (default: eegstream)')
    parser.add_argument('--pi-ip', type=str, required=True,
                       help='Tailscale IP address of Raspberry Pi (e.g., 100.x.x.x)')
    parser.add_argument('--game-port', type=int, default=5005,
                       help='UDP port for game on Pi (default: 5005)')
    parser.add_argument('--dashboard-port', type=int, default=5006,
                       help='UDP port for dashboard on Pi (default: 5006)')
    parser.add_argument('--threshold', type=float, default=DEFAULT_FOCUS_THRESHOLD,
                       help='Focus threshold (beta power threshold, default: 70.0, try higher like 100-150 if too sensitive)')
    parser.add_argument('--update-rate', type=float, default=0.016,
                       help='Update rate in seconds (default: 0.016 = ~60 Hz)')
    parser.add_argument('--mode', choices=['game', 'dashboard', 'both'], default='both',
                       help='Which application(s) to send data to (default: both)')
    
    args = parser.parse_args()
    
    if not PYLSL_AVAILABLE:
        print("❌ pylsl not available. Install with: pip install pylsl")
        sys.exit(1)
    
    print("=" * 60)
    print("LSL Forwarder - Laptop → Raspberry Pi (Tailscale)")
    print("=" * 60)
    print(f"📡 LSL Stream: {args.stream_name}")
    print(f"➡️  Forwarding to: {args.pi_ip}")
    print(f"   Game port: {args.game_port}")
    print(f"   Dashboard port: {args.dashboard_port}")
    print(f"   Mode: {args.mode}")
    print(f"⚙️  Focus Threshold: {args.threshold}")
    print(f"⏱️  Update Rate: {args.update_rate * 1000:.0f} ms ({1/args.update_rate:.1f} Hz)")
    print("=" * 60)
    
    # Setup UDP sockets
    sock_game = None
    sock_dashboard = None
    
    if args.mode in ['game', 'both']:
        sock_game = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"📤 Game UDP: {args.pi_ip}:{args.game_port}")
    
    if args.mode in ['dashboard', 'both']:
        sock_dashboard = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"📤 Dashboard UDP: {args.pi_ip}:{args.dashboard_port}")
    
    # Connect to LSL stream locally
    print("\n🔌 Connecting to LSL stream locally...")
    print("   Make sure OpenBCI GUI is running and LSL stream is started!")
    lsl_reader = LSLReader(stream_name=args.stream_name, timeout=10.0)
    
    if not lsl_reader.connect():
        print("❌ Failed to connect to LSL stream!")
        print("   Make sure:")
        print("   1. OpenBCI GUI is running")
        print("   2. LSL stream is started in Networking widget")
        print("   3. Stream name matches: " + args.stream_name)
        sys.exit(1)
    
    # Initialize processor
    sampling_rate = lsl_reader.sampling_rate
    processor = BetaWaveProcessor(sampling_rate=sampling_rate)
    focus_threshold = args.threshold
    
    # Ready flag state
    ready_timer = 0.0
    ready_flag = False
    
    print("\n✅ Connected! Forwarding data to Raspberry Pi...")
    print("   Press Ctrl+C to stop.")
    print("=" * 60)
    
    last_time = time.time()
    
    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Get EEG data from LSL
            data = lsl_reader.get_data(n_samples=250)
            if data is not None:
                processor.add_data(data)
            
            # Compute beta power and attention score
            beta_power = processor.get_beta_power()
            attention_score = processor.get_focus_score(beta_power, focus_threshold)
            
            # Debug output (print every 2 seconds)
            if not hasattr(main, '_last_debug_time'):
                main._last_debug_time = 0
            if current_time - main._last_debug_time > 2.0:
                print(f"\n[Forwarder] Beta: {beta_power:.2f} | Threshold: {focus_threshold} | Focus: {attention_score*100:.1f}%")
                main._last_debug_time = current_time
            
            # Compute ready flag
            ready_flag, ready_timer = compute_ready_flag(attention_score, ready_timer, dt)
            
            # Send to game (attention score only)
            if sock_game is not None:
                msg = str(attention_score).encode()
                try:
                    sock_game.sendto(msg, (args.pi_ip, args.game_port))
                except Exception as e:
                    print(f"⚠️  Error sending to game: {e}")
            
            # Send to dashboard (attention score and ready flag)
            if sock_dashboard is not None:
                # Format: "attention_score,ready_flag"
                msg = f"{attention_score:.4f},{1 if ready_flag else 0}".encode()
                try:
                    sock_dashboard.sendto(msg, (args.pi_ip, args.dashboard_port))
                except Exception as e:
                    print(f"⚠️  Error sending to dashboard: {e}")
            
            # Print status
            ready_status = "🟢 READY" if ready_flag else "⚪ Not Ready"
            print(f"Attention: {attention_score*100:5.1f}% | Beta: {beta_power:6.2f} | {ready_status} | → {args.pi_ip}", end='\r')
            
            # Sleep to control update rate
            time.sleep(args.update_rate)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping forwarder...")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("   Disconnecting...")
        lsl_reader.disconnect()
        if sock_game:
            sock_game.close()
        if sock_dashboard:
            sock_dashboard.close()
        print("   ✅ Forwarder stopped.")


if __name__ == "__main__":
    main()

