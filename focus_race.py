import pygame
import sys
import random

# --------------------------
# CONFIG
# --------------------------
WIDTH, HEIGHT = 900, 500
FPS = 60
FINISH_LINE = WIDTH - 120

AI_SPEED = 9
MIN_SPEED = 2
MAX_SPEED = 16

# Desired sprite display size (width, height)
SPRITE_W, SPRITE_H = 170, 100

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Focus Car Racing: Yellow (You) vs White (AI)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)
small_font = pygame.font.SysFont("Arial", 20)


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
        self.x = 50
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
    try:
        sky_img = pygame.image.load("images/grass.png").convert()
        sky_img = pygame.transform.smoothscale(sky_img, (WIDTH, 140))  # only above road
        screen.blit(sky_img, (0, 0))
    except:
        pygame.draw.rect(screen, (100, 180, 255), (0, 0, WIDTH, 140))  # fallback sky

    # --- Road ---
    pygame.draw.rect(screen, GREY, (0, 140, WIDTH, 220))
    for i in range(0, WIDTH, 40):
        pygame.draw.rect(screen, WHITE, (i, 245, 20, 10))
    pygame.draw.line(screen, RED, (FINISH_LINE, 120), (FINISH_LINE, 390), 8)

    # --- Lower background ---
    try:
        dirt_img = pygame.image.load("images/dirt.png").convert()
        dirt_img = pygame.transform.smoothscale(dirt_img, (WIDTH, HEIGHT-360))
        screen.blit(dirt_img, (0, 360))
    except:
        pygame.draw.rect(screen, (150, 120, 80), (0, 360, WIDTH, HEIGHT-360))


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
    label_text = font.render("Focus", True, WHITE)
    screen.blit(label_text, (bar_x + 8, bar_y - 1))  # slightly inside left side
    value_text = font.render(f"{focus:.0f}%", True, WHITE)
    value_rect = value_text.get_rect(right=bar_x + bar_w - 8, centery=bar_y + bar_h // 2)
    screen.blit(value_text, value_rect)

    # --- Motivational message ABOVE the bar (with more spacing) ---
    total_path = max(FINISH_LINE - 50 - player.img.get_width(), 1)
    player_dist = min(max((player.x / total_path) * 100, 0), 100)
    ai_dist = min(max((ai.x / total_path) * 100, 0), 100)
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
    rect = text.get_rect(topleft=(bar_x, bar_y - 55))  # more gap (used to be -35)
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
        except Exception:
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
                    main()  # restart game
                    return



# --------------------------
# MAIN LOOP
# --------------------------
def main():
    player = Car(player_img, 150)
    ai = Car(ai_img, 270)
    running = True
    winner = None
    smoke_particles = []
    focus_value = 50  # initial focus

    while running:
        dt = clock.tick(FPS)

        # --- Optional manual focus adjustment ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            focus_value = min(focus_value + 1, 100)
        elif keys[pygame.K_DOWN]:
            focus_value = max(focus_value - 1, 0)
        else:
            focus_value = max(focus_value - 0.05, 0)  # slowly decay

        # --- Update car speeds ---
        player.speed = map_focus_to_speed(focus_value)
        ai.speed = AI_SPEED

        # Smoke effect if focus high
        if focus_value >= 75:
            smoke_particles.extend(create_smoke(player.x, player.y + player.img.get_height() // 2))

        player.update()
        ai.update()

        # --- DRAW SECTION ---
        draw_background()
        player.draw()
        ai.draw()

        # draw_ui now also includes the bottom-left distance panel
        player_dist, ai_dist = draw_ui(focus_value, player, ai)
        animate_smoke(smoke_particles)

        # --- Check winner ---
        if (player.finished or ai.finished) and winner is None:
            winner = "player" if player.finished else "ai"
            draw_winner(winner)
            show_end_screen(winner)

        pygame.display.flip()

if __name__ == "__main__":
    main()