import pygame
import random
import math
import sys

# --- Init ---
pygame.init()
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird 2.5D")
clock = pygame.time.Clock()

# --- Constants ---
HORIZON_Y = HEIGHT // 3  # y position of horizon line
NEAR_Z = 100    # bird's z (close to camera)
FAR_Z = 2000    # where pipes spawn
PIPE_SPEED = 15  # z units per frame
PIPE_GAP = 120   # gap size in world units
PIPE_WIDTH = 80  # pipe width in world units
GRAVITY = 0.4
FLAP = -7
BIRD_Z = NEAR_Z

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (20, 100, 20)
SKY_TOP = (70, 130, 200)
SKY_BOTTOM = (180, 220, 255)
GROUND_COLOR = (120, 180, 80)
GROUND_DARK = (80, 140, 50)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
RED = (255, 50, 50)
SMOKE_GREY = (100, 100, 100)


def project(x, y, z):
    """Perspective projection: world (x, y, z) -> screen (sx, sy, scale)"""
    scale = NEAR_Z / z
    sx = WIDTH // 2 + int(x * scale)
    sy = HORIZON_Y + int(y * scale)
    return sx, sy, scale


# --- Fire particle ---
class FireParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 6)
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle) - 1
        self.life = random.randint(15, 35)
        self.max_life = self.life
        self.size = random.randint(4, 9)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.vx *= 0.97
        self.vy *= 0.97
        self.life -= 1
        self.size *= 0.96

    def draw(self, surface):
        t = self.life / self.max_life
        size = max(1, int(self.size))
        if t > 0.7: color = (255, 255, 200)
        elif t > 0.5: color = (255, 215, 0)
        elif t > 0.3: color = (255, 120, 0)
        elif t > 0.15: color = (200, 50, 0)
        else: color = (100, 20, 0)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


class SmokeParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-5, 5)
        self.y = y + random.uniform(-5, 5)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-1.5, -0.5)
        self.life = random.randint(40, 80)
        self.max_life = self.life
        self.size = random.randint(5, 12)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx += random.uniform(-0.05, 0.05)
        self.vy -= 0.01
        self.life -= 1
        self.size += 0.2

    def draw(self, surface):
        t = self.life / self.max_life
        size = int(self.size)
        grey = int(80 + 60 * (1 - t))
        for dx, dy in [(0,0),(2,0),(-2,0),(0,2),(0,-2)]:
            pygame.draw.circle(surface, (grey,grey,grey), (int(self.x)+dx, int(self.y)+dy), size)


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
        self.color = random.choice([YELLOW, ORANGE, (200, 160, 0)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.vx *= 0.99
        self.rotation += self.rot_speed
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0: return
        t = self.life / self.max_life
        size = max(1, int(self.size * t))
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.rect(s, self.color, (0, 0, size*2, size))
        rotated = pygame.transform.rotate(s, self.rotation)
        surface.blit(rotated, rotated.get_rect(center=(int(self.x), int(self.y))))


class Shockwave:
    def __init__(self, x, y):
        self.x = x; self.y = y
        self.life = 20; self.max_life = 20

    def update(self):
        self.life -= 1

    def draw(self, surface):
        t = 1 - self.life / self.max_life
        radius = int(10 + t * 80)
        width = max(1, int(4 * (1 - t)))
        alpha = int(180 * (1 - t))
        s = pygame.Surface((radius*2+width*2, radius*2+width*2), pygame.SRCALPHA)
        cx = radius + width
        pygame.draw.circle(s, (255, 200, 100, alpha), (cx, cx), radius, width)
        surface.blit(s, (self.x - cx, self.y - cx))


class Explosion:
    def __init__(self, x, y):
        self.fire = [FireParticle(x, y) for _ in range(30)]
        self.smoke = [SmokeParticle(x, y) for _ in range(15)]
        self.debris = [DebrisParticle(x, y) for _ in range(12)]
        self.shockwave = Shockwave(x, y)

    def update(self):
        for p in self.fire: p.update()
        self.fire = [p for p in self.fire if p.life > 0]
        for p in self.smoke: p.update()
        self.smoke = [p for p in self.smoke if p.life > 0]
        for p in self.debris: p.update()
        self.debris = [p for p in self.debris if p.life > 0]
        self.shockwave.update()

    def draw(self, surface):
        self.shockwave.draw(surface)
        for p in self.smoke: p.draw(surface)
        for p in self.fire: p.draw(surface)
        for p in self.debris: p.draw(surface)

    @property
    def done(self):
        return not self.fire and not self.smoke and not self.debris and self.shockwave.life <= 0


# --- Bird ---
class Bird:
    def __init__(self):
        self.world_x = 0  # horizontal position in world space
        self.world_y = 0  # vertical position
        self.vel = 0
        self.alive = True
        self.wing_frame = 0
        self.wing_timer = 0

    def flap(self):
        self.vel = FLAP
        self.wing_frame = 1
        self.wing_timer = 0

    def move(self, dx):
        self.world_x += dx

    def update(self):
        self.vel += GRAVITY
        self.world_y += self.vel
        self.wing_timer += 1
        if self.wing_timer > 8:
            self.wing_frame = 0
            self.wing_timer = 0

    def screen_pos(self):
        return project(self.world_x, self.world_y, BIRD_Z)

    def draw(self, surface):
        sx, sy, scale = self.screen_pos()
        r = int(15 * scale)
        if r < 3: r = 3

        # Body
        pygame.draw.ellipse(surface, YELLOW, (sx - r, sy - r, r*2, r*2))
        # Eye
        pygame.draw.circle(surface, WHITE, (sx + r//3, sy - r//3), max(2, r//3))
        pygame.draw.circle(surface, BLACK, (sx + r//3, sy - r//3), max(1, r//4))
        # Beak (facing camera = triangle pointing at viewer)
        pygame.draw.polygon(surface, ORANGE, [
            (sx, sy + r//4), (sx - r//3, sy + r//2), (sx + r//3, sy + r//2)
        ])
        # Wings
        wing_offset = 3 if self.wing_frame == 0 else -3
        pygame.draw.ellipse(surface, ORANGE, (sx - r - 4, sy + wing_offset, r, r//2))
        pygame.draw.ellipse(surface, ORANGE, (sx, sy + wing_offset, r, r//2))

    def world_bounds(self):
        """Return (left, right, top, bottom) in world units for collision"""
        r = 15
        return (self.world_x - r, self.world_x + r,
                self.world_y - r, self.world_y + r)


# --- Pipe ---
class Pipe:
    def __init__(self, z):
        self.z = z
        self.gap_x = random.randint(-200, 200)  # horizontal center of gap
        self.gap_y = random.randint(-100, 150)   # vertical center of gap
        self.passed = False

    def update(self):
        self.z -= PIPE_SPEED

    def draw(self, surface):
        if self.z <= NEAR_Z * 0.5:
            return
        scale = NEAR_Z / self.z
        w = int(PIPE_WIDTH * scale)
        gap_w = int(PIPE_GAP * scale)
        if w < 2:
            return

        # Project center of pipe
        cx, cy, _ = project(self.gap_x, self.gap_y, self.z)

        # Gap edges in screen space
        gap_half = gap_w // 2
        # Top pipe: from top of screen to gap top
        top_h = int((self.gap_y - PIPE_GAP/2 - 300) * scale)
        # Bottom pipe: from gap bottom to bottom
        bot_y = int((self.gap_y + PIPE_GAP/2) * scale)
        bot_h = int((300 - self.gap_y - PIPE_GAP/2) * scale)

        # Draw top pipe (dark green with lighter edge)
        top_rect = pygame.Rect(cx - w//2, cy - gap_half - top_h, w, top_h)
        pygame.draw.rect(surface, DARK_GREEN, top_rect)
        pygame.draw.rect(surface, GREEN, (top_rect.x, top_rect.y, top_rect.width, min(8, top_h)))

        # Draw bottom pipe
        bot_rect = pygame.Rect(cx - w//2, cy + gap_half, w, bot_h)
        pygame.draw.rect(surface, DARK_GREEN, bot_rect)
        pygame.draw.rect(surface, GREEN, (bot_rect.x, bot_rect.y, bot_rect.width, min(8, bot_h)))

        # Pipe cap highlights
        cap_h = max(2, int(15 * scale))
        pygame.draw.rect(surface, (50, 160, 50), (cx - w//2 - 2, cy - gap_half - cap_h, w + 4, cap_h))
        pygame.draw.rect(surface, (50, 160, 50), (cx - w//2 - 2, cy + gap_half, w + 4, cap_h))

    def check_collision(self, bird):
        """Check if bird is at this pipe's z and in the pipe (not gap)"""
        if abs(self.z - BIRD_Z) > PIPE_SPEED * 1.5:
            return False
        bx1, bx2, by1, by2 = bird.world_bounds()
        gap_half = PIPE_GAP / 2
        pipe_left = self.gap_x - PIPE_WIDTH / 2
        pipe_right = self.gap_x + PIPE_WIDTH / 2
        gap_top = self.gap_y - gap_half
        gap_bot = self.gap_y + gap_half

        # Bird overlaps pipe horizontally AND is outside gap vertically
        if bx2 > pipe_left and bx1 < pipe_right:
            if by1 < gap_top or by2 > gap_bot:
                return True
        return False


# --- Ground (perspective grid) ---
def draw_ground(surface):
    # Horizon line
    pygame.draw.line(surface, GROUND_DARK, (0, HORIZON_Y), (WIDTH, HORIZON_Y), 2)
    # Ground fill
    ground_surf = pygame.Surface((WIDTH, HEIGHT - HORIZON_Y), pygame.SRCALPHA)
    for y in range(HEIGHT - HORIZON_Y):
        t = y / (HEIGHT - HORIZON_Y)
        r = int(GROUND_COLOR[0] * (1 - t * 0.4))
        g = int(GROUND_COLOR[1] * (1 - t * 0.3))
        b = int(GROUND_COLOR[2] * (1 - t * 0.4))
        pygame.draw.line(ground_surf, (r, g, b), (0, y), (WIDTH, y))
    surface.blit(ground_surf, (0, HORIZON_Y))

    # Perspective grid lines (horizontal - getting closer together near horizon)
    for i in range(1, 20):
        z = i * 100
        scale = NEAR_Z / z
        y = HORIZON_Y + int(50 * scale)
        if y < HEIGHT:
            alpha = max(30, int(80 * scale))
            pygame.draw.line(surface, GROUND_DARK, (0, y), (WIDTH, y), 1)

    # Perspective grid lines (vertical - converging to vanishing point)
    for i in range(-10, 11):
        x_world = i * 100
        x_near, _, _ = project(x_world, 0, NEAR_Z)
        x_far, y_far, _ = project(x_world, 0, FAR_Z)
        pygame.draw.line(surface, GROUND_DARK, (x_far, y_far), (x_near, HEIGHT), 1)


# --- Sky ---
def draw_sky(surface):
    for y in range(HORIZON_Y):
        t = y / HORIZON_Y
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))
    # Sun
    pygame.draw.circle(surface, (255, 250, 200), (WIDTH - 80, 50), 30)
    pygame.draw.circle(surface, (255, 240, 150), (WIDTH - 80, 50), 25)


# --- Game state ---
def reset():
    bird = Bird()
    pipes = []
    for i in range(5):
        pipes.append(Pipe(NEAR_Z + 300 + i * 400))
    score = 0
    explosion = None
    shake = 0
    return bird, pipes, score, explosion, shake

bird, pipes, score, explosion, shake = reset()
game_over = False
font = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 22)

# --- Main loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_over:
                    bird, pipes, score, explosion, shake = reset()
                    game_over = False
                else:
                    bird.flap()
            if event.key == pygame.K_ESCAPE:
                running = False

    if not game_over:
        # Input: left/right to steer
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            bird.move(-4)
        if keys[pygame.K_RIGHT]:
            bird.move(4)

        bird.update()
        for p in pipes:
            p.update()

        # Spawn new pipes
        if pipes[-1].z < NEAR_Z + 400:
            pipes.append(Pipe(pipes[-1].z + 400))
        # Remove passed pipes
        if pipes[0].z < NEAR_Z - 100:
            pipes.pop(0)

        # Collision
        crashed = False
        if bird.world_y > 250 or bird.world_y < -250:
            crashed = True
        for p in pipes:
            if p.check_collision(bird):
                crashed = True

        if crashed:
            game_over = True
            bird.alive = False
            sx, sy, _ = bird.screen_pos()
            explosion = Explosion(sx, sy)
            shake = 20

        # Score
        for p in pipes:
            if not p.passed and p.z < BIRD_Z - 20:
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
        off_x = random.randint(-shake, shake)
        off_y = random.randint(-shake, shake)
    else:
        off_x = off_y = 0

    # --- Draw ---
    draw_sky(screen)
    draw_ground(screen)

    # Draw pipes far to near (painter's algorithm)
    sorted_pipes = sorted(pipes, key=lambda p: -p.z)
    for p in sorted_pipes:
        p.draw(screen)

    # Bird
    if bird.alive:
        bird.draw(screen)

    # Explosion
    if explosion:
        explosion.draw(screen)

    # UI
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    if game_over:
        go_text = font.render("Game Over!", True, BLACK)
        restart_text = font_small.render("SPACE to restart | ESC to quit", True, BLACK)
        screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 30))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 10))
    else:
        hint = font_small.render("SPACE = flap | LEFT/RIGHT = steer", True, BLACK)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()   