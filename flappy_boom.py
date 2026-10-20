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
GRAVITY = 0.6
FLAP = -9
PIPE_WIDTH = 60
PIPE_GAP = 140
PIPE_SPEED = 3
PIPE_SPACING = 200
GROUND_HEIGHT = 80

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (20, 100, 20)
SKY_TOP = (100, 180, 235)
SKY_BOTTOM = (180, 230, 255)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
RED = (255, 50, 50)
BROWN = (160, 120, 60)
LIGHT_BROWN = (200, 170, 100)
CLOUD_WHITE = (240, 240, 240)
SMOKE_GREY = (100, 100, 100)
DARK_SMOKE = (60, 60, 60)

# --- Fire particle ---
class FireParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 6)
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle) - 1  # slight upward bias
        self.life = random.randint(15, 35)
        self.max_life = self.life
        self.size = random.randint(4, 9)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # less gravity than debris
        self.vx *= 0.97  # drag
        self.vy *= 0.97
        self.life -= 1
        self.size *= 0.96  # shrink over time

    def draw(self, surface):
        t = self.life / self.max_life
        size = max(1, int(self.size))
        # Color: white -> yellow -> orange -> red -> dark
        if t > 0.7:
            color = (255, 255, 200)
        elif t > 0.5:
            color = (255, 215, 0)
        elif t > 0.3:
            color = (255, 120, 0)
        elif t > 0.15:
            color = (200, 50, 0)
        else:
            color = (100, 20, 0)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


# --- Smoke particle ---
class SmokeParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-5, 5)
        self.y = y + random.uniform(-5, 5)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-1.5, -0.5)  # rises
        self.life = random.randint(40, 80)
        self.max_life = self.life
        self.size = random.randint(5, 12)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx += random.uniform(-0.05, 0.05)  # drift
        self.vy -= 0.01  # accelerate upward
        self.life -= 1
        self.size += 0.2  # expand

    def draw(self, surface):
        t = self.life / self.max_life
        size = int(self.size)
        grey = int(80 + 60 * (1 - t))
        color = (grey, grey, grey)
        # Draw as soft circle (multiple overlapping for softness)
        for dx, dy in [(0, 0), (2, 0), (-2, 0), (0, 2), (0, -2)]:
            pygame.draw.circle(surface, color, (int(self.x) + dx, int(self.y) + dy), size)


# --- Debris particle ---
class DebrisParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 10)
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.life = random.randint(30, 60)
        self.max_life = self.life
        self.size = random.randint(2, 5)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-10, 10)
        self.color = random.choice([YELLOW, ORANGE, (200, 160, 0), (180, 120, 0)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3  # strong gravity
        self.vx *= 0.99
        self.rotation += self.rot_speed
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0:
            return
        t = self.life / self.max_life
        # Draw as small rotating rectangle
        size = max(1, int(self.size * t))
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.rect(s, self.color, (0, 0, size * 2, size))
        rotated = pygame.transform.rotate(s, self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


# --- Flash effect ---
class Flash:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 8
        self.max_life = 8

    def update(self):
        self.life -= 1

    def draw(self, surface):
        t = self.life / self.max_life
        radius = int(20 + (1 - t) * 60)
        # White flash that expands and fades
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        alpha = int(200 * t)
        pygame.draw.circle(s, (255, 255, 255, alpha), (radius, radius), radius)
        surface.blit(s, (self.x - radius, self.y - radius), special_flags=pygame.BLEND_RGBA_ADD)


# --- Shockwave ring ---
class Shockwave:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 20
        self.max_life = 20

    def update(self):
        self.life -= 1

    def draw(self, surface):
        t = 1 - self.life / self.max_life
        radius = int(10 + t * 80)
        width = max(1, int(4 * (1 - t)))
        alpha = int(180 * (1 - t))
        s = pygame.Surface((radius * 2 + width * 2, radius * 2 + width * 2), pygame.SRCALPHA)
        cx = radius + width
        pygame.draw.circle(s, (255, 200, 100, alpha), (cx, cx), radius, width)
        surface.blit(s, (self.x - cx, self.y - cx))


# --- Explosion manager ---
class Explosion:
    def __init__(self, x, y):
        self.fire = [FireParticle(x, y) for _ in range(30)]
        self.smoke = [SmokeParticle(x, y) for _ in range(15)]
        self.debris = [DebrisParticle(x, y) for _ in range(12)]
        self.flash = Flash(x, y)
        self.shockwave = Shockwave(x, y)

    def update(self):
        for p in self.fire:
            p.update()
        self.fire = [p for p in self.fire if p.life > 0]

        for p in self.smoke:
            p.update()
        self.smoke = [p for p in self.smoke if p.life > 0]

        for p in self.debris:
            p.update()
        self.debris = [p for p in self.debris if p.life > 0]

        self.flash.update()
        self.shockwave.update()

    def draw(self, surface):
        # Draw order: shockwave, smoke, fire, debris, flash
        self.shockwave.draw(surface)
        for p in self.smoke:
            p.draw(surface)
        for p in self.fire:
            p.draw(surface)
        for p in self.debris:
            p.draw(surface)
        if self.flash.life > 0:
            self.flash.draw(surface)

    @property
    def done(self):
        return (len(self.fire) == 0 and len(self.smoke) == 0
                and len(self.debris) == 0 and self.flash.life <= 0
                and self.shockwave.life <= 0)


# --- Cloud class ---
class Cloud:
    def __init__(self):
        self.x = random.randint(WIDTH, WIDTH + 200)
        self.y = random.randint(30, 200)
        self.speed = random.uniform(0.3, 0.8)
        self.w = random.randint(60, 120)
        self.h = random.randint(20, 35)

    def update(self):
        self.x -= self.speed
        if self.x + self.w < 0:
            self.x = WIDTH + random.randint(0, 100)
            self.y = random.randint(30, 200)

    def draw(self, surface):
        r = self.h // 2
        pygame.draw.ellipse(surface, CLOUD_WHITE, (self.x, self.y, self.w, self.h))
        pygame.draw.ellipse(surface, CLOUD_WHITE, (self.x + self.w * 0.2, self.y - r, self.w * 0.5, self.h))
        pygame.draw.ellipse(surface, CLOUD_WHITE, (self.x + self.w * 0.4, self.y - r // 2, self.w * 0.4, self.h))


# --- Bird class ---
class Bird:
    def __init__(self):
        self.x = 80
        self.y = HEIGHT // 2
        self.vel = 0
        self.radius = 15
        self.alive = True
        self.rotation = 0
        self.wing_frame = 0
        self.wing_timer = 0

    def flap(self):
        self.vel = FLAP
        self.wing_frame = 1
        self.wing_timer = 0

    def update(self):
        self.vel += GRAVITY
        self.vel *= 0.998
        self.y += self.vel
        target_rot = math.degrees(math.atan2(self.vel, 4))
        target_rot = max(-30, min(70, target_rot))
        self.rotation += (target_rot - self.rotation) * 0.15
        self.wing_timer += 1
        if self.wing_timer > 8:
            self.wing_frame = 0
            self.wing_timer = 0

    def draw(self, surface):
        rotated_surf = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
        cx, cy = self.radius + 5, self.radius + 5
        pygame.draw.circle(rotated_surf, YELLOW, (cx, cy), self.radius)
        pygame.draw.circle(rotated_surf, WHITE, (cx + 6, cy - 5), 5)
        pygame.draw.circle(rotated_surf, BLACK, (cx + 7, cy - 5), 2)
        pygame.draw.polygon(rotated_surf, ORANGE, [(cx + 12, cy - 2), (cx + 20, cy + 1), (cx + 12, cy + 4)])
        wing_y = cy + (3 if self.wing_frame == 0 else -3)
        pygame.draw.ellipse(rotated_surf, ORANGE, (cx - 8, wing_y - 5, 14, 10))
        rotated = pygame.transform.rotate(rotated_surf, -self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


# --- Pipe class ---
class Pipe:
    CAP_HEIGHT = 20
    CAP_EXTRA = 6

    def __init__(self, x):
        self.x = x
        self.gap_y = random.randint(120, HEIGHT - GROUND_HEIGHT - 120 - PIPE_GAP)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self, surface):
        cap_w = PIPE_WIDTH + self.CAP_EXTRA * 2
        pygame.draw.rect(surface, GREEN, (self.x, 0, PIPE_WIDTH, self.gap_y - self.CAP_HEIGHT))
        pygame.draw.rect(surface, DARK_GREEN, (self.x - self.CAP_EXTRA, self.gap_y - self.CAP_HEIGHT, cap_w, self.CAP_HEIGHT))
        bottom_y = self.gap_y + PIPE_GAP
        pygame.draw.rect(surface, DARK_GREEN, (self.x - self.CAP_EXTRA, bottom_y, cap_w, self.CAP_HEIGHT))
        pygame.draw.rect(surface, GREEN, (self.x, bottom_y + self.CAP_HEIGHT, PIPE_WIDTH, HEIGHT - GROUND_HEIGHT - bottom_y - self.CAP_HEIGHT))

    def top_rect(self):
        return pygame.Rect(self.x, 0, PIPE_WIDTH, self.gap_y)

    def bottom_rect(self):
        bottom_y = self.gap_y + PIPE_GAP
        return pygame.Rect(self.x, bottom_y, PIPE_WIDTH, HEIGHT - GROUND_HEIGHT - bottom_y)


# --- Ground ---
class Ground:
    def __init__(self):
        self.offset = 0
        self.stripe_w = 40

    def update(self):
        self.offset = (self.offset + PIPE_SPEED) % (self.stripe_w * 2)

    def draw(self, surface):
        y = HEIGHT - GROUND_HEIGHT
        pygame.draw.rect(surface, LIGHT_BROWN, (0, y, WIDTH, GROUND_HEIGHT))
        pygame.draw.rect(surface, BROWN, (0, y, WIDTH, 12))
        for i in range(-1, WIDTH // (self.stripe_w * 2) + 2):
            x = i * self.stripe_w * 2 - self.offset
            pygame.draw.polygon(surface, BROWN, [
                (x, y + 12), (x + self.stripe_w, y + 12),
                (x + self.stripe_w - 8, y + 24), (x - 8, y + 24)
            ])


# --- Game state ---
def reset():
    bird = Bird()
    pipes = [Pipe(WIDTH + i * PIPE_SPACING) for i in range(3)]
    clouds = [Cloud() for _ in range(5)]
    ground = Ground()
    score = 0
    explosion = None
    shake = 0
    return bird, pipes, clouds, ground, score, explosion, shake

bird, pipes, clouds, ground, score, explosion, shake = reset()
game_over = False
font = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)


def draw_sky(surface):
    for y in range(HEIGHT - GROUND_HEIGHT):
        t = y / (HEIGHT - GROUND_HEIGHT)
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))


# --- Main loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_over:
                    bird, pipes, clouds, ground, score, explosion, shake = reset()
                    game_over = False
                else:
                    bird.flap()
            if event.key == pygame.K_ESCAPE:
                running = False

    if not game_over:
        bird.update()
        ground.update()
        for c in clouds:
            c.update()
        for p in pipes:
            p.update()

        if pipes[-1].x < WIDTH - PIPE_SPACING:
            pipes.append(Pipe(pipes[-1].x + PIPE_SPACING))
        if pipes[0].x + PIPE_WIDTH < 0:
            pipes.pop(0)

        bird_rect = bird.rect()
        crashed = False
        if bird.y + bird.radius > HEIGHT - GROUND_HEIGHT or bird.y - bird.radius < 0:
            crashed = True
        for p in pipes:
            if bird_rect.colliderect(p.top_rect()) or bird_rect.colliderect(p.bottom_rect()):
                crashed = True

        if crashed:
            game_over = True
            bird.alive = False
            explosion = Explosion(bird.x, bird.y)
            shake = 20

        for p in pipes:
            if not p.passed and p.x + PIPE_WIDTH < bird.x:
                p.passed = True
                score += 1

    # Update explosion
    if explosion:
        explosion.update()
        if explosion.done:
            explosion = None

    # Screen shake
    if shake > 0:
        shake -= 1
        offset_x = random.randint(-shake, shake)
        offset_y = random.randint(-shake, shake)
    else:
        offset_x = 0
        offset_y = 0

    # --- Draw ---
    draw_sky(screen)
    for c in clouds:
        c.draw(screen)
    for p in pipes:
        p.draw(screen)
    ground.draw(screen)
    if bird.alive:
        bird.draw(screen)
    if explosion:
        explosion.draw(screen)

    # UI
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    if game_over:
        go_text = font.render("Game Over!", True, BLACK)
        restart_text = font_small.render("Press SPACE to restart", True, BLACK)
        screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 30))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()   