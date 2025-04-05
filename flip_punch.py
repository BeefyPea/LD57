import pygame
import random
import math
import time
from os import listdir
from os.path import isfile, join

# --- Constants ---
WIDTH, HEIGHT = 512, 512
PLAYER_VEL = 4
TILE_SIZE = 32
GRID_ROWS, GRID_COLS = 8, 3  # Grid size
WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH, HEIGHT

# --- Pygame Setup ---
pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Das Koks U-Boot")

# Load background and scale
BG = pygame.image.load("sprites/background_fish.png")
BG = pygame.transform.scale(BG, (WIDTH, HEIGHT))

# --- Helper Functions ---
def load_sprite(path, width, height):
    sprite_sheet = pygame.image.load(path).convert_alpha()
    sprite_sheet = pygame.transform.scale(sprite_sheet, (width, height))
    return sprite_sheet

# --- Classes ---
class Player(pygame.sprite.Sprite):
    COLOR = (125, 125, 125)

    def __init__(self, x, y, width, height, sprite, hit):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.width = width
        self.height = height
        self.sprite = sprite
        self.original_sprite = sprite
        self.hit = hit
        self.flip = 0

    def move(self, dx, dy):
        if self.x_vel != 0 and self.y_vel != 0:
            norm = math.sqrt(2)
            self.rect.x += dx / norm
            self.rect.y += dy / norm
        else:
            self.rect.x += dx
            self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel

    def move_right(self, vel):
        self.x_vel = vel

    def move_up(self, vel):
        self.y_vel = -vel

    def move_down(self, vel):
        self.y_vel = vel

    def update(self, window_rect):
        self.move(self.x_vel, self.y_vel)
        self.rect.x = max(window_rect.left, min(self.rect.x, window_rect.right - self.width))
        self.rect.y = max(window_rect.top, min(self.rect.y, window_rect.bottom - self.height))

    def draw(self, win):
        if self.x_vel < 0 and self.flip == 0:
            self.sprite = pygame.transform.flip(self.sprite, True, False)
            self.flip = 1
        elif self.x_vel > 0 and self.flip == 1:
            self.sprite = pygame.transform.flip(self.sprite, True, False)
            self.flip = 0
        win.blit(self.sprite, (self.rect.x, self.rect.y))

class projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite, flip, lifespan):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.sprite = sprite
        self.flip = flip
        self.start = time.time()
        self.lifespan = lifespan

        if self.flip == 1:
            self.sprite = pygame.transform.flip(self.sprite, True, False)

    def draw(self, win):
        win.blit(self.sprite, (self.rect.x, self.rect.y))

    def fly(self):
        self.rect.x += PLAYER_VEL * 2 * (-1) ** self.flip

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite, speed):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.original_sprite = sprite
        self.sprite = sprite
        self.speed = speed
        self.flip = 0

    def hunt(self, playerx, playery):
        distx = self.rect.x - playerx
        disty = self.rect.y - playery
        x = -1 if distx < 0 else 1
        y = -1 if disty < 0 else 1
        self.flip = x

        if (distx ** 2 + disty ** 2) ** 0.5 < 250:
            self.rect.x -= x * self.speed
            self.rect.y -= y * self.speed

    def collide(self, proj):
        return pygame.Rect.colliderect(self.rect, proj)

    def draw(self, win):
        self.sprite = self.original_sprite if self.flip > 0 else pygame.transform.flip(self.original_sprite, True, False)
        win.blit(self.sprite, (self.rect.x, self.rect.y))

class Window:
    def __init__(self, x, y, width, height, player_sprite, player_hit, row, col):
        self.rect = pygame.Rect(x, y, width, height)
        self.player = Player(256, 256, 50, 50, player_sprite, player_hit)
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.blit(BG, (0, 0))
        self.row = row
        self.col = col

    def draw(self, win):
        win.blit(self.background, (self.rect.x, self.rect.y))
        self.player.draw(win)
        border_thickness = 8
        border_color = (0, 0, 0)
        if self.row == 0:
            pygame.draw.line(win, border_color, (0, 0), (WIDTH, 0), border_thickness)
        if self.row == GRID_ROWS - 1:
            pygame.draw.line(win, border_color, (0, HEIGHT - 1), (WIDTH, HEIGHT - 1), border_thickness)
        if self.col == 0:
            pygame.draw.line(win, border_color, (0, 0), (0, HEIGHT), border_thickness)
        if self.col == GRID_COLS - 1:
            pygame.draw.line(win, border_color, (WIDTH - 1, 0), (WIDTH - 1, HEIGHT), border_thickness)
        pygame.draw.rect(win, (255, 255, 255), self.rect, 2)

    def update(self):
        self.player.update(self.rect)

    def check_transition(self, current_row, current_col, windows):
        if self.player.rect.right >= self.rect.right and current_col < GRID_COLS - 1:
            next_window = windows[current_row][current_col + 1]
            next_window.player.rect.x = next_window.rect.left
            next_window.player.rect.y = self.player.rect.y
            return current_row, current_col + 1
        elif self.player.rect.left <= self.rect.left and current_col > 0:
            prev_window = windows[current_row][current_col - 1]
            prev_window.player.rect.x = prev_window.rect.right - prev_window.player.width
            prev_window.player.rect.y = self.player.rect.y
            return current_row, current_col - 1
        elif self.player.rect.bottom >= self.rect.bottom and current_row < GRID_ROWS - 1:
            next_window = windows[current_row + 1][current_col]
            next_window.player.flip = self.player.flip
            next_window.player.rect.y = next_window.rect.top
            next_window.player.rect.x = self.player.rect.x
            return current_row + 1, current_col
        elif self.player.rect.top <= self.rect.top and current_row > 0:
            prev_window = windows[current_row - 1][current_col]
            prev_window.player.flip = self.player.flip
            prev_window.player.rect.y = prev_window.rect.bottom - prev_window.player.height
            prev_window.player.rect.x = self.player.rect.x
            return current_row - 1, current_col
        return current_row, current_col

# --- Game Functions ---
def draw_char(player, proj, enemy):
    collider = pygame.Rect(-100, -100, 1, 1)
    window.blit(BG, (0, 0))

    for ind, punch in enumerate(proj):
        if time.time() - punch.start > punch.lifespan:
            proj.pop(ind)
        else:
            collider = punch.rect
            punch.fly()
            punch.draw(window)

    for ind, en in enumerate(enemy):
        if en.collide(collider):
            enemy.pop(ind)
            proj.pop()
        else:
            en.hunt(player.rect.x, player.rect.y)
            en.draw(window)

def draw_window(window_obj):
    window.fill((0, 0, 0))
    window_obj.draw(window)

def handle_movement(player, proj):
    keys = pygame.key.get_pressed()
    player.x_vel = 0
    player.y_vel = 0
    if keys[pygame.K_a]:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d]:
        player.move_right(PLAYER_VEL)
    if keys[pygame.K_w]:
        player.move_up(PLAYER_VEL)
    if keys[pygame.K_s]:
        player.move_down(PLAYER_VEL)
    if keys[pygame.K_SPACE]:
        if len(proj) < 1:
            proj.append(projectile(player.rect.x + (-1) ** player.flip * 24, player.rect.y, 16, 16, player.hit, player.flip, 0.5))

# --- Main Loop ---
def main():
    proj = []
    enemy = []
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 24)
    sprite = load_sprite("sprites/uboot.png", 32, 32)
    hit = load_sprite("sprites/punch.png", 32, 32)
    fish = load_sprite("sprites/fish.png", 32, 32)
    light = load_sprite("sprites/kegel.png", 128, 128)
    lightR = light
    lightL = pygame.transform.flip(light, True, False)

    windows = [[Window(0, 0, WIDTH, HEIGHT, sprite, hit, row, col) for col in range(GRID_COLS)] for row in range(GRID_ROWS)]
    current_row, current_col = 0, 1
    current_window = windows[current_row][current_col]

    enemy.append(Enemy(300, 300, 50, 50, fish, 2))

    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        current_row, current_col = current_window.check_transition(current_row, current_col, windows)
        current_window = windows[current_row][current_col]

        draw_window(current_window)
        draw_char(current_window.player, proj, enemy)
        handle_movement(current_window.player, proj)
        current_window.player.draw(window)
        current_window.update()

        filter = pygame.surface.Surface((540, 540))
        filter.fill((115, 115, 115))
        if current_window.player.flip == 0:
            light = lightR
            filter.blit(light, (current_window.player.rect.x + 40, current_window.player.rect.y - 40))
        elif current_window.player.flip == 1:
            light = lightL
            filter.blit(light, (current_window.player.rect.x - 115, current_window.player.rect.y - 40))
        window.blit(filter, (-10, -10), special_flags=pygame.BLEND_RGBA_SUB)

        # --- Depth Meter ---
        player_y = current_window.player.rect.y
        depth = current_row * 100 + int((player_y / HEIGHT) * 100)
        depth_text = font.render(f"Depth: {depth} m", True, (255, 255, 255))
        window.blit(depth_text, (10, 10))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
