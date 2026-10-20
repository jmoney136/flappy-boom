import pygame
import random
import math
import sys

# --- Init ---
pygame.init()
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

# --- Constants ---
GRAVITY = 0.5
FLAP = -8
PIPE_WIDTH = 60
PIPE_GAP = 150
PIPE_SPEED = 3
PIPE_SPACING = 200

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
BLUE = (135, 206, 235)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
RED = (255, 50, 50)

# --- Particle class ---
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.life = random.randint(20, 50)
        self.max_life = self.life
        self.size = random.randint(2, 6)
        self.color = random.choice([RED, ORANGE, YELLOW, WHITE])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surface):
        alpha = self.life / self.max_life
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)


def spawn_explosion(x, y, particles, count=40):
    for _ in range(count):
        particles.append(Particle(x, y))


# --- Bird class ---
class Bird:
    def __init__(self):
        self.x = 80
        self.y = HEIGHT // 2
        self.vel = 0
        self.radius = 15
        self.alive = True

    def flap(self):
        self.vel = FLAP

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel

    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 5, int(self.y) - 5), 3)
        pygame.draw.ellipse(surface, ORANGE, (self.x - 5, self.y, 15, 10))

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


# --- Pipe class ---
class Pipe:
    def __init__(self, x):
        self.x = x
        self.gap_y = random.randint(150, HEIGHT - 150 - PIPE_GAP)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self, surface):
        pygame.draw.rect(surface, GREEN, (self.x, 0, PIPE_WIDTH, self.gap_y))
        bottom_y = self.gap_y + PIPE_GAP
        pygame.draw.rect(surface, GREEN, (self.x, bottom_y, PIPE_WIDTH, HEIGHT - bottom_y))

    def top_rect(self):
        return pygame.Rect(self.x, 0, PIPE_WIDTH, self.gap_y)

    def bottom_rect(self):
        bottom_y = self.gap_y + PIPE_GAP
        return pygame.Rect(self.x, bottom_y, PIPE_WIDTH, HEIGHT - bottom_y)   

# --- Game state ---
def reset():
    bird = Bird()
    pipes = [Pipe(WIDTH + i * PIPE_SPACING) for i in range(3)]
    score = 0
    particles = []
    return bird, pipes, score, particles

bird, pipes, score, particles = reset()
game_over = False
font = pygame.font.SysFont(None, 36)

# --- Main loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_over:
                    bird, pipes, score, particles = reset()
                    game_over = False
                else:
                    bird.flap()
            if event.key == pygame.K_ESCAPE:
                running = False

    if not game_over:
        bird.update()
        for p in pipes:
            p.update()

        if pipes[-1].x < WIDTH - PIPE_SPACING:
            pipes.append(Pipe(pipes[-1].x + PIPE_SPACING))
        if pipes[0].x + PIPE_WIDTH < 0:
            pipes.pop(0)

        # Collision check
        bird_rect = bird.rect()
        crashed = False
        if bird.y + bird.radius > HEIGHT or bird.y - bird.radius < 0:
            crashed = True
        for p in pipes:
            if bird_rect.colliderect(p.top_rect()) or bird_rect.colliderect(p.bottom_rect()):
                crashed = True

        if crashed:
            game_over = True
            bird.alive = False
            spawn_explosion(bird.x, bird.y, particles, count=40)

        for p in pipes:
            if not p.passed and p.x + PIPE_WIDTH < bird.x:
                p.passed = True
                score += 1

    # Update & draw particles
    for i in range(len(particles) - 1, -1, -1):
        particles[i].update()
        if particles[i].life <= 0:
            particles.pop(i)

    # --- Draw ---
    screen.fill(BLUE)
    for p in pipes:
        p.draw(screen)
    if bird.alive:
        bird.draw(screen)

    for particle in particles:
        particle.draw(screen)

    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    if game_over:
        go_text = font.render("Game Over! Press SPACE to restart", True, BLACK)
        screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()   