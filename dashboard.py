import time
import random
import socket
from datetime import datetime
from typing import Optional, Tuple

import streamlit as st

# -----------------------------
# UI Config & Defaults
# -----------------------------
st.set_page_config(page_title="Pediatric Focus‑Drive • Doctor UI", layout="centered")

DEFAULTS = {
    "FOCUS_THRESHOLD": 70,
    "STILLNESS_THRESHOLD": 0.15,
    "READY_SECONDS": 8.0,
    "READY_WINDOW_HOLD": 4.0,
    "UPDATE_HZ": 10,
}
# UDP port used by local focus servers (focus_server.py and server+display)
# Dashboard uses port 5006 to avoid conflict with game (port 5005)
UDP_PORT = 5006

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("Settings")
st.sidebar.caption("⚠️ Note: These settings only affect the dashboard UI. The actual focus calculation threshold is set in focus_server.py with --threshold argument.")
FOCUS_THRESHOLD = st.sidebar.slider("Focus threshold (for READY state)", 0, 100, DEFAULTS["FOCUS_THRESHOLD"], 
                                     help="Attention level (0-100) required to trigger READY state. This is for UI display only - does not affect EEG processing.")
READY_SECONDS = st.sidebar.slider("Seconds required to become READY", 2, 15, int(DEFAULTS["READY_SECONDS"]))
READY_WINDOW_HOLD = st.sidebar.slider("READY hold (seconds)", 1, 10, int(DEFAULTS["READY_WINDOW_HOLD"]))
UPDATE_HZ = st.sidebar.slider("UI update rate (Hz)", 2, 20, DEFAULTS["UPDATE_HZ"])

stop_btn = st.sidebar.button("Stop app")

if stop_btn:
    st.stop()

# -----------------------------
# Session State
# -----------------------------
ss = st.session_state
if "ready_timer" not in ss:
    ss.ready_timer = 0.0
if "in_ready" not in ss:
    ss.in_ready = False
if "ready_window_start" not in ss:
    ss.ready_window_start = None
if "ready_log" not in ss:
    ss.ready_log = []  # list of (start_ts_str, duration_s)
if "last_update" not in ss:
    ss.last_update = time.time()
if "att_base" not in ss:
    ss.att_base = random.randint(40, 85)
if "att_history" not in ss:
    ss.att_history = []
if "artifact_history" not in ss:
    ss.artifact_history = []
if "ts_history" not in ss:
    ss.ts_history = []
if "using_demo" not in ss:
    ss.using_demo = True
if "last_real_data_time" not in ss:
    ss.last_real_data_time = None
if "data_source_status" not in ss:
    ss.data_source_status = "Demo Mode"
if "smoothed_focus" not in ss:
    ss.smoothed_focus = 50.0  # Initialize smoothed focus (same as game)
if "smoothing_alpha" not in ss:
    ss.smoothing_alpha = 0.15  # Same smoothing as game (15% new, 85% old)
if "ready_flag_from_lsl" not in ss:
    ss.ready_flag_from_lsl = None  # Ready flag from LSL subscriber

# -----------------------------
# Title & Header
# -----------------------------
st.title("👩‍⚕️ Pediatric Focus‑Drive — Doctor Dashboard")
conn_col, mode_col = st.columns([1,1])

# Status placeholder (will be updated in the loop)
status_placeholder = conn_col.empty()

with conn_col:
    st.caption("Connection")
    # Initial status - will be updated in the loop via placeholder
    status_placeholder.info("🟡 Initializing...")

with mode_col:
    st.caption("Update rate")
    st.write(f"{UPDATE_HZ} Hz")

st.divider()

# -----------------------------
# Layout Placeholders
# -----------------------------
ri_col, cd_col = st.columns([1,1])
ready_placeholder = ri_col.empty()
ready_bar_placeholder = ri_col.empty()
countdown_placeholder = cd_col.empty()

att_row = st.columns([3,1])
att_bar_placeholder = att_row[0].empty()
att_num_placeholder = att_row[1].empty()
st.subheader("Status")
sp1, sp2, sp3 = st.columns([1,1,2])
artifact_placeholder = sp1.empty()
still_placeholder = sp2.empty()
log_placeholder = sp3.empty()

# Charts area (attention + artifact history)
graph_placeholder = st.empty()

# -----------------------------
# Demo mode (same pattern as focus_race.py)
# -----------------------------
def demo_attention() -> int:
    """Return simulated attention 0-100 using a random walk."""
    base = ss.att_base
    step = random.randint(-5, 5)
    base = max(25, min(98, base + step))
    ss.att_base = base
    return base

# -----------------------------
# Rendering
# -----------------------------
def render_ready(ready: bool):
    if ready:
        ready_placeholder.markdown(
            "<h3 style='background:#18a55822;border:1px solid #18a558;padding:10px;border-radius:12px;text-align:center;'>"
            "🟢 READY</h3>", unsafe_allow_html=True)
    else:
        ready_placeholder.markdown(
            "<h3 style='background:#ddd;border:1px solid #aaa;padding:10px;border-radius:12px;text-align:center;'>"
            "⚪ Not Ready</h3>", unsafe_allow_html=True)

def render_countdown(seconds_left: float):
    cd = f'{max(0.0, seconds_left):.1f}'
    countdown_placeholder.markdown(
        f"<div style='text-align:center'><h4>Countdown to READY</h4>"
        f"<div style='font-size:28px;'><b>{cd} s</b></div></div>", unsafe_allow_html=True)

def render_attention(attention: int):
    att_bar_placeholder.progress(attention/100.0, text=f"Attention {attention}/100")
    att_num_placeholder.metric("Attention", f"{attention}")

def render_status():
    """Show focus history"""
    if ss.ready_log:
        rows = "\n".join([f"- {t} • {d:.1f}s" for (t, d) in ss.ready_log[-5:]])
    else:
        rows = "_No ready windows yet_"
    log_placeholder.markdown(f"**Recent Ready Windows (last 5)**  \n{rows}")

# -----------------------------
# UDP socket to receive focus from server (same as focus_race.py)
# Store socket in session state to persist across Streamlit reruns
# -----------------------------
UDP_IP = "127.0.0.1"
if "udp_sock" not in ss:
    ss.udp_sock = None
    ss.socket_bound = False
    try:
        ss.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ss.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow multiple binds
        try:
            ss.udp_sock.bind((UDP_IP, UDP_PORT))
            ss.udp_sock.setblocking(False)
            ss.socket_bound = True
            ss.data_source_status = f"✅ Listening on UDP port {UDP_PORT} (waiting for focus_server.py...)"
            print(f"[Dashboard] Successfully bound to UDP port {UDP_PORT}")
        except OSError as e:
            # Port already in use - this shouldn't happen with separate ports
            ss.udp_sock.setblocking(False)
            ss.socket_bound = False
            ss.data_source_status = f"⚠️ Port {UDP_PORT} in use - cannot receive data"
            print(f"[Dashboard] ERROR: Port {UDP_PORT} is already in use: {e}")
    except Exception as e:
        print(f"[Dashboard] ERROR: Could not create UDP socket ({e}). Using demo mode.")
        ss.data_source_status = f"❌ Demo Mode (socket error: {str(e)[:40]})"

# Use socket from session state
sock = ss.udp_sock
socket_bound = ss.socket_bound

# -----------------------------
# Main loop (same pattern as focus_race.py)
# -----------------------------
try:
    while True:
        now = time.time()
        dt = now - ss.last_update
        if dt <= 0:
            dt = 1.0/UPDATE_HZ
        ss.last_update = now

        # Default if no UDP data arrives (same as focus_race.py)
        attention = 50
        received_real_data = False

        # Try to get UDP focus data (0-1 float from focus_server)
        if sock is not None:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode()
                
                # LSL subscriber sends "attention_score,ready_flag" format
                # Old format (just number) is also supported for backward compatibility
                if ',' in msg:
                    parts = msg.split(',')
                    focus_value = float(parts[0])
                    ready_flag = int(parts[1]) == 1 if len(parts) > 1 else False
                    # Store ready flag in session state
                    ss.ready_flag_from_lsl = ready_flag
                else:
                    # Old format - just a number
                    focus_value = float(msg)
                    ss.ready_flag_from_lsl = None
                
                raw_focus = focus_value * 100  # server sends 0-1, map to 0-100
                
                # Apply same smoothing as game (exponential moving average)
                ss.smoothed_focus = ss.smoothing_alpha * raw_focus + (1 - ss.smoothing_alpha) * ss.smoothed_focus
                attention = int(ss.smoothed_focus)  # Use smoothed value
                
                received_real_data = True
                ss.last_real_data_time = now
                ss.using_demo = False
                ss.data_source_status = f"✅ Receiving EEG Data (focus: {focus_value:.3f})"
                # Debug: print to console (visible in terminal)
                if not hasattr(ss, '_last_print_time') or (now - ss._last_print_time) > 5.0:
                    print(f"[Dashboard] Received EEG data: raw={raw_focus:.1f}, smoothed={ss.smoothed_focus:.1f}, attention={attention}%")
                    ss._last_print_time = now
            except BlockingIOError:
                # No data available this frame - check if we should use demo or last known value
                if ss.last_real_data_time is not None and (now - ss.last_real_data_time) < 2.0:
                    # Recently received real data, keep using smoothed value (same as game)
                    attention = int(ss.smoothed_focus)  # Use last smoothed value
                    received_real_data = True
                    ss.using_demo = False
                    ss.data_source_status = "✅ Receiving EEG Data (buffered)"
                else:
                    # No real data for a while, use demo
                    attention = demo_attention()
                    received_real_data = False
                    ss.using_demo = True
                    if socket_bound:
                        ss.data_source_status = "⚠️ Demo Mode (no data received)"
                    else:
                        ss.data_source_status = "⚠️ Demo Mode (port conflict)"
            except Exception as e:
                # Socket error - use demo
                attention = demo_attention()
                received_real_data = False
                ss.using_demo = True
                ss.data_source_status = f"⚠️ Demo Mode (error: {str(e)[:30]})"
        else:
            # No socket available
            attention = demo_attention()
            received_real_data = False
            ss.using_demo = True
            ss.data_source_status = "⚠️ Demo Mode (no socket)"

        # Use ready flag from LSL if available, otherwise compute from attention
        if ss.ready_flag_from_lsl is not None:
            focused = ss.ready_flag_from_lsl
        else:
            focused = attention >= FOCUS_THRESHOLD

        # --- append to rolling history for graphs ---
        # Always use smoothed value for history (same as what's displayed)
        maxlen = max(10, int(UPDATE_HZ * 30))  # keep ~30s of data at UI rate
        try:
            # Use smoothed_focus directly if available, otherwise use attention
            history_value = int(ss.smoothed_focus) if hasattr(ss, 'smoothed_focus') and ss.smoothed_focus is not None else int(attention)
            ss.att_history.append(history_value)
        except Exception:
            ss.att_history.append(0)
        ss.ts_history.append(now)
        # trim
        if len(ss.att_history) > maxlen:
            ss.att_history = ss.att_history[-maxlen:]
            ss.ts_history = ss.ts_history[-maxlen:]

        if not ss.in_ready:
            if focused:
                ss.ready_timer += dt
            else:
                ss.ready_timer = max(0.0, ss.ready_timer - dt*0.5)  # gentle decay if not focused
            seconds_left = max(0.0, READY_SECONDS - ss.ready_timer)
            if ss.ready_timer >= READY_SECONDS:
                ss.in_ready = True
                ss.ready_window_start = now
                seconds_left = 0.0
        else:
            seconds_left = 0.0
            if (now - ss.ready_window_start) >= READY_WINDOW_HOLD:
                ts = datetime.now().strftime("%H:%M:%S")
                ss.ready_log.append((ts, float(READY_WINDOW_HOLD)))
                ss.in_ready = False
                ss.ready_timer = 0.0
                ss.ready_window_start = None

        # Update status display
        current_time_for_status = time.time()
        is_receiving_real_status = False
        time_since_last_data_status = None
        
        if "last_real_data_time" in ss and ss.last_real_data_time is not None:
            time_since_last_data_status = current_time_for_status - ss.last_real_data_time
            if time_since_last_data_status < 2.0:  # Received data in last 2 seconds
                is_receiving_real_status = True
        
        # Determine status text
        if is_receiving_real_status:
            status_emoji = "🟢"
            status_text = ss.get("data_source_status", "✅ Receiving EEG Data")
            status_detail = f"✅ Receiving real EEG data ({time_since_last_data_status:.1f}s ago)"
        elif "last_real_data_time" in ss and ss.last_real_data_time is not None:
            status_emoji = "🟡"
            status_text = f"⚠️ No recent data ({time_since_last_data_status:.1f}s ago)"
            status_detail = f"⚠️ Last data: {time_since_last_data_status:.1f}s ago - Check focus_server.py"
        else:
            status_emoji = "🟡"
            status_text = ss.get("data_source_status", "⚠️ Demo Mode - Waiting for focus_server.py")
            status_detail = "⚠️ Make sure focus_server.py is running and sending to port 5006!"
        
        status_placeholder.info(f"{status_emoji} {status_text}")
        # Note: We can't update the caption dynamically, so the detail is in the main status text
        
        render_ready(ss.in_ready)
        render_countdown(seconds_left)
        render_attention(attention)
        render_status()

        # Render readiness progress bar (0..1)
        try:
            progress = min(1.0, ss.ready_timer / float(READY_SECONDS))
        except Exception:
            progress = 0.0
        ready_bar_placeholder.progress(progress, text=f"Readiness: {int(progress*100)}%")

        # Render history chart (attention only, like focus_race.py's display)
        try:
            if len(ss.att_history) > 1:
                # Use simple lists for plotting; no pandas needed
                # Create a dict with index for better chart updates
                chart_data = {f"t{i}": val for i, val in enumerate(ss.att_history)}
                graph_placeholder.line_chart(ss.att_history, use_container_width=True)
        except Exception as e:
            # Debug: print chart errors
            if not hasattr(ss, '_chart_error_printed'):
                print(f"[Dashboard] Chart error: {e}")
                ss._chart_error_printed = True
            pass

        time.sleep(1.0/UPDATE_HZ)

except (KeyboardInterrupt, SystemExit):
    # Normal termination
    pass
except Exception:
    # Streamlit may terminate the loop on reruns; ignore for clean exit
    # This catches StopException and other Streamlit rerun exceptions
    pass
