# -*- coding: utf-8 -*-
"""
level.py - De bouwstenen én de verzamelplek voor de levels
"""
import pygame
from settings import TILE_SIZE

# --- HIER LADEN WE JOUW LOSSE BESTANDEN IN ---
from level_1 import MAP as L1
from level_2 import MAP as L2

# De lijst die main.py nodig heeft
ALL_LEVELS = [L1, L2]

# --- DE BOUWSTENEN (Niet weggooien!) ---
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.tile_type = tile_type
        self.color = (100, 100, 100) 
        if tile_type == 'castle': self.color = (150, 150, 150)
        elif tile_type == 'tree': self.color = (34, 139, 34)
        elif tile_type == 'door': self.color = (255, 0, 0)
        elif tile_type == 'exit_door': self.color = (139, 69, 19)
        
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self, surface, camera):
        surface.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))

class FloorTile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((50, 50, 50)) 
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self, surface, camera):
        surface.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))