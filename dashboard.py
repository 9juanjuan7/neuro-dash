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
UDP_PORT = 5005

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("Settings")
FOCUS_THRESHOLD = st.sidebar.slider("Focus threshold", 0, 100, DEFAULTS["FOCUS_THRESHOLD"])
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

# -----------------------------
# Title & Header
# -----------------------------
st.title("👩‍⚕️ Pediatric Focus‑Drive — Doctor Dashboard")
conn_col, mode_col = st.columns([1,1])

with conn_col:
    st.caption("Connection")
    st.info(f"Listening for focus on UDP port {UDP_PORT}")

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
# -----------------------------
UDP_IP = "127.0.0.1"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)
except Exception as e:
    print(f"Warning: Could not bind UDP socket ({e}). Using demo mode.")

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

        # Try to get UDP focus data (0-1 float from focus_server)
        try:
            data, _ = sock.recvfrom(1024)
            attention = int(float(data.decode()) * 100)  # server sends 0-1, map to 0-100
        except BlockingIOError:
            attention = demo_attention()  # fall back to demo
        except Exception:
            attention = demo_attention()  # fall back to demo

        focused = attention >= FOCUS_THRESHOLD

        # --- append to rolling history for graphs ---
        maxlen = max(10, int(UPDATE_HZ * 30))  # keep ~30s of data at UI rate
        try:
            ss.att_history.append(int(attention))
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
            if len(ss.ts_history) > 1:
                # Use simple lists for plotting; no pandas needed
                graph_placeholder.line_chart(ss.att_history)
        except:
            pass

        time.sleep(1.0/UPDATE_HZ)

except st.runtime.scriptrunner.script_run_context.ScriptRunContext:
    # Streamlit may terminate the loop on reruns; ignore for clean exit.
    pass
