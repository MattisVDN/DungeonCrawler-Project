# -*- coding: utf-8 -*-
import pygame
import os
from settings import TILE_SIZE

from level_1 import MAP as L1
from level_2 import MAP as L2
from level_3 import MAP as L3
from level_4 import MAP as L4

ALL_LEVELS = [L1, L2, L3, L4]  

# --- DE MAGISCHE ROUTENAVIGATIE ---
# Dit vertelt Python: Ga 1 map omhoog uit 'Python codes', en zoek dan de map "PNG's"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG_DIR = os.path.join(BASE_DIR, "PNG's")

def laad_tegel(bestandsnaam, fallback_kleur):
    # We zoeken in "Different PNG", en als vangnet direct in "PNG's"
    pad1 = os.path.join(PNG_DIR, "Different PNG", bestandsnaam)
    pad2 = os.path.join(PNG_DIR, bestandsnaam)
    
    werkend_pad = None
    if os.path.exists(pad1): werkend_pad = pad1
    elif os.path.exists(pad2): werkend_pad = pad2
    
    if werkend_pad:
        try:
            img = pygame.image.load(werkend_pad).convert_alpha()
            return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        except Exception as e:
            print(f"Fout bij laden {bestandsnaam}: {e}")
            
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(fallback_kleur)
    return surf

TEGEL_CACHE = {}

def get_muur():
    if "muur" not in TEGEL_CACHE:
        TEGEL_CACHE["muur"] = laad_tegel("muur.png", (100, 100, 100))
    return TEGEL_CACHE["muur"]

def get_vloer():
    if "vloer" not in TEGEL_CACHE:
        TEGEL_CACHE["vloer"] = laad_tegel("vloer.png", (40, 40, 40))
    return TEGEL_CACHE["vloer"]

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.tile_type = tile_type
        
        if tile_type == 'dungeon':
            self.image = get_muur()
        else:
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
        self.image = get_vloer()
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self, surface, camera):
        surface.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))