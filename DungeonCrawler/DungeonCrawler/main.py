# -*- coding: utf-8 -*-
"""
main.py - Nu met Level Progressie!
"""

import pygame
import sys
from settings import WIDTH, HEIGHT, FPS, TILE_SIZE, BLACK, WHITE, RED, YELLOW, GREEN
from camera import Camera
from entities import Player, Enemy, NPC, Item, Potion
from level import Tile, FloorTile
from maps import ALL_LEVELS # NIEUW: We halen de levels nu uit maps.py!

def load_level(level_index):
    floors, walls, entities = [], [], []
    exit_tiles = []
    player = None
    map_data = ALL_LEVELS[level_index]

    for row_index, row in enumerate(map_data):
        for col_index, char in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            floors.append(FloorTile(x, y))

            if char == '1': walls.append(Tile(x, y, 'dungeon'))
            elif char == 'C': walls.append(Tile(x, y, 'castle'))
            elif char == 'T': walls.append(Tile(x, y, 'tree'))
            elif char == 'D': walls.append(Tile(x, y, 'door'))
            elif char == 'X': exit_tiles.append(Tile(x, y, 'exit_door'))
            elif char == 'P':
                player = Player(x, y)
                player.start_x, player.start_y = x, y
                entities.append(player)
            elif char == 'E': entities.append(Enemy(x, y))
            elif char == 'N': entities.append(NPC(x, y))
            elif char == 'L': entities.append(Item(x, y, "Gouden Sleutel"))
            elif char == 'H': entities.append(Potion(x, y)) 
            
    return floors, walls, entities, player, exit_tiles

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT)) 
    pygame.display.set_caption("Dungeon Crawler RPG Quest")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    font_hud = pygame.font.Font(None, 22)
    camera = Camera()

    current_level_index = 0
    floors, walls, entities, player, exit_tiles = load_level(current_level_index)

    game_state = "PLAYING"
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state in ["GAMEOVER", "WIN"]:
                    if event.key == pygame.K_r:
                        current_level_index = 0 # Begin weer helemaal opnieuw bij level 1
                        floors, walls, entities, player, exit_tiles = load_level(current_level_index)
                        game_state = "PLAYING"
                
                elif game_state == "PLAYING" and player:
                    if event.key == pygame.K_SPACE:
                        enemies = [e for e in entities if isinstance(e, Enemy)]
                        player.attack(enemies)
                    
                    elif event.key == pygame.K_e:
                        interact_rect = player.rect.inflate(40, 40) 
                        for entity in entities:
                            if entity == player: continue
                            if interact_rect.colliderect(entity.rect):
                                if isinstance(entity, NPC):
                                    entity.interact(player)
                                elif isinstance(entity, Item):
                                    entity.interact(player)

        if game_state == "PLAYING":
            if player and player.health <= 0:
                game_state = "GAMEOVER"
            else:
                for entity in entities:
                    entity.update(walls, player)
                
                if player: camera.update(player)

                # --- LEVEL PROGRESSIE LOGICA ---
                if player:
                    for ex in exit_tiles:
                        if player.rect.colliderect(ex.rect):
                            # In Level 1 heb je de Kasteel Toegang nodig. In latere levels mag je gewoon doorlopen.
                            if current_level_index == 0 and "Kasteel Toegang" not in player.inventory:
                                continue # Ga niet door de deur als je de quest nog niet af hebt in level 1
                            
                            # Check of er nog een level is
                            if current_level_index < len(ALL_LEVELS) - 1:
                                current_level_index += 1
                                floors, walls, entities, player, exit_tiles = load_level(current_level_index)
                                # Speler is weer helemaal genezen en inventory is weer leeg voor het nieuwe level
                            else:
                                game_state = "WIN" # Geen levels meer over? Dan heb je het hele spel uitgespeeld!

                # Deuren openen als vijanden dood zijn
                living_enemies = [e for e in entities if isinstance(e, Enemy) and e.health > 0]
                if len(living_enemies) == 0:
                    walls = [w for w in walls if w.tile_type != 'door']

                entities = [e for e in entities if not (isinstance(e, Enemy) and e.is_removable)]
                entities = [e for e in entities if not (isinstance(e, Potion) and e.is_picked_up)]
                entities.sort(key=lambda e: e.y) 

        # --- TEKENEN ---
        screen.fill(BLACK) 
        
        if game_state == "PLAYING":
            for floor in floors: floor.draw(screen, camera)
            for ex in exit_tiles: ex.draw(screen, camera)
            for wall in walls: wall.draw(screen, camera)
            for entity in entities: entity.draw(screen, camera)

            if player:
                living_enemies = [e for e in entities if isinstance(e, Enemy) and e.health > 0]
                screen.blit(font.render(f"Level: {current_level_index + 1}", True, WHITE), (10, 10))
                screen.blit(font.render(f"Goblins: {len(living_enemies)}", True, YELLOW), (10, 50))
                inv_text = f"Loot: {', '.join(player.inventory)}" if player.inventory else "Loot: Niets"
                screen.blit(font.render(inv_text, True, WHITE), (10, 30))
                
                screen.blit(font_hud.render("[SPATIE] Slaan", True, WHITE), (WIDTH - 150, 10))
                screen.blit(font_hud.render("[E] Interactie", True, WHITE), (WIDTH - 150, 30))

        elif game_state == "GAMEOVER":
            screen.fill((50, 0, 0)) 
            txt = pygame.font.Font(None, 80).render("JE BENT DOOD", True, RED)
            sub = pygame.font.Font(None, 32).render("Druk op 'R' om opnieuw te proberen", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 30))
            
        elif game_state == "WIN":
            screen.fill((0, 50, 0))
            txt = pygame.font.Font(None, 80).render("SPEL UITGESPEELD!", True, GREEN)
            sub = pygame.font.Font(None, 32).render("Je bent de ultieme dungeon master!", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()