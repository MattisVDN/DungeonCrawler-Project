# -*- coding: utf-8 -*-
import pygame
import sys
import math
import random
from settings import WIDTH, HEIGHT, FPS, TILE_SIZE, BLACK, WHITE, RED, YELLOW, GREEN
from camera import Camera
from entities import Player, Enemy, NPC, Item, Potion, Boss, WhiteOrc, Trap, Fireball, DamageText, PushableRock, PressurePlate
from level import Tile, FloorTile, genereer_random_kerker
from level import ALL_LEVELS  

def load_level(level_index, persistent_player=None, difficulty="Normal"):
    floors, walls, entities = [], [], []
    exit_tiles = []
    player = persistent_player 
    
    # Random kerker genereren als we voorbij de vaste levels zijn (Level 5+)
    if level_index >= len(ALL_LEVELS): 
        map_data = genereer_random_kerker()
    else: 
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
                    player = Player(x, y)
                else:
                    player.x, player.y = x, y
                    player.rect.topleft = (x, y)
                    player.health = min(player.max_health, player.health + 50) # Heal 50hp per level
                
                player.start_x, player.start_y = x, y
                entities.append(player)
            
            # Vijanden spawnen mét de moeilijkheidsgraad!
            elif char == 'E': entities.append(Enemy(x, y, difficulty))
            elif char == 'B': entities.append(Boss(x, y, difficulty))
            elif char == 'W': entities.append(WhiteOrc(x, y, difficulty))
            
            # NPC krijgt nu het level index mee!
            elif char == 'N': entities.append(NPC(x, y, level_index))
            
            elif char == 'L': entities.append(Item(x, y, "Gouden Sleutel"))
            elif char == 'H': entities.append(Potion(x, y)) 
            elif char == 'U': entities.append(Item(x, y, "Magisch Zwaard"))
            elif char == 'O': entities.append(Item(x, y, "Schild"))
            elif char == 'M': entities.append(Item(x, y, "Vuurboek"))
            elif char == 'S': entities.append(Trap(x, y))
            elif char == 'R': entities.append(PushableRock(x, y))
            elif char == 'V': entities.append(PressurePlate(x, y))
            
    return floors, walls, entities, player, exit_tiles

def check_level_events(current_level_index, current_wave, entities, walls, difficulty):
    from entities import Enemy, Boss
    living_enemies = [e for e in entities if isinstance(e, Enemy) and e.health > 0]
    if len(living_enemies) > 0: return current_wave, walls

    if current_level_index == 2:  # De Troonzaal (Level 3)
        if current_wave == 1:
            current_wave = 2
            spawn_points = [(800, 200), (1000, 200), (1200, 200), (1400, 200), (900, 300), (1100, 300), (1300, 300), (1100, 400)]
            for sx, sy in spawn_points: entities.append(Enemy(sx, sy, difficulty))
        elif current_wave == 2:
            current_wave = 3
            entities.append(Boss(1100, 150, difficulty)) # Boss is nu de Orc Generaal
        elif current_wave == 3: walls = [w for w in walls if w.tile_type != 'door']
    else: walls = [w for w in walls if w.tile_type != 'door']
        
    return current_wave, walls

def draw_ui(screen, player, current_level_index, current_wave, living_enemies, fonts, entities, difficulty):
    font, font_hud, font_wave = fonts
    
    screen.blit(font.render(f"Level: {current_level_index + 1} | Mode: {difficulty}", True, WHITE), (10, 10))
    screen.blit(font.render(f"Goblins: {living_enemies}", True, YELLOW), (10, 50))
    inv_text = f"Loot: {', '.join(player.inventory)}" if player.inventory else "Loot: Niets"
    screen.blit(font.render(inv_text, True, WHITE), (10, 30))
    
    start_y = 170 
    screen.blit(font_hud.render("[SPATIE] Slaan / Tekst", True, WHITE), (WIDTH - 150, start_y))
    screen.blit(font_hud.render("[E] Interactie", True, WHITE), (WIDTH - 150, start_y + 20))
    
    if "Schild" in player.inventory: 
        screen.blit(font_hud.render("[SHIFT] Blocken", True, (0, 191, 255)), (WIDTH - 150, start_y + 40))
        start_y += 20
        
    if "Vuurboek" in player.inventory:
        screen.blit(font_hud.render("[F] Vuurbal", True, (255, 100, 0)), (WIDTH - 150, start_y + 40))
        screen.blit(font_hud.render("[ESC] Pauze", True, (150, 150, 150)), (WIDTH - 150, start_y + 60))
    else: 
        screen.blit(font_hud.render("[ESC] Pauze", True, (150, 150, 150)), (WIDTH - 150, start_y + 40))
        
    if current_level_index == 2:
        wave_text = font_wave.render(f"WAVE: {current_wave} / 3", True, RED)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 20))
        
    # HP Balk voor de Orc Generaal óf de Witte Orc!
    if current_wave == 3 or any(isinstance(e, WhiteOrc) for e in entities):
        for entity in entities:
            if (isinstance(entity, Boss) or isinstance(entity, WhiteOrc)) and entity.health > 0:
                bar_width, bar_height = 400, 20
                boss_hp_percent = max(0, entity.health / entity.max_health)
                bx, by = (WIDTH // 2) - (bar_width // 2), HEIGHT - 40
                pygame.draw.rect(screen, (50, 0, 0), (bx, by, bar_width, bar_height)) 
                pygame.draw.rect(screen, (255, 0, 0), (bx, by, int(bar_width * boss_hp_percent), bar_height))
                pygame.draw.rect(screen, WHITE, (bx, by, bar_width, bar_height), 2) 
                
                naam = "DE WITTE ORC" if isinstance(entity, WhiteOrc) else "ORC GENERAAL"
                boss_text = font_hud.render(f"{naam} ({int(entity.health)}/{entity.max_health})", True, WHITE)
                screen.blit(boss_text, (bx + (bar_width // 2) - (boss_text.get_width() // 2), by - 20))
                break

def draw_fog_of_war(screen, player, camera):
    fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fog.fill((10, 10, 20, 245)) 
    
    if player:
        cx = int(player.x - camera.x + player.width // 2)
        cy = int(player.y - camera.y + player.height // 2)
        
        t = pygame.time.get_ticks()
        pulse = math.sin(t / 200.0) * 8 
        flicker = random.randint(-2, 2)   
        
        light_radius = int(220 + pulse + flicker)
        light = pygame.Surface((light_radius * 2, light_radius * 2), pygame.SRCALPHA)
        light.fill((255, 255, 255, 255)) 
        
        steps = 30
        for i in range(steps):
            current_radius = int(light_radius - (i * (light_radius / steps)))
            alpha = int(255 - (i / steps) * 255) 
            pygame.draw.circle(light, (255, 255, 255, alpha), (light_radius, light_radius), current_radius)
        
        fog.blit(light, (cx - light_radius, cy - light_radius), special_flags=pygame.BLEND_RGBA_MIN)
        
    screen.blit(fog, (0, 0))

def draw_minimap(screen, player, walls, entities, exit_tiles):
    mm_size = 150
    mm_x = WIDTH - mm_size - 10
    mm_y = 10
    scale = 0.1 
    
    mm_surf = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
    mm_surf.fill((0, 0, 0, 200)) 
    
    cx, cy = mm_size // 2, mm_size // 2
    
    def draw_on_map(x, y, color, size, is_rect=True):
        rel_x = (x - player.x) * scale
        rel_y = (y - player.y) * scale
        if -cx <= rel_x <= cx and -cy <= rel_y <= cy:
            if is_rect: pygame.draw.rect(mm_surf, color, (cx + rel_x, cy + rel_y, size, size))
            else: pygame.draw.circle(mm_surf, color, (int(cx + rel_x), int(cy + rel_y)), size)

    for wall in walls: draw_on_map(wall.rect.x, wall.rect.y, (100, 100, 100), TILE_SIZE * scale)
    for ex in exit_tiles: draw_on_map(ex.rect.x, ex.rect.y, (139, 69, 19), TILE_SIZE * scale)
        
    for e in entities:
        if isinstance(e, Enemy) and e.health > 0:
            color = RED if not isinstance(e, Boss) else (150, 0, 255) 
            size = 3 if not isinstance(e, Boss) else 6
            draw_on_map(e.x, e.y, color, size, is_rect=False)
        elif isinstance(e, Item) and not getattr(e, 'is_picked_up', False):
            draw_on_map(e.x, e.y, YELLOW, 2, is_rect=False) 

    pygame.draw.circle(mm_surf, GREEN, (cx, cy), 4)
    pygame.draw.rect(mm_surf, WHITE, (0, 0, mm_size, mm_size), 2)
    screen.blit(mm_surf, (mm_x, mm_y))
    
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT)) 
    pygame.display.set_caption("Dungeon Crawler RPG Quest")
    clock = pygame.time.Clock()
    
    font = pygame.font.Font(None, 24)
    font_hud = pygame.font.Font(None, 22)
    font_wave = pygame.font.Font(None, 40) 
    font_title = pygame.font.Font(None, 80)
    font_menu = pygame.font.Font(None, 40)
    
    camera = Camera()
    
    difficulties = ["Easy", "Normal", "Hard", "Impossible"]
    diff_colors = [(0, 255, 0), (255, 255, 255), (255, 100, 0), (255, 0, 0)]
    selected_diff_idx = 1 # Standaard op 'Normal'
    active_difficulty = "Normal"

    current_level_index, current_wave = 0, 1 
    floors, walls, entities, player, exit_tiles = load_level(current_level_index, None, active_difficulty)

    game_state = "START"
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state == "START":
                    if event.key == pygame.K_UP: selected_diff_idx = max(0, selected_diff_idx - 1)
                    elif event.key == pygame.K_DOWN: selected_diff_idx = min(len(difficulties)-1, selected_diff_idx + 1)
                    elif event.key == pygame.K_RETURN: 
                        active_difficulty = difficulties[selected_diff_idx]
                        current_level_index, current_wave = 0, 1 
                        floors, walls, entities, player, exit_tiles = load_level(current_level_index, None, active_difficulty)
                        game_state = "PLAYING"
                        
                elif game_state == "PAUSED":
                    if event.key == pygame.K_ESCAPE: game_state = "PLAYING"
                    elif event.key == pygame.K_q: running = False
                    
                elif game_state in ["GAMEOVER", "WIN"]:
                    if event.key == pygame.K_r:
                        current_level_index, current_wave = 0, 1
                        floors, walls, entities, player, exit_tiles = load_level(current_level_index, None, active_difficulty)
                        game_state = "PLAYING"
                
                elif game_state == "PLAYING" and player:
                    if event.key == pygame.K_ESCAPE: game_state = "PAUSED"
                        
                    elif event.key == pygame.K_SPACE:
                        # --- KIJK EERST OF WE AAN HET PRATEN ZIJN ---
                        talking_npc = None
                        for e in entities:
                            if isinstance(e, NPC) and getattr(e, 'is_talking', False):
                                talking_npc = e
                                break
                        
                        if talking_npc:
                            # Als we praten, ga naar de volgende zin
                            talking_npc.advance_dialogue()
                        else:
                            # Als we NIET praten, voer de oude zwaard-aanval uit
                            enemies = [e for e in entities if isinstance(e, Enemy)]
                            health_before = {e: e.health for e in enemies}
                            player.attack(enemies, walls)
                            
                            hit_someone = False
                            for e in enemies:
                                dmg = health_before[e] - e.health
                                if dmg > 0:
                                    entities.append(DamageText(e.rect.centerx, e.rect.top, f"-{int(dmg)}", YELLOW))
                                    hit_someone = True
                                    
                            if hit_someone: camera.trigger_shake(3, 2)
                    
                    elif event.key == pygame.K_f and "Vuurboek" in player.inventory:
                        if player.spell_cooldown == 0:
                            entities.append(Fireball(player.x + 15, player.y + 15, player.facing))
                            player.spell_cooldown = 60
                            
                    elif event.key == pygame.K_e:
                        interact_rect = player.rect.inflate(40, 40) 
                        for entity in entities:
                            if entity != player and interact_rect.colliderect(entity.rect):
                                if isinstance(entity, (NPC, Item)): entity.interact(player)

        if game_state == "PLAYING":
            # --- PUZZELS ---
            rocks = [e for e in entities if isinstance(e, PushableRock)]
            plates = [e for e in entities if isinstance(e, PressurePlate)]
            
            for plate in plates:
                was_pressed = plate.is_pressed
                plate.is_pressed = False
                for rock in rocks:
                    if plate.rect.collidepoint(rock.rect.center): plate.is_pressed = True
                plate.image = plate.image_down if plate.is_pressed else plate.image_up
                if plate.is_pressed and not was_pressed:
                    camera.trigger_shake(10, 5)
                    walls = [w for w in walls if w.tile_type != 'door']
            
            # --- GAME OVER / WIN CONDITIE ---
            if player and player.health <= 0: 
                game_state = "GAMEOVER"
            
            # WIN CONDITIE: Als er een Witte Orc in het level zat, en zijn health is nu 0 of hij is weg: WIN!
            elif current_level_index >= 4 and any(isinstance(e, WhiteOrc) for e in entities) and not any(isinstance(e, WhiteOrc) and e.health > 0 for e in entities):
                game_state = "WIN"
                
            else:
                oude_player_hp = player.health if player else 0
                for entity in entities:
                    if isinstance(entity, Player): entity.update(walls, player=None, entities=entities)
                    else: entity.update(walls, player)
                        
                    if isinstance(entity, Potion) and hasattr(entity, 'spawn_heal_text') and entity.spawn_heal_text:
                        entities.append(DamageText(player.rect.centerx, player.rect.top, "+30", GREEN))
                        entity.spawn_heal_text = False
                    if isinstance(entity, Boss) or isinstance(entity, WhiteOrc):
                        if hasattr(entity, 'just_spawned') and entity.just_spawned:
                            camera.trigger_shake(45, 15); entity.just_spawned = False
                        if hasattr(entity, 'trigger_slam_shake') and entity.trigger_slam_shake:
                            camera.trigger_shake(20, 15); entity.trigger_slam_shake = False
                    
                    if isinstance(entity, Fireball):
                        for e in entities:
                            if isinstance(e, Enemy) and e.health > 0 and entity.rect.colliderect(e.rect):
                                e.health -= 30
                                entities.append(DamageText(e.rect.centerx, e.rect.top, "-30", (255, 100, 0)))
                                entity.is_removable = True
                                camera.trigger_shake(4, 3)
                                break 
                
                if player and player.health < oude_player_hp:
                    dmg = oude_player_hp - player.health
                    entities.append(DamageText(player.rect.centerx, player.rect.top, f"-{int(dmg)}", RED))
                    camera.trigger_shake(8, 6)
                
                if player: camera.update(player)

                # --- EXIT DEUR (Nieuw Level) ---
                if player:
                    for ex in exit_tiles:
                        if player.rect.colliderect(ex.rect):
                            if current_level_index == 0 and "Gouden Sleutel" not in player.inventory and "Kasteel Toegang" not in player.inventory: 
                                continue
                                
                            current_level_index += 1
                            current_wave = 1
                            floors, walls, entities, player, exit_tiles = load_level(current_level_index, player, active_difficulty)
                            entities.append(DamageText(player.rect.centerx, player.rect.top, "+50 HP BONUS", GREEN))

                current_wave, walls = check_level_events(current_level_index, current_wave, entities, walls, active_difficulty)
                entities = [e for e in entities if not (hasattr(e, 'is_removable') and e.is_removable)]
                entities = [e for e in entities if not (hasattr(e, 'is_picked_up') and e.is_picked_up)]
                entities.sort(key=lambda e: e.y) 

        # --- TEKEN ALLES ---
        screen.fill(BLACK) 
        if game_state == "START":
            title = font_title.render("DUNGEON CRAWLER", True, YELLOW)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
            
            for i, diff in enumerate(difficulties):
                color = diff_colors[i] if i == selected_diff_idx else (100, 100, 100)
                prefix = "> " if i == selected_diff_idx else "  "
                text = font_menu.render(prefix + diff, True, color)
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + (i * 40)))
                
            sub = font.render("Gebruik PIJLTJES en druk op ENTER", True, WHITE)
            if pygame.time.get_ticks() % 1000 < 600: 
                screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT - 50))
     
        elif game_state in ["PLAYING", "PAUSED"]:
            for floor in floors: floor.draw(screen, camera)
            for ex in exit_tiles: ex.draw(screen, camera)
            for wall in walls: wall.draw(screen, camera)
            for entity in entities: entity.draw(screen, camera)
            
            if player:
                draw_fog_of_war(screen, player, camera)
                draw_minimap(screen, player, walls, entities, exit_tiles)
                draw_ui(screen, player, current_level_index, current_wave, len([e for e in entities if isinstance(e, Enemy) and e.health > 0]), (font, font_hud, font_wave), entities, active_difficulty)
            
            if game_state == "PAUSED":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180)) 
                screen.blit(overlay, (0, 0))
                p_title = font_title.render("PAUZE", True, WHITE)
                p_sub1 = font_menu.render("[ESC] Verder spelen", True, YELLOW)
                p_sub2 = font_menu.render("[Q] Afsluiten", True, RED)
                screen.blit(p_title, (WIDTH // 2 - p_title.get_width() // 2, HEIGHT // 3))
                screen.blit(p_sub1, (WIDTH // 2 - p_sub1.get_width() // 2, HEIGHT // 2))
                screen.blit(p_sub2, (WIDTH // 2 - p_sub2.get_width() // 2, HEIGHT // 2 + 60))

        elif game_state == "GAMEOVER":
            screen.fill((50, 0, 0)) 
            txt = font_title.render("JE BENT DOOD", True, RED)
            sub = font_menu.render("Druk op 'R' om opnieuw te proberen", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 50))
            
        elif game_state == "WIN":
            screen.fill((0, 50, 0))
            txt = font_title.render("SPEL UITGESPEELD!", True, GREEN)
            sub = font_menu.render("Je hebt de Witte Orc verslagen!", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 50))

        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()