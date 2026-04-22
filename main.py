# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:08:28 2026

@author: VDNSpare
"""

# main.py
import pygame
import sys
from settings import *
from entities import Player, Enemy, NPC, Item
from level import Tile, LEVEL_MAP, FloorTile
from camera import Camera

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dungeon Crawler RPG")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    floors = []
    walls = []
    entities = []
    player = None
    camera = Camera()

    # Inladen van de Map
    for row_index, row in enumerate(LEVEL_MAP):
        for col_index, char in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            if char == '1': walls.append(Tile(x, y, 'dungeon'))
            elif char == 'C': walls.append(Tile(x, y, 'castle'))
            elif char == 'T': walls.append(Tile(x, y, 'tree'))
            elif char == 'D': walls.append(Tile(x, y, 'door'))
            elif char == '0': floors.append(FloorTile(x, y))
            elif char == 'P':
                player = Player(x, y)
                player.start_x = x # Bewaar het beginpunt voor respawn!
                player.start_y = y
                entities.append(player)
            elif char == 'E': entities.append(Enemy(x, y))
            elif char == 'N': entities.append(NPC(x, y))
            elif char == 'L': entities.append(Item(x, y, "Gouden Sleutel"))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # --- NIEUW: Knoppen die je maar 1 keer indrukt (Vechten) ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player:
                    # Zoek alle vijanden op de map en geef ze mee aan de attack functie
                    alle_vijanden = [e for e in entities if isinstance(e, Enemy)]
                    player.attack(alle_vijanden)

        # --- NIEUW: Game Over / Respawn Logica ---
        if player and player.health <= 0:
            print("GAME OVER! Je bent teruggezet naar het begin.")
            player.health = 100
            player.inventory.clear() # Je verliest je loot!
            player.x, player.y = player.start_x, player.start_y
            player.rect.topleft = (player.x, player.y)

        # Update Fase
        for entity in entities:
            entity.update(walls, player)
            
        if player:
            camera.update(player)

        # Verwijder dode dingen
        entities = [e for e in entities if not (isinstance(e, Enemy) and e.health <= 0)]
        entities = [e for e in entities if not (isinstance(e, Item) and e.is_picked_up)]

        # Teken Fase
        screen.fill(BLACK) 

        for floor in floors:
            floor.draw(screen, camera)
        for wall in walls:
            wall.draw(screen, camera)
        for entity in entities:
            entity.draw(screen, camera)
            
            if isinstance(entity, NPC) and entity.is_talking:
                text_surface = font.render(entity.message, True, WHITE, BLACK)
                screen.blit(text_surface, (10, HEIGHT - 40))

        # HUD
        if player:
            # We tekenen het HP-balkje nu in Rood als je bijna dood bent!
            hp_color = RED if player.health < 30 else WHITE
            health_text = font.render(f"HP: {player.health}", True, hp_color)
            inv_text = font.render(f"Loot: {', '.join(player.inventory)}", True, WHITE)
            screen.blit(health_text, (10, 10))
            screen.blit(inv_text, (10, 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()