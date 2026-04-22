# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:08:09 2026

@author: VDNSpare
"""

# level.py
import pygame
from settings import *

class FloorTile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        try:
            loaded_img = pygame.image.load("vloer.png")
            self.image = pygame.transform.scale(loaded_img, (TILE_SIZE, TILE_SIZE))
        except:
            self.image = None

    def draw(self, surface, camera):
        draw_rect = self.rect.move(-camera.x, -camera.y)
        if self.image: surface.blit(self.image, draw_rect.topleft)
        else: pygame.draw.rect(surface, (100, 100, 100), draw_rect)

class Tile:
    def __init__(self, x, y, tile_type):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.tile_type = tile_type
        self.image = None
        
        if self.tile_type in ['dungeon', 'castle']:
            try:
                loaded_img = pygame.image.load("muur.png")
                self.image = pygame.transform.scale(loaded_img, (TILE_SIZE, TILE_SIZE))
            except: pass
        elif self.tile_type == 'door': 
            self.color = (139, 69, 19) # Bruine deur
        elif self.tile_type == 'tree': 
            self.color = TREE_GREEN

    def draw(self, surface, camera):
        draw_rect = self.rect.move(-camera.x, -camera.y)
        if self.image:
            surface.blit(self.image, draw_rect.topleft)
        else:
            pygame.draw.rect(surface, getattr(self, 'color', BLACK), draw_rect)

# --- MAPS ---
LEVEL_1 = [
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "T00000000000000000000000000000000000000T",
    "T00P0000T000000N000CCCCCCCCCCCCC0000000T",
    "T000000000000000000C000000000E0C0000000T",
    "T000T00000000000000C000011D1111C0000000T",
    "T00TTT0000000000000C0000100L00010000000T",
    "T000T00000000000000C0000100E00010000000T",
    "T000000000000000000C0000111001110000000T",
    "T000000000000000000CCCCCCCCCCCCC0000000T",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
]

LEVEL_2 = [
    "1111111111111111111111111111111111111111",
    "1000000000000010000000000000000000000001",
    "100P00000E00001000E000011111111111000001",
    "1000000000000010000000010000000001000001",
    "111111000111111000E00001000L00E001000001",
    "10000000000000000000000D0000000001000001",
    "1000E00000000000000000011111111111000001",
    "1000000001111111111100000000000000000001",
    "1111111111111111111111111111111111111111"
]

ALL_LEVELS = [LEVEL_1, LEVEL_2]