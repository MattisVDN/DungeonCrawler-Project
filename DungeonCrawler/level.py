# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:08:09 2026

@author: VDNSpare
"""

# level.py
import pygame

TILE_SIZE = 32

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.tile_type = tile_type
        self.color = (100, 100, 100) 
        if tile_type == 'castle': self.color = (150, 150, 150)
        elif tile_type == 'tree': self.color = (34, 139, 34)
        elif tile_type == 'door': self.color = (255, 0, 0) # RODE DEUR (Voor de kist!)
        elif tile_type == 'exit_door': self.color = (139, 69, 19) # BRUINE DEUR (Uitgang)
        
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

# De gefixte map: De Kistkamer (met D) is nu super duidelijk en in het midden!
LEVEL_1 = [
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "T00000000000000000000000000000000000000000000000000000000T",
    "T00P0000000000000000000H000000000000000000000000000000000T",
    "T00000000000000000000000000000000000000000000000000000000T",
    "T00000000TTTTTTTTTTTTTTTTTTTTTTTT000000000000000000000000T",
    "T00000000T0000000000000000000000T000000000000000000000000T",
    "T00000H00T0000000000000000000000T000000000000000000000000T",
    "T00N00000T0000E00000000E00000000T0000CCCCCC000CCCCCCC0000T",
    "T00000000T000000000E00000000E000T0000C00000000000000C0000T",
    "T00000000T0000000000000000000000T0000C00000000000000C0000T",
    "TTTTTT000TTTTTTT0000TTTTTTTTTTT0T0000C00000000000000C0000T",
    "T00000000000000T0000T00000000000T0000C00011111100000C0000T",
    "T00000000000000T0000T00000000000T0000C000D0000100000X0000T",
    "T000E000000E00000000000E00000000T0000C000D00L0100000X0000T",
    "T000000E0000000000E00000000E0000T0000C000D0000100000X0000T",
    "T00000000000000T0000T00000000000T0000C00011111100000C0000T",
    "T00000H00000000T0000T0000000000000000C00000000000000C0000T",
    "T000T0000TTTTTTT0000TTTTTTTTTTTTT0000C00000000000000C0000T",
    "T000T0000000000T0000T0000000000000000C000000H0000000C0000T",
    "T000T00000000000000000000000000000000CCCCCCCCCCCCCCCC0000T",
    "T000T0000000000000000000000000000000000000000000000000000T",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
]

ALL_LEVELS = [LEVEL_1]