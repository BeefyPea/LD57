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
BG = pygame.image.load("sprites/background_fish.png")
BG = pygame.transform.scale(BG, (WIDTH, HEIGHT))

# --- Helper Functions ---
def load_sprite(path, width, height):
    # Load the sprite from the given path
    sprite_sheet = pygame.image.load(path).convert_alpha()
    
    # Scale the sprite to the desired width and height (32x32)
    sprite_sheet = pygame.transform.scale(sprite_sheet, (width, height))
    
    return sprite_sheet

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
        self.original_sprite = sprite  # Save the original sprite for flipping
        self.flip = 0

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
        # Flip the sprite when moving left, otherwise keep it the same
        if self.x_vel < 0 and self.flip == 0:  # Moving left
            self.sprite = pygame.transform.flip(self.sprite, True, False)
            self.flip = 1
        elif self.x_vel > 0 and self.flip == 1:  # Moving left
            self.sprite = pygame.transform.flip(self.sprite, True, False)
            self.flip = 0
        # Draw the (possibly flipped) player sprite on the window
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
    
    # Load the sprite (assuming the file is "uboot.png" and we upscale it to 32x32)
    sprite = load_sprite("sprites/uboot.png", 32, 32)
    
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