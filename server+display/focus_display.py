import pygame
import socket

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("Focus Intensity")

# Receive focus data (same port as from focus_server.py)
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

focus = 0.0
running = True
clock = pygame.time.Clock()

while running:
    # Handle window events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Receive latest focus
    try:
        data, _ = sock.recvfrom(1024)
        focus = float(data.decode())
    except BlockingIOError:
        pass

    # Draw focus bar
    screen.fill((30, 30, 30))
    bar_height = int(focus * 150)
    pygame.draw.rect(screen, (0, 255, 0), (100, 180 - bar_height, 100, bar_height))
    
    # Draw text
    font = pygame.font.Font(None, 36)
    txt = font.render(f"Focus: {focus:.2f}", True, (255, 255, 255))
    screen.blit(txt, (60, 20))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
