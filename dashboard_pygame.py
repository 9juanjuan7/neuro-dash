"""
Doctor-Facing Dashboard - Pygame UI
Uses the same data acquisition and UI style as the game.
"""

try:
    import pygame
except ModuleNotFoundError:
    print("Error: pygame is not installed in this Python environment.")
    print("Install it into your active venv, for example:")
    print("  python3 -m pip install pygame")
    print("Then re-run: python3 dashboard_pygame.py")
    import sys
    sys.exit(1)

import sys
import socket
from collections import deque
from datetime import datetime

# UDP socket to receive focus from forwarder/subscriber
# Bind to 0.0.0.0 to accept from localhost (from forwarder) or external sources
UDP_IP = "0.0.0.0"
UDP_PORT = 5006  # Dashboard port

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)
print(f"[Dashboard] UDP socket bound to {UDP_IP}:{UDP_PORT} - waiting for data...")

# --------------------------
# CONFIG
# --------------------------
WIDTH, HEIGHT = 1200, 800
FPS = 60

# Colors (same as game)
WHITE = (255, 255, 255)
GREY = (120, 120, 120)
BLUE = (50, 150, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (230, 60, 60)
BG = (220, 240, 255)
ORANGE = (255, 120, 0)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pediatric Focus-Drive • Doctor Dashboard")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.Font(None, 48)
large_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 32)
title_font = pygame.font.Font(None, 64)

# --------------------------
# DATA STORAGE
# --------------------------
focus_history = deque(maxlen=300)  # Store last 300 values (~5 seconds at 60 FPS)
time_history = deque(maxlen=300)
ready_flag_history = deque(maxlen=300)

# --------------------------
# UI DRAWING FUNCTIONS
# --------------------------

def draw_focus_bar(focus, x, y, width, height):
    """Draw focus bar (same style as game)"""
    # Border
    pygame.draw.rect(screen, BLACK, (x - 2, y - 2, width + 4, height + 4), 3, border_radius=6)
    # Background
    pygame.draw.rect(screen, GREY, (x, y, width, height), border_radius=6)
    
    # Color mapping for focus (same as game)
    if focus >= 80:
        color = GREEN
    elif focus >= 60:
        color = BLUE
    elif focus >= 40:
        color = ORANGE
    else:
        color = RED
    
    # Fill bar
    fill_width = int((focus / 100.0) * width)
    if fill_width > 0:
        pygame.draw.rect(screen, color, (x, y, fill_width, height), border_radius=6)
    
    # Label
    label_text = font.render("Focus", True, BLACK)
    screen.blit(label_text, (x + 8, y - 1))
    
    # Value text
    value_text = font.render(f"{focus:.1f}%", True, BLACK)
    value_rect = value_text.get_rect()
    value_rect.right = x + width - 8
    value_rect.centery = y + height // 2
    screen.blit(value_text, value_rect)

def draw_status_panel(focus, ready_flag, connection_status, x, y, width, height):
    """Draw status information panel"""
    panel_bg = (240, 250, 255)
    pygame.draw.rect(screen, panel_bg, (x, y, width, height), border_radius=10)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2, border_radius=10)
    
    # Title
    title = title_font.render("Status", True, BLACK)
    screen.blit(title, (x + 20, y + 20))
    
    # Connection status
    status_y = y + 100
    status_label = small_font.render("Connection:", True, BLACK)
    screen.blit(status_label, (x + 20, status_y))
    
    status_color = GREEN if connection_status == "Connected" else RED
    status_text = font.render(connection_status, True, status_color)
    screen.blit(status_text, (x + 20, status_y + 35))
    
    # Ready status
    ready_y = status_y + 100
    ready_label = small_font.render("Ready State:", True, BLACK)
    screen.blit(ready_label, (x + 20, ready_y))
    
    ready_text = "READY" if ready_flag else "Not Ready"
    ready_color = GREEN if ready_flag else GREY
    ready_display = font.render(ready_text, True, ready_color)
    screen.blit(ready_display, (x + 20, ready_y + 35))
    
    # Focus level category
    category_y = ready_y + 100
    category_label = small_font.render("Focus Level:", True, BLACK)
    screen.blit(category_label, (x + 20, category_y))
    
    if focus >= 80:
        category_text = "High"
        category_color = GREEN
    elif focus >= 60:
        category_text = "Medium"
        category_color = BLUE
    elif focus >= 40:
        category_text = "Low"
        category_color = ORANGE
    else:
        category_text = "Very Low"
        category_color = RED
    
    category_display = font.render(category_text, True, category_color)
    screen.blit(category_display, (x + 20, category_y + 35))

def draw_history_chart(x, y, width, height):
    """Draw focus history chart"""
    if len(focus_history) < 2:
        return
    
    # Background
    chart_bg = (250, 250, 255)
    pygame.draw.rect(screen, chart_bg, (x, y, width, height), border_radius=10)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2, border_radius=10)
    
    # Title
    title = title_font.render("Focus History", True, BLACK)
    screen.blit(title, (x + 20, y + 20))
    
    # Chart area
    chart_x = x + 20
    chart_y = y + 80
    chart_w = width - 40
    chart_h = height - 100
    
    # Draw grid lines
    for i in range(5):
        y_pos = chart_y + (i * chart_h // 4)
        pygame.draw.line(screen, (200, 200, 200), (chart_x, y_pos), (chart_x + chart_w, y_pos), 1)
        # Labels
        label_value = 100 - (i * 25)
        label_text = small_font.render(f"{label_value}", True, GREY)
        screen.blit(label_text, (chart_x - 30, y_pos - 10))
    
    # Draw focus line
    if len(focus_history) > 1:
        points = []
        max_val = max(focus_history) if focus_history else 100
        min_val = min(focus_history) if focus_history else 0
        range_val = max_val - min_val if max_val > min_val else 100
        
        for i, val in enumerate(focus_history):
            x_pos = chart_x + int((i / len(focus_history)) * chart_w)
            normalized = (val - min_val) / range_val if range_val > 0 else 0.5
            y_pos = chart_y + chart_h - int(normalized * chart_h)
            points.append((x_pos, y_pos))
        
        # Draw line
        if len(points) > 1:
            pygame.draw.lines(screen, BLUE, False, points, 3)
        
        # Draw current value indicator
        if points:
            last_point = points[-1]
            pygame.draw.circle(screen, GREEN, last_point, 5)
            pygame.draw.circle(screen, BLACK, last_point, 5, 2)

def draw_info_panel(x, y, width, height):
    """Draw information panel with stats"""
    panel_bg = (240, 250, 255)
    pygame.draw.rect(screen, panel_bg, (x, y, width, height), border_radius=10)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2, border_radius=10)
    
    # Title
    title = title_font.render("Statistics", True, BLACK)
    screen.blit(title, (x + 20, y + 20))
    
    if len(focus_history) > 0:
        current = focus_history[-1]
        avg = sum(focus_history) / len(focus_history)
        max_val = max(focus_history)
        min_val = min(focus_history)
        
        stats_y = y + 100
        line_height = 50
        
        # Current
        current_label = small_font.render("Current:", True, BLACK)
        screen.blit(current_label, (x + 20, stats_y))
        current_val = font.render(f"{current:.1f}%", True, BLUE)
        screen.blit(current_val, (x + 150, stats_y))
        
        # Average
        avg_label = small_font.render("Average:", True, BLACK)
        screen.blit(avg_label, (x + 20, stats_y + line_height))
        avg_val = font.render(f"{avg:.1f}%", True, BLUE)
        screen.blit(avg_val, (x + 150, stats_y + line_height))
        
        # Max
        max_label = small_font.render("Maximum:", True, BLACK)
        screen.blit(max_label, (x + 20, stats_y + line_height * 2))
        max_val_text = font.render(f"{max_val:.1f}%", True, GREEN)
        screen.blit(max_val_text, (x + 150, stats_y + line_height * 2))
        
        # Min
        min_label = small_font.render("Minimum:", True, BLACK)
        screen.blit(min_label, (x + 20, stats_y + line_height * 3))
        min_val_text = font.render(f"{min_val:.1f}%", True, RED)
        screen.blit(min_val_text, (x + 150, stats_y + line_height * 3))
        
        # Data points
        count_label = small_font.render("Data Points:", True, BLACK)
        screen.blit(count_label, (x + 20, stats_y + line_height * 4))
        count_val = font.render(f"{len(focus_history)}", True, BLUE)
        screen.blit(count_val, (x + 150, stats_y + line_height * 4))

# --------------------------
# MAIN LOOP
# --------------------------
def main():
    focus = 50
    smoothed_focus = 50
    smoothing_alpha = 0.15  # Same as game
    connection_status = "Waiting..."
    ready_flag = False
    has_received_data = False
    last_focus_value = 50.0
    
    running = True
    
    while running:
        dt = clock.tick(FPS)
        
        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # --- Get focus from UDP socket (same logic as game) ---
        raw_focus = last_focus_value
        
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode()
            
            # LSL subscriber/forwarder sends "attention_score,ready_flag" format
            if ',' in msg:
                parts = msg.split(',')
                focus_value = float(parts[0])
                ready_flag = int(parts[1]) == 1 if len(parts) > 1 else False
            else:
                # Old format - just a number
                focus_value = float(msg)
                ready_flag = False
            
            raw_focus = focus_value * 100  # server sends 0-1, map to 0-100
            has_received_data = True
            last_focus_value = raw_focus
            connection_status = "Connected"
            
            # Debug: print occasionally
            if not hasattr(main, '_last_debug_time'):
                main._last_debug_time = 0
            current_time = pygame.time.get_ticks() / 1000.0
            if current_time - main._last_debug_time > 2.0:
                print(f"[Dashboard] Focus: {raw_focus:.1f}% | Smoothed: {smoothed_focus:.1f}% | Ready: {ready_flag}")
                main._last_debug_time = current_time
                
        except BlockingIOError:
            # No new data - use last received value
            if not has_received_data:
                raw_focus = 50.0
            else:
                raw_focus = last_focus_value
            if has_received_data:
                connection_status = "Connected (buffered)"
            else:
                connection_status = "Waiting for data..."
        except Exception as e:
            # Error - use last value or default
            if has_received_data:
                raw_focus = last_focus_value
                connection_status = "Connected (error)"
            else:
                raw_focus = 50.0
                connection_status = f"Error: {str(e)[:30]}"
        
        # Smooth the focus value (same as game)
        smoothed_focus = smoothing_alpha * raw_focus + (1 - smoothing_alpha) * smoothed_focus
        focus = smoothed_focus
        
        # Store in history
        focus_history.append(focus)
        time_history.append(pygame.time.get_ticks())
        ready_flag_history.append(1 if ready_flag else 0)
        
        # --- DRAW ---
        screen.fill(BG)
        
        # Title
        title = large_font.render("Pediatric Focus-Drive • Doctor Dashboard", True, BLACK)
        title_rect = title.get_rect(center=(WIDTH // 2, 40))
        screen.blit(title, title_rect)
        
        # Main focus bar (large, centered top)
        bar_width = 600
        bar_height = 60
        bar_x = (WIDTH - bar_width) // 2
        bar_y = 120
        draw_focus_bar(focus, bar_x, bar_y, bar_width, bar_height)
        
        # Status panel (left)
        status_panel_width = 350
        status_panel_height = 300
        draw_status_panel(focus, ready_flag, connection_status, 50, 220, status_panel_width, status_panel_height)
        
        # Info panel (right)
        info_panel_width = 350
        info_panel_height = 300
        info_x = WIDTH - info_panel_width - 50
        draw_info_panel(info_x, 220, info_panel_width, info_panel_height)
        
        # History chart (bottom, full width)
        chart_height = 300
        draw_history_chart(50, 550, WIDTH - 100, chart_height)
        
        # Footer
        footer_text = small_font.render("Press ESC or close window to exit", True, GREY)
        footer_rect = footer_text.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        screen.blit(footer_text, footer_rect)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

