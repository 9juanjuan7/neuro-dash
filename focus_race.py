try:
    import pygame
except ModuleNotFoundError:
    print("Error: pygame is not installed in this Python environment.")
    print("Install it into your active venv, for example:")
    print("  python3 -m pip install pygame")
    print("Then re-run: python3 focus_race.py")
    import sys
    sys.exit(1)

import sys
import random

import socket

# UDP socket to receive focus from server
# Bind to 0.0.0.0 to receive from external sources (like laptop forwarder over Tailscale)
UDP_IP = "0.0.0.0"  # Changed from 127.0.0.1 to accept external connections
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)  # so it doesn't freeze the game loop

# --------------------------
# CONFIG
# --------------------------
WIDTH, HEIGHT = 900, 500
FPS = 60
FINISH_LINE = WIDTH - 120

AI_SPEED = 14
MIN_SPEED = 2
MAX_SPEED = 30

# Desired sprite display size (width, height)
SPRITE_W, SPRITE_H = 170, 100

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Focus Car Racing: Yellow (You) vs White (AI)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)
small_font = pygame.font.SysFont("Arial", 20)

# Preload background images once at the top
try:
    SKY_IMG = pygame.image.load("images/grass.png").convert()
    SKY_IMG = pygame.transform.smoothscale(SKY_IMG, (WIDTH, 140))
except:
    SKY_IMG = None

try:
    DIRT_IMG = pygame.image.load("images/dirt.png").convert()
    DIRT_IMG = pygame.transform.smoothscale(DIRT_IMG, (WIDTH, HEIGHT - 360))
except:
    DIRT_IMG = None


WHITE = (255, 255, 255)
GREY = (120, 120, 120)
BLUE = (50, 150, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (230, 60, 60)
BG = (220, 240, 255)

# --------------------------
# LOAD IMAGES & SCALE SAFELY
# --------------------------
def load_and_scale(path, fallback_color):
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (SPRITE_W, SPRITE_H))
    except Exception:
        img = pygame.Surface((SPRITE_W, SPRITE_H), pygame.SRCALPHA)
        img.fill(fallback_color)
    return img

player_img = load_and_scale("images/yellow-car.png", RED)
ai_img = load_and_scale("images/white-car.png", GREEN)

# --------------------------
# CLASSES
# --------------------------
class Car:
    def __init__(self, img, y):
        self.img = img
        self.start_x = 50
        self.x = self.start_x
        self.y = y
        self.speed = 0
        self.finished = False

    def update(self):
        if not self.finished:
            self.x += self.speed / FPS
            if (self.x + self.img.get_width()) >= FINISH_LINE:
                self.finished = True

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

def map_focus_to_speed(focus):
    return MIN_SPEED + (focus / 100) * (MAX_SPEED - MIN_SPEED)

# --------------------------
# DRAW FUNCTIONS
# --------------------------
def draw_background():
    # --- Upper background ---
    if SKY_IMG:
        screen.blit(SKY_IMG, (0, 0))
    else:
        pygame.draw.rect(screen, (100, 180, 255), (0, 0, WIDTH, 140))

    # --- Road ---
    pygame.draw.rect(screen, GREY, (0, 140, WIDTH, 220))
    for i in range(0, WIDTH, 40):
        pygame.draw.rect(screen, WHITE, (i, 245, 20, 10))
    pygame.draw.line(screen, RED, (FINISH_LINE - 8, 140), (FINISH_LINE - 8, 390), 8)

    # --- Lower background ---
    if DIRT_IMG:
        screen.blit(DIRT_IMG, (0, 360))
    else:
        pygame.draw.rect(screen, (150, 120, 80), (0, 360, WIDTH, HEIGHT - 360))


def draw_ui(focus, player, ai):
    # --- Focus bar ---
    bar_x, bar_y, bar_w, bar_h = 50, HEIGHT - 60, 300, 30
    pygame.draw.rect(screen, BLACK, (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), 3, border_radius=6)
    pygame.draw.rect(screen, GREY, (bar_x, bar_y, bar_w, bar_h), border_radius=6)

    # Color mapping for focus
    if focus < 25:
        color = (230, 50, 50)
    elif focus < 50:
        color = (255, 150, 0)
    elif focus < 75:
        color = (255, 230, 0)
    else:
        color = (0, 200, 0)

    filled_w = int((focus / 100) * bar_w)
    pygame.draw.rect(screen, color, (bar_x, bar_y, filled_w, bar_h), border_radius=6)

    # --- Label inside bar ---
    label_text = font.render("Focus", True, BLACK)
    screen.blit(label_text, (bar_x + 8, bar_y - 1))  # slightly inside left side
    # Percentage removed - just show the bar

    # --- Motivational message ABOVE the bar (with more spacing) ---
    total_path = max(FINISH_LINE - player.start_x - player.img.get_width(), 1)
    player_dist = min(max(((player.x - player.start_x) / total_path) * 100, 0), 100)
    ai_dist = min(max(((ai.x - ai.start_x) / total_path) * 100, 0), 100)
    diff = player_dist - ai_dist

    if diff < -50:
        msg = "You're way behind! Stay focused!"
        color = RED
    elif diff < -25:
        msg = "Keep it up! Focus more!"
        color = (255, 120, 0)
    elif diff < 25:
        msg = "On the same track! Push harder!"
        color = (251, 255, 133)
    elif diff < 50:
        msg = "You're leading! Hang in there!"
        color = (201,255,244)
    else:
        msg = "Way ahead! Keep it that way!"
        color = (160, 247, 148)

    # Give it extra spacing above the bar
    text = font.render(msg, True, color)
    rect = text.get_rect(topleft=(bar_x, bar_y - 55))  # more gap
    screen.blit(text, rect)

    # --- Bottom-right status panel ---
    panel_w, panel_h = 200, 120
    panel_x, panel_y = WIDTH - panel_w - 10, HEIGHT - panel_h - 10

    # Shadow
    shadow_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (50, 50, 50, 100), (0, 0, panel_w, panel_h), border_radius=12)
    screen.blit(shadow_surf, (panel_x + 4, panel_y + 4))

    # Panel background
    pygame.draw.rect(screen, (245, 245, 250), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(screen, (180, 180, 180), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)

    def safe_scale(img, size):
        try:
            return pygame.transform.smoothscale(img, size)
        except:
            surf = pygame.Surface(size)
            surf.fill((200, 200, 200))
            return surf

    def draw_avatar(img, label, distance, y):
        center_x = panel_x + 40
        pygame.draw.circle(screen, (230, 230, 255), (center_x, y), 22)
        avatar = safe_scale(img, (50, 30))
        screen.blit(avatar, (center_x - 25, y - 15))
        text = small_font.render(label, True, BLACK)
        screen.blit(text, (center_x + 45, y - 18))
        dist_text = small_font.render(f"{distance:.1f}%", True, BLACK)
        screen.blit(dist_text, (center_x + 45, y + 6))

    draw_avatar(player.img, "You", 100 - player_dist, panel_y + 35)
    draw_avatar(ai.img, "AI", 100 - ai_dist, panel_y + 80)

    return player_dist, ai_dist




# --- PARTICLE EFFECT HELPERS ---

def create_fireworks():
    particles = []
    for _ in range(100):
        x = random.randint(100, WIDTH - 100)
        y = random.randint(100, HEIGHT - 200)
        color = random.choice([(255, 50, 50), (50, 255, 50), (50, 150, 255), (255, 255, 50)])
        radius = random.randint(2, 4)
        speed_x = random.uniform(-3, 3)
        speed_y = random.uniform(-5, -1)
        life = random.randint(40, 70)
        particles.append([x, y, radius, color, speed_x, speed_y, life])
    return particles


def animate_fireworks(particles):
    for p in particles[:]:
        x, y, r, c, sx, sy, life = p
        pygame.draw.circle(screen, c, (int(x), int(y)), r)
        p[0] += sx
        p[1] += sy
        p[6] -= 1
        p[5] += 0.2  # gravity pull
        if p[6] <= 0:
            particles.remove(p)


def create_rain():
    drops = []
    for _ in range(200):
        x = random.randint(0, WIDTH)
        y = random.randint(-HEIGHT, 0)
        speed = random.uniform(4, 10)
        drops.append([x, y, speed])
    return drops


def animate_rain(drops):
    for d in drops:
        x, y, speed = d
        pygame.draw.line(screen, (100, 100, 255), (x, y), (x, y + 10), 2)
        d[1] += speed
        if d[1] > HEIGHT:
            d[1] = random.randint(-50, 0)
            d[0] = random.randint(0, WIDTH)

# --- SMOKE EFFECT ---
def create_smoke(x, y):
    """Create a burst of smoke particles at given (x, y)."""
    particles = []
    for _ in range(5):  # number of smoke puffs per frame
        radius = random.randint(4, 8)
        gray = random.randint(180, 240)
        particles.append({
            "x": x + random.randint(-5, 5),
            "y": y + random.randint(-5, 5),
            "r": radius,
            "color": (gray, gray, gray),
            "life": random.randint(20, 40),
            "vy": random.uniform(-0.5, -1.5),
            "vx": random.uniform(-0.3, 0.3)
        })
    return particles


def animate_smoke(particles):
    """Update and draw smoke particles."""
    for p in particles[:]:
        pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), int(p["r"]))
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        p["r"] = max(0, p["r"] - 0.1)  # slowly shrink
        if p["life"] <= 0:
            particles.remove(p)



# --- MAIN WIN/LOSE ANIMATION ---

def draw_winner(winner):
    msg = "Hurraayy!! YOU WIN!!" if winner == "player" else "Boooo!! YOU LOST!!"
    color = (255, 255, 255) if winner == "player" else (255, 200, 200)

    particles = create_fireworks() if winner == "player" else []
    rain = create_rain() if winner == "ai" else []

    t0 = pygame.time.get_ticks()
    while pygame.time.get_ticks() - t0 < 3000:  # 3 seconds
        screen.fill(BLACK)

        # effect
        if winner == "player":
            animate_fireworks(particles)
        else:
            animate_rain(rain)

        # text
        text = font.render(msg, True, color)
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)

        pygame.display.flip()
        clock.tick(60)

def show_end_screen(winner):
    """Display final winner result and wait for user input"""
    screen.fill(BG)
    msg = "!!YOU WIN!!" if winner == "player" else "!!YOU LOST!!"
    color = GREEN if winner == "player" else RED
    text = font.render(msg, True, color)
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, rect)

    sub = font.render("Press [R] to restart or [Q] to quit", True, BLACK)
    sub_rect = sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
    screen.blit(sub, sub_rect)

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_r:
                    waiting = False  # Exit end screen and restart game


# --------------------------
# MAIN LOOP
# --------------------------
def main():
    while True:  # outer loop for restarts
        # --- INITIALIZE GAME STATE ---
        player = Car(player_img, 150)
        ai = Car(ai_img, 270)
        smoke_particles = []
        focus = 50
        smoothed_focus = 50  # For smoothing the focus bar
        smoothing_alpha = 0.15  # Lower = more smoothing (15% new, 85% old)
        winner = None
        running = True

        # Doctor UI is not auto-started by default. Run dashboard.py separately if desired.

        while running:
            dt = clock.tick(FPS)

            # --- EVENTS ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # --- Get focus from server via UDP socket ---
            # Default if no new data arrives
            raw_focus = 50  

            try:
                data, addr = sock.recvfrom(1024)
                raw_focus = float(data.decode()) * 100  # server sends 0–1, map to 0–100
                # Debug: print occasionally to verify data is being received
                if not hasattr(main, '_last_udp_debug_time'):
                    main._last_udp_debug_time = 0
                current_time = pygame.time.get_ticks() / 1000.0
                if current_time - main._last_udp_debug_time > 2.0:
                    print(f"[Game] Received focus: {raw_focus:.1f}% from {addr}")
                    main._last_udp_debug_time = current_time
            except BlockingIOError:
                pass  # no new data this frame
            except Exception as e:
                # Debug: print errors
                if not hasattr(main, '_last_error_time'):
                    main._last_error_time = 0
                current_time = pygame.time.get_ticks() / 1000.0
                if current_time - main._last_error_time > 5.0:
                    print(f"[Game] UDP error: {e}")
                    main._last_error_time = current_time

            # Smooth the focus value to reduce jumpiness
            smoothed_focus = smoothing_alpha * raw_focus + (1 - smoothing_alpha) * smoothed_focus
            focus = smoothed_focus

            # --- Update car speeds ---
            player.speed = map_focus_to_speed(focus)
            ai.speed = AI_SPEED

            # Smoke effect if focus high
            if focus >= 75 and len(smoke_particles) < 200:
                smoke_particles.extend(create_smoke(player.x, player.y + player.img.get_height() // 2))

            player.update()
            ai.update()

            # --- DRAW SECTION ---
            draw_background()
            player.draw()
            ai.draw()
            player_dist, ai_dist = draw_ui(focus, player, ai)
            animate_smoke(smoke_particles)

            # --- Check winner ---
            if (player.finished or ai.finished) and winner is None:
                winner = "player" if player.finished else "ai"
                draw_winner(winner)
                show_end_screen(winner)
                running = False  # break inner loop to restart

            pygame.display.flip()
if __name__ == "__main__":
    main()