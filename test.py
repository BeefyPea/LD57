import pygame
import random
import time
from os import listdir
from os.path import isfile, join

WIDTH, HEIGHT = 1000, 700                              #shape of wondow parameters
playervel = 5




window = pygame.display.set_mode((WIDTH, HEIGHT))       #declares window shape
pygame.display.set_caption("Das Koks U-Boot")

BG = pygame.image.load("grey.png")         #loading in backgroundpic

BG = pygame.transform.scale(BG, (WIDTH, HEIGHT))        #scales bakgroundpicture to windows dimensions
########## Player Handling #########



class Player(pygame.sprite.Sprite):
    COLOR = (125, 125, 125)



    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.direction = 'up'
        self.mask = None
        self.animation_counter = 0
    
    def move(self, dx, dy ):
        self.rect.x += dx
        self.rect.y += dy
    
    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != 'left':
            self.direction = 'left'
            self.animation_count=0
    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != 'right':
            self.direction = 'right'
            self.animation_count=0
    def move_up(self, vel):
        self.y_vel = -vel
        if self.direction != 'up':
            self.direction = 'up'
            self.animation_count=0
    def move_down(self, vel):
        self.y_vel = vel
        if self.direction != 'down':
            self.direction = 'down'
            self.animation_count=0

    def update(self):
        self.move(self.x_vel, self.y_vel)
        
    
    def draw(self, win):
        self.sprite = self.SPRITES["move"][0]
        win.blit(self.sprite, (self.rect.x, self.rect.y))
        #pygame.draw.rect(win, self.COLOR, self.rect)
########### Player handling #################



def draw_window(player):
    window.blit(BG, (0, 0))

    player.draw(window)

    pygame.display.update()

def handle_movement(player):
    keys =pygame.key.get_pressed()

    player.x_vel = 0
    player.y_vel = 0

    if keys[pygame.K_a]:
        player.move_left(playervel)
    if keys[pygame.K_d]:
        player.move_right(playervel)
    if keys[pygame.K_w]:
        player.move_up(playervel)
    if keys[pygame.K_s]:
        player.move_down(playervel)





def main():


    run = True
    clock = pygame.time.Clock()

    player = Player(100,100, 50, 50)



    while run:
        clock.tick(60)  # Limit to 60 FPS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        


        player.update()
        handle_movement(player)  # Update player position based on keys pressed
        draw_window(player)  # Draw background continuously

    pygame.quit()

if __name__ == "__main__":
    main()