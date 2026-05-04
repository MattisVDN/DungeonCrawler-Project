# -*- coding: utf-8 -*-
"""
main.py - Gefixte versie (De uitgang werkt nu echt!)
"""

import pygame
import sys
from settings import WIDTH, HEIGHT, FPS, TILE_SIZE, BLACK, WHITE, RED, YELLOW
from camera import Camera
from entities import Player, Enemy, NPC, Item, Potion
from level import Tile, FloorTile, ALL_LEVELS

def load_level(level_index):
    floors, walls, entities = [], [], []
    exit_tiles = [] # NIEUW: Een aparte lijst voor de win-locatie
    player = None
    map_data = ALL_LEVELS[level_index]

    for row_index, row in enumerate(map_data):
        for col_index, char in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            # Altijd een vloer tekenen
            floors.append(FloorTile(x, y))

            if char == '1': walls.append(Tile(x, y, 'dungeon'))
            elif char == 'C': walls.append(Tile(x, y, 'castle'))
            elif char == 'T': walls.append(Tile(x, y, 'tree'))
            elif char == 'D': walls.append(Tile(x, y, 'door'))
            elif char == 'X': 
                # De uitgang komt in een speciale lijst die niet blokkeert
                exit_tiles.append(Tile(x, y, 'exit_door'))
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
    # We laden nu ook de exit_tiles in
    floors, walls, entities, player, exit_tiles = load_level(current_level_index)

    game_state = "PLAYING"

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if event.type == pygame.KEYDOWN:
                # Herstarten (werkt nu met elke R/r toets)
                if game_state in ["GAMEOVER", "WIN"]:
                    if event.key == pygame.K_r:
                        current_level_index = 0
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
                                    # We verwijderen GEEN muren meer hier, 
                                    # dat doen we automatisch in de update!
                                elif isinstance(entity, Item):
                                    entity.interact(player)

        if game_state == "PLAYING":
            if player and player.health <= 0:
                game_state = "GAMEOVER"
            else:
                for entity in entities:
                    entity.update(walls, player)
                
                if player: camera.update(player)

                # --- WIN CHECK ---
                # We kijken of de speler een van de exit_tiles aanraakt
                if player:
                    for ex in exit_tiles:
                        if player.rect.colliderect(ex.rect):
                            if "Kasteel Toegang" in player.inventory:
                                game_state = "WIN"

                # --- DEUR LOGICA ---
                living_enemies = [e for e in entities if isinstance(e, Enemy) and e.health > 0]
                if len(living_enemies) == 0:
                    walls = [w for w in walls if w.tile_type != 'door']

                # Filter lijsten
                entities = [e for e in entities if not (isinstance(e, Enemy) and e.is_removable)]
                entities = [e for e in entities if not (isinstance(e, Potion) and e.is_picked_up)]
                entities.sort(key=lambda e: e.y) 

        # --- TEKENEN ---
        screen.fill(BLACK) 
        
        if game_state == "PLAYING":
            for floor in floors: floor.draw(screen, camera)
            
            # Teken de uitgang (alleen als de quest nog NIET gedaan is, anders is hij 'open')
            # Maar we checken de collision nog steeds!
            for ex in exit_tiles:
                ex.draw(screen, camera)

            for wall in walls: wall.draw(screen, camera)
            for entity in entities: entity.draw(screen, camera)

            if player:
                living_enemies = [e for e in entities if isinstance(e, Enemy) and e.health > 0]
                screen.blit(font.render(f"Goblins: {len(living_enemies)}", True, YELLOW), (10, 50))
                inv_text = f"Loot: {', '.join(player.inventory)}" if player.inventory else "Loot: Niets"
                screen.blit(font.render(inv_text, True, WHITE), (10, 30))
                
                # Uitleg
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
            txt = pygame.font.Font(None, 80).render("GEWONNEN!", True, (0, 255, 0))
            sub = pygame.font.Font(None, 32).render("Je bent veilig ontsnapt!", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()  