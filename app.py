"""
EEG Car Race Game - Main Application
Simple browser-based car race controlled by EEG focus (beta waves).
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time

from eeg_backend import EEGStreamer, BetaWaveProcessor
import eeg_backend
from game_logic import CarRaceGame, GameState
from leaderboard import Leaderboard

# Check if BrainFlow is available
BRAINFLOW_AVAILABLE = getattr(eeg_backend, 'BRAINFLOW_AVAILABLE', False)

# Configure Streamlit page
st.set_page_config(
    page_title="EEG Car Race",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'eeg_streamer' not in st.session_state:
    st.session_state.eeg_streamer = None
if 'eeg_processor' not in st.session_state:
    st.session_state.eeg_processor = BetaWaveProcessor()
if 'game' not in st.session_state:
    st.session_state.game = CarRaceGame()
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = Leaderboard()
if 'use_demo_mode' not in st.session_state:
    st.session_state.use_demo_mode = True
if 'player_name' not in st.session_state:
    st.session_state.player_name = "Player1"
if 'focus_threshold' not in st.session_state:
    st.session_state.focus_threshold = 70.0  # Increased from 30 to 70 for much harder difficulty


def main():
    """Main application."""
    st.title("🏎️ EEG Car Race")
    st.markdown("Race to the finish line using your focus! Maintain high beta waves to move faster.")
    
    # Sidebar
    with st.sidebar:
        st.subheader("⚙️ Settings")
        
        # Demo mode toggle
        st.checkbox(
            "Demo Mode (No Hardware)",
            value=st.session_state.use_demo_mode,
            key="use_demo_mode"
        )
        
        # Hardware connection
        if not st.session_state.use_demo_mode:
            st.info("Connect your OpenBCI device")
            
            # Board selection
            board_type = st.selectbox(
                "Board Type",
                ["Cyton", "Ganglion", "Cyton + Daisy"],
                key="board_type",
                help="Select your OpenBCI board type. This must match your hardware."
            )
            
            # Connection options
            connection_type = st.radio(
                "Connection Type",
                ["Serial Port (USB)", "Bluetooth (MAC)"],
                key="connection_type"
            )
            
            serial_port = None
            mac_address = None
            
            if connection_type == "Serial Port (USB)":
                # Windows: COM3, COM4, etc.
                # Mac: /dev/tty.usbserial-*
                # Linux: /dev/ttyUSB0
                serial_port = st.text_input(
                    "Serial Port",
                    value="COM3",
                    placeholder="COM3 (Windows) or /dev/ttyUSB0 (Linux/Mac)",
                    key="serial_port_input"
                )
                st.caption("💡 Find your port: Windows (Device Manager) or Mac/Linux (ls /dev/tty*)")
            elif connection_type == "Bluetooth (MAC)":
                mac_address = st.text_input(
                    "MAC Address",
                    value="",
                    placeholder="00:11:22:33:44:55",
                    key="mac_address_input"
                )
                st.caption("💡 Find MAC address in your computer's Bluetooth settings")
            
            if st.button("Connect to OpenBCI", type="primary", key="connect"):
                try:
                    # Validate BrainFlow availability
                    if not BRAINFLOW_AVAILABLE:
                        st.error("BrainFlow not installed! Run: pip install brainflow")
                        st.stop()
                    
                    # Import BrainFlow board IDs
                    from brainflow.board_shim import BoardIds
                    
                    # Map board type to BrainFlow ID
                    board_id_map = {
                        "Cyton": BoardIds.CYTON_BOARD.value,
                        "Ganglion": BoardIds.GANGLION_BOARD.value,
                        "Cyton + Daisy": BoardIds.CYTON_DAISY_BOARD.value,
                    }
                    
                    board_id = board_id_map.get(board_type)
                    if board_id is None:
                        st.error(f"Invalid board type: {board_type}")
                        st.stop()
                    
                    # Clean up input: convert empty strings to None
                    if serial_port and serial_port.strip():
                        serial_port = serial_port.strip()
                    else:
                        serial_port = None
                    
                    if mac_address and mac_address.strip():
                        mac_address = mac_address.strip()
                    else:
                        mac_address = None
                    
                    # Validate connection parameters
                    if connection_type == "Serial Port (USB)":
                        if not serial_port:
                            st.error("❌ Please enter a serial port (e.g., COM3 or /dev/ttyUSB0)")
                            st.stop()
                        # Ganglion via USB should work with serial port
                        # Cyton always uses serial port
                    elif connection_type == "Bluetooth (MAC)":
                        if not mac_address:
                            st.error("❌ Please enter a MAC address (e.g., 00:11:22:33:44:55)")
                            st.stop()
                        # Only Ganglion supports BLE
                        if board_type != "Ganglion":
                            st.warning("⚠️ Bluetooth connection is only supported for Ganglion boards")
                            st.stop()
                    
                    # Show connection attempt info
                    with st.spinner(f"Connecting to {board_type}..."):
                        streamer = EEGStreamer(use_demo=False)
                        if streamer.connect(serial_port=serial_port, mac_address=mac_address, board_id=board_id):
                            if streamer.start_streaming():
                                st.session_state.eeg_streamer = streamer
                                st.success("Connected! ✅")
                                st.rerun()
                            else:
                                st.error("❌ Connected but failed to start streaming")
                                st.error("Check that the board is powered on and ready")
                        else:
                            st.error("❌ Connection failed")
                            st.error("**Common issues:**")
                            st.error("1. Device is not connected or powered on")
                            st.error(f"2. {'Serial port' if serial_port else 'MAC address'} is incorrect")
                            st.error("3. Board type doesn't match your device")
                            st.error("4. Another application is using the device")
                            st.error("5. Drivers not installed (Windows) - Install FTDI drivers")
                            st.error("6. Device not in the correct mode")
                            st.info("💡 **Windows Drivers**: Download FTDI VCP drivers from https://ftdichip.com/drivers/vcp-drivers/")
                            st.info("💡 See WINDOWS_DRIVERS.md for detailed driver installation instructions")
                            st.info("💡 Check the terminal/console for detailed error messages")
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    st.error(f"❌ Connection error: {str(e)}")
                    with st.expander("Show detailed error"):
                        st.code(error_details)
                    st.info("💡 See QUICK_CONNECT.md for troubleshooting steps")
        
        # Player name
        st.text_input(
            "Player Name",
            value=st.session_state.player_name,
            key="player_name"
        )
        
        # Focus threshold (for beta power, not normalized focus score)
        st.slider(
            "Focus Threshold",
            10.0, 100.0,
            st.session_state.focus_threshold,
            1.0,
            key="focus_threshold",
            help="Beta power threshold. Higher = requires more focus to move. Game uses normalized threshold (80% default - very hard!)."
        )
        
        # Show game difficulty info
        st.caption("🎯 **Difficulty**: EXTREMELY HIGH focus required! Need ~80%+ focus to move, ~90%+ for good speed.")
        
        # Show calibrated threshold if available
        if 'calibrated_threshold' in st.session_state:
            st.caption(f"💡 Calibrated: {st.session_state.calibrated_threshold:.1f}")
        
        # Update game threshold - focus_score is 0-1, so threshold should be 0-1
        if st.session_state.game.focus_threshold <= 0 or st.session_state.game.focus_threshold > 1:
            st.session_state.game.focus_threshold = 0.80  # Default normalized threshold (80% - much harder!)
        
        # Leaderboard
        st.subheader("🏆 Leaderboard")
        top_records = st.session_state.leaderboard.get_top_records(5)
        if top_records:
            for i, record in enumerate(top_records):
                st.text(f"{i+1}. {record.player_name}: {record.race_time:.2f}s")
        else:
            st.info("No records yet!")
        
        best_time = st.session_state.leaderboard.get_best_time()
        if best_time > 0:
            st.metric("Best Time", f"{best_time:.2f}s")
        st.metric("Best Streak", st.session_state.leaderboard.get_best_streak())
    
    # Initialize EEG streamer if needed
    current_demo_mode = st.session_state.use_demo_mode
    if st.session_state.eeg_streamer is None:
        st.session_state.eeg_streamer = EEGStreamer(use_demo=current_demo_mode)
        st.session_state.eeg_streamer.start_streaming()
    elif st.session_state.eeg_streamer.use_demo != current_demo_mode:
        # Demo mode changed - recreate streamer
        st.session_state.eeg_streamer.disconnect()
        st.session_state.eeg_streamer = EEGStreamer(use_demo=current_demo_mode)
        st.session_state.eeg_streamer.start_streaming()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_race()
    
    with col2:
        render_focus_tracker()


def render_race():
    """Render the race track and controls."""
    game = st.session_state.game
    
    # Race controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Race", type="primary", key="start_race"):
            if game.state == GameState.MENU or game.state == GameState.FINISHED:
                # Start calibration first
                game.start_calibration()
                st.rerun()
    
    with col2:
        if st.button("🔄 Reset", key="reset_race"):
            game.state = GameState.MENU
            st.session_state.eeg_processor.reset()
            st.rerun()
    
    with col3:
        if game.state == GameState.FINISHED:
            if st.button("🏁 New Race", key="new_race"):
                game.state = GameState.MENU
                st.rerun()
    
    # Calibration screen
    if game.state == GameState.CALIBRATING:
        render_calibration()
        return
    
    # Race screen
    if game.state == GameState.RACING:
        # Get EEG data and process
        data = st.session_state.eeg_streamer.get_data(n_samples=250)
        if data is not None:
            st.session_state.eeg_processor.add_data(data)
        
        # Get beta power and focus score
        beta_power = st.session_state.eeg_processor.get_beta_power()
        focus_score = st.session_state.eeg_processor.get_focus_score(
            beta_power, st.session_state.focus_threshold
        )
        
        # Update game threshold
        if game.focus_threshold <= 0 or game.focus_threshold > 1:
            game.focus_threshold = 0.80  # Default normalized threshold (80% - much harder!)
        
        # Update game
        game.update_focus(focus_score)
        
        # Update game state
        current_time = time.time()
        if game.last_update > 0:
            delta_time = current_time - game.last_update
        else:
            delta_time = 0.016  # ~60 FPS
        game.update(delta_time)
        game.last_update = current_time
        
        # Check if race finished
        if game.state == GameState.FINISHED:
            # Save record
            st.session_state.leaderboard.add_record(
                st.session_state.player_name,
                game.race_time,
                game.max_focus_streak
            )
    
    # Render race visualization
    game_data = game.get_game_data()
    render_race_track(game_data)
    
    # Auto-refresh if racing
    if game.state == GameState.RACING:
        time.sleep(0.05)  # ~20 FPS
        st.rerun()


def render_calibration():
    """Render calibration screen."""
    game = st.session_state.game
    
    st.subheader("🎯 Calibration")
    st.info("Please focus for 10 seconds. Keep your attention steady.")
    
    if game.calibration_start_time is None:
        game.calibration_start_time = time.time()
    
    elapsed = time.time() - game.calibration_start_time
    progress = elapsed / game.calibration_duration
    st.progress(min(progress, 1.0))
    st.caption(f"Time: {elapsed:.1f}s / {game.calibration_duration:.1f}s")
    
    # Get EEG data during calibration
    data = st.session_state.eeg_streamer.get_data(n_samples=250)
    if data is not None:
        st.session_state.eeg_processor.add_data(data)
        beta_power = st.session_state.eeg_processor.get_beta_power()
        game.add_calibration_sample(beta_power)
    
    # Check if calibration complete
    if game.is_calibration_complete():
        threshold = game.finish_calibration()
        # Store calibrated threshold (don't modify widget-managed session state)
        st.session_state.calibrated_threshold = threshold
        
        st.success(f"Calibration complete! Recommended threshold: {threshold:.1f}")
        st.info(f"💡 The threshold slider is currently set to {st.session_state.focus_threshold:.1f}. "
                f"You can adjust it if needed, then click 'Start Race'.")
        
        if st.button("Start Race", key="start_after_calibration"):
            # Set normalized threshold for game (focus_score is 0-1)
            # Increased threshold for much harder difficulty
            game.focus_threshold = 0.80  # Normalized threshold (80% - much harder!)
            game.start_race()
            st.rerun()
    else:
        # Show current beta power
        if len(game.calibration_samples) > 0:
            current_beta = np.mean(game.calibration_samples[-10:])
            st.metric("Current Beta Power", f"{current_beta:.1f}")
        
        # Auto-refresh during calibration
        time.sleep(0.1)
        st.rerun()


def render_race_track(game_data: dict):
    """Render simplified horizontal race track with block car."""
    
    st.markdown("### Race Track")
    
    # Get progress - ensure valid value
    progress = game_data.get('progress', 0.0)
    progress = max(0.0, min(progress, 100.0))  # Clamp to valid range
    
    # Create simple Plotly visualization
    fig = go.Figure()
    
    # Track background (horizontal bar)
    track_y = 0.5
    track_height = 0.4
    fig.add_shape(
        type="rect",
        x0=0, y0=track_y - track_height/2, x1=100, y1=track_y + track_height/2,
        fillcolor="#1a1a1a",
        line=dict(color="#666", width=3),
        layer="below"
    )
    
    # Start line (green) - wider for visibility
    fig.add_shape(
        type="rect",
        x0=0, y0=track_y - track_height/2, x1=3, y1=track_y + track_height/2,
        fillcolor="#00ff00",
        line=dict(color="#00aa00", width=2),
        layer="above"
    )
    
    # Finish line (red) - wider for visibility
    fig.add_shape(
        type="rect",
        x0=97, y0=track_y - track_height/2, x1=100, y1=track_y + track_height/2,
        fillcolor="#ff0000",
        line=dict(color="#aa0000", width=2),
        layer="above"
    )
    
    # Car block (red square) - always show if racing or finished
    if game_data['state'] in ['racing', 'finished']:
        # Use actual progress, but clamp for visibility
        car_pos = max(3.0, min(progress, 97.0))
        fig.add_trace(go.Scatter(
            x=[car_pos],
            y=[track_y],
            mode='markers',
            marker=dict(
                size=40,
                color='#ff4444',
                symbol='square',
                line=dict(width=4, color='white'),
                opacity=0.9
            ),
            name='Car',
            showlegend=False,
            hovertemplate='Car<br>Progress: %{x:.1f}%<extra></extra>'
        ))
    elif game_data['state'] == 'menu':
        # Show car at start line in menu
        fig.add_trace(go.Scatter(
            x=[2.0],
            y=[track_y],
            mode='markers',
            marker=dict(
                size=40,
                color='#888888',
                symbol='square',
                line=dict(width=4, color='white'),
                opacity=0.5
            ),
            name='Car',
            showlegend=False
        ))
    
    # Progress bar below track
    if game_data['state'] in ['racing', 'finished']:
        fig.add_shape(
            type="rect",
            x0=0, y0=0.15, x1=progress, y1=0.20,
            fillcolor="#4444ff",
            line=dict(color="#2222aa", width=1),
            layer="above"
        )
        # Progress text
        fig.add_annotation(
            x=progress/2, y=0.175,
            text=f"{progress:.1f}%",
            showarrow=False,
            font=dict(size=12, color="white"),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1
        )
    
    fig.update_layout(
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
        template='plotly_dark',
        height=250,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Race stats
    if game_data['state'] == 'racing':
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Time", f"{game_data['race_time']:.2f}s")
        col2.metric("Speed", f"{game_data['car_speed']:.1f}")
        col3.metric("Progress", f"{game_data['progress']:.1f}%")
        col4.metric("Focus", f"{game_data['current_focus']*100:.0f}%")
    elif game_data['state'] == 'finished':
        st.success(f"🏁 Race Finished! Time: {game_data['race_time']:.2f}s")
        st.info("Check the leaderboard to see your rank!")
    else:
        st.info("Click 'Start Race' to begin")


def render_focus_tracker():
    """Render focus tracking and attention graph."""
    st.subheader("🧠 Focus Tracker")
    
    game = st.session_state.game
    processor = st.session_state.eeg_processor
    
    # Current focus
    current_focus = game.current_focus if game.state == GameState.RACING else 0.0
    focus_threshold = game.focus_threshold
    
    # Focus bar
    st.progress(current_focus)
    st.caption(f"Focus: {current_focus*100:.1f}% | Threshold: {focus_threshold*100:.1f}%")
    
    # Focus status
    if game.state == GameState.RACING:
        if current_focus >= focus_threshold:
            st.success("✅ Focused - Moving!")
        else:
            st.error("❌ Unfocused - Slowing down")
    
    # Focus metrics
    if game.state == GameState.RACING:
        st.metric("Focus Streak", game.focus_streak)
        st.metric("Max Streak", game.max_focus_streak)
    
    # Attention tracker graph
    st.subheader("📈 Attention Tracker")
    timestamps, beta_power, focus_scores = processor.get_history()
    
    if len(timestamps) > 0:
        # Convert timestamps to relative time
        if len(timestamps) > 1:
            time_relative = timestamps - timestamps[0]
        else:
            time_relative = np.array([0])
        
        # Create plot
        fig = go.Figure()
        
        # Beta power
        fig.add_trace(go.Scatter(
            x=time_relative[-100:],  # Last 100 samples
            y=beta_power[-100:],
            mode='lines',
            name='Beta Power',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 0, 255, 0.1)'
        ))
        
        # Threshold line
        fig.add_hline(
            y=st.session_state.focus_threshold,
            line_dash="dash",
            line_color="yellow",
            annotation_text="Threshold"
        )
        
        # Focus scores
        if len(focus_scores) > 0:
            fig.add_trace(go.Scatter(
                x=time_relative[-100:],
                y=[s * 100 for s in focus_scores[-100:]],  # Scale to 0-100
                mode='lines',
                name='Focus Score (%)',
                line=dict(color='green', width=2, dash='dash'),
                yaxis='y2'
            ))
        
        fig.update_layout(
            title="Real-time Attention Tracking",
            xaxis_title="Time (seconds)",
            yaxis_title="Beta Power",
            yaxis2=dict(title="Focus Score (%)", overlaying='y', side='right'),
            template='plotly_dark',
            height=300,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data yet. Start the race to see your attention levels.")


if __name__ == "__main__":
    main()