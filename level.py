# -*- coding: utf-8 -*-
"""
level.py - Met slimme Lazy Loading voor afbeeldingen (Oplossing voor de crash!)
"""
import pygame
import os
from settings import TILE_SIZE

# --- HIER LADEN WE JOUW LOSSE BESTANDEN IN ---
from level_1 import MAP as L1
from level_2 import MAP as L2

ALL_LEVELS = [L1, L2]

huidige_map = os.path.dirname(os.path.abspath(__file__))

def laad_tegel(bestandsnaam, fallback_kleur):
    pad = os.path.join(huidige_map, bestandsnaam)
    if os.path.exists(pad):
        try:
            img = pygame.image.load(pad).convert_alpha()
            # Rek hem uit zodat hij precies zo groot is als een tegel (bijv 40x40)
            return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        except Exception as e:
            print(f"Fout bij laden {bestandsnaam}: {e}")
            
    # Als het plaatje mist, val dan terug op het oude, saaie blokje verf
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(fallback_kleur)
    return surf


# --- HET GEHEUGEN (LAZY LOADING) ---
# We maken een leeg lijstje. We laden het plaatje pas zodra het scherm 
# in main.py is opgestart en er voor het eerst om een muur wordt gevraagd!
TEGEL_CACHE = {}

def get_muur():
    if "muur" not in TEGEL_CACHE:
        TEGEL_CACHE["muur"] = laad_tegel("muur.png", (100, 100, 100))
    return TEGEL_CACHE["muur"]

def get_vloer():
    if "vloer" not in TEGEL_CACHE:
        TEGEL_CACHE["vloer"] = laad_tegel("vloer.png", (40, 40, 40))
    return TEGEL_CACHE["vloer"]


# --- DE BOUWSTENEN ---
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.tile_type = tile_type
        
        # Als het een dungeon-muur ('1') is, vraag dan het plaatje op!
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
        # Vraag het vloer-plaatje op!
        self.image = get_vloer()
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self, surface, camera):
        surface.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))