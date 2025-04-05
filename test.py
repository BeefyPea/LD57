import pygame
import random
import time
from os import listdir
from os.path import isfile, join

# --- Constants ---
WIDTH, HEIGHT = 512, 512
PLAYER_VEL = 5

# --- Pygame Setup ---
pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Das Koks U-Boot")

# Load background and scale
BG = pygame.image.load("grey.png")
BG = pygame.transform.scale(BG, (WIDTH, HEIGHT))

# --- Helper Functions ---
def load_sprite(path, width, height):
    # Load the sprite from the given path
    sprite_sheet = pygame.image.load(path).convert_alpha()
    
    # Create a surface to hold the sprite (scale the sprite to desired size, if necessary)
    surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    surface.blit(sprite_sheet, (0, 0), (0, 0, width, height))  # Crop the sprite if needed
    
    return surface

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    COLOR = (125, 125, 125)

    def __init__(self, x, y, width, height, sprite):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.width = width
        self.height = height
        self.sprite = sprite  # The sprite image for the player

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

    def update(self):
        self.move(self.x_vel, self.y_vel)

    def draw(self, win):
        # Draw the player sprite on the window
        win.blit(self.sprite, (self.rect.x, self.rect.y))

# --- Game Functions ---
def draw_window(player):
    window.blit(BG, (0, 0))
    player.draw(window)
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
    
    # Load the sprite (assuming the file is "player.png" and is 16x16 pixels)
    sprite = load_sprite("uboot.png", 16, 16)
    
    player = Player(100, 100, 50, 50, sprite)  # Set the player size to 50x50 for visibility

    run = True
    while run:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        handle_movement(player)
        player.update()
        draw_window(player)

    pygame.quit()

if __name__ == "__main__":
    main()

