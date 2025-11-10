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
import argparse
from collections import deque
from datetime import datetime

# Parse command line arguments
parser = argparse.ArgumentParser(description='Doctor Dashboard for Focus-Drive Game')
parser.add_argument('--pi-ip', type=str, default=None,
                    help='Raspberry Pi IP address (e.g., 100.72.174.84) for sending game commands. If not provided, buttons will be disabled.')
args = parser.parse_args()

# UDP socket to receive focus from forwarder/subscriber
# Bind to 0.0.0.0 to accept from localhost (from forwarder) or external sources
UDP_IP = "0.0.0.0"
UDP_PORT = 5006  # Dashboard port
GAME_COMMAND_PORT = 5007  # Port for sending commands to game on Pi

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)
print(f"[Dashboard] UDP socket bound to {UDP_IP}:{UDP_PORT} - waiting for data...")

# Command socket for sending commands to game
command_sock = None
if args.pi_ip:
    command_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[Dashboard] Command socket ready - will send commands to {args.pi_ip}:{GAME_COMMAND_PORT}")
else:
    print(f"[Dashboard] Warning: No Pi IP provided. Game control buttons will be disabled.")
    print(f"   Run with --pi-ip <pi-ip-address> to enable game control")

# --------------------------
# CONFIG
# --------------------------
INITIAL_WIDTH, INITIAL_HEIGHT = 1200, 800
MIN_WIDTH, MIN_HEIGHT = 800, 600
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
screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Pediatric Focus-Drive • Doctor Dashboard (F11: Fullscreen, ESC: Exit)")
clock = pygame.time.Clock()

# Track window size and fullscreen state
WIDTH, HEIGHT = INITIAL_WIDTH, INITIAL_HEIGHT
fullscreen = False

# Fonts (will be scaled dynamically)
base_font_size = 48
base_large_font_size = 72
base_small_font_size = 32
base_title_font_size = 64

def get_scaled_fonts():
    """Get fonts scaled to current window size"""
    scale = min(WIDTH / INITIAL_WIDTH, HEIGHT / INITIAL_HEIGHT)
    return {
        'font': pygame.font.Font(None, int(base_font_size * scale)),
        'large_font': pygame.font.Font(None, int(base_large_font_size * scale)),
        'small_font': pygame.font.Font(None, int(base_small_font_size * scale)),
        'title_font': pygame.font.Font(None, int(base_title_font_size * scale)),
    }

# Initial fonts
fonts = get_scaled_fonts()
font = fonts['font']
large_font = fonts['large_font']
small_font = fonts['small_font']
title_font = fonts['title_font']

# --------------------------
# DATA STORAGE
# --------------------------
focus_history = deque(maxlen=300)  # Store last 300 values (~5 seconds at 60 FPS)
time_history = deque(maxlen=300)
ready_flag_history = deque(maxlen=300)

# --------------------------
# UI DRAWING FUNCTIONS
# --------------------------

def draw_focus_bar(focus, x, y, width, height, fonts):
    """Draw focus bar (same style as game) - scaled"""
    scale = min(WIDTH / INITIAL_WIDTH, HEIGHT / INITIAL_HEIGHT)
    border_width = max(1, int(3 * scale))
    border_radius = max(1, int(6 * scale))
    
    # Border
    pygame.draw.rect(screen, BLACK, (x - 2*scale, y - 2*scale, width + 4*scale, height + 4*scale), border_width, border_radius=border_radius)
    # Background
    pygame.draw.rect(screen, GREY, (x, y, width, height), border_radius=border_radius)
    
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
        pygame.draw.rect(screen, color, (x, y, fill_width, height), border_radius=border_radius)
    
    # Label
    label_text = fonts['font'].render("Focus", True, BLACK)
    screen.blit(label_text, (x + 8*scale, y - 1*scale))
    
    # Value text
    value_text = fonts['font'].render(f"{focus:.1f}%", True, BLACK)
    value_rect = value_text.get_rect()
    value_rect.right = x + width - 8*scale
    value_rect.centery = y + height // 2
    screen.blit(value_text, value_rect)

def draw_status_panel(focus, ready_flag, connection_status, x, y, width, height, fonts):
    """Draw status information panel - scaled"""
    scale = min(WIDTH / INITIAL_WIDTH, HEIGHT / INITIAL_HEIGHT)
    border_width = max(1, int(2 * scale))
    border_radius = max(1, int(10 * scale))
    padding = 20 * scale
    spacing = 100 * scale
    line_spacing = 35 * scale
    
    panel_bg = (240, 250, 255)
    pygame.draw.rect(screen, panel_bg, (x, y, width, height), border_radius=border_radius)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), border_width, border_radius=border_radius)
    
    # Title
    title = fonts['title_font'].render("Status", True, BLACK)
    screen.blit(title, (x + padding, y + padding))
    
    # Connection status
    status_y = y + spacing
    status_label = fonts['small_font'].render("Connection:", True, BLACK)
    screen.blit(status_label, (x + padding, status_y))
    
    status_color = GREEN if "Connected" in connection_status else RED
    status_text = fonts['font'].render(connection_status[:30], True, status_color)  # Truncate if too long
    screen.blit(status_text, (x + padding, status_y + line_spacing))
    
    # Ready status
    ready_y = status_y + spacing
    ready_label = fonts['small_font'].render("Ready State:", True, BLACK)
    screen.blit(ready_label, (x + padding, ready_y))
    
    ready_text = "READY" if ready_flag else "Not Ready"
    ready_color = GREEN if ready_flag else GREY
    ready_display = fonts['font'].render(ready_text, True, ready_color)
    screen.blit(ready_display, (x + padding, ready_y + line_spacing))
    
    # Focus level category
    category_y = ready_y + spacing
    category_label = fonts['small_font'].render("Focus Level:", True, BLACK)
    screen.blit(category_label, (x + padding, category_y))
    
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
    
    category_display = fonts['font'].render(category_text, True, category_color)
    screen.blit(category_display, (x + padding, category_y + line_spacing))

def draw_history_chart(x, y, width, height, fonts):
    """Draw focus history chart - scaled"""
    if len(focus_history) < 2:
        return
    
    scale = min(WIDTH / INITIAL_WIDTH, HEIGHT / INITIAL_HEIGHT)
    border_width = max(1, int(2 * scale))
    border_radius = max(1, int(10 * scale))
    padding = 20 * scale
    title_spacing = 80 * scale
    label_offset = 30 * scale
    
    # Background
    chart_bg = (250, 250, 255)
    pygame.draw.rect(screen, chart_bg, (x, y, width, height), border_radius=border_radius)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), border_width, border_radius=border_radius)
    
    # Title
    title = fonts['title_font'].render("Focus History", True, BLACK)
    screen.blit(title, (x + padding, y + padding))
    
    # Chart area
    chart_x = x + padding
    chart_y = y + title_spacing
    chart_w = width - 2 * padding
    chart_h = height - title_spacing - padding
    
    # Draw grid lines
    line_width = max(1, int(1 * scale))
    for i in range(5):
        y_pos = chart_y + (i * chart_h // 4)
        pygame.draw.line(screen, (200, 200, 200), (chart_x, y_pos), (chart_x + chart_w, y_pos), line_width)
        # Labels
        label_value = 100 - (i * 25)
        label_text = fonts['small_font'].render(f"{label_value}", True, GREY)
        screen.blit(label_text, (chart_x - label_offset, y_pos - 10*scale))
    
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
            line_thickness = max(1, int(3 * scale))
            pygame.draw.lines(screen, BLUE, False, points, line_thickness)
        
        # Draw current value indicator
        if points:
            last_point = points[-1]
            circle_radius = max(3, int(5 * scale))
            pygame.draw.circle(screen, GREEN, last_point, circle_radius)
            pygame.draw.circle(screen, BLACK, last_point, circle_radius, max(1, int(2 * scale)))

def draw_info_panel(x, y, width, height, fonts):
    """Draw information panel with stats - scaled"""
    scale = min(WIDTH / INITIAL_WIDTH, HEIGHT / INITIAL_HEIGHT)
    border_width = max(1, int(2 * scale))
    border_radius = max(1, int(10 * scale))
    padding = 20 * scale
    stats_y_offset = 100 * scale
    line_height = 50 * scale
    value_x = 150 * scale
    
    panel_bg = (240, 250, 255)
    pygame.draw.rect(screen, panel_bg, (x, y, width, height), border_radius=border_radius)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), border_width, border_radius=border_radius)
    
    # Title
    title = fonts['title_font'].render("Statistics", True, BLACK)
    screen.blit(title, (x + padding, y + padding))
    
    if len(focus_history) > 0:
        current = focus_history[-1]
        avg = sum(focus_history) / len(focus_history)
        max_val = max(focus_history)
        min_val = min(focus_history)
        
        stats_y = y + stats_y_offset
        
        # Current
        current_label = fonts['small_font'].render("Current:", True, BLACK)
        screen.blit(current_label, (x + padding, stats_y))
        current_val = fonts['font'].render(f"{current:.1f}%", True, BLUE)
        screen.blit(current_val, (x + value_x, stats_y))
        
        # Average
        avg_label = fonts['small_font'].render("Average:", True, BLACK)
        screen.blit(avg_label, (x + padding, stats_y + line_height))
        avg_val = fonts['font'].render(f"{avg:.1f}%", True, BLUE)
        screen.blit(avg_val, (x + value_x, stats_y + line_height))
        
        # Max
        max_label = fonts['small_font'].render("Maximum:", True, BLACK)
        screen.blit(max_label, (x + padding, stats_y + line_height * 2))
        max_val_text = fonts['font'].render(f"{max_val:.1f}%", True, GREEN)
        screen.blit(max_val_text, (x + value_x, stats_y + line_height * 2))
        
        # Min
        min_label = fonts['small_font'].render("Minimum:", True, BLACK)
        screen.blit(min_label, (x + padding, stats_y + line_height * 3))
        min_val_text = fonts['font'].render(f"{min_val:.1f}%", True, RED)
        screen.blit(min_val_text, (x + value_x, stats_y + line_height * 3))
        
        # Data points
        count_label = fonts['small_font'].render("Data Points:", True, BLACK)
        screen.blit(count_label, (x + padding, stats_y + line_height * 4))
        count_val = fonts['font'].render(f"{len(focus_history)}", True, BLUE)
        screen.blit(count_val, (x + value_x, stats_y + line_height * 4))

def draw_control_panel(x, y, width, height, pi_ip, fonts):
    """Draw game control panel with Play Again and Quit buttons - scaled"""
    scale = min(WIDTH / INITIAL_WIDTH, HEIGHT / INITIAL_HEIGHT)
    border_width = max(1, int(2 * scale))
    border_radius = max(1, int(10 * scale))
    padding = 20 * scale
    button_padding = 20 * scale
    button_height = 60 * scale
    button_spacing = 20 * scale
    title_spacing = 100 * scale
    button_border = max(1, int(3 * scale))
    button_radius = max(1, int(8 * scale))
    
    panel_bg = (240, 250, 255)
    pygame.draw.rect(screen, panel_bg, (x, y, width, height), border_radius=border_radius)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), border_width, border_radius=border_radius)
    
    # Title
    title = fonts['title_font'].render("Game Control", True, BLACK)
    screen.blit(title, (x + padding, y + padding))
    
    if not pi_ip:
        # Show warning if no Pi IP
        warning = fonts['small_font'].render("No Pi IP configured", True, RED)
        screen.blit(warning, (x + padding, y + title_spacing))
        hint = fonts['small_font'].render("Run with --pi-ip", True, GREY)
        screen.blit(hint, (x + padding, y + title_spacing + 30*scale))
        return None, None
    
    # Button dimensions
    button_width = width - 2 * button_padding
    
    # Play Again button
    play_y = y + title_spacing
    play_again_rect = pygame.Rect(x + button_padding, play_y, button_width, button_height)
    mouse_pos = pygame.mouse.get_pos()
    play_hover = play_again_rect.collidepoint(mouse_pos)
    play_color = (50, 200, 50) if play_hover else (100, 150, 100)
    pygame.draw.rect(screen, play_color, play_again_rect, border_radius=button_radius)
    pygame.draw.rect(screen, BLACK, play_again_rect, button_border, border_radius=button_radius)
    play_text = fonts['font'].render("Play Again", True, WHITE)
    play_text_rect = play_text.get_rect(center=play_again_rect.center)
    screen.blit(play_text, play_text_rect)
    
    # Quit button
    quit_y = play_y + button_height + button_spacing
    quit_rect = pygame.Rect(x + button_padding, quit_y, button_width, button_height)
    quit_hover = quit_rect.collidepoint(mouse_pos)
    quit_color = (200, 50, 50) if quit_hover else (150, 100, 100)
    pygame.draw.rect(screen, quit_color, quit_rect, border_radius=button_radius)
    pygame.draw.rect(screen, BLACK, quit_rect, button_border, border_radius=button_radius)
    quit_text = fonts['font'].render("Quit Game", True, WHITE)
    quit_text_rect = quit_text.get_rect(center=quit_rect.center)
    screen.blit(quit_text, quit_text_rect)
    
    return play_again_rect, quit_rect

# --------------------------
# MAIN LOOP
# --------------------------
def main():
    global WIDTH, HEIGHT, fullscreen, screen
    
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
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                if not fullscreen:
                    WIDTH, HEIGHT = max(MIN_WIDTH, event.w), max(MIN_HEIGHT, event.h)
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    # Update fonts for new size
                    fonts = get_scaled_fonts()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    # Toggle fullscreen
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        WIDTH, HEIGHT = screen.get_size()
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    # Update fonts for new size
                    fonts = get_scaled_fonts()
                elif event.key == pygame.K_ESCAPE:
                    if fullscreen:
                        # Exit fullscreen on ESC
                        fullscreen = False
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    else:
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
        
        # Update fonts if window size changed
        fonts = get_scaled_fonts()
        scale = min(WIDTH / INITIAL_WIDTH, HEIGHT / INITIAL_HEIGHT)
        
        # --- DRAW ---
        screen.fill(BG)
        
        # Calculate scaled positions and sizes
        title_y = 40 * scale
        bar_y = 120 * scale
        bar_width = 600 * scale
        bar_height = 60 * scale
        bar_x = (WIDTH - bar_width) // 2
        
        panels_y = 220 * scale
        panel_spacing = 20 * scale
        status_panel_width = 350 * scale
        status_panel_height = 300 * scale
        info_panel_width = 350 * scale
        info_panel_height = 250 * scale
        control_panel_width = 350 * scale
        control_panel_height = 200 * scale
        
        side_padding = 50 * scale
        chart_y = 550 * scale
        chart_height = 300 * scale
        footer_y = HEIGHT - 20 * scale
        
        # Title
        title = fonts['large_font'].render("Pediatric Focus-Drive • Doctor Dashboard", True, BLACK)
        title_rect = title.get_rect(center=(WIDTH // 2, title_y))
        screen.blit(title, title_rect)
        
        # Main focus bar (large, centered top)
        draw_focus_bar(focus, bar_x, bar_y, bar_width, bar_height, fonts)
        
        # Status panel (left)
        draw_status_panel(focus, ready_flag, connection_status, side_padding, panels_y, status_panel_width, status_panel_height, fonts)
        
        # Info panel (right top)
        info_x = WIDTH - info_panel_width - side_padding
        draw_info_panel(info_x, panels_y, info_panel_width, info_panel_height, fonts)
        
        # Control panel (right bottom) - draw and get button rects
        control_x = WIDTH - control_panel_width - side_padding
        control_y = panels_y + info_panel_height + panel_spacing
        play_rect, quit_rect = draw_control_panel(control_x, control_y, control_panel_width, control_panel_height, args.pi_ip, fonts)
        
        # History chart (bottom, full width)
        draw_history_chart(side_padding, chart_y, WIDTH - 2 * side_padding, chart_height, fonts)
        
        # Footer
        footer_msg = "F11: Fullscreen | ESC: Exit" if not fullscreen else "F11: Windowed | ESC: Exit Fullscreen"
        footer_text = fonts['small_font'].render(footer_msg, True, GREY)
        footer_rect = footer_text.get_rect(center=(WIDTH // 2, footer_y))
        screen.blit(footer_text, footer_rect)
        
        pygame.display.flip()
        
        # Handle button clicks (after drawing to get button rects, but before next frame)
        # We need to process mouse events separately since we need button rects
        mouse_events = [e for e in pygame.event.get() if e.type == pygame.MOUSEBUTTONDOWN]
        for event in mouse_events:
            if event.button == 1:  # Left mouse button
                if play_rect and play_rect.collidepoint(event.pos):
                    # Send restart command to game
                    if command_sock and args.pi_ip:
                        try:
                            command_sock.sendto(b"restart", (args.pi_ip, GAME_COMMAND_PORT))
                            print(f"[Dashboard] Sent 'restart' command to {args.pi_ip}:{GAME_COMMAND_PORT}")
                        except Exception as e:
                            print(f"[Dashboard] Error sending restart command: {e}")
                elif quit_rect and quit_rect.collidepoint(event.pos):
                    # Send quit command to game
                    if command_sock and args.pi_ip:
                        try:
                            command_sock.sendto(b"quit", (args.pi_ip, GAME_COMMAND_PORT))
                            print(f"[Dashboard] Sent 'quit' command to {args.pi_ip}:{GAME_COMMAND_PORT}")
                        except Exception as e:
                            print(f"[Dashboard] Error sending quit command: {e}")
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

