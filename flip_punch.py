import pygame
import random
import time
import math
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

shoot = mixer.Sound("./sounds/shoot.mp3")
mixer.Sound.set_volume(shoot,0.5)

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
                pygame.draw.rect(surface, "darkkhaki", (self.x, self.y, self.w, self.h))
                pygame.draw.rect(surface, "yellow", (self.x, self.y, self.w * ratio, self.h))
            if self.w * self.hp / self.max_hp <= 0:
                main_men()
        if self.parent == "depth":
            pygame.draw.rect(surface, "Gray", (self.x, self.y, self.w, self.h))
            pygame.draw.rect(surface, "Blue", (self.x, self.y, self.w * ratio, self.h))
            if self.w * self.hp / self.max_hp <= 0:
                game_over()
            


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
    def __init__(self, x, y, width, height, sprite, flip, lifespan):
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
        def __init__(self, dict):
            super().__init__()
            self.dict = dict
            self.rect = pygame.Rect(dict['pos'][0],dict['pos'][1] ,dict['size'] ,dict['size'])
            self.x_vel = 0
            self.y_vel = 0
            self.width = dict['size']
            self.height = dict['size']
            self.sprite = dict['sprite']  # The sprite image for the player
            self.original_sprite = dict['sprite']  # Save the original sprite for flipping
            self.aggr = dict['aggr']
            self.speed = 1
            self.flip = 0
            self.ambient_x = 0
            self.ambient_y = 0
            if self.aggr == 0:
                self.dmg = 180
            else:
                self.dmg = dict['ad']
            self.shot = dict['shot']
            self.spawn = dict['spawned']
            if self.spawn != False:
                dict['spawned'] == True


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

            if self.aggr == 0:
                self.dmg += 1
                if self.dmg >= 180:
                    self.ambient_x = random.randint(30,482)
                    self.ambient_y = random.randint(30,482)
                    self.dmg = 0

            distx = self.rect.x -playerx*self.aggr - (1-self.aggr)*self.ambient_x
            disty = self.rect.y -playery*self.aggr - (1-self.aggr)*self.ambient_y

            if distx >= 0:
                x = 1
            else:
                x = -1

            if disty >= 0:
                y = 1
            else:
                y = -1
            if np.abs(distx)>5 and np.abs(disty)>5:
                self.flip = x
            if self.aggr ==1:
                if (distx**2 + disty**2)**0.5 < 250  :
                    self.x_vel -= x * self.speed 
                    self.y_vel -= y * self.speed
            else:
                self.x_vel -= x * self.speed 
                self.y_vel -= y * self.speed
            
            if np.abs(distx) <= 3 and np.abs(disty) <= 3 and self.aggr == 1:
                health_bar_player.hp -= self.dmg
            
            self.move(self.x_vel,self.y_vel)
        

        def collide(self,proj):
            bool = pygame.Rect.colliderect(self.rect,proj)
            if bool == True:
                self.shot = bool
            return bool

        def draw(self,win):
            fishL = pygame.transform.flip(self.original_sprite, True, False)
            fishR = self.original_sprite
            if self.flip <= 0:  # Moving left
                self.sprite = fishL
            else:               # Moving left
                self.sprite = fishR
            win.blit(self.sprite, (self.rect.x, self.rect.y))

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite, ad, bg_sprite):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.sprite = sprite
        self.dmg = ad
        self.last_attack_time = time.time()
        self.bg_sprite = bg_sprite

        self.attacks = []  # Liste mit Angriffen
        self.rage = False
    
    def attack(self, player_pos):
        update_music("intro_epic_ver")
        
        if health_bar_boss.hp >= health_bar_boss.max_hp * 0.5:
            self.attack_cooldown = 1.5    # Sek. bis zur nächsten Warnung
            self.warning_duration = 1.5   # Sek. Warnung
            self.attack_duration = 1.5    # Sek. aktiver Angriff
            self.rage = False

        if health_bar_boss.hp < health_bar_boss.max_hp * 0.5:
            for index,item in enumerate(self.attacks):
                if item['rage'] == False:
                    self.attacks.pop(index)
            self.rage = True
            self.attack_cooldown = 1
            self.warning_duration = .75
            self.attack_duration = 1

        current_time = time.time()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            self.last_attack_time = current_time

            if self.rage == False:
                x = player_pos[0] - 32
                y = 100
                attack_rect = pygame.Rect(x, y, 64, 412)
                flip = "None"

            if self.rage == True:
                x = [0,100]
                x = random.choice(x)
                if x == 0:
                    flip = "left"
                if x == 100:
                    flip = "right"
                y = player_pos[1]- 32
                attack_rect = pygame.Rect(x, y, 412, 64)

            self.attacks.append({
                'rect': attack_rect,
                'warning_start': current_time,
                'attack_start': None,
                'state': 'warning',
                'rage' : self.rage,
                'flip' : flip
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
                        sprite = pygame.transform.rotate(sprite, 90)
                        if atk['flip'] == "left":
                            sprite = pygame.transform.flip(sprite, True, False)
                        if atk['flip'] == "right":
                            sprite = pygame.transform.flip(sprite, False, False)
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
    def __init__(self, x, y, width, height, player_sprite,player_hit, row, col, items):
        self.rect = pygame.Rect(x, y, width, height)
        self.player = Player(256, 256, 32, 32, player_sprite, player_hit)
        self.background = pygame.Surface((WIDTH, HEIGHT))
        # self.background.blit(BG, (0, 0))
        self.row = row
        self.col = col
        self.items = items

    def update_cutout(self,win):
        cutout = pygame.Rect(self.col*512,self.row*512,512,512)
        self.background.blit(BG, (0, 0),cutout)
        if self.col == 0 and self.row == 2:
            boss_sprite = load_sprite("sprites/big_boy_okto.png", 512, 512)
            self.background.blit(boss_sprite, (0,0))

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

    def update(self):
        self.items.clear()
        self.player.update(self.rect)

    def check_transition(self, current_row, current_col, windows):
        # Transition right
        if self.player.rect.right >= self.rect.right and current_col < GRID_COLS - 1:
            next_window = windows[current_row][current_col + 1]
            next_window.player.rect.x = next_window.rect.left  # Align player at left of next window
            next_window.player.rect.y = self.player.rect.y    # Keep same vertical position
            return current_row, current_col + 1

        # Transition left
        elif self.player.rect.left <= self.rect.left and current_col > 0:
            prev_window = windows[current_row][current_col - 1]
            prev_window.player.rect.x = prev_window.rect.right - prev_window.player.width  # Align player at right of previous window
            prev_window.player.rect.y = self.player.rect.y    # Keep same vertical position
            return current_row, current_col - 1

        # Transition down
        elif self.player.rect.bottom >= self.rect.bottom and current_row < GRID_ROWS - 1:
            next_window = windows[current_row + 1][current_col]
            next_window.player.flip = self.player.flip
            next_window.player.rect.y = next_window.rect.top  # Align player at top of next window
            next_window.player.rect.x = self.player.rect.x    # Keep same horizontal position
            return current_row + 1, current_col

        # Transition up
        elif self.player.rect.top <= self.rect.top and current_row > 0:
            prev_window = windows[current_row - 1][current_col]
            prev_window.player.flip = self.player.flip
            prev_window.player.rect.y = prev_window.rect.bottom - prev_window.player.height  # Align player at bottom of previous window
            prev_window.player.rect.x = self.player.rect.x    # Keep same horizontal position
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

class Pickup(pygame.sprite.Sprite):
    def __init__(self, width, height, item):
        super().__init__()
        self.dict = item

        self.xpos = item['koords'][0]
        self.ypos = item['koords'][1]
        self.name = item['name']
        self.gotten = item['status']

        self.width = width
        self.height = height
        self.sprite = item['sprite']

        self.rect = pygame.Rect(self.xpos, self.ypos, width, height)
        self.item_count = 1

    def buff(self, player_pos):
        global light_value
        player_rect = pygame.Rect(player_pos[0], player_pos[1], 50, 50)
        for item in range(0, self.item_count):
            window.blit(self.sprite, (self.xpos, self.ypos))

        if pygame.Rect.colliderect(self.rect, player_rect):
            if self.name == "hp_buff" and health_bar_player.hp <= health_bar_player.max_hp-20:
                health_bar_player.hp += 20

            # -- useless atm, need to change how light value is handled --
            if self.name == "light_buff":
                if light_value > 10:
                    light_value -= 10

            if self.name == "oxygen_buff":
                drowning_bar_player.hp = drowning_bar_player.max_hp+1

            self.dict['status'] = True

# --- Game Functions ---
def draw_char(player,proj,enemy,walls, boss, items,dict):
    global start_time, time_since_pop, boss_beaten
    coll = []
    # window.blit(BG, (0, 0))   

    for ind,punch in enumerate(proj): #check for projectiles, delete if too old
        if time.time() - punch.start > punch.lifespan:
            proj.pop(ind)
        else:
            coll.append(punch.rect)
            punch.fly()
            punch.draw(window)

    for ind,en in enumerate(enemy): #check for enemies, delete if collided
        # for collider in coll:
        #     if en.collide(collider) == True:
        #         enemy.pop(ind)
        #         proj.pop()
        # else: 
        #     en.hunt(player.rect.x,player.rect.y)
        #     en.draw(window)
        if en.spawn == False:
            if coll != []:
                for collider in coll:
                    if en.collide(collider) == True:
                        proj.clear()
                        enemy.pop(ind)
                        #en['shot'] = True
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

    for int,thing in enumerate(items):
        thing.buff(player.rect.center)
        if thing.gotten == True:
            items.pop(int)
       
def update_music(track_path, loop=-1):
    global _current_track
    if _current_track != track_path:
        mixer.music.unload
        mixer.music.load(f'./sounds/{track_path}.wav')
        mixer.music.play(loop)
        _current_track = track_path

def draw_window(window_obj):
    window.fill((0, 0, 0))
    window_obj.draw(window)

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
    if keys[pygame.K_ESCAPE]:
        main_men()
    # debug option
    # if keys[pygame.K_p]:
    #     print(f'current x-pos: {player.rect.center[0]}  current y-pos: {player.rect.center[1]}')

# --- some global variables ---
health_bar_player = healthbar(80,25,100,10,100,"player")
drowning_bar_player = healthbar(80,40,100,10,180,"depth")
health_bar_boss = healthbar(25, 475, 462, 25, 400, "boss")
cooldown = 0.5
_current_track = "new intro"

# --- dialogue ---
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
    global light_value
    proj = []
    enemy = []
    coll = []
    boss = []
    items = []
    pending_spawns = []

    def handle_enemy_spawns():
        for spawn in pending_spawns:
            enemy.append(Enemy(spawn))
        pending_spawns.clear()

    light_value = 90
    update_music("Vibes")
    ambience = mixer.Sound("./sounds/ambience.mp3")
    mixer.Sound.play(ambience, -1)
    mixer.Sound.set_volume(ambience, 1)

    # --- walls ---
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
    
    # Load the sprite (assuming the file is "uboot.png" and we upscale it to 32x32)
    sprite = load_sprite("sprites/uboot.png", 32, 32)
    hit = load_sprite("sprites/punch.png", 32,32)
    fish1 = load_sprite("sprites/fish.png", 32,32)
    fish2 = load_sprite("sprites/shark.png", 64, 32)
    jellyfish1 = load_sprite("sprites/jellyfish1.png", 32, 32)
    jellyfish2 = load_sprite("sprites/jellyfish2.png", 32, 32)
    anglerfish = load_sprite("sprites/anglerfish.png", 32, 32)
    aal = load_sprite("sprites/aal.png", 128, 32)
    fish3 = load_sprite("sprites/big_jelly.png", 32, 64)
    squid = load_sprite("sprites/squid.png", 32, 32)
    tentacle = load_sprite("sprites/tentacle.png", 64, 412)
    big_boss = load_sprite("sprites/big_boy_okto.png", 512, 512)
    coll_x = load_sprite("sprites/coll_x.png", 512,40)
    coll_y = load_sprite("sprites/coll_y.png", 40,512)
    light = load_sprite("sprites/kegel.png", 128,128)
    item1 = load_sprite("sprites/item1.png", 32, 32)
    item2 = load_sprite("sprites/item2.png", 16, 16)
    lightR = light
    lightL = pygame.transform.flip(light, True, False)

    # --- hardcode enemies ---
    enemy_dict = [{
        'room' : (0,4),
       'pos': (256,256),
       'size': 50,
       'sprite' : fish2,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
       'spawned' : False
    },
    {
        'room' : (1,0),
       'pos': (312,124),
       'size': 50,
       'sprite' : fish1,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False
    },
    {  'room' : (1,1),
       'pos': (312,124),
       'size': 50,
       'sprite' : fish1,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False},
    {  'room' : (2,2),
       'pos': (32,194),
       'size': 50,
       'sprite' : jellyfish1,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       },
    {  'room' : (4,2),
       'pos': (32,194),
       'size': 50,
       'sprite' : fish2,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False
       },
    {  'room' : (4,2),
       'pos': (32,194),
       'size': 50,
       'sprite' : fish2,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False
       },
    {  'room' : (3,0),
       'pos': (290,400),
       'size': 50,
       'sprite' : squid,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       }, 
    {  'room' : (3,0),
       'pos': (290,400),
       'size': 50,
       'sprite' : squid,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       },  
    {  'room' : (4,1),
       'pos': (290,400),
       'size': 50,
       'sprite' : squid,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       },  
    {  'room' : (4,1),
       'pos': (290,400),
       'size': 50,
       'sprite' : squid,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       },
    {  'room' : (4,1),
       'pos': (290,400),
       'size': 50,
       'sprite' : squid,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       }, 
    {  'room' : (4,1),
       'pos': (290,400),
       'size': 50,
       'sprite' : squid,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       }, 
    {  'room' : (4,5),
       'pos': (290,400),
       'size': 50,
       'sprite' : squid,
       'ad' : 10,
       'aggr' : 0,
       'shot' : False,
        'spawned' : False
       }, 
    {  'room' : (5,0),
       'pos': (210,300),
       'size': 50,
       'sprite' : anglerfish,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False
       },   
    {  'room' : (5,2),
       'pos': (210,300),
       'size': 50,
       'sprite' : anglerfish,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False
       }, 
    {  'room' : (5,5),
       'pos': (110,290),
       'size': 50,
       'sprite' : anglerfish,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False
       }, 
    {  'room' : (5,5),
       'pos': (210,40),
       'size': 50,
       'sprite' : anglerfish,
       'ad' : 10,
       'aggr' : 1,
       'shot' : False,
        'spawned' : False}]

    # --- hardcode items ---
    items_dict = [{
        'name' : 'hp_buff',
        'room' : (1,3),
        'koords' : (213,383),
        'sprite' : item1, 
        'status' : False 
        },{
        'name' : 'hp_buff',
        'room' : (2,4),
        'koords' : (186, 475),
        'sprite' : item1,
        'status' : False
        },{
        'name' : 'hp_buff',
        'room' : (2,2),
        'koords' : (434, 387),
        'sprite' : item1,
        'status' : False
        },{
        'name' : 'hp_buff',
        'room' : (0,4),
        'koords' : (222, 436),
        'sprite' : item1,
        'status' : False
        },{
        'name' : 'oxygen_buff',
        'room' : (4,4),
        'koords' : (369, 427),
        'sprite' : item2,
        'status' : False
    }]

    # Create a 8x3 grid of windows
    windows = [[Window(0, 0, WIDTH, HEIGHT, sprite, hit, row, col, items) for col in range(GRID_COLS)] for row in range(GRID_ROWS)]
    current_row, current_col = 0, 2  # Start in the center window
    current_window = windows[current_row][current_col]

    # Initialize Minimap
    minimap = Minimap(10,10,64,64,MM)    

    # Dialogue and spawn timers
    BossTime = None
    SpwanTime = None
    easteregg_time = None
    dialogue_duration = 4000  # 3 seconds in milliseconds
    enemyT1 = None
    enemyT2 = None
    enemyT3 = None
    enemy_spawn_duration = 10  # 10 milliseconds

    run = True
    while run:
        clock.tick(30)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False     

        # Check for transitions and update the window
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

        zone = 0
        if current_row <2:
            zone=1
        elif  current_row ==2:
            zone=2
        elif current_row >2:
            zone=3       
        
        for entry in enemy_dict:
            if entry['room'] == (current_row,current_col) and entry['shot'] == False:
                pending_spawns.append(entry)
                entry['shot'] = True

        handle_enemy_spawns()

        # On-screen Movement
        draw_window(current_window)

        # # ----------spawn enemys --------
        # if current_row == 1 and current_col == 2:  
        #     if enemyT1 is None:
        #         enemyT1 = pygame.time.get_ticks()  # Record the start time when entering the room
        #     elapsed_time = pygame.time.get_ticks() - enemyT1
        #     if elapsed_time < enemy_spawn_duration:
        #         enemy.append(Enemy(300, 300, 50, 50, fish1, 3, 1))
        # if current_row == 0 and current_col == 0:  
        #     if enemyT2 is None:
        #         enemyT2 = pygame.time.get_ticks()  # Record the start time when entering the room
        #     elapsed_time = pygame.time.get_ticks() - enemyT2
        #     if elapsed_time < enemy_spawn_duration:
        #         enemy.append(Enemy(300, 300, 70, 70, fish2, 4, 2))
        # if current_row == 0 and current_col == 4:  
        #     if enemyT3 is None:
        #         enemyT3 = pygame.time.get_ticks()  # Record the start time when entering the room
        #     elapsed_time = pygame.time.get_ticks() - enemyT3
        #     if elapsed_time < enemy_spawn_duration:
        #         enemy.append(Enemy(300, 300, 30, 30, fish3, 2, 2))

        for item in items_dict:
            if current_col == item['room'][0] and current_row == item['room'][1] and item['status'] == False:
                items.append(Pickup(32, 32, item))


        health_bar_player.draw(window)

        # Boss only in boss room
        if current_row == 2 and current_col == 0:
            
            if boss == [] and current_window.player.rect.right < 480 :
                boss.append(Boss(400, 50, 64, 461, tentacle, 10, big_boss))
            if boss == [] and current_window.player.rect.right < 480 or boss != []:
                coll.append(Collider(498, 0, 40, 512, coll_y))
            
            health_bar_boss.draw(window)

        draw_char(current_window.player, proj, enemy, coll,boss, items,enemy_dict) 
        
        handle_movement(current_window.player, proj,cooldown)
        current_window.player.draw(window)
        current_window.update() 

        # Light rendering
        filter = pygame.surface.Surface((512, 512))
        if current_row <= 1:
            light_vacl_1 = 90
            filter.fill((light_vacl_1, light_vacl_1, light_vacl_1))
        elif current_row == 2:
            light_vacl_2 = 100
            filter.fill((light_vacl_2, light_vacl_2, light_vacl_2))
        elif current_row > 2:
            light_vacl_3 = 120
            filter.fill((light_vacl_3, light_vacl_3, light_vacl_3))

        if current_window.player.flip == 0:
            light = lightR
            filter.blit(light, (current_window.player.rect.x + 28, current_window.player.rect.y -50))
        elif current_window.player.flip == 1:
            light = lightL
            filter.blit(light, (current_window.player.rect.x - 125, current_window.player.rect.y - 50))
        window.blit(filter, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # --- DEPTH METER ---
        player_y = current_window.player.rect.y
        depth = current_row * 100 + int((player_y / HEIGHT) * 100)
        if depth > 3:
            drowning_bar_player.hp -= 1/60
        elif depth <= 3 and drowning_bar_player.hp < 180:
            drowning_bar_player.hp += 40/60
        shadow_text = font.render(f"Depth: {depth*2} m", True, (0, 0, 0))
        depth_text = font.render(f"Depth: {depth*2} m", True, (255, 255, 255))
        drowning_text = font.render(f"{int(drowning_bar_player.hp/1.8)}%", True, ("Lightblue"))
        health_text = font.render(f"{int(health_bar_player.hp/health_bar_player.max_hp * 100)}", True, ("green"))
        window.blit(shadow_text, (95, 11))  # Shadow for #contrast
        window.blit(depth_text, (96, 10))   # Actual text
        window.blit(drowning_text, (185, 40))
        window.blit(health_text, (185, 25))

        health_bar_player.draw(window)
        drowning_bar_player.draw(window)

        #Minimap draw
        minimap.draw(window,current_window.player,current_row,current_col)

        # --- Dialogue ---
        if current_row == 2 and current_col == 0:
            if BossTime is None:
                BossTime = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - BossTime

            if elapsed_time < dialogue_duration:
                draw_dialogue_box(window, "Lets throw hands fucker!")

        if current_row == 0 and current_col == 2:
            if SpwanTime is None:
                SpwanTime = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - SpwanTime

            if elapsed_time < dialogue_duration:
                draw_dialogue_box(window, "Well then, lets start investigating...")

        if current_row == 4 and current_col == 0:
            if easteregg_time is None:
                easteregg_time = pygame.time.get_ticks()  # Record the start time when entering the room
            elapsed_time = pygame.time.get_ticks() - easteregg_time

            if elapsed_time < dialogue_duration:
                draw_dialogue_box(window, "This looks ... fishy")

        pygame.display.flip()

    pygame.quit()


def start_game():
    global start_time, time_since_pop
    global dmg_player
    health_bar_player.hp = 100
    drowning_bar_player.hp = 180
    dmg_player = 50
    start_time = time.time()
    time_since_pop = 0

    health_bar_boss.hp = 500
    main()

def game_over():
    game_over_font = pygame_menu.font.FONT_8BIT
    game_over_img = pygame_menu.baseimage.BaseImage(image_path = "sprites/GameOver.png", drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL)
    game_over_theme = Theme(background_color = game_over_img, widget_font = game_over_font, title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE)

    mixer.init()
    update_music("new_intro")

    if mixer.get_busy():
        mixer.stop()

    gameover = pygame_menu.Menu("", WIDTH, HEIGHT, theme = game_over_theme)
    gameover.add.label("Game Over")
    gameover.add.label("")
    gameover.add.label("")
    gameover.add.button("Try again", main_men)
    gameover.add.button("Exit", pygame_menu.events.EXIT)

    gameover.mainloop(window)

def main_men():
    global _current_track
    main_menu_font = pygame_menu.font.FONT_8BIT
    main_menu_img = pygame_menu.baseimage.BaseImage(image_path="./sprites/Main_men_bg.png", drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL)
    main_theme = Theme(background_color = main_menu_img, widget_font = main_menu_font, title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE)

    mixer.init()
    update_music("new_intro")

    if mixer.get_busy():
        mixer.stop()

    mainmenu = pygame_menu.Menu("", WIDTH, HEIGHT, theme = main_theme)
    mainmenu.add.button("Play", intro)
    mainmenu.add.button("Exit", pygame_menu.events.EXIT)

    mainmenu.mainloop(window)

def intro():
    # Custom font for both text and menu
    Fent_font = "font/PressStart2P-Regular.ttf"
    font = pygame.font.Font(Fent_font, 15)

    # Background and menu theme
    win_img = pygame_menu.baseimage.BaseImage(
        image_path="sprites/Intro.png", drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL
    )
    win_theme = Theme(
        background_color=win_img,
        widget_font=Fent_font,
        widget_font_size=17,
        title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE
    )

    # Typing message
    message = "For a while now, boats\nkeep disappearing far out.\n\nDue to your history \nwith deepsea shenanigans, you \nwere contracted by the state.\n\nThe village relies on your help."
    lines = message.split('\n')
    text_speed = 15  # ms between characters

    display_text = ""
    char_index = 0
    line_index = 0
    last_update = pygame.time.get_ticks()
    text_done = False

    while True:
        window.fill((0, 0, 0))
        window.blit(win_img.get_surface(), (0, 0))

        now = pygame.time.get_ticks()
        if not text_done and now - last_update > text_speed:
            if line_index < len(lines):
                line = lines[line_index]
                if char_index < len(line):
                    display_text += line[char_index]
                    char_index += 1
                    last_update = now
                else:
                    display_text += '\n'
                    line_index += 1
                    char_index = 0
            else:
                text_done = True
                text_done_time = pygame.time.get_ticks()

        # Render left-aligned text
        y = HEIGHT // 6
        padding = 35
        for i, line in enumerate(display_text.split('\n')):
            text_surface = font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.topleft = (padding, y + i * 40)
            window.blit(text_surface, text_rect)

        # Show hint after short delay
        if text_done and now - text_done_time > 1000:
            hint_font = pygame.font.Font(Fent_font, 16)
            hint = hint_font.render("Press ENTER to continue", True, (200, 200, 200))
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 60))
            window.blit(hint, hint_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if not text_done:
                    display_text = message
                    text_done = True
                    text_done_time = pygame.time.get_ticks()
                else:
                    # Final menu after message
                    win = pygame_menu.Menu("", WIDTH, HEIGHT, theme=win_theme)
                    win.add.label("Find the cause",font_color=(210, 210, 210))
                    win.add.label("for the disappearences.",font_color=(210, 210, 210))
                    win.add.label("")
                    win.add.label("Be cautios tho, these waters",font_color=(210, 210, 210))
                    win.add.label(" aren't to well explored...",font_color=(210, 210, 210))
                    win.add.vertical_margin(20)
                    win.add.label("Are you ready?",font_color=(210, 210, 210))
                    win.add.label("")
                    win.add.label("")
                    win.add.label("")
                      # small spacer
                    win.add.button("Submerge", start_game)
                    win.mainloop(window)
                    return

def win():
    # Custom font for both text and menu
    Fent_font = "font/PressStart2P-Regular.ttf"
    font = pygame.font.Font(Fent_font, 15)

    # Background and menu theme
    win_img = pygame_menu.baseimage.BaseImage(
        image_path="sprites/GameOver.png", drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL
    )
    win_theme = Theme(
        background_color=win_img,
        widget_font=Fent_font,
        widget_font_size=20,
        title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE
    )

    # Typing message
    message = "After a long fight, \npeace returns to the land.\nYou did well.\nThe Hamburger Hafen is safe,\nat least for now..."
    lines = message.split('\n')
    text_speed = 17  # ms between characters

    display_text = ""
    char_index = 0
    line_index = 0
    last_update = pygame.time.get_ticks()
    text_done = False

    while True:
        window.fill((0, 0, 0))
        window.blit(win_img.get_surface(), (0, 0))

        now = pygame.time.get_ticks()
        if not text_done and now - last_update > text_speed:
            if line_index < len(lines):
                line = lines[line_index]
                if char_index < len(line):
                    display_text += line[char_index]
                    char_index += 1
                    last_update = now
                else:
                    display_text += '\n'
                    line_index += 1
                    char_index = 0
            else:
                text_done = True
                text_done_time = pygame.time.get_ticks()

        # Render left-aligned text
        y = HEIGHT // 4
        padding = 40
        for i, line in enumerate(display_text.split('\n')):
            text_surface = font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.topleft = (padding, y + i * 40)
            window.blit(text_surface, text_rect)

        # Show hint after short delay
        if text_done and now - text_done_time > 1000:
            hint_font = pygame.font.Font(Fent_font, 16)
            hint = hint_font.render("Press ENTER to continue", True, (200, 200, 200))
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 60))
            window.blit(hint, hint_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if not text_done:
                    display_text = message
                    text_done = True
                    text_done_time = pygame.time.get_ticks()
                else:
                    # Final menu after message
                    win = pygame_menu.Menu("", WIDTH, HEIGHT, theme=win_theme)
                    win.add.label("The creature was bested",font_color=(210, 210, 210))
                    win.add.label("")
                    win.add.label("The seven seas still",font_color=(210, 210, 210))
                    win.add.label("need your help",font_color=(210, 210, 210))
                    win.add.vertical_margin(20)
                    win.add.label("Are you ready?",font_color=(210, 210, 210))
                    win.add.label("")
                    win.add.label("")
                    win.add.label("")
                      # small spacer
                    win.add.button("Continue", main_men)
                    win.mainloop(window)
                    return

main_men()
