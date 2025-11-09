import socket
import numpy as np
from scipy.signal import welch
import time

# Receive raw EEG data from OpenBCI GUI (UDP)
UDP_IP = "127.0.0.1"
UDP_PORT_IN = 12345  # same as in OpenBCI GUI
UDP_PORT_OUT = 5005  # game + display listen here

sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_in.bind((UDP_IP, UDP_PORT_IN))

sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def compute_focus(eeg, fs=200):
    """Compute beta/alpha power ratio as focus intensity (0–1)."""
    freqs, psd = welch(eeg, fs=fs, nperseg=fs*2)
    alpha = np.sum(psd[(freqs >= 8) & (freqs <= 13)])
    beta  = np.sum(psd[(freqs >= 13) & (freqs <= 30)])
    focus = beta / (alpha + 1e-6)
    return float(np.clip(focus / 5, 0, 1))  # normalize

buffer = []

print("Listening for EEG data on port", UDP_PORT_IN)
while True:
    data, _ = sock_in.recvfrom(1024)
    try:
        values = np.array(list(map(float, data.decode().strip().split(','))))
        buffer.append(values[0])  # just first channel for now
    except:
        continue

    if len(buffer) >= 400:  # ~2 seconds at 200Hz
        eeg_segment = np.array(buffer[-400:])
        focus = compute_focus(eeg_segment)
        msg = str(focus).encode()
        sock_out.sendto(msg, (UDP_IP, UDP_PORT_OUT))
        print(f"Focus: {focus:.2f}")
        buffer = buffer[-400:]
        time.sleep(0.2)
