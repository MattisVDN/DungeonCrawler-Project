# -*- coding: utf-8 -*-
import pygame
import random 
import math
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
        
       

def genereer_random_kerker(breedte=50, hoogte=30, stappen=1500):
    """AI Algoritme om een ruimere, gevarieerde random kerker te genereren met een Safe Zone."""
    # 1. Vul de hele kaart met massieve muren ('1')
    grid = [['1' for _ in range(breedte)] for _ in range(hoogte)]

    # 2. Bepaal het startpunt (Speler)
    px, py = breedte // 2, hoogte // 2
    grid[py][px] = 'P' 
    
    # Hou bij welke vakjes we hebben uitgegraven
    uitgegraven = [(px, py)]
    x, y = px, py

    # 3. Dronken Graafmachine (Nu met een bredere boor!)
    for _ in range(stappen):
        # Kies een richting
        richting = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        x += richting[0]
        y += richting[1]

        # Zorg dat we goed uit de buurt van de buitenste rand blijven
        x = max(2, min(breedte - 3, x))
        y = max(2, min(hoogte - 3, y))

        # Graaf niet alleen dít vakje, maar willekeurig ook een vakje ernaast uit (Maakt grote ruimtes!)
        for dx in [0, random.choice([-1, 1])]:
            for dy in [0, random.choice([-1, 1])]:
                nx, ny = x + dx, y + dy
                if grid[ny][nx] == '1':
                    grid[ny][nx] = ' '
                    uitgegraven.append((nx, ny))

    # 4. De allerlaatste stap van de machine maken we de Uitgang
    laatste_x, laatste_y = uitgegraven[-1]
    grid[laatste_y][laatste_x] = 'X'

    # 5. Spawnen met SAFE ZONES (Afstand berekenen!)
    aantal_goblins = random.randint(8, 15)
    for _ in range(aantal_goblins):
        rx, ry = random.choice(uitgegraven)
        # Check: Is de goblin minimaal 8 blokjes weg van de speler (px, py)?
        if grid[ry][rx] == ' ' and math.hypot(rx - px, ry - py) > 8: 
            grid[ry][rx] = 'E'
            
    aantal_vallen = random.randint(6, 12)
    for _ in range(aantal_vallen):
        rx, ry = random.choice(uitgegraven)
        # Vallen mogen iets dichterbij, maar nog steeds niet óp de speler (minimaal 4 blokjes)
        if grid[ry][rx] == ' ' and math.hypot(rx - px, ry - py) > 4: 
            grid[ry][rx] = 'S'
            
    aantal_potions = random.randint(2, 5)
    for _ in range(aantal_potions):
        rx, ry = random.choice(uitgegraven)
        if grid[ry][rx] == ' ': grid[ry][rx] = 'H'

    # 6. Variatie: 25% kans op een verrassings-Boss in de eindeloze modus!
    if random.random() < 0.25:
        rx, ry = random.choice(uitgegraven)
        # Een baas moet ECHT ver weg spawnen (minimaal 12 blokjes)
        if grid[ry][rx] == ' ' and math.hypot(rx - px, ry - py) > 12: 
            grid[ry][rx] = 'B'

    # 7. Zet ons grid om naar de lijst met strings zoals ALL_LEVELS ze kent
    return ["".join(rij) for rij in grid]        