import pygame
import random
import time
from os import listdir
from os.path import isfile, join
import pygame_menu
from pygame_menu import themes
import pygame_menu.baseimage
import pygame_menu.events
from pygame_menu.themes import Theme
import pygame_menu.widgets
from pygame.locals import *
from pygame import mixer

# --- Constants ---
WIDTH, HEIGHT = 512, 512
PLAYER_VEL = 4

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

    def __init__(self, x, y, width, height, sprite,hit):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.width = width
        self.height = height
        self.sprite = sprite  # The sprite image for the player
        self.original_sprite = sprite  # Save the original sprite for flipping
        self.hit = hit
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

class projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite,flip,lifespan):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.width = width
        self.height = height
        self.sprite = sprite  # The sprite image for the projectile
        self.flip = flip
        self.start = time.time()
        self.lifespan = lifespan

        if self.flip == 1:
            self.sprite = pygame.transform.flip(self.sprite, True, False)

    def draw(self,win):
        win.blit(self.sprite, (self.rect.x, self.rect.y))

    def fly(self):
        self.rect.x += PLAYER_VEL*2 * (-1)**self.flip

class Enemy(pygame.sprite.Sprite):
        def __init__(self, x, y, width, height, sprite,speed):
            super().__init__()
            self.rect = pygame.Rect(x, y, width, height)
            self.x_vel = 0
            self.y_vel = 0
            self.width = width
            self.height = height
            self.sprite = sprite  # The sprite image for the player
            self.original_sprite = sprite  # Save the original sprite for flipping
            self.speed = speed
            self.flip = 0

        def hunt(self,playerx,playery):
            distx = self.rect.x - playerx
            disty = self.rect.y - playery
            x = y = 0 
            if distx > 0:
                x = 1
            else:
                x = -1

            if disty > 0:
                y = 1
            else:
                y = -1

            self.flip = x

            if (distx**2 + disty**2)**0.5 < 250:
                self.rect.x -= x * self.speed
                self.rect.y -= y * self.speed

        def collide(self,proj):
            return pygame.Rect.colliderect(self.rect,proj)

        def draw(self,win):
            fishL = pygame.transform.flip(self.original_sprite, True, False)
            fishR = self.original_sprite
            if self.flip <= 0:  # Moving left
                self.sprite = fishL
            else:               # Moving left
                self.sprite = fishR
            win.blit(self.sprite, (self.rect.x, self.rect.y))

    

# --- Game Functions ---
def draw_window(player,proj,enemy):
    collider = pygame.Rect(-100,-100,1,1)
    window.blit(BG, (0, 0))

    for ind,punch in enumerate(proj): #check for projectiles, delete if too old
        if time.time() - punch.start > punch.lifespan:
            proj.pop(ind)
        else:
            collider = punch.rect
            punch.fly()
            punch.draw(window)

    for ind,en in enumerate(enemy):
        if en.collide(collider) == True:
                enemy.pop(ind)
                proj.pop()
        else: 
            en.hunt(player.rect.x,player.rect.y)
            en.draw(window)

    player.draw(window)
    

    pygame.display.update()

def handle_movement(player,proj):
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
            proj.append(projectile(player.rect.x + (-1)**player.flip*24,player.rect.y,16,16,player.hit,player.flip,1))
    if keys[pygame.K_ESCAPE]:
        main_men()


# --- Main Loop ---

def main():
    mixer.music.load("./sounds/level1_explore.wav")
    mixer.music.set_volume(50 / 100)
    mixer.music.play(-1,0.0)
    proj = []
    enemy = []
    clock = pygame.time.Clock()
    
    # Load the sprite (assuming the file is "uboot.png" and we upscale it to 32x32)
    sprite = load_sprite("sprites/uboot.png", 32, 32)
    hit = load_sprite("sprites/punch.png", 32,32)
    fish = load_sprite("sprites/fish.png", 32,32)
    shark = load_sprite("sprites/shark.png", 64, 32)
    jellyfish1 = load_sprite("sprites/jellyfish1.png", 32, 32)
    jellyfish2 = load_sprite("sprites/jellyfish2.png", 32, 32)
    
    player = Player(100, 100, 50, 50, sprite,hit)  # Set the player size to 50x50 for visibility
    enemy.append(Enemy(300,300,20,20,fish,2))
    enemy.append(Enemy(400,400,64,32,shark,1))
    enemy.append(Enemy(300,400,32,32,jellyfish2,1))
    enemy.append(Enemy(200,400,32,32,jellyfish1,1))

    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        handle_movement(player,proj)
        
        player.update()
        draw_window(player,proj,enemy)

    pygame.quit()

# if __name__ == "__main__":
#     main()

def start_game():
    mixer.music.fadeout(1)
    main()

def main_men():
    main_menu_font = pygame_menu.font.FONT_8BIT
    main_menu_img = pygame_menu.baseimage.BaseImage(image_path="./sprites/Main_men_bg.png", drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL)
    main_theme = Theme(background_color = main_menu_img, widget_font = main_menu_font, title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE)

    mixer.init()
    mixer.music.load('./sounds/main_menu_theme.wav')
    mixer.music.play(-1, 0.0)

    mainmenu = pygame_menu.Menu("", WIDTH, HEIGHT, theme = main_theme)
    mainmenu.add.button("Play", start_game)
    mainmenu.add.button("Exit", pygame_menu.events.EXIT)

    mainmenu.mainloop(window)

main_men()
