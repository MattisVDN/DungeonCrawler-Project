# -*- coding: utf-8 -*-
import pygame
import math
import os
import heapq
from settings import *
import random 

# --- DE MAGISCHE ROUTENAVIGATIE ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG_DIR = os.path.join(BASE_DIR, "PNG's")

def get_path(start_tile, goal_tile, walls):
    blocked = set((w.rect.x // TILE_SIZE, w.rect.y // TILE_SIZE) for w in walls)
    frontier = []
    heapq.heappush(frontier, (0, start_tile))
    came_from = {start_tile: None}
    cost_so_far = {start_tile: 0}
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal_tile: break

        for dx, dy in directions:
            next_node = (current[0] + dx, current[1] + dy)
            if next_node in blocked: continue
            
            if dx != 0 and dy != 0:
                if (current[0] + dx, current[1]) in blocked or (current[0], current[1] + dy) in blocked: continue

            step_cost = 1.4 if dx != 0 and dy != 0 else 1
            new_cost = cost_so_far[current] + step_cost
            
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + math.hypot(goal_tile[0] - next_node[0], goal_tile[1] - next_node[1])
                heapq.heappush(frontier, (priority, next_node))
                came_from[next_node] = current

    current = goal_tile
    path = []
    if current not in came_from: return [] 
    while current != start_tile:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, speed, max_health):
        super().__init__()
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.color = color
        self.speed = speed
        self.max_health = max_health
        self.health = max_health
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.attack_timer = 0

    # FIX: entities=None toegevoegd
    def move_and_collide(self, dx, dy, walls, entities=None):
        if dx != 0:
            self.x += dx
            self.rect.topleft = (self.x, self.y)
            hitbox = self.rect.inflate(-15, -15)
            for wall in walls:
                if hitbox.colliderect(wall.rect):
                    self.x -= dx; self.rect.topleft = (self.x, self.y); break
            if entities:
                for e in entities:
                    if isinstance(e, PushableRock) and hitbox.colliderect(e.rect):
                        e.x += dx # Duw de rots!
                        e.rect.topleft = (e.x, e.y)
                        # Check of de rots nu niet in een muur zit
                        for w in walls:
                            if e.rect.colliderect(w.rect):
                                e.x -= dx; e.rect.topleft = (e.x, e.y) # Rots zit vast
                                self.x -= dx; self.rect.topleft = (self.x, self.y) # Speler zit vast
                                break
        if dy != 0:
            self.y += dy
            self.rect.topleft = (self.x, self.y)
            hitbox = self.rect.inflate(-15, -15)
            for wall in walls:
                if hitbox.colliderect(wall.rect):
                    self.y -= dy; self.rect.topleft = (self.x, self.y); break
            if entities:
                for e in entities:
                    if isinstance(e, PushableRock) and hitbox.colliderect(e.rect):
                        e.y += dy # Duw de rots!
                        e.rect.topleft = (e.x, e.y)
                        # Check of de rots nu niet in een muur zit
                        for w in walls:
                            if e.rect.colliderect(w.rect):
                                e.y -= dy; e.rect.topleft = (e.x, e.y)
                                self.y -= dy; self.rect.topleft = (self.x, self.y)
                                break

    def draw_health_bar(self, surface, camera, offset_y=-12):
        bar_width = self.width
        bar_height = 6
        fill = max(0, (self.health / self.max_health) * bar_width)
        bx = self.x - camera.x
        by = self.y - camera.y + offset_y
        pygame.draw.rect(surface, RED, (bx, by, bar_width, bar_height)) 
        pygame.draw.rect(surface, GREEN, (bx, by, fill, bar_height))    

    def draw(self, surface, camera):
        draw_pos = (self.x - camera.x, self.y - camera.y)
        if hasattr(self, 'image') and self.image: surface.blit(self.image, draw_pos)
        else: pygame.draw.rect(surface, self.color, (*draw_pos, self.width, self.height))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50, BLUE, 5, max_health=100)
        self.inventory = [] 
        self.frame_index = 0.0      
        self.animation_speed = 0.2
        self.facing = 'down'        
        self.is_moving = False
        self.is_blocking = False
        self.spell_cooldown = 0 
        self.animations = {'up': [], 'down': [], 'left': [], 'right': []}
        
        try:
            for direction in ['up', 'down', 'left', 'right']:
                i = 0
                while True:
                    pad = os.path.join(PNG_DIR, "Movement", direction, f"{i}.png")
                    if not os.path.exists(pad): break
                    img = pygame.image.load(pad).convert_alpha()
                    img = pygame.transform.scale(img, (self.width, self.height))
                    self.animations[direction].append(img)
                    i += 1
            if self.animations['down']: self.image = self.animations['down'][0] 
        except: self.image = None
        
        # We hebben de sword_img code verwijderd, we gaan pure energie tekenen!

    def take_damage(self, amount): 
        if self.is_blocking: return 
        self.health -= amount

    def attack(self, enemies, walls): 
        if self.is_blocking: return 
        self.attack_timer = 15 
        for enemy in enemies:
            dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if dist < 90: 
                muur_in_de_weg = False
                for wall in walls:
                    if wall.rect.clipline(self.rect.center, enemy.rect.center):
                        muur_in_de_weg = True; break 
                if muur_in_de_weg: continue
                
                if "Magisch Zwaard" in self.inventory: enemy.health -= 40
                else: enemy.health -= 20
                
                # --- HIER IS DE FIX: De Baas krijgt GEEN knockback! ---
                if type(enemy).__name__ != 'Boss':
                    old_x, old_y = enemy.x, enemy.y
                    if self.facing == 'left': enemy.x -= 40
                    elif self.facing == 'right': enemy.x += 40
                    elif self.facing == 'up': enemy.y -= 40
                    elif self.facing == 'down': enemy.y += 40
                    
                    enemy.rect.topleft = (enemy.x, enemy.y)
                    for wall in walls:
                        if enemy.rect.colliderect(wall.rect):
                            enemy.x, enemy.y = old_x, old_y
                            enemy.rect.topleft = (enemy.x, enemy.y)
                            break 

    def update(self, walls: list, player=None, entities=None):
        if self.attack_timer > 0: self.attack_timer -= 1
        if self.spell_cooldown > 0: self.spell_cooldown -= 1
        
        keys = pygame.key.get_pressed()
        self.is_moving = False 

        # TACTISCH SCHILD: Je kan nu lopen, maar op halve snelheid!
        if keys[pygame.K_LSHIFT] and "Schild" in self.inventory:
            self.is_blocking = True
            actuele_speed = self.speed / 2 
        else:
            self.is_blocking = False
            actuele_speed = self.speed

        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -actuele_speed; self.facing = 'left'; self.is_moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = actuele_speed; self.facing = 'right'; self.is_moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -actuele_speed; self.facing = 'up'; self.is_moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = actuele_speed; self.facing = 'down'; self.is_moving = True

        self.move_and_collide(dx, dy, walls, entities)

        if self.is_moving:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.facing]): self.frame_index = 0.0
        else: self.frame_index = 0.0
            
        if self.animations[self.facing]: self.image = self.animations[self.facing][int(self.frame_index)]

    def draw(self, surface, camera):
        super().draw(surface, camera)
        self.draw_health_bar(surface, camera) 
        draw_rect = self.rect.move(-camera.x, -camera.y)
        cx, cy = draw_rect.center 
        
        # --- HET NIEUWE DIRECTIONELE SCHILD ---
        if self.is_blocking:
            shield_dist = 30
            if self.facing == 'up': p1, p2 = (cx - 25, cy - shield_dist), (cx + 25, cy - shield_dist)
            elif self.facing == 'down': p1, p2 = (cx - 25, cy + shield_dist), (cx + 25, cy + shield_dist)
            elif self.facing == 'left': p1, p2 = (cx - shield_dist, cy - 25), (cx - shield_dist, cy + 25)
            elif self.facing == 'right': p1, p2 = (cx + shield_dist, cy - 25), (cx + shield_dist, cy + 25)

            # Teken de dikke energiemuur voor de speler
            pygame.draw.line(surface, (0, 255, 255), p1, p2, 8) # Dikke Cyaan rand
            pygame.draw.line(surface, WHITE, p1, p2, 3)         # Felle witte kern
        
        # --- DE BLAUWE ENERGIE STRAAL (ZWAARD) ---
        if self.attack_timer > 0 and not self.is_blocking:
            # Het magische zwaard is extra lang (75 pixels)
            zwaard_lengte = 75 if "Magisch Zwaard" in self.inventory else 40
            
            if self.facing == 'up': end_pos = (cx, cy - zwaard_lengte)
            elif self.facing == 'down': end_pos = (cx, cy + zwaard_lengte)
            elif self.facing == 'left': end_pos = (cx - zwaard_lengte, cy)
            else: end_pos = (cx + zwaard_lengte, cy)

            if "Magisch Zwaard" in self.inventory:
                # 1. Diepblauwe basis
                pygame.draw.line(surface, (0, 0, 200), (cx, cy), end_pos, 14)
                # 2. Cyaan gloed eroverheen
                pygame.draw.line(surface, (0, 255, 255), (cx, cy), end_pos, 8)
                # 3. Gloeiend hete witte kern
                pygame.draw.line(surface, WHITE, (cx, cy), end_pos, 4)

                # 4. Knetterende vonken aan het uiteinde!
                for _ in range(4):
                    vx = end_pos[0] + random.randint(-12, 12)
                    vy = end_pos[1] + random.randint(-12, 12)
                    pygame.draw.circle(surface, (0, 255, 255), (vx, vy), random.randint(2, 4))
            else:
                # Het normale stalen zwaard
                pygame.draw.line(surface, (150, 150, 150), (cx, cy), end_pos, 6) 
                pygame.draw.line(surface, WHITE, (cx, cy), end_pos, 2)  

class Enemy(Entity):
    def __init__(self, x, y, difficulty="Normal"):
        self.difficulty = difficulty
        
        # HIER STELLEN WE DE MOEILIJKHEIDSGRAAD IN! (HP_Multiplier, Damage_Multiplier)
        mults = {
            "Easy": (0.75, 0.5),     # Zwak en doet weinig pijn
            "Normal": (1.0, 1.0),    # Standaard
            "Hard": (1.5, 1.5),      # Sterk en pijnlijk
            "Impossible": (2.5, 3.0) # Absolute nachtmerrie
        }
        self.hp_mult, self.dmg_mult = mults.get(difficulty, (1.0, 1.0))
        
        base_hp = 50
        super().__init__(x, y, 50, 50, RED, 2, max_health=int(base_hp * self.hp_mult)) 
        
        self.visual_size = 80 
        self.attack_cooldown = 0
        self.current_anim_state = 'idle'
        self.frame_index = 0.0
        self.animation_speed = 0.1
        self.facing_right = True
        self.is_removable = False
        self.path = []
        self.path_timer = 0
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'death': []}
        
        try:
            for state in ['idle', 'walk', 'attack', 'death']:
                i = 0
                while True:
                    pad = os.path.join(PNG_DIR, "Goblin PNG", f"goblin_{state}", f"{i}.png")
                    if not os.path.exists(pad):
                        pad = os.path.join(PNG_DIR, "Goblin PNG", state, f"{i}.png")
                        if not os.path.exists(pad): break
                    img = pygame.image.load(pad)
                    img = pygame.transform.scale(img, (self.visual_size, self.visual_size))
                    self.animations[state].append(img)
                    i += 1
            if self.animations['idle']: self.image = self.animations['idle'][0]
        except: self.image = None

    def update(self, walls, player=None):
        if self.health <= 0:
            self.current_anim_state = 'death'
            if self.animations['death']:
                self.frame_index += self.animation_speed
                if self.frame_index >= len(self.animations['death']) - 1:
                    self.frame_index = len(self.animations['death']) - 1
                    self.is_removable = True
                self.image = self.animations['death'][int(self.frame_index)]
                if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
            else: self.is_removable = True
            return

        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.attack_timer > 0: self.attack_timer -= 1
        
        is_moving = False
        dist = math.hypot(self.x - player.x, self.y - player.y) if player else 999
        
        can_see_player = False
        if dist < 300: 
            can_see_player = True
            for wall in walls:
                if wall.rect.clipline(self.rect.center, player.rect.center):
                    can_see_player = False 
                    break
                    
        ai_state = 'chase' if can_see_player else 'patrol'

        if ai_state == 'chase' and self.attack_timer == 0:
            is_moving = True
            dx, dy = 0, 0
            self.path_timer += 1
            
            if self.path_timer >= 30 or not self.path:
                self.path_timer = 0
                start_tile = (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
                goal_tile = (int(player.rect.centerx // TILE_SIZE), int(player.rect.centery // TILE_SIZE))
                self.path = get_path(start_tile, goal_tile, walls)

            if self.path:
                next_tile = self.path[0]
                target_x = next_tile[0] * TILE_SIZE + (TILE_SIZE // 2) - (self.width // 2)
                target_y = next_tile[1] * TILE_SIZE + (TILE_SIZE // 2) - (self.height // 2)
                dir_x, dir_y = target_x - self.x, target_y - self.y
                dist_to_target = math.hypot(dir_x, dir_y)
                
                if dist_to_target > self.speed:
                    dx = (dir_x / dist_to_target) * self.speed
                    dy = (dir_y / dist_to_target) * self.speed
                    self.facing_right = dx > 0
                else: self.path.pop(0)
            else:
                dir_x, dir_y = player.x - self.x, player.y - self.y
                dist_to_player = math.hypot(dir_x, dir_y)
                if dist_to_player > 0:
                    dx = (dir_x / dist_to_player) * self.speed
                    dy = (dir_y / dist_to_player) * self.speed
                    self.facing_right = dx > 0
            
            self.move_and_collide(dx, dy, walls)

        # HIER GEBRUIKEN WE DE DAMAGE MULTIPLIER!
        if player and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            player.take_damage(int(10 * self.dmg_mult))
            self.attack_timer = 30; self.attack_cooldown = 90; is_moving = False

        if self.attack_timer > 0: self.current_anim_state = 'attack'
        elif is_moving: self.current_anim_state = 'walk'
        else: self.current_anim_state = 'idle'

        if self.animations[self.current_anim_state]:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.current_anim_state]): self.frame_index = 0.0
            self.image = self.animations[self.current_anim_state][int(self.frame_index)]
            if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, surface, camera):
        if hasattr(self, 'image') and self.image:
            offset_x = (self.visual_size - self.width) // 2
            offset_y = (self.visual_size - self.height) // 2
            surface.blit(self.image, (self.x - camera.x - offset_x, self.y - camera.y - offset_y))
        else:
            pygame.draw.rect(surface, self.color, (self.x - camera.x, self.y - camera.y, self.width, self.height))
        if not self.is_removable and self.health > 0:
            self.draw_health_bar(surface, camera, offset_y=-30) 

class Boss(Enemy):
    def __init__(self, x, y, difficulty="Normal"):
        super().__init__(x, y, difficulty) # Haal de multipliers uit de Enemy klasse
        
        # Vermenigvuldig de gigantische HP van de baas! (Impossible = 1250 HP!)
        self.max_health = int(500 * self.hp_mult)
        self.health = self.max_health
        self.speed = 1.5 
        
        self.width, self.height = 70, 70
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.visual_size = 200 
        
        self.special_cooldown, self.slam_timer, self.slam_radius = 180, 0, 120        
        self.just_spawned, self.trigger_slam_shake = True, False
        
        self.charge_cooldown = 240 
        self.charge_timer = 0      
        self.charge_duration = 0   
        self.charge_dx = 0
        self.charge_dy = 0
        
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'death': []}
        try:
            for state in ['idle', 'walk', 'attack', 'death']:
                i = 0
                while True:
                    pad = os.path.join(PNG_DIR, "Boss PNG", f"boss_{state}", f"{i}.png")
                    if not os.path.exists(pad):
                        pad = os.path.join(PNG_DIR, "Boss PNG", state, f"{i}.png")
                        if not os.path.exists(pad): break
                    img = pygame.image.load(pad)
                    img = pygame.transform.scale(img, (self.visual_size, self.visual_size))
                    self.animations[state].append(img)
                    i += 1
            if self.animations['idle']: self.image = self.animations['idle'][0]
        except: self.image = None

    def update(self, walls, player=None):
        if self.health <= 0:
            self.current_anim_state = 'death'
            if self.animations['death']:
                self.frame_index += self.animation_speed
                if self.frame_index >= len(self.animations['death']) - 1:
                    self.frame_index = len(self.animations['death']) - 1
                    self.is_removable = True
                self.image = self.animations['death'][int(self.frame_index)]
                if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
            else: self.is_removable = True
            return

        dist = math.hypot(self.x - player.x, self.y - player.y) if player else 999
        if self.special_cooldown > 0: self.special_cooldown -= 1
        if self.charge_cooldown > 0: self.charge_cooldown -= 1

        if dist < self.slam_radius and self.special_cooldown == 0 and self.slam_timer == 0 and self.charge_timer == 0 and self.charge_duration == 0:
            self.slam_timer = 60; self.special_cooldown = 240; self.current_anim_state = 'attack'; self.frame_index = 0.0

        if self.slam_timer > 0:
            self.slam_timer -= 1; self.current_anim_state = 'attack'
            if self.animations['attack']:
                self.frame_index += (self.animation_speed * 0.5) 
                if self.frame_index >= len(self.animations['attack']): self.frame_index = 0.0
                self.image = self.animations['attack'][int(self.frame_index)]
                if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)
            if self.slam_timer == 5: 
                self.trigger_slam_shake = True  
                if dist <= self.slam_radius: 
                    # Slam damage scaling!
                    player.take_damage(int(25 * self.dmg_mult)) 
            return 

        if dist > 150 and dist < 400 and self.charge_cooldown == 0 and self.charge_timer == 0 and self.slam_timer == 0:
            self.charge_timer = 45 
            self.charge_cooldown = 300 
            self.current_anim_state = 'idle'
            
            dir_x, dir_y = player.x - self.x, player.y - self.y
            if dist > 0:
                self.charge_dx = (dir_x / dist) * 12 
                self.charge_dy = (dir_y / dist) * 12
                self.facing_right = self.charge_dx > 0
            return

        if self.charge_timer > 0:
            self.charge_timer -= 1
            self.current_anim_state = 'idle' 
            if self.charge_timer == 0:
                self.charge_duration = 15 
            return
            
        if self.charge_duration > 0:
            self.charge_duration -= 1
            self.current_anim_state = 'walk'
            self.move_and_collide(self.charge_dx, self.charge_dy, walls)
            
            if player and self.rect.colliderect(player.rect):
                # Dash damage scaling!
                player.take_damage(int(25 * self.dmg_mult))
                self.trigger_slam_shake = True
                self.charge_duration = 0 
                self.attack_cooldown = 60 
            return

        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.attack_timer > 0: self.attack_timer -= 1
        
        is_moving = False
        
        can_see_player = False
        if dist < 400: 
            can_see_player = True
            for wall in walls:
                if wall.rect.clipline(self.rect.center, player.rect.center):
                    can_see_player = False 
                    break
                    
        ai_state = 'chase' if can_see_player else 'patrol'

        if ai_state == 'chase' and self.attack_timer == 0:
            is_moving = True; dx, dy = 0, 0
            self.path_timer += 1
            if self.path_timer >= 30 or not self.path:
                self.path_timer = 0
                start_tile = (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
                goal_tile = (int(player.rect.centerx // TILE_SIZE), int(player.rect.centery // TILE_SIZE))
                self.path = get_path(start_tile, goal_tile, walls)

            if self.path:
                next_tile = self.path[0]
                target_x = next_tile[0] * TILE_SIZE + (TILE_SIZE // 2) - (self.width // 2)
                target_y = next_tile[1] * TILE_SIZE + (TILE_SIZE // 2) - (self.height // 2)
                dir_x, dir_y = target_x - self.x, target_y - self.y
                dist_to_target = math.hypot(dir_x, dir_y)
                
                if dist_to_target > self.speed:
                    dx = (dir_x / dist_to_target) * self.speed
                    dy = (dir_y / dist_to_target) * self.speed
                    self.facing_right = dx > 0
                else: self.path.pop(0)
            else:
                dir_x, dir_y = player.x - self.x, player.y - self.y
                dist_to_player = math.hypot(dir_x, dir_y)
                if dist_to_player > 0:
                    dx = (dir_x / dist_to_player) * self.speed
                    dy = (dir_y / dist_to_player) * self.speed
                    self.facing_right = dx > 0
            self.move_and_collide(dx, dy, walls)

        if player and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            # Kleine snelle aanval scaling!
            player.take_damage(int(10 * self.dmg_mult)); self.attack_timer = 30; self.attack_cooldown = 90; is_moving = False

        if self.attack_timer > 0: self.current_anim_state = 'attack'
        elif is_moving: self.current_anim_state = 'walk'
        else: self.current_anim_state = 'idle'

        if self.animations[self.current_anim_state]:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.current_anim_state]): self.frame_index = 0.0
            self.image = self.animations[self.current_anim_state][int(self.frame_index)]
            if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, surface, camera):
        if self.charge_timer > 0:
            cx = self.x - camera.x + (self.width // 2)
            cy = self.y - camera.y + (self.height // 2)
            end_x = cx + (self.charge_dx * 20)
            end_y = cy + (self.charge_dy * 20)
            if (self.charge_timer // 5) % 2 == 0:
                pygame.draw.line(surface, (255, 0, 0), (cx, cy), (end_x, end_y), 4)

        if self.slam_timer > 0:
            cx = self.x - camera.x + (self.width // 2)
            cy = self.y - camera.y + (self.height // 2)
            progress = 1.0 - (self.slam_timer / 60.0)
            current_radius = int(self.slam_radius * progress)
            warning_surface = pygame.Surface((self.slam_radius*2, self.slam_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(warning_surface, (255, 0, 0, 60), (self.slam_radius, self.slam_radius), self.slam_radius) 
            pygame.draw.circle(warning_surface, (255, 100, 0, 200), (self.slam_radius, self.slam_radius), current_radius, 4) 
            surface.blit(warning_surface, (cx - self.slam_radius, cy - self.slam_radius))
            
        super().draw(surface, camera)

class NPC(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, (128, 0, 128), 0, max_health=100)
        self.quest_state = 'start'
        self.message, self.talk_timer = "", 0 
        try:
            pad = os.path.join(PNG_DIR, "Different PNG", "wizard.png")
            if os.path.exists(pad):
                img = pygame.image.load(pad)
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        if self.talk_timer > 0: self.talk_timer -= 1

    def interact(self, player):
        self.talk_timer = 180 
        if self.quest_state == 'start':
            self.message = "Goblins bewaken de kist! Versla ze allemaal!"
            self.quest_state = 'waiting'
        elif self.quest_state == 'waiting':
            if "Gouden Sleutel" in player.inventory:
                self.message = "Geweldig! De Uitgang is nu geopend! Succes!"
                player.inventory.remove("Gouden Sleutel")
                player.inventory.append("Kasteel Toegang") 
                self.quest_state = 'done'
            else: self.message = "Versla alle Goblins en breng me de sleutel!"
        elif self.quest_state == 'done':
            self.message = "De uitgang is vrij!"

    def draw(self, surface, camera):
        super().draw(surface, camera)
        if self.talk_timer > 0:
            font = pygame.font.Font(None, 24)
            text_surf = font.render(self.message, True, WHITE, BLACK)
            text_rect = text_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 10 - camera.y)
            surface.blit(text_surf, text_rect)

class Item(Entity):
    def __init__(self, x, y, item_name):
        super().__init__(x, y, 50, 50, YELLOW, 0, max_health=1)
        self.item_name, self.is_picked_up = item_name, False
        self.frames, self.frame_index, self.animation_speed = [], 0.0, 0.2
        self.is_opening, self.is_open = False, False
        try:
            i = 0
            while True:
                pad = os.path.join(PNG_DIR, "Chest PNG", f"kist", f"{i}.png")
                if not os.path.exists(pad):
                    pad = os.path.join(PNG_DIR, "Chest PNG", f"{i}.png")
                    if not os.path.exists(pad): break
                img = pygame.image.load(pad)
                img = pygame.transform.scale(img, (self.width, self.height))
                self.frames.append(img)
                i += 1
            if self.frames: self.image = self.frames[0] 
            else: self.image = None
        except: self.image = None

    def interact(self, player):
        if not self.is_open and not self.is_opening: self.is_opening = True

    def update(self, walls=None, player=None):
        if self.is_opening:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.frames) - 1:
                self.frame_index = len(self.frames) - 1
                self.is_opening = False; self.is_open = True
                if player and not self.is_picked_up:
                    player.inventory.append(self.item_name); self.is_picked_up = True
            if self.frames: self.image = self.frames[int(self.frame_index)]

class Potion(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, (255, 20, 147), 0, max_health=1)
        self.is_picked_up = False
        try:
            pad = os.path.join(PNG_DIR, "Different PNG", "potion.png")
            if os.path.exists(pad):
                img = pygame.image.load(pad)
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        if player and self.rect.colliderect(player.rect) and not self.is_picked_up:
            if player.health < player.max_health:
                heal_amount = 30
                player.health = min(player.max_health, player.health + heal_amount)
                self.spawn_heal_text = True 
                self.is_picked_up = True
                
class Trap(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, (100, 100, 100), 0, max_health=1)
        self.damage_cooldown, self.is_active, self.timer, self.switch_time = 0, True, 0, 90  
        self.image_active = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image_active, (60, 60, 60), (0, 0, 40, 40)) 
        for i in range(4): pygame.draw.polygon(self.image_active, (200, 0, 0), [(i*10, 40), (i*10+5, 10), (i*10+10, 40)])
        self.image_safe = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image_safe, (60, 60, 60), (0, 0, 40, 40)) 
        for i in range(4): pygame.draw.circle(self.image_safe, (20, 20, 20), (i*10 + 5, 20), 4)
        self.image = self.image_active

    def update(self, walls=None, player=None):
        self.timer += 1
        if self.timer >= self.switch_time:
            self.timer = 0; self.is_active = not self.is_active 
            self.image = self.image_active if self.is_active else self.image_safe
            
        if self.damage_cooldown > 0: self.damage_cooldown -= 1
        
        if self.is_active and player:
            trap_hitbox = self.rect.inflate(-20, -20) 
            
            if trap_hitbox.colliderect(player.rect) and self.damage_cooldown == 0:
                if not getattr(player, 'is_invincible', False):
                    player.take_damage(20); self.damage_cooldown = 60
                    
class Fireball(Entity):
    def __init__(self, x, y, facing):
        super().__init__(x, y, 20, 20, (255, 100, 0), 12, 1) 
        self.facing, self.is_removable = facing, False
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 69, 0), (10, 10), 10) 
        pygame.draw.circle(self.image, (255, 255, 0), (10, 10), 5)  

    def update(self, walls=None, player=None):
        if self.facing == 'up': self.y -= self.speed
        elif self.facing == 'down': self.y += self.speed
        elif self.facing == 'left': self.x -= self.speed
        elif self.facing == 'right': self.x += self.speed
        self.rect.topleft = (self.x, self.y)
        for wall in walls:
            if self.rect.colliderect(wall.rect): self.is_removable = True; return

class DamageText(Entity):
    def __init__(self, x, y, text, color):
        super().__init__(x, y, 0, 0, color, 1, 1) # Onzichtbare body
        self.text = text
        self.color = color
        self.timer = 45 # Blijft 0.75 seconde op het scherm (60 FPS * 0.75)
        self.is_removable = False
        self.font = pygame.font.Font(None, 36)
        
        # Geef het getalletje een kleine random positie zodat meerdere klappen niet overlappen
        self.x += random.randint(-15, 15)
        self.y += random.randint(-10, 10)

    def update(self, walls=None, player=None):
        self.y -= 1.5 # Zweef langzaam omhoog!
        self.timer -= 1
        if self.timer <= 0:
            self.is_removable = True

    def draw(self, surface, camera):
        text_surf = self.font.render(self.text, True, self.color)
        outline_surf = self.font.render(self.text, True, (0, 0, 0)) # Zwart randje voor leesbaarheid
        
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        
        # Teken 4x de zwarte outline
        for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            surface.blit(outline_surf, (draw_x + dx, draw_y + dy))
        
        # Teken de gekleurde tekst in het midden
        surface.blit(text_surf, (draw_x, draw_y))
            
class PushableRock(Entity):
    def __init__(self, x, y):
        # Een grote zware bruine vierkante steen
        super().__init__(x, y, 46, 46, (139, 69, 19), speed=0, max_health=999) 
        self.image = pygame.Surface((46, 46))
        self.image.fill((100, 70, 40))
        pygame.draw.rect(self.image, (60, 40, 20), (0, 0, 46, 46), 4) # Donker randje
        # Extra lijnen zodat het op een rots lijkt
        pygame.draw.line(self.image, (60, 40, 20), (10, 10), (36, 36), 3)
        pygame.draw.line(self.image, (60, 40, 20), (36, 10), (10, 36), 3)

    def update(self, walls=None, player=None):
        pass # De logica zit bij de speler die hem duwt

class PressurePlate(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 36, 36, (150, 150, 150), speed=0, max_health=999)
        self.is_pressed = False
        
        # Plaatje als hij NIET is ingedrukt
        self.image_up = pygame.Surface((36, 36))
        self.image_up.fill((100, 100, 100))
        pygame.draw.rect(self.image_up, (200, 200, 200), (4, 4, 28, 28))
        
        # Plaatje als hij WEL is ingedrukt (zakt in de vloer)
        self.image_down = pygame.Surface((36, 36))
        self.image_down.fill((80, 80, 80))
        pygame.draw.rect(self.image_down, (100, 255, 100), (8, 8, 20, 20)) # Groen lampje!
        
        self.image = self.image_up

    def update(self, walls=None, player=None):
        pass # Wordt geregeld in main.py


class WhiteOrc(Boss):
    def __init__(self, x, y, difficulty="Normal"):
        super().__init__(x, y, difficulty)
        
        # De Witte Orc is het ultieme kwaad! Dubbel zoveel HP als de Generaal!
        self.max_health = int(1000 * self.hp_mult)
        self.health = self.max_health
        self.speed = 2.0 # Hij is extreem snel
        self.visual_size = 250 # Gigantisch!
        
        # We proberen zijn eigen plaatjes in te laden, anders maken we hem wit.
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'death': []}
        try:
            for state in ['idle', 'walk', 'attack', 'death']:
                i = 0
                while True:
                    pad = os.path.join(PNG_DIR, "White Orc PNG", f"white_{state}", f"{i}.png")
                    if not os.path.exists(pad): break
                    img = pygame.image.load(pad).convert_alpha()
                    img = pygame.transform.scale(img, (self.visual_size, self.visual_size))
                    self.animations[state].append(img)
                    i += 1
            if self.animations['idle']: self.image = self.animations['idle'][0]
        except: 
            # Fallback: Een gigantisch spierwit, onheilspellend vierkant als je de PNGs nog niet hebt!
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((255, 255, 255)) 

class NPC(Entity):
    def __init__(self, x, y, level_index=0): 
        super().__init__(x, y, 40, 40, (128, 0, 128), 0, max_health=100)
        self.level_index = level_index
        self.is_talking = False   # Houdt bij of we in gesprek zijn
        self.dialogue_pages = []  # Alle 'schermen' tekst
        self.current_page = 0     # Op welk scherm we nu zijn
        self.has_spoken = False 
        try:
            pad = os.path.join(PNG_DIR, "Different PNG", "wizard.png")
            if os.path.exists(pad):
                img = pygame.image.load(pad)
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        # NIEUW: Als je te ver weg loopt, stopt hij automatisch met praten!
        if self.is_talking and player:
            dist = math.hypot(self.x - player.x, self.y - player.y)
            if dist > 80: 
                self.is_talking = False

    def interact(self, player):
        if self.is_talking: return # Als we al praten, doet [E] even niets
        
        self.has_spoken = True 
        self.is_talking = True
        self.current_page = 0
        
        # --- VUL DE DIALOOG PAGINA'S PER LEVEL ---
        if self.level_index == 0:
            self.dialogue_pages = [
                ["Help! Ik zit hier al 60 jaar vast...", "Ik weet dat er meer dan 3 levels zijn,", "maar ik durfde niet verder."],
                ["In level 3 zit een gruwelijke baas.", "Ik ben gillend weggerend!", "Versla telkens alle monsters om de deur te openen."],
                ["Dood alle monsters hier om verder te gaan!", "Succes, dappere held..."]
            ]
        elif self.level_index == 1:
            self.dialogue_pages = [
                ["Pas op, dit is een gevaarlijk doolhof", "vol met dodelijke vallen!"],
                ["Versla weer alle monsters om door te gaan.", "Ergens hier is een Magisch Zwaard verstopt!", "Zoek het voordat je verder gaat."],
                ["Vind het Magisch Zwaard en versla", "alle goblins in dit doolhof!"]
            ]
        elif self.level_index == 2:
            self.dialogue_pages = [
                ["We zijn in de troonzaal!", "Dit is een arena. Je moet", "alle waves zien te overleven."],
                ["Aan het einde van de waves", "verschijnt de Orc Generaal!", "Maak je klaar voor het gevecht!"],
                ["Overleef de waves en", "versla de Orc Generaal!"]
            ]
        elif self.level_index == 3:
            self.dialogue_pages = [
                ["Ongelofelijk... Ik ben nog nooit", "zo diep in de kerker geweest!"],
                ["Het is hier snikheet in deze", "Vuur-Catacomben.", "Ik weet wel dat hier ergens een Schild ligt!"],
                ["Zoek het Schild en blijf in leven!"]
            ]
        else:
            self.dialogue_pages = [
                ["Overleef deze oneindige catacomben", "tot je de Witte Orc vindt..."]
            ]

    def advance_dialogue(self):
        """Deze functie wordt aangeroepen als we op SPATIE drukken"""
        if self.current_page < len(self.dialogue_pages) - 1:
            self.current_page += 1 # Ga naar het volgende stukje tekst
        else:
            self.is_talking = False # We zijn klaar met praten

    def draw(self, surface, camera):
        super().draw(surface, camera)
        font = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 20)
        
        # 1. Aandacht trekken als je nog niet gepraat hebt
        if not self.has_spoken:
            t = pygame.time.get_ticks()
            bounce = math.sin(t / 200.0) * 5 
            text_surf = font.render("Praat met mij [E]!", True, GREEN, BLACK)
            text_rect = text_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 15 + bounce - camera.y)
            surface.blit(text_surf, text_rect)

        # 2. Tekst tekenen als we praten
        if self.is_talking and self.dialogue_pages:
            huidige_lijst = self.dialogue_pages[self.current_page]
            
            for i, regel in enumerate(huidige_lijst):
                text_surf = font.render(regel, True, YELLOW, BLACK)
                # +1 omdat de "[SPATIE]" prompt er nog onder moet passen
                y_offset = (len(huidige_lijst) - i + 1) * 20
                text_rect = text_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 5 - y_offset - camera.y)
                surface.blit(text_surf, text_rect)
                
            # Teken de prompt om verder te gaan
            spatie_surf = font_small.render("[SPATIE] Verder", True, (0, 255, 255), BLACK)
            spatie_rect = spatie_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 10 - camera.y)
            surface.blit(spatie_surf, spatie_rect)