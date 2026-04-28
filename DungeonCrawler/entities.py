# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:07:37 2026

@author: VDNSpare
"""

# entities.py
import pygame
import math
import os
from settings import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, speed, max_health):
        super().__init__()
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.color = color
        self.speed = speed
        self.max_health = max_health
        self.health = max_health
        
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.attack_timer = 0

    def draw_health_bar(self, surface, camera):
        bar_width = self.width
        bar_height = 6
        fill = max(0, (self.health / self.max_health) * bar_width)
        bx = self.x - camera.x
        by = self.y - camera.y - 12 
        pygame.draw.rect(surface, RED, (bx, by, bar_width, bar_height)) 
        pygame.draw.rect(surface, GREEN, (bx, by, fill, bar_height))    

    def draw(self, surface, camera):
        if self.image: surface.blit(self.image, (self.x - camera.x, self.y - camera.y))
        else: pygame.draw.rect(surface, self.color, (self.x - camera.x, self.y - camera.y, self.width, self.height))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50, BLUE, 5, max_health=100)
        self.inventory = [] 
        self.frame_index = 0.0      
        self.animation_speed = 0.2
        self.facing = 'down'        
        self.is_moving = False
        self.animations = {'up': [], 'down': [], 'left': [], 'right': []}
        try:
            for direction in ['up', 'down', 'left', 'right']:
                i = 0
                while os.path.exists(f"{direction}/{i}.png"):
                    img = pygame.image.load(f"{direction}/{i}.png")
                    img = pygame.transform.scale(img, (self.width, self.height))
                    self.animations[direction].append(img)
                    i += 1
            if self.animations['down']: self.image = self.animations['down'][0] 
        except: self.image = None

    def take_damage(self, amount): self.health -= amount

    def attack(self, enemies):
        self.attack_timer = 15 
        for enemy in enemies:
            dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if dist < 80: enemy.health -= 15 

    def update(self, walls: list, player=None):
        if self.attack_timer > 0: self.attack_timer -= 1
        keys = pygame.key.get_pressed()
        old_x, old_y = self.x, self.y
        self.is_moving = False 

        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.x -= self.speed; self.facing = 'left'; self.is_moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.x += self.speed; self.facing = 'right'; self.is_moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.y -= self.speed; self.facing = 'up'; self.is_moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: self.y += self.speed; self.facing = 'down'; self.is_moving = True

        self.rect.topleft = (self.x, self.y)
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                self.x, self.y = old_x, old_y
                self.rect.topleft = (self.x, self.y)

        if self.is_moving:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.facing]): self.frame_index = 0.0
        else: self.frame_index = 0.0
            
        if self.animations[self.facing]: self.image = self.animations[self.facing][int(self.frame_index)]

    def draw(self, surface, camera):
        super().draw(surface, camera)
        self.draw_health_bar(surface, camera) 
        draw_rect = self.rect.move(-camera.x, -camera.y)
        if self.attack_timer > 0:
            cx, cy = draw_rect.center 
            if self.facing == 'up': pygame.draw.arc(surface, WHITE, (cx - 25, cy - 35, 50, 50), 0, math.pi, 4)
            elif self.facing == 'down': pygame.draw.arc(surface, WHITE, (cx - 25, cy - 15, 50, 50), math.pi, 2 * math.pi, 4)
            elif self.facing == 'left': pygame.draw.arc(surface, WHITE, (cx - 35, cy - 25, 50, 50), math.pi / 2, 1.5 * math.pi, 4)
            elif self.facing == 'right': pygame.draw.arc(surface, WHITE, (cx - 15, cy - 25, 50, 50), -math.pi / 2, math.pi / 2, 4)

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 80, 80, RED, 2, max_health=50) 
        self.patrol_timer = 0
        self.patrol_direction = 1
        self.attack_cooldown = 0
        self.current_anim_state = 'idle'
        self.frame_index = 0.0
        self.animation_speed = 0.1
        self.facing_right = True
        self.is_removable = False
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'death': []}
        try:
            for state in ['idle', 'walk', 'attack', 'death']:
                i = 0
                while os.path.exists(f"goblin_{state}/{i}.png"):
                    img = pygame.image.load(f"goblin_{state}/{i}.png")
                    img = pygame.transform.scale(img, (self.width, self.height))
                    self.animations[state].append(img)
                    i += 1
            if self.animations['idle']: self.image = self.animations['idle'][0]
        except: self.image = None

    def update(self, walls, player=None):
        if self.health <= 0:
            self.current_anim_state = 'death'
            if self.animations['death']:
                self.frame_index += self.animation_speed
                if self.frame_index >= len(self.animations['death']) - 1:
                    self.frame_index = len(self.animations['death']) - 1
                    self.is_removable = True
                self.image = self.animations['death'][int(self.frame_index)]
                if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
            else: self.is_removable = True
            return

        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.attack_timer > 0: self.attack_timer -= 1
        old_x, old_y = self.x, self.y
        is_moving = False
        dist = math.hypot(self.x - player.x, self.y - player.y) if player else 999
        ai_state = 'chase' if dist < 300 else 'patrol'

        if ai_state == 'chase' and self.attack_timer == 0:
            is_moving = True
            if self.x < player.x: self.x += self.speed; self.facing_right = True
            elif self.x > player.x: self.x -= self.speed; self.facing_right = False
            if self.y < player.y: self.y += self.speed
            elif self.y > player.y: self.y -= self.speed
        
        self.rect.topleft = (self.x, self.y)
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                self.x, self.y = old_x, old_y; self.rect.topleft = (self.x, self.y); is_moving = False

        if player and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            player.take_damage(10); self.attack_timer = 30; self.attack_cooldown = 90; is_moving = False

        if self.attack_timer > 0: self.current_anim_state = 'attack'
        elif is_moving: self.current_anim_state = 'walk'
        else: self.current_anim_state = 'idle'

        if self.animations[self.current_anim_state]:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.current_anim_state]): self.frame_index = 0.0
            self.image = self.animations[self.current_anim_state][int(self.frame_index)]
            if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, surface, camera):
        super().draw(surface, camera)
        if not self.is_removable and self.health > 0:
            self.draw_health_bar(surface, camera) 

class NPC(Entity):
    def __init__(self, x, y):
        # We maken de tovenaar donkerpaars als er geen plaatje is
        super().__init__(x, y, 40, 40, (128, 0, 128), 0, max_health=100)
        self.quest_state = 'start'
        self.message = ""
        self.talk_timer = 0 
        
        # TOVENAAR PLAATJE INLADEN
        try:
            if os.path.exists("wizard.png"):
                img = pygame.image.load("wizard.png")
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        if self.talk_timer > 0: self.talk_timer -= 1

    def interact(self, player):
        self.talk_timer = 180 
        if self.quest_state == 'start':
            self.message = "Goblins bewaken de kist! Versla ze allemaal, pak de sleutel en kom terug!"
            self.quest_state = 'waiting'
        elif self.quest_state == 'waiting':
            if "Gouden Sleutel" in player.inventory:
                self.message = "Geweldig! De Uitgang (Bruine Deur) is nu geopend! Succes!"
                player.inventory.remove("Gouden Sleutel")
                player.inventory.append("Kasteel Toegang") 
                self.quest_state = 'done'
            else:
                self.message = "Versla alle Goblins zodat de kist opent, en breng me de sleutel!"
        elif self.quest_state == 'done':
            self.message = "De uitgang is vrij!"

    def draw(self, surface, camera):
        super().draw(surface, camera)
        if self.talk_timer > 0:
            font = pygame.font.Font(None, 24)
            text_surf = font.render(self.message, True, WHITE, BLACK)
            text_rect = text_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 10 - camera.y)
            surface.blit(text_surf, text_rect)

class Item(Entity):
    def __init__(self, x, y, item_name):
        super().__init__(x, y, 50, 50, YELLOW, 0, max_health=1)
        self.item_name = item_name
        self.is_picked_up = False
        self.frames = []
        self.frame_index = 0.0
        self.animation_speed = 0.2
        self.is_opening = False
        self.is_open = False
        try:
            i = 0
            while os.path.exists(f"kist/{i}.png"):
                img = pygame.image.load(f"kist/{i}.png")
                img = pygame.transform.scale(img, (self.width, self.height))
                self.frames.append(img)
                i += 1
            if self.frames: self.image = self.frames[0] 
            else: self.image = None
        except: self.image = None

    def interact(self, player):
        if not self.is_open and not self.is_opening: self.is_opening = True

    def update(self, walls=None, player=None):
        if self.is_opening:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.frames) - 1:
                self.frame_index = len(self.frames) - 1
                self.is_opening = False
                self.is_open = True
                if player and not self.is_picked_up:
                    player.inventory.append(self.item_name)
                    self.is_picked_up = True
            if self.frames: self.image = self.frames[int(self.frame_index)]

class Potion(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 20, (255, 20, 147), 0, max_health=1)
        self.is_picked_up = False
        try:
            if os.path.exists("potion.png"):
                img = pygame.image.load("potion.png")
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        if player and self.rect.colliderect(player.rect) and not self.is_picked_up:
            if player.health < player.max_health:
                player.health += 30 
                if player.health > player.max_health: player.health = player.max_health
                self.is_picked_up = True