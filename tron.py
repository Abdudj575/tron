import pygame
import sys
import math
import colorsys
import random
import time

pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Neon Tron-like Game")

clock = pygame.time.Clock()
font = pygame.font.Font(None, 50)

speed = 3

directions = [(speed, 0), (0, speed), (-speed, 0), (0, -speed)]

# Shield power-up settings
SHIELD_DURATION = 5  # seconds
SHIELD_SPAWN_INTERVAL = 7  # seconds
SHIELD_RADIUS = 12

class Cycle:
    def __init__(self, x, y, dir_idx, color, keys_dict=None, is_ai=False):
        self.x = x
        self.y = y
        self.dir_idx = dir_idx
        self.color = color  # for drawing the cycle
        self.keys = keys_dict if not is_ai else {}
        self.alive = True
        self.is_ai = is_ai
        self.dx, self.dy = directions[dir_idx]
        self.shielded = False
        self.shield_end_time = 0

    def handle_input(self, pressed):
        for key, new_dir in self.keys.items():
            if pressed[key]:
                if (new_dir - self.dir_idx) % 4 != 2:
                    self.dir_idx = new_dir
                    self.dx, self.dy = directions[new_dir]

    def ai_decide(self):
        look_ahead = 50

        def is_safe(d):
            dx, dy = directions[d]
            unit_x = dx / speed if dx != 0 else 0
            unit_y = dy / speed if dy != 0 else 0
            for i in range(1, look_ahead + 1):
                cx = int(self.x + unit_x * i)
                cy = int(self.y + unit_y * i)
                if cx < 0 or cx >= width or cy < 0 or cy >= height:
                    return False
                if collision_surface.get_at((cx, cy)) == (255, 255, 255):
                    return False
            return True

        current_safe = is_safe(self.dir_idx)
        if not current_safe:
            left_dir = (self.dir_idx - 1) % 4
            right_dir = (self.dir_idx + 1) % 4
            left_safe = is_safe(left_dir)
            right_safe = is_safe(right_dir)
            if left_safe and right_safe:
                if random.random() < 0.5:
                    self.dir_idx = left_dir
                else:
                    self.dir_idx = right_dir
            elif left_safe:
                self.dir_idx = left_dir
            elif right_safe:
                self.dir_idx = right_dir
            # else keep going
        else:
            if random.random() < 0.01:
                left_dir = (self.dir_idx - 1) % 4
                right_dir = (self.dir_idx + 1) % 4
                new_d = left_dir if random.random() < 0.5 else right_dir
                if is_safe(new_d):
                    self.dir_idx = new_d
        self.dx, self.dy = directions[self.dir_idx]

    def give_shield(self):
        self.shielded = True
        self.shield_end_time = time.time() + SHIELD_DURATION

    def update_shield(self):
        if self.shielded and time.time() > self.shield_end_time:
            self.shielded = False

menu = True
is_single = False  # default
while menu:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                is_single = True
                menu = False
            elif event.key == pygame.K_2:
                is_single = False
                menu = False

    screen.fill((0, 0, 0))
    text = font.render("Press 1 for Single Player, 2 for Multiplayer", True, (255, 255, 255))
    screen.blit(text, (width // 2 - text.get_width() // 2, height // 2 - text.get_height() // 2))
    pygame.display.flip()
    clock.tick(60)

keys_wasd = {
    pygame.K_d: 0,
    pygame.K_s: 1,
    pygame.K_a: 2,
    pygame.K_w: 3
}

keys_arrows = {
    pygame.K_RIGHT: 0,
    pygame.K_DOWN: 1,
    pygame.K_LEFT: 2,
    pygame.K_UP: 3
}

if is_single:
    player1 = Cycle(100, height // 2, 0, (0, 255, 0), keys_arrows, is_ai=False)  # green, starting right, user
    player2 = Cycle(width - 100, height // 2, 2, (255, 0, 255), is_ai=True)  # magenta, starting left, AI
else:
    player1 = Cycle(100, height // 2, 0, (0, 255, 0), keys_wasd, is_ai=False)  # green, starting right, player1
    player2 = Cycle(width - 100, height // 2, 2, (255, 0, 255), keys_arrows, is_ai=False)  # magenta, starting left, player2

cycles = [player1, player2]

collision_surface = pygame.Surface((width, height))
collision_surface.fill((0, 0, 0))

visual_surface1 = pygame.Surface((width, height), pygame.SRCALPHA)
visual_surface1.fill((0, 0, 0, 0))

visual_surface2 = pygame.Surface((width, height), pygame.SRCALPHA)
visual_surface2.fill((0, 0, 0, 0))

running = True

# Shield power-up state
shield_pos = None
last_shield_spawn = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pressed = pygame.key.get_pressed()

    # Spawn shield if needed
    now = time.time()
    if (shield_pos is None) and (now - last_shield_spawn > SHIELD_SPAWN_INTERVAL):
        while True:
            sx = random.randint(40, width - 40)
            sy = random.randint(40, height - 40)
            # Avoid spawning on a trail
            if collision_surface.get_at((sx, sy)) == (0, 0, 0):
                shield_pos = (sx, sy)
                break
        last_shield_spawn = now

    # Update shield timers
    for cycle in cycles:
        cycle.update_shield()

    # Handle input or AI decide for each cycle
    for cycle in cycles:
        if cycle.alive:
            if not cycle.is_ai:
                cycle.handle_input(pressed)
            else:
                cycle.ai_decide()

    # Move and check collision for each cycle
    for cycle in cycles:
        if cycle.alive:
            old_x, old_y = cycle.x, cycle.y
            cycle.x += cycle.dx
            cycle.y += cycle.dy

            # Check collision along the movement path
            collided = False
            vec_x = cycle.dx
            vec_y = cycle.dy
            length = math.sqrt(vec_x ** 2 + vec_y ** 2)
            if length > 0:
                for i in range(1, int(length) + 1):
                    factor = i / length
                    cx = int(old_x + vec_x * factor)
                    cy = int(old_y + vec_y * factor)
                    if cx < 0 or cx >= width or cy < 0 or cy >= height:
                        collided = True
                        break
                    if collision_surface.get_at((cx, cy)) == (255, 255, 255):
                        collided = True
                        break

            # Check for shield pickup
            if shield_pos is not None:
                dist = math.hypot(cycle.x - shield_pos[0], cycle.y - shield_pos[1])
                if dist < SHIELD_RADIUS + 6:
                    cycle.give_shield()
                    shield_pos = None

            if collided:
                if cycle.shielded:
                    # Ignore collision if shielded
                    pass
                else:
                    cycle.alive = False
            else:
                # Draw the trail on collision and visual surfaces
                pygame.draw.line(collision_surface, (255, 255, 255), (int(old_x), int(old_y)), (int(cycle.x), int(cycle.y)), 1)
                if cycle == player1:
                    pygame.draw.line(visual_surface1, (255, 255, 255, 255), (int(old_x), int(old_y)), (int(cycle.x), int(cycle.y)), 10)
                elif cycle == player2:
                    pygame.draw.line(visual_surface2, (255, 255, 255, 255), (int(old_x), int(old_y)), (int(cycle.x), int(cycle.y)), 10)

    # Check if game over
    if sum(cycle.alive for cycle in cycles) < 2:
        running = False

    # Get current neon background color
    current_time = pygame.time.get_ticks() / 1000.0
    hue = (current_time / 10)  % 1.0
    bg_rgb = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0))
    comp_hue1 = (hue + 0.4) % 1.0
    comp_rgb1 = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(comp_hue1, 1.0, 1.0))
    comp_hue2 = (hue + 0.6) % 1.0
    comp_rgb2 = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(comp_hue2, 1.0, 1.0))

    screen.fill(bg_rgb)

    # Create colored trail displays
    trail_display1 = visual_surface1.copy()
    trail_display1.fill(comp_rgb1 + (255,), special_flags=pygame.BLEND_MULT)
    screen.blit(trail_display1, (0, 0))

    trail_display2 = visual_surface2.copy()
    trail_display2.fill(comp_rgb2 + (255,), special_flags=pygame.BLEND_MULT)
    screen.blit(trail_display2, (0, 0))

    # Draw shield power-up
    if shield_pos is not None:
        pygame.draw.circle(screen, (0, 200, 255), shield_pos, SHIELD_RADIUS)
        pygame.draw.circle(screen, (255, 255, 255), shield_pos, SHIELD_RADIUS, 2)

    # Draw cycles
    for cycle in cycles:
        if cycle.alive:
            if cycle.shielded:
                # Draw a glowing outline if shielded
                pygame.draw.circle(screen, (0, 200, 255), (int(cycle.x), int(cycle.y)), 10, 3)
            pygame.draw.circle(screen, cycle.color, (int(cycle.x), int(cycle.y)), 5)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()