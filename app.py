"""
EEG Car Race Game - Main Application
Simple browser-based car race controlled by EEG focus (beta waves).
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time

from eeg_backend import EEGStreamer, BetaWaveProcessor
from game_logic import CarRaceGame, GameState
from leaderboard import Leaderboard

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
    st.session_state.focus_threshold = 30.0


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
            
            # Connection options
            connection_type = st.radio(
                "Connection Type",
                ["Auto-detect", "Serial Port", "Bluetooth (MAC)"],
                key="connection_type"
            )
            
            serial_port = None
            mac_address = None
            
            if connection_type == "Serial Port":
                # Windows: COM3, COM4, etc.
                # Mac: /dev/tty.usbserial-*
                # Linux: /dev/ttyUSB0
                serial_port = st.text_input(
                    "Serial Port",
                    value="COM3",
                    placeholder="COM3 (Windows) or /dev/ttyUSB0 (Linux/Mac)",
                    key="serial_port_input"
                )
            elif connection_type == "Bluetooth (MAC)":
                mac_address = st.text_input(
                    "MAC Address",
                    value="",
                    placeholder="XX:XX:XX:XX:XX:XX",
                    key="mac_address_input"
                )
            
            if st.button("Connect to OpenBCI", key="connect"):
                streamer = EEGStreamer(use_demo=False)
                if streamer.connect(serial_port=serial_port, mac_address=mac_address):
                    if streamer.start_streaming():
                        st.session_state.eeg_streamer = streamer
                        st.success("Connected! ✅")
                    else:
                        st.error("Failed to start streaming")
                else:
                    st.error("Connection failed. Please check:")
                    st.error("1. Device is connected and powered on")
                    st.error("2. Serial port/MAC address is correct")
                    st.error("3. No other applications are using the device")
                    st.error("4. Drivers are installed (Windows)")
                    st.info("💡 See OPENBCI_SETUP.md for detailed instructions")
        
        # Player name
        st.text_input(
            "Player Name",
            value=st.session_state.player_name,
            key="player_name"
        )
        
        # Focus threshold
        st.slider(
            "Focus Threshold",
            10.0, 100.0,
            st.session_state.focus_threshold,
            1.0,
            key="focus_threshold"
        )
        
        # Show calibrated threshold if available
        if 'calibrated_threshold' in st.session_state:
            st.caption(f"💡 Calibrated: {st.session_state.calibrated_threshold:.1f}")
        
        # Update game threshold - focus_score is 0-1, so threshold should be 0-1
        if st.session_state.game.focus_threshold <= 0 or st.session_state.game.focus_threshold > 1:
            st.session_state.game.focus_threshold = 0.6  # Default normalized threshold
        
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
            game.focus_threshold = 0.6  # Default normalized threshold
        
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
            game.focus_threshold = 0.6  # Normalized threshold
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
    """Render race track using Plotly."""
    fig = go.Figure()
    
    # Background (track)
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=800, y1=600,
        fillcolor="#1a1a1a",
        line=dict(color="white", width=2)
    )
    
    # Draw track lines
    for y in range(0, 600, 50):
        fig.add_shape(
            type="line",
            x0=350, y0=y, x1=450, y1=y,
            line=dict(color="yellow", width=2, dash="dash")
        )
    
    # Finish line (top)
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=800, y1=20,
        fillcolor="green",
        line=dict(color="white", width=2),
        opacity=0.5
    )
    
    if game_data['state'] == 'racing' or game_data['state'] == 'finished':
        # Draw car
        car_x = game_data['car_x']
        car_y = game_data['car_y']
        # Clamp to visible area
        car_x = max(25, min(775, car_x))
        car_y = max(25, min(575, car_y))
        
        fig.add_trace(go.Scatter(
            x=[car_x],
            y=[car_y],
            mode='markers',
            marker=dict(size=40, color='red', symbol='square', line=dict(width=3, color='white')),
            name='Car'
        ))
        
        # Progress bar
        progress = game_data['progress']
        fig.add_shape(
            type="rect",
            x0=50, y0=580, x1=50 + (700 * progress / 100), y1=590,
            fillcolor="blue",
            line=dict(color="white", width=1)
        )
    
    elif game_data['state'] == 'finished':
        # Finished screen
        fig.add_annotation(
            x=400, y=300,
            text="🏁 FINISHED!",
            showarrow=False,
            font=dict(size=40, color="green")
        )
        fig.add_annotation(
            x=400, y=250,
            text=f"Time: {game_data['race_time']:.2f}s",
            showarrow=False,
            font=dict(size=24, color="white")
        )
    else:
        # Menu screen
        fig.add_annotation(
            x=400, y=300,
            text="🏎️ EEG CAR RACE",
            showarrow=False,
            font=dict(size=30, color="cyan")
        )
        fig.add_annotation(
            x=400, y=250,
            text="Click 'Start Race' to begin",
            showarrow=False,
            font=dict(size=18, color="white")
        )
    
    fig.update_layout(
        xaxis=dict(range=[0, 800], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[600, 0], showgrid=False, zeroline=False, showticklabels=False),
        template='plotly_dark',
        height=500,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, width='stretch')
    
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