# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:08:28 2026

@author: VDNSpare
"""

import pygame
import sys
from settings import *
from camera import Camera
from entities import Player, Enemy, NPC, Item, Potion
from level import Tile, FloorTile, ALL_LEVELS

def load_level(level_index):
    floors, walls, entities = [], [], []
    player = None
    map_data = ALL_LEVELS[level_index]

    for row_index, row in enumerate(map_data):
        for col_index, char in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            if char == '1': walls.append(Tile(x, y, 'dungeon'))
            elif char == 'C': walls.append(Tile(x, y, 'castle'))
            elif char == 'T': walls.append(Tile(x, y, 'tree'))
            elif char == 'D': walls.append(Tile(x, y, 'door'))
            elif char == 'X': walls.append(Tile(x, y, 'exit_door'))
            elif char == '0': floors.append(FloorTile(x, y))
            elif char == 'P':
                player = Player(x, y)
                player.start_x, player.start_y = x, y
                entities.append(player)
            elif char == 'E': entities.append(Enemy(x, y))
            elif char == 'N': entities.append(NPC(x, y))
            elif char == 'L': entities.append(Item(x, y, "Gouden Sleutel"))
            elif char == 'H': entities.append(Potion(x, y)) 
            
    return floors, walls, entities, player

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768)) 
    pygame.display.set_caption("Dungeon Crawler RPG Quest")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    camera = Camera()

    current_level_index = 0
    floors, walls, entities, player = load_level(current_level_index)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player:
                    alle_vijanden = [e for e in entities if isinstance(e, Enemy)]
                    player.attack(alle_vijanden)
                
                elif event.key == pygame.K_e and player:
                    interact_rect = player.rect.inflate(30, 30) 
                    for entity in entities:
                        if entity == player: continue
                        if interact_rect.colliderect(entity.rect):
                            if isinstance(entity, NPC):
                                entity.interact(player)
                                if entity.quest_state == 'done':
                                    walls = [w for w in walls if w.tile_type != 'exit_door']
                            elif isinstance(entity, Item):
                                entity.interact(player)

        if player and player.health <= 0:
            print("GAME OVER! Je begint opnieuw.")
            floors, walls, entities, player = load_level(current_level_index) 

        for entity in entities:
            if isinstance(entity, Enemy) or isinstance(entity, Player) or isinstance(entity, Item) or isinstance(entity, NPC) or isinstance(entity, Potion):
                entity.update(walls, player)
            
        if player: camera.update(player)

        # LOGICA: DEUR NAAR KIST OPENEN (Alleen als Goblin teller 0 is!)
        living_enemies = [e for e in entities if isinstance(e, Enemy) and e.health > 0]
        if len(living_enemies) == 0:
            walls = [w for w in walls if w.tile_type != 'door']

        # Verwijder opgedronken potions en dode enemies van de map
        entities = [e for e in entities if not (isinstance(e, Enemy) and e.is_removable)]
        entities = [e for e in entities if not (isinstance(e, Potion) and e.is_picked_up)]

        if player and player.x > 1800 and "Kasteel Toegang" in player.inventory: 
             print("GEFELICITEERD! JE HEBT HET SPEL UITGESPEELD!")
             running = False 

        entities.sort(key=lambda e: e.y) 

        screen.fill(BLACK) 
        for floor in floors: floor.draw(screen, camera)
        for wall in walls: wall.draw(screen, camera)
        for entity in entities: entity.draw(screen, camera)

        if player:
            # HUD Tekenen: Gebruikt directe kleuren zodat je settings.py niet crasht!
            screen.blit(font.render(f"Goblins te gaan: {len(living_enemies)}", True, (255,255,0)), (10, 50))
            inv_text = f"Loot: {', '.join(player.inventory)}" if player.inventory else "Loot: Niets"
            screen.blit(font.render(inv_text, True, (255,255,255)), (10, 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()