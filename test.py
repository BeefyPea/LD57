import pygame
import math

# --- Constants ---
WIDTH, HEIGHT = 512, 512
PLAYER_VEL = 5
TILE_SIZE = 32
WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH, HEIGHT

# --- Pygame Setup ---
pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Das Koks U-Boot")

# Load background and scale
BG = pygame.image.load("grey.png")
BG = pygame.transform.scale(BG, (WIDTH, HEIGHT))

# --- Helper Functions ---
def load_sprite(path, width, height):
    sprite_sheet = pygame.image.load(path).convert_alpha()
    sprite_sheet = pygame.transform.scale(sprite_sheet, (width, height))
    return sprite_sheet

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.width = width
        self.height = height
        self.sprite = sprite
        self.original_sprite = sprite

    def move(self, dx, dy):
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
        # Normalize diagonal movement
        if self.x_vel != 0 and self.y_vel != 0:
            norm = math.sqrt(2)
            self.x_vel /= norm
            self.y_vel /= norm

        self.move(self.x_vel, self.y_vel)

        # Clamp position inside window bounds
        self.rect.x = max(window_rect.left, min(self.rect.x, window_rect.right - self.width))
        self.rect.y = max(145, min(self.rect.y, window_rect.bottom - self.height))  # Enforce y >= 305

    def draw(self, win):
        flipped_sprite = self.sprite
        if self.x_vel < 0:
            flipped_sprite = pygame.transform.flip(self.original_sprite, True, False)
        win.blit(flipped_sprite, (self.rect.x, self.rect.y))

# --- Window Class ---
class Window:
    def __init__(self, x, y, width, height, player_sprite):
        self.rect = pygame.Rect(x, y, width, height)
        self.player = Player(200, 150, 50, 50, player_sprite)  # Start position (200, 300)
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.blit(BG, (0, 0))

    def draw(self, win):
        win.blit(self.background, (self.rect.x, self.rect.y))
        self.player.draw(win)
        pygame.draw.rect(win, (255, 0, 0), self.rect, 2)  # Debug border

    def update(self):
        self.player.update(self.rect)

    def check_transition(self, current_index, windows):
        if self.player.rect.right >= self.rect.right and current_index < len(windows) - 1:
            next_window = windows[current_index + 1]
            next_window.player.rect.x = next_window.rect.left + 50
            next_window.player.rect.y = self.player.rect.y
            return current_index + 1

        elif self.player.rect.left <= self.rect.left and current_index > 0:
            prev_window = windows[current_index - 1]
            prev_window.player.rect.x = prev_window.rect.right - 50 - self.player.width
            prev_window.player.rect.y = self.player.rect.y
            return current_index - 1

        return current_index

# --- Game Functions ---
def draw_window(window_obj):
    window.fill((0, 0, 0))
    window_obj.draw(window)
    pygame.display.update()

def handle_movement(player):
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

# --- Main Loop ---
def main():
    clock = pygame.time.Clock()
    sprite = load_sprite("uboot.png", 32, 32)

    # Create multiple windows
    windows = [Window(0, 0, WIDTH, HEIGHT, sprite) for _ in range(5)]
    current_index = 2
    current_window = windows[current_index]

    run = True
    while run:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        handle_movement(current_window.player)
        current_window.update()

        # Handle window transition
        new_index = current_window.check_transition(current_index, windows)
        if new_index != current_index:
            current_index = new_index
            current_window = windows[current_index]

        draw_window(current_window)

    pygame.quit()

if __name__ == "__main__":
    main()
