# -*- coding: utf-8 -*-
import pygame
import sys
from settings import WIDTH, HEIGHT, FPS, TILE_SIZE, BLACK, WHITE, RED, YELLOW, GREEN
from camera import Camera
from entities import Player, Enemy, NPC, Item, Potion, Boss, Trap, Fireball
from level import Tile, FloorTile
from level import ALL_LEVELS  

def load_level(level_index, persistent_player=None):
    floors, walls, entities = [], [], []
    exit_tiles = []
    player = persistent_player 
    map_data = ALL_LEVELS[level_index]

    for row_index, row in enumerate(map_data):
        for col_index, char in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            if char not in ['1', 'C', 'T', 'D', 'X']: floors.append(FloorTile(x, y))

            if char == '1': walls.append(Tile(x, y, 'dungeon'))
            elif char == 'C': walls.append(Tile(x, y, 'castle'))
            elif char == 'T': walls.append(Tile(x, y, 'tree'))
            elif char == 'D': walls.append(Tile(x, y, 'door'))
            elif char == 'X': exit_tiles.append(Tile(x, y, 'exit_door'))
            elif char == 'P':
                if player is None:
                    # Eerste keer dat we de game starten
                    player = Player(x, y)
                else:
                    # Speler komt uit vorig level: Positie resetten & Bonus HP!
                    player.x = x
                    player.y = y
                    player.rect.topleft = (x, y)
                    
                    # --- DE BONUS HP LOGICA ---
                    player.health += 50 
                    if player.health > player.max_health:
                        player.health = player.max_health
                
                player.start_x, player.start_y = x, y
                entities.append(player)
            
            # Alle andere entities (vijanden, items, etc.)
            elif char == 'E': entities.append(Enemy(x, y))
            elif char == 'N': entities.append(NPC(x, y))
            elif char == 'L': entities.append(Item(x, y, "Gouden Sleutel"))
            elif char == 'H': entities.append(Potion(x, y)) 
            elif char == 'U': entities.append(Item(x, y, "Magisch Zwaard"))
            elif char == 'O': entities.append(Item(x, y, "Schild"))
            elif char == 'M': entities.append(Item(x, y, "Vuurboek"))
            elif char == 'S': entities.append(Trap(x, y))
            elif char == 'B': entities.append(Boss(x, y))
            
    return floors, walls, entities, player, exit_tiles

def check_level_events(current_level_index, current_wave, entities, walls):
    """Beheert de waves en de deuren voor alle levels, zodat main() schoon blijft."""
    from entities import Enemy, Boss
    living_enemies = [e for e in entities if isinstance(e, Enemy) and e.health > 0]
    
    # Als er nog vijanden zijn, deuren dicht houden en wave niet veranderen
    if len(living_enemies) > 0:
        return current_wave, walls

    if current_level_index == 2:  # De Troonzaal
        if current_wave == 1:
            current_wave = 2
            spawn_points = [(800, 200), (1000, 200), (1200, 200), (1400, 200), (900, 300), (1100, 300), (1300, 300), (1100, 400)]
            for sx, sy in spawn_points: entities.append(Enemy(sx, sy))
        elif current_wave == 2:
            current_wave = 3
            entities.append(Boss(1100, 150))
        elif current_wave == 3: 
            walls = [w for w in walls if w.tile_type != 'door']
    else: 
        # Standaard levels
        walls = [w for w in walls if w.tile_type != 'door']
        
    return current_wave, walls

def draw_ui(screen, player, current_level_index, current_wave, living_enemies, fonts, entities):
    """Tekent de hele interface, inclusief de epische Boss Health Bar."""
    from entities import Boss
    font, font_hud, font_wave = fonts
    
    screen.blit(font.render(f"Level: {current_level_index + 1}", True, WHITE), (10, 10))
    screen.blit(font.render(f"Goblins: {living_enemies}", True, YELLOW), (10, 50))
    inv_text = f"Loot: {', '.join(player.inventory)}" if player.inventory else "Loot: Niets"
    screen.blit(font.render(inv_text, True, WHITE), (10, 30))
    
    screen.blit(font_hud.render("[SPATIE] Slaan", True, WHITE), (WIDTH - 150, 10))
    screen.blit(font_hud.render("[E] Interactie", True, WHITE), (WIDTH - 150, 30))
    
    if "Schild" in player.inventory:
        screen.blit(font_hud.render("[SHIFT] Blocken", True, (0, 191, 255)), (WIDTH - 150, 50))
    if "Vuurboek" in player.inventory:
        screen.blit(font_hud.render("[F] Vuurbal", True, (255, 100, 0)), (WIDTH - 150, 70))
        
    if current_level_index == 2:
        wave_text = font_wave.render(f"WAVE: {current_wave} / 3", True, RED)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 20))
        
        # --- BOSS HEALTH BAR ---
        if current_wave == 3:
            for entity in entities:
                if isinstance(entity, Boss) and entity.health > 0:
                    bar_width, bar_height = 400, 20
                    boss_hp_percent = max(0, entity.health / entity.max_health)
                    bx, by = (WIDTH // 2) - (bar_width // 2), HEIGHT - 40
                    
                    pygame.draw.rect(screen, (50, 0, 0), (bx, by, bar_width, bar_height)) 
                    pygame.draw.rect(screen, (255, 0, 0), (bx, by, int(bar_width * boss_hp_percent), bar_height))
                    pygame.draw.rect(screen, WHITE, (bx, by, bar_width, bar_height), 2) 
                    
                    boss_text = font_hud.render(f"GOBLIN KONING ({int(entity.health)}/{entity.max_health})", True, WHITE)
                    screen.blit(boss_text, (bx + (bar_width // 2) - (boss_text.get_width() // 2), by - 20))
                    break

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT)) 
    pygame.display.set_caption("Dungeon Crawler RPG Quest")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    font_hud = pygame.font.Font(None, 22)
    font_wave = pygame.font.Font(None, 40) 
    camera = Camera()

    current_level_index = 0  # We beginnen bij Level 1 (index 0)
    current_wave = 1 
    floors, walls, entities, player, exit_tiles = load_level(current_level_index)

    game_state = "PLAYING"
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state in ["GAMEOVER", "WIN"]:
                    if event.key == pygame.K_r:
                        current_level_index = 0 
                        current_wave = 1 
                        # Geef 'None' mee om een compleet nieuwe Player te maken
                        floors, walls, entities, player, exit_tiles = load_level(current_level_index, None)
                        game_state = "PLAYING"
                
                elif game_state == "PLAYING" and player:
                    if event.key == pygame.K_SPACE:
                        enemies = [e for e in entities if isinstance(e, Enemy)]
                        oude_hp = sum(e.health for e in enemies) 
                        player.attack(enemies, walls)
                        nieuwe_hp = sum(e.health for e in enemies) 
                                
                        if nieuwe_hp < oude_hp: 
                            camera.trigger_shake(3, 2) 
                    
                    elif event.key == pygame.K_f and "Vuurboek" in player.inventory:
                        if player.spell_cooldown == 0:
                            entities.append(Fireball(player.x + 15, player.y + 15, player.facing))
                            player.spell_cooldown = 60
                            
                    elif event.key == pygame.K_e:
                        interact_rect = player.rect.inflate(40, 40) 
                        for entity in entities:
                            if entity == player: continue
                            if interact_rect.colliderect(entity.rect):
                                if isinstance(entity, (NPC, Item)):
                                    entity.interact(player)

        if game_state == "PLAYING":
            if player and player.health <= 0: 
                game_state = "GAMEOVER"
          
            else:
                oude_player_hp = player.health if player else 0
                
                for entity in entities:
                    entity.update(walls, player)
                    
                    # --- BOSS TRILLING LOGICA ---
                    if isinstance(entity, Boss):
                        if hasattr(entity, 'just_spawned') and entity.just_spawned:
                            camera.trigger_shake(45, 15) 
                            entity.just_spawned = False  
                            
                        if hasattr(entity, 'trigger_slam_shake') and entity.trigger_slam_shake:
                            camera.trigger_shake(20, 15) 
                            entity.trigger_slam_shake = False 
                            
                    # --- Vuurbal Schade Logica ---
                    if isinstance(entity, Fireball):
                        for e in entities:
                            if isinstance(e, Enemy) and e.health > 0 and entity.rect.colliderect(e.rect):
                                e.health -= 30 
                                entity.is_removable = True 
                                camera.trigger_shake(4, 3) 
                
                # Trilling als speler sterft of geraakt wordt
                if player and player.health < oude_player_hp:
                    camera.trigger_shake(8, 6) 
                
                # Update camera
                if player: camera.update(player)

                # Controleer Deuren en Uitgangen
                if player:
                    for ex in exit_tiles:
                        if player.rect.colliderect(ex.rect):
                            if current_level_index == 0 and "Gouden Sleutel" not in player.inventory and "Kasteel Toegang" not in player.inventory:
                                continue
                            
                            if current_level_index < len(ALL_LEVELS) - 1:
                                current_level_index += 1
                                current_wave = 1 
                                floors, walls, entities, player, exit_tiles = load_level(current_level_index, player)
                            else: 
                                game_state = "WIN"

                # --- LEVEL PROGRESSIE & WAVES ---
                current_wave, walls = check_level_events(current_level_index, current_wave, entities, walls)

                # Verwijder dode vijanden, opgepakte potions, EN opgebrande vuurballen
                entities = [e for e in entities if not (isinstance(e, Enemy) and e.is_removable)]
                entities = [e for e in entities if not (isinstance(e, Potion) and e.is_picked_up)]
                entities = [e for e in entities if not (isinstance(e, Fireball) and e.is_removable)]
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
                fonts = (font, font_hud, font_wave)
                draw_ui(screen, player, current_level_index, current_wave, len(living_enemies), fonts, entities)

        elif game_state == "GAMEOVER":
            screen.fill((50, 0, 0)) 
            txt = pygame.font.Font(None, 80).render("JE BENT DOOD", True, RED)
            sub = pygame.font.Font(None, 32).render("Druk op 'R' om opnieuw te proberen", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 30))
            
        elif game_state == "WIN":
            screen.fill((0, 50, 0))
            txt = pygame.font.Font(None, 80).render("SPEL UITGESPEELD!", True, GREEN)
            sub = pygame.font.Font(None, 32).render("Je hebt de Goblin Koning verslagen!", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()