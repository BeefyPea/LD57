import pygame
import random
import math
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
import numpy as np


# --- Constants ---
WIDTH, HEIGHT = 512, 512
PLAYER_VEL = 4
TILE_SIZE = 32
GRID_ROWS, GRID_COLS = 5, 5  # Grid size
WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH, HEIGHT


# --- Pygame Setup ---
pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Das Koks U-Boot")


# Load background and scale
BG = pygame.image.load("sprites/BG_big.png")
BG = pygame.transform.scale(BG, (2560, 2560))

MM = pygame.image.load("sprites/minimap.png")
MM = pygame.transform.scale(MM, (64, 64))

boss_beaten = False

shoot = mixer.Sound("./sounds/shoot-6.mp3")
mixer.Sound.set_volume(shoot,0.08)


# --- Helper Functions ---
def load_sprite(path, width, height):
    sprite_sheet = pygame.image.load(path).convert_alpha()
    sprite_sheet = pygame.transform.scale(sprite_sheet, (width, height))
    return sprite_sheet
       

# --- Classes ---


class healthbar():
    def __init__(self, x, y, w, h, max_hp, parent):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hp = max_hp
        self.max_hp = max_hp
        self.parent = parent

    def draw(self, surface):
        global boss_beaten
        #calculate health ratio
        ratio = self.hp / self.max_hp

        if self.parent == "player":
            pygame.draw.rect(surface, "darkred", (self.x, self.y, self.w, self.h))
            pygame.draw.rect(surface, "green", (self.x, self.y, self.w * ratio, self.h))
            if self.w * self.hp / self.max_hp <= 0:
                game_over()
        if self.parent == "boss":
            if self.w * self.hp / self.max_hp != 0:
                pygame.draw.rect(surface, "darkred", (self.x, self.y, self.w, self.h))
                pygame.draw.rect(surface, "purple", (self.x, self.y, self.w * ratio, self.h))
            if self.w * self.hp / self.max_hp <= 0:
                main_men()

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
        self.shottime = time.time()

    def move(self, dx, dy):
        if self.x_vel != 0 and self.y_vel !=0:
            norm = math.sqrt(2)
            self.rect.x += dx/norm
            self.rect.y += dy/norm
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

    def update(self,window_rect):
        self.move(self.x_vel, self.y_vel)
                # Clamp player within window bounds
        self.rect.x = max(window_rect.left, min(self.rect.x, window_rect.right - self.width))
        self.rect.y = max(window_rect.top, min(self.rect.y, window_rect.bottom - self.height))

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
        def __init__(self, x, y, width, height, sprite,speed,ad):
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
            self.dmg = ad
            self.dmg = ad

        def move(self, dx, dy):
            if self.x_vel != 0 and self.y_vel !=0:
                norm = math.sqrt(2)
                self.rect.x += dx/norm
                self.rect.y += dy/norm
            else:
                self.rect.x += dx
                self.rect.y += dy

        def hunt(self,playerx,playery):
            self.x_vel = self.y_vel = 0
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

            if np.abs(distx) <= 3 and np.abs(disty) <= 3:
                health_bar_player.hp -= self.dmg

            if np.abs(distx) <= 3 and np.abs(disty) <= 3:
                health_bar_player.hp -= self.dmg

            if (distx**2 + disty**2)**0.5 < 250:
                self.x_vel -= x * self.speed
                self.y_vel -= y * self.speed

            self.move(self.x_vel,self.y_vel)
        

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

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite, ad):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.sprite = sprite
        self.dmg = ad
        self.last_attack_time = time.time()

        self.attacks = []  # Liste mit Angriffen
        self.rage = False

    def attack(self, player_pos):
        self.attack_cooldown = 2  # Sek. bis zur nächsten Warnung
        self.warning_duration = 1  # Sek. Warnung
        self.attack_duration = 2     # Sek. aktiver Angriff
        
        #if health_bar_boss.hp >= health_bar_boss.max_hp * 0.7:
        #    self.rage = False
        #if health_bar_boss.hp < health_bar_boss.max_hp * 0.5:
        #    self.rage = True


        current_time = time.time()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            self.last_attack_time = current_time

            if self.rage == False:
                x = player_pos[0] - 32
                y = 50
                attack_rect = pygame.Rect(x, y, 64, 412)

            if self.rage == True:
                x = [0,100]
                x = random.choice(x)
                y = player_pos[1]- 32
                attack_rect = pygame.Rect(x, y, 412, 64)

            self.attacks.append({
                'rect': attack_rect,
                'warning_start': current_time,
                'attack_start': None,
                'state': 'warning',
            })


    def update_attacks(self, window, player, proj):
        current_time = time.time()
        updated_attacks = []

        for atk in self.attacks:
            current_time = time.time()

            if atk['state'] == 'warning':
                if current_time - atk['warning_start'] < self.warning_duration:
                    pygame.draw.rect(window, (255, 0, 0), atk['rect'], 2)
                else:
                    atk['state'] = 'active'
                    atk['attack_start'] = current_time  # Neu für Angriff
                    updated_attacks.append(atk)

            elif atk['state'] == 'active':
                if current_time - atk['attack_start'] < self.attack_duration:
                    sprite = self.sprite
                    if self.rage == True:
                        sprite = pygame.transform.rotate(self.sprite, 90)
                    window.blit(sprite, (atk['rect'].x, atk['rect'].y))
                    if atk['rect'].colliderect(player.rect):
                        health_bar_player.hp -= self.dmg
                    updated_attacks.append(atk)

                    # Kollision mit Projektilen prüfen
                    for proj_obj in proj:
                        if atk['rect'].colliderect(proj_obj.rect):
                            proj.remove(proj_obj)  # Projektil löschen
                            updated_attacks.append(atk)  # Tentakelangriff beibehalten
                            #health_bar_boss.hp -= dmg_player

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite, ad):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.sprite = sprite
        self.dmg = ad
        self.last_attack_time = time.time()

        self.attacks = []  # Liste mit Angriffen
        self.rage = False

    def attack(self, player_pos):
        self.attack_cooldown = 2  # Sek. bis zur nächsten Warnung
        self.warning_duration = 1  # Sek. Warnung
        self.attack_duration = 2     # Sek. aktiver Angriff
        
        if health_bar_boss.hp >= health_bar_boss.max_hp * 0.5:
            self.rage = False
        if health_bar_boss.hp < health_bar_boss.max_hp * 0.5:
            self.rage = True
            self.attack_cooldown = 1  # Sek. bis zur nächsten Warnung
            self.warning_duration = 1.5  # Sek. Warnung
            self.attack_duration = 1     # Sek. aktiver Angriff


        current_time = time.time()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            self.last_attack_time = current_time

            if self.rage == False:
                x = player_pos[0] - 32
                y = 50
                attack_rect = pygame.Rect(x, y, 64, 412)

            if self.rage == True:
                x = [0,100]
                x = random.choice(x)
                y = player_pos[1]- 32
                attack_rect = pygame.Rect(x, y, 412, 64)

            self.attacks.append({
                'rect': attack_rect,
                'warning_start': current_time,
                'attack_start': None,
                'state': 'warning',
            })


    def update_attacks(self, window, player, proj):
        current_time = time.time()
        updated_attacks = []

        for atk in self.attacks:
            current_time = time.time()

            if atk['state'] == 'warning':
                if current_time - atk['warning_start'] < self.warning_duration:
                    pygame.draw.rect(window, (255, 0, 0), atk['rect'], 2)
                else:
                    atk['state'] = 'active'
                    atk['attack_start'] = current_time  # Neu für Angriff
                    updated_attacks.append(atk)

            elif atk['state'] == 'active':
                if current_time - atk['attack_start'] < self.attack_duration:
                    sprite = self.sprite
                    if self.rage == True:
                        sprite = pygame.transform.rotate(self.sprite, 90)
                    window.blit(sprite, (atk['rect'].x, atk['rect'].y))
                    if atk['rect'].colliderect(player.rect):
                        health_bar_player.hp -= self.dmg
                    updated_attacks.append(atk)

                    # Kollision mit Projektilen prüfen
                    for proj_obj in proj:
                        if atk['rect'].colliderect(proj_obj.rect):
                            proj.remove(proj_obj)  # Projektil löschen
                            updated_attacks.append(atk)  # Tentakelangriff beibehalten
                            health_bar_boss.hp -= dmg_player

class Window:
    def __init__(self, x, y, width, height, player_sprite,player_hit, row, col):
        self.rect = pygame.Rect(x, y, width, height)
        self.player = Player(256, 256, 32, 32, player_sprite,player_hit)
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.row = row
        self.col = col

    def update_cutout(self,win):
        cutout = pygame.Rect(self.col*512,self.row*512,512,512)
        self.background.blit(BG, (0, 0),cutout)

    def draw(self, win):
        self.update_cutout(win)
        win.blit(self.background, (0,0))
        self.player.draw(win)

        # Draw outer borders (green) on the edges of the grid
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

        # Optional: draw a thin red rectangle around each window (debug)
        pygame.draw.rect(win, (255, 255, 255), self.rect, 2)

    def update(self):
        self.player.update(self.rect)

    def check_transition(self, current_row, current_col, windows):
        # Transition right
        if self.player.rect.right >= self.rect.right and current_col < GRID_COLS - 1:
            next_window = windows[current_row][current_col + 1]
            next_window.player.rect.x = next_window.rect.left  # Align player at left of next window
            next_window.player.rect.y = self.player.rect.y    # Keep same vertical position
            next_window.player.shottime = self.player.shottime
            return current_row, current_col + 1

        # Transition left
        elif self.player.rect.left <= self.rect.left and current_col > 0:
            prev_window = windows[current_row][current_col - 1]
            prev_window.player.rect.x = prev_window.rect.right - prev_window.player.width  # Align player at right of previous window
            prev_window.player.rect.y = self.player.rect.y    # Keep same vertical position
            prev_window.player.shottime = self.player.shottime
            return current_row, current_col - 1

        # Transition down
        elif self.player.rect.bottom >= self.rect.bottom and current_row < GRID_ROWS - 1:
            next_window = windows[current_row + 1][current_col]
            next_window.player.rect.y = next_window.rect.top  # Align player at top of next window
            next_window.player.rect.x = self.player.rect.x    # Keep same horizontal position
            next_window.player.shottime = self.player.shottime
            return current_row + 1, current_col

        # Transition up
        elif self.player.rect.top <= self.rect.top and current_row > 0:
            prev_window = windows[current_row - 1][current_col]
            prev_window.player.rect.y = prev_window.rect.bottom - prev_window.player.height  # Align player at bottom of previous window
            prev_window.player.rect.x = self.player.rect.x    # Keep same horizontal position
            prev_window.player.shottime = self.player.shottime
            return current_row - 1, current_col

        return current_row, current_col
 
class Collider(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.height = height
        self.sprite = sprite  # The sprite image for the projectile

    def collision_bool(self, entity):
        return pygame.Rect.colliderect(self.rect,entity.rect)

    def collision_entity(self, entity):
        if pygame.Rect.colliderect(self.rect,entity.rect) == True:
            entity.rect.x += -1*entity.x_vel*1
            entity.rect.y += -1*entity.y_vel*1
            entity.x_vel = entity.y_vel = 0

    def draw(self,win):
        win.blit(self.sprite, (self.rect.x, self.rect.y))
        
class Minimap(pygame.sprite.Sprite):
    COLOR = (125, 125, 125)

    def __init__(self, x, y, width, height, sprite):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.height = height
        self.sprite = sprite  # The sprite image for the player
        self.original_sprite = sprite  # Save the original sprite for flipping

    def point(self,player,r,c):
        point = (self.rect.topleft[0]+4 + player.rect.x/(5*512/self.width) + c*12,self.rect.topleft[1]+4 + player.rect.y/(5*512/self.width)+r*12)
        return point
    
    def draw(self,win,player,r,c):
        win.blit(self.sprite, (self.rect.x, self.rect.y))
        circle_pos = self.point(player,r,c)
        pygame.draw.circle(window,"RED",circle_pos,2)
    

# --- Game Functions ---

def draw_char(player,proj,enemy,walls,boss):
    coll = []  

    for ind,punch in enumerate(proj): #check for projectiles, delete if too old
        if time.time() - punch.start > punch.lifespan:
            proj.pop(ind)
        else:
            coll.append(punch.rect)
            punch.fly()
            punch.draw(window)

    for ind,en in enumerate(enemy): #check for enemies, delete if collided
        for collider in coll:
            if en.collide(collider) == True:
                enemy.pop(ind)
                proj.pop()
        else: 
            en.hunt(player.rect.x,player.rect.y)
            en.draw(window)

    for collider in walls:
        collider.collision_entity(player)
        collider.draw(window)
        for en in enemy:
            collider.collision_entity(en)
        for ind,punch in enumerate(proj):
            if collider.collision_bool(punch) == True:
                proj.pop(ind)

    for boss_obj in boss:
        boss_obj.attack(player.rect.center)
        boss_obj.update_attacks(window, player, proj)

   
def draw_window(window_obj):
    window.fill((0, 0, 0))
    window_obj.draw(window)
    #pygame.display.update()

def handle_movement(player,proj,cooldown):
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
        if len(proj) < 1 and time.time() - player.shottime > cooldown :
            player.shottime = time.time()
            mixer.Sound.play(shoot)
            proj.append(projectile(player.rect.x + (-1)**player.flip*24,player.rect.y,16,16,player.hit,player.flip,0.5))



            

# --- define healthbars ---
health_bar_player = healthbar(95,35,100,10,100,"player")
health_bar_boss = healthbar(50, 462, 400, 25, 400, "boss")
cooldown = 0.5








def draw_dialogue_box(win, text):
    """Draws a simple dialogue box with text on the screen."""
    font = pygame.font.SysFont("Arial", 20)
    
    # Dialogue box background (semi-transparent)
    box_width = 400
    box_height = 60
    box_x = (WIDTH - box_width) // 2
    box_y =  400
    pygame.draw.rect(win, (0, 0, 0), (box_x, box_y, box_width, box_height), 0)  # Box background
    pygame.draw.rect(win, (255, 255, 255), (box_x, box_y, box_width, box_height), 3)  # Box border

    # Text (centered in the box)
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(WIDTH // 2, 400+ box_height//2))
    win.blit(text_surface, text_rect)





# --- Main Loop ---

def main():
    proj = []
    enemy = []
    coll = []
    boss = []
    mixer.music.load("./sounds/Vibes.wav")
    mixer.music.play(-1, 0.0)
    boss = []

    mixer.music.load("./sounds/Vibes.wav")
    mixer.music.load("./sounds/ambience.mp3")
    mixer.music.play(-1, 0.0)

    y_walls = [[0,0,0,0],
               [0,1,0,1],
               [0,1,1,1],
               [0,1,0,1],
               [0,0,0,0]]
    
    x_walls = [[0,0,0,0,0], #0
               [1,1,0,0,0], #1
               [1,0,1,0,0],
               [0,1,0,0,0],
               [0,0,0,0,0],]

    clock = pygame.time.Clock()

    # --- DEPTH METER FONT ---
    font = pygame.font.SysFont("Roboto", 20)

    # Load sprites
    sprite = load_sprite("sprites/uboot.png", 32, 32)
    hit = load_sprite("sprites/punch.png", 32, 32)
    fish1 = load_sprite("sprites/fish.png", 32, 32)
    fish2 = load_sprite("sprites/shark.png", 50, 25)   
    fish3 = load_sprite("sprites/big_jelly.png", 25, 50)
    coll_x = load_sprite("sprites/coll_x.png", 512, 40)
    coll_y = load_sprite("sprites/coll_y.png", 40, 512)
    tentacle = load_sprite("sprites/tentacle.png", 64, 412)  
    light = load_sprite("sprites/kegel.png", 128, 128)
    lightR = light
    lightL = pygame.transform.flip(light, True, False)

    # Create a grid of windows
    windows = [[Window(0, 0, WIDTH, HEIGHT, sprite, hit, row, col) for col in range(GRID_COLS)] for row in range(GRID_ROWS)]
    current_row, current_col = 0, 2  # Start in center window
    current_window = windows[current_row][current_col]

    # Initialize Minimap
    minimap = Minimap(25,10,64,64,MM)

    # Dialogue and spawn timers
    BossTime = None
    SpwanTime = None
    dialogue_duration = 3500  # 3 seconds in milliseconds
    enemyT1 = None
    enemyT2 = None
    enemyT3 = None
    enemy_spawn_duration = 10  # 10 milliseconds


    run = True
    while run:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False     

        current_row, current_col = current_window.check_transition(current_row, current_col, windows)
        current_window = windows[current_row][current_col]
        current_window.row,current_window.col = current_row, current_col
        coll = []

        if x_walls[current_row][current_col] == 1:
            coll.append(Collider(0, 498, 512, 40, coll_x))
        if x_walls[current_row - 1][current_col] == 1:
            coll.append(Collider(0, -20, 512, 40, coll_x))
        if current_row > 0:
            if y_walls[current_row][current_col - 1] == 1:
                coll.append(Collider(-20, 0, 40, 512, coll_y))
        if current_col < 4:
            if y_walls[current_row][current_col] == 1:
                coll.append(Collider(498, 0, 40, 512, coll_y))

        draw_window(current_window) 

        # ----------spawn enemys --------
        if current_row == 1 and current_col == 2:  
            if enemyT1 is None:
                enemyT1 = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - enemyT1
            if elapsed_time < enemy_spawn_duration:
                enemy.append(Enemy(300, 300, 50, 50, fish1, 3, 1))
        if current_row == 0 and current_col == 0:  
            if enemyT2 is None:
                enemyT2 = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - enemyT2
            if elapsed_time < enemy_spawn_duration:
                enemy.append(Enemy(300, 300, 70, 70, fish2, 4, 2))
        if current_row == 0 and current_col == 4:  
            if enemyT3 is None:
                enemyT3 = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - enemyT3
            if elapsed_time < enemy_spawn_duration:
                enemy.append(Enemy(300, 300, 30, 30, fish3, 2, 2))

        health_bar_player.draw(window)

        # Boss only in boss room
        if current_row == 2 and current_col == 0:
            
            if boss == [] and current_window.player.rect.right < 480 :
                boss.append(Boss(400, 50, 64, 461, tentacle, 10))
            if boss == [] and current_window.player.rect.right < 480 or boss != []:
                coll.append(Collider(498, 0, 40, 512, coll_y))
            
            health_bar_boss.draw(window)
        
        draw_char(current_window.player, proj, enemy, coll,boss) 
        handle_movement(current_window.player, proj,cooldown)
        current_window.player.draw(window)
        current_window.update() 

        # Light rendering
        filter = pygame.surface.Surface((540, 540))
        filter.fill((90, 90, 90))
        if current_window.player.flip == 0:
            light = lightR
            filter.blit(light, (current_window.player.rect.x + 40, current_window.player.rect.y - 40))
        elif current_window.player.flip == 1:
            light = lightL
            filter.blit(light, (current_window.player.rect.x - 115, current_window.player.rect.y - 40))
        window.blit(filter, (-10, -10), special_flags=pygame.BLEND_RGBA_SUB)

        # --- DEPTH METER ---
        player_y = current_window.player.rect.y
        depth = current_row * 100 + int((player_y / HEIGHT) * 100)
        shadow_text = font.render(f"Depth: {depth} m", True, (0, 0, 0))
        depth_text = font.render(f"Depth: {depth} m", True, (255, 255, 255))
        window.blit(shadow_text, (95, 11))  # Shadow for #contrast
        window.blit(depth_text, (96, 10))   # Actual text

        health_bar_player.draw(window)

        #Minimap draw
        minimap.draw(window,current_window.player,current_row,current_col)
        
        # --- Dialogue ---
        if current_row == 2 and current_col == 0:
            if BossTime is None:
                BossTime = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - BossTime

            if elapsed_time < dialogue_duration:
                draw_dialogue_box(window, "Lets throw hands fucker")
        if current_row == 0 and current_col == 2:
            if SpwanTime is None:
                SpwanTime = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - SpwanTime

            if elapsed_time < dialogue_duration:
                draw_dialogue_box(window, "Damn this octopus got my Fent")



        pygame.display.flip()
    pygame.quit()

#if __name__ == "__main__":
 #   main()





def start_game():
    global start_time, time_since_pop
    global dmg_player
    health_bar_player.hp = 100
    dmg_player = 50
    start_time = time.time()
    time_since_pop = 0

    health_bar_boss.hp = 400
    mixer.music.fadeout(1)
    main()


def game_over():
    game_over_font = pygame_menu.font.FONT_8BIT
    game_over_img = pygame_menu.baseimage.BaseImage(image_path = "sprites/GameOver.png", drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL)
    game_over_theme = Theme(background_color = game_over_img, widget_font = game_over_font, title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE)

    mixer.music.fadeout(100)
    mixer.music.load("./sounds/new_intro.wav")
    mixer.music.play(-1, 0.0)

    gameover = pygame_menu.Menu("", WIDTH, HEIGHT, theme = game_over_theme)
    gameover.add.label("Game Over")
    gameover.add.label("")
    gameover.add.label("")
    gameover.add.button("Try again", main_men)
    gameover.add.button("Exit", pygame_menu.events.EXIT)

    gameover.mainloop(window)

def main_men():
    main_menu_font = pygame_menu.font.FONT_8BIT
    main_menu_img = pygame_menu.baseimage.BaseImage(image_path="./sprites/Main_men_bg.png", drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL)
    main_theme = Theme(background_color = main_menu_img, widget_font = main_menu_font, title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE)

    mixer.init()
    mixer.music.load('./sounds/new_intro.wav')
    mixer.music.play(-1, 0.0)

    mainmenu = pygame_menu.Menu("", WIDTH, HEIGHT, theme = main_theme)
    mainmenu.add.button("Play", start_game)
    mainmenu.add.button("Exit", pygame_menu.events.EXIT)

    mainmenu.mainloop(window)
main_men()