import pygame
import random
import time

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("Focus Intensity (Mock Data)")

focus = 0.0
running = True
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# For smooth transitions
target_focus = random.random()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Simulate focus changing gradually
    if abs(focus - target_focus) < 0.02:
        target_focus = random.random()  # pick a new random focus target
    focus += (target_focus - focus) * 0.05  # smooth movement

    # Draw background
    screen.fill((30, 30, 30))

    # Draw focus bar
    bar_height = int(focus * 150)
    pygame.draw.rect(screen, (0, 255, 0), (100, 180 - bar_height, 100, bar_height))

    # Draw text
    txt = font.render(f"Focus: {focus:.2f}", True, (255, 255, 255))
    screen.blit(txt, (60, 20))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
