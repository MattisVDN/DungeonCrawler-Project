# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:07:37 2026

@author: VDNSpare
"""

# entities.py
import pygame
import math
from abc import ABC, abstractmethod
from settings import *

class Entity(ABC):
    def __init__(self, x, y, width, height, color, speed, max_health=100):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.speed = speed
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.max_health = max_health
        self.health = max_health
        self.attack_timer = 0 

    @abstractmethod
    def update(self, walls: list, player=None):
        pass

    def draw_healthbar(self, surface, draw_rect):
        if self.health < self.max_health and self.health > 0:
            bar_width = self.width
            bar_height = 5
            health_ratio = self.health / self.max_health
            pygame.draw.rect(surface, RED, (draw_rect.x, draw_rect.y - 10, bar_width, bar_height))
            pygame.draw.rect(surface, (0, 255, 0), (draw_rect.x, draw_rect.y - 10, bar_width * health_ratio, bar_height))

    def draw(self, surface, camera):
        draw_rect = self.rect.move(-camera.x, -camera.y)
        if getattr(self, 'image', None):
            surface.blit(self.image, draw_rect.topleft)
        else:
            pygame.draw.rect(surface, self.color, draw_rect)
        self.draw_healthbar(surface, draw_rect)

class Item(Entity):
    def __init__(self, x, y, item_type):
        super().__init__(x, y, 20, 20, GOLD, 0)
        self.item_type = item_type
        self.is_picked_up = False

    def update(self, walls: list, player=None):
        if player and not self.is_picked_up:
            if self.rect.colliderect(player.rect):
                self.is_picked_up = True
                player.inventory.append(self.item_type)

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 30, 30, BLUE, 5, max_health=100)
        self.inventory = [] 
        
        self.frame_index = 0.0      
        self.animation_speed = 0.15 
        self.facing = 'down'        
        self.is_moving = False

        self.animations = {'up': [], 'down': [], 'left': [], 'right': []}

        try:
            for direction in ['up', 'down', 'left', 'right']:
                for i in range(4): 
                    img = pygame.image.load(f"{direction}/{i}.png")
                    img = pygame.transform.scale(img, (self.width, self.height))
                    self.animations[direction].append(img)
            self.image = self.animations['down'][0] 
        except FileNotFoundError:
            print("LET OP: Animatie mapjes (up, down, left, right) niet gevonden!")
            self.image = None

    def take_damage(self, amount):
        self.health -= amount

    def attack(self, enemies):
        self.attack_timer = 15 
        for enemy in enemies:
            dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if dist < 70:
                enemy.health -= 15

    def update(self, walls: list, player=None):
        if self.attack_timer > 0: self.attack_timer -= 1

        keys = pygame.key.get_pressed()
        old_x, old_y = self.x, self.y
        self.is_moving = False 

        if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
            self.x -= self.speed
            self.facing = 'left'
            self.is_moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: 
            self.x += self.speed
            self.facing = 'right'
            self.is_moving = True
            
        if keys[pygame.K_UP] or keys[pygame.K_w]: 
            self.y -= self.speed
            self.facing = 'up'
            self.is_moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: 
            self.y += self.speed
            self.facing = 'down'
            self.is_moving = True

        self.rect.topleft = (self.x, self.y)

        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if wall.tile_type == 'door' and "Gouden Sleutel" in self.inventory:
                    self.inventory.remove("Gouden Sleutel")
                    return "NEXT_LEVEL" 
                else:
                    self.x, self.y = old_x, old_y
                    self.rect.topleft = (self.x, self.y)

        if self.is_moving:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.facing]):
                self.frame_index = 0.0
        else:
            self.frame_index = 0.0
            
        if self.animations[self.facing]: 
            self.image = self.animations[self.facing][int(self.frame_index)]

        return None

    def draw(self, surface, camera):
        super().draw(surface, camera) 
        draw_rect = self.rect.move(-camera.x, -camera.y)
        
        # Zwaard animatie (wordt over speler getekend)
        if self.attack_timer > 0:
            pygame.draw.arc(surface, WHITE, (draw_rect.x-10, draw_rect.y-10, 50, 50), 0, 3.14, 4)

class Enemy(Entity):
    def __init__(self, x, y):
        # We geven de vijand tijdelijk even een RODE kleur als fallback
        super().__init__(x, y, 30, 30, RED, 2, max_health=30)
        self.state = 'patrol'
        self.patrol_timer = 0
        self.patrol_direction = 1
        self.attack_cooldown = 0
        
        # Dit TRY blok zorgt ervoor dat de game NIET crasht als het plaatje faalt!
        try:
            import os
            # Een extra slimme manier om het plaatje te zoeken
            if os.path.exists("goblin.png"):
                loaded_image = pygame.image.load("goblin.png")
                self.image = pygame.transform.scale(loaded_image, (self.width, self.height))
            else:
                print("Goblin plaatje niet gevonden, ik gebruik een rood vierkantje!")
                self.image = None
        except Exception as e:
            print(f"Fout bij laden goblin: {e}")
            self.image = None

    def update(self, walls: list, player=None):
        if self.attack_timer > 0: self.attack_timer -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1

        old_x, old_y = self.x, self.y

        if player and self.health > 0:
            dist = math.hypot(self.x - player.x, self.y - player.y)
            if dist < 250: self.state = 'chase'
            elif dist > 350: self.state = 'patrol'

        if self.state == 'patrol':
            self.x += self.speed * self.patrol_direction
            self.patrol_timer += 1
            if self.patrol_timer > 60:
                self.patrol_direction *= -1
                self.patrol_timer = 0
        elif self.state == 'chase' and player and self.health > 0:
            if self.x < player.x: self.x += self.speed
            if self.x > player.x: self.x -= self.speed
            if self.y < player.y: self.y += self.speed
            if self.y > player.y: self.y -= self.speed

        self.rect.topleft = (self.x, self.y)

        if player and self.rect.colliderect(player.rect) and self.health > 0 and self.attack_cooldown == 0:
            player.take_damage(10)
            self.attack_timer = 10 
            self.attack_cooldown = 60 
            self.x, self.y = old_x, old_y
            self.rect.topleft = (self.x, self.y)

        for wall in walls:
            if self.rect.colliderect(wall.rect):
                self.x, self.y = old_x, old_y
                self.rect.topleft = (self.x, self.y)
                if self.state == 'patrol': self.patrol_direction *= -1

    def draw(self, surface, camera):
        super().draw(surface, camera)
        if self.attack_timer > 0:
            draw_rect = self.rect.move(-camera.x, -camera.y)
            pygame.draw.line(surface, (200, 200, 200), draw_rect.center, (draw_rect.centerx + 20, draw_rect.centery), 3)
class NPC(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 30, 30, YELLOW, 0)
        self.message = "Vind de sleutel om naar Level 2 te gaan!"
        self.is_talking = False

    def update(self, walls: list, player=None):
        if player:
            dist = math.hypot(self.x - player.x, self.y - player.y)
            self.is_talking = dist < 60