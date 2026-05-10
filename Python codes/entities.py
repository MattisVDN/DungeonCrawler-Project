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

    iterations = 0
    max_iterations = 400 # <--- DE FIX: Maximaal rekenwerk instellen!

    while frontier:
        iterations += 1
        # Stop met zoeken als het te zwaar wordt, anders bevriest de game!
        if iterations > max_iterations: 
            break 

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
    while current and current != start_tile:
        path.append(current)
        current = came_from.get(current)
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
                        self.x -= dx; self.rect.topleft = (self.x, self.y); break
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
                        self.y -= dy; self.rect.topleft = (self.x, self.y); break

    def draw_health_bar(self, surface, camera, offset_y=-12):
        bar_width = int(self.width)
        bar_height = 8 
        fill = int(max(0, (self.health / self.max_health) * bar_width))
        bx = int(self.x - camera.x)
        by = int(self.y - camera.y + offset_y)
        
        pygame.draw.rect(surface, (150, 0, 0), (bx, by, bar_width, bar_height)) 
        pygame.draw.rect(surface, (0, 200, 0), (bx, by, fill, bar_height))    
        pygame.draw.rect(surface, (255, 255, 255), (bx, by, bar_width, bar_height), 1)

    def draw(self, surface, camera):
        draw_pos = (self.x - camera.x, self.y - camera.y)
        if hasattr(self, 'image') and self.image: surface.blit(self.image, draw_pos)
        else: pygame.draw.rect(surface, self.color, (*draw_pos, self.width, self.height))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50, BLUE, 5, max_health=100)
        self.inventory = [] 
        
        # --- MATTIS STAMINA SYSTEEM ---
        self.max_stamina = 100
        self.stamina = 100
        
        self.frame_index = 0.0      
        self.animation_speed = 0.2
        self.facing = 'down'        
        self.is_moving = False
        self.is_blocking = False
        self.spell_cooldown = 0 
        
        # --- JOUW DASH VARIABELEN ---
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_speed = 18 
        self.is_invincible = False 
        
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
        
        self.sword_img = None

    def take_damage(self, amount): 
        if self.is_blocking or self.is_invincible: return 
        self.health -= amount

    def attack(self, enemies, walls): 
        if self.is_blocking or self.is_dashing: return 
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
                
                if not isinstance(enemy, Boss):
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
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        
        # --- STAMINA HERSTEL ---
        if self.stamina < self.max_stamina:
            self.stamina += 0.6  
            if self.stamina > self.max_stamina: self.stamina = self.max_stamina
        
        keys = pygame.key.get_pressed()
        self.is_moving = False 

        is_grabbing = False
        grabbed_rock = None
        
        if keys[pygame.K_e] and entities: 
            check_rect = self.rect.copy()
            if self.facing == 'up': check_rect.y -= 15
            elif self.facing == 'down': check_rect.y += 15
            elif self.facing == 'left': check_rect.x -= 15
            elif self.facing == 'right': check_rect.x += 15
            for e in entities:
                if isinstance(e, PushableRock) and check_rect.colliderect(e.rect):
                    is_grabbing = True
                    grabbed_rock = e
                    break

        if is_grabbing:
            dx, dy = 0, 0
            loopsnelheid = self.speed * 0.6 
            if self.facing in ['left', 'right']:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -loopsnelheid
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = loopsnelheid
            elif self.facing in ['up', 'down']:
                if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -loopsnelheid
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = loopsnelheid
                
            if dx != 0 or dy != 0:
                self.is_moving = True
                duw_geslaagd = grabbed_rock.move_rock(dx, dy, walls, player=self)
                if duw_geslaagd:
                    self.x += dx; self.y += dy
                    self.rect.topleft = (self.x, self.y)
                    hitbox = self.rect.inflate(-15, -15)
                    for w in walls:
                        if hitbox.colliderect(w.rect):
                            self.x -= dx; self.y -= dy
                            self.rect.topleft = (self.x, self.y)
                            grabbed_rock.move_rock(-dx, -dy, walls, player=self) 
                            break

        elif keys[pygame.K_LSHIFT] and "Schild" in self.inventory:
            self.is_blocking = True
            actuele_speed = self.speed / 2 
        else:
            self.is_blocking = False
            actuele_speed = self.speed

        # --- JOUW DASH LOGICA OP LINKER CTRL ---
        if keys[pygame.K_LCTRL] and self.dash_cooldown == 0 and not self.is_blocking and not is_grabbing:
            self.is_dashing = True
            self.dash_timer = 8 
            self.dash_cooldown = 45 

        if self.is_dashing:
            self.is_invincible = True
            self.dash_timer -= 1
            dx, dy = 0, 0
            if self.facing == 'left': dx = -self.dash_speed
            elif self.facing == 'right': dx = self.dash_speed
            elif self.facing == 'up': dy = -self.dash_speed
            elif self.facing == 'down': dy = self.dash_speed
            
            self.move_and_collide(dx, dy, walls, entities)
            
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.is_invincible = False
                
        elif not is_grabbing:
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -actuele_speed; self.facing = 'left'; self.is_moving = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = actuele_speed; self.facing = 'right'; self.is_moving = True
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -actuele_speed; self.facing = 'up'; self.is_moving = True
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = actuele_speed; self.facing = 'down'; self.is_moving = True
            self.move_and_collide(dx, dy, walls, entities)

        if self.is_moving or self.is_dashing:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.facing]): self.frame_index = 0.0
        else: self.frame_index = 0.0
            
        if self.animations[self.facing]: self.image = self.animations[self.facing][int(self.frame_index)]

    # --- MATTIS STAMINA BALK ---
    def draw_stamina_bar(self, surface, camera, offset_y=-4):
        bar_width = self.width
        bar_height = 4
        fill = max(0, (self.stamina / self.max_stamina) * bar_width)
        bx = self.x - camera.x
        by = self.y - camera.y + offset_y
        pygame.draw.rect(surface, (0, 0, 100), (bx, by, bar_width, bar_height)) 
        pygame.draw.rect(surface, (0, 255, 255), (bx, by, fill, bar_height)) 

    def draw(self, surface, camera):
        super().draw(surface, camera)
        self.draw_health_bar(surface, camera) 
        self.draw_stamina_bar(surface, camera) 
        draw_rect = self.rect.move(-camera.x, -camera.y)
        cx, cy = draw_rect.center 
        
        if self.is_blocking:
            shield_dist = 30
            if self.facing == 'up': p1, p2 = (cx - 25, cy - shield_dist), (cx + 25, cy - shield_dist)
            elif self.facing == 'down': p1, p2 = (cx - 25, cy + shield_dist), (cx + 25, cy + shield_dist)
            elif self.facing == 'left': p1, p2 = (cx - shield_dist, cy - 25), (cx - shield_dist, cy + 25)
            elif self.facing == 'right': p1, p2 = (cx + shield_dist, cy - 25), (cx + shield_dist, cy + 25)

            pygame.draw.line(surface, (0, 255, 255), p1, p2, 8) 
            pygame.draw.line(surface, WHITE, p1, p2, 3)         
        
        if self.attack_timer > 0 and not self.is_blocking:
            zwaard_lengte = 75 if "Magisch Zwaard" in self.inventory else 40
            if self.facing == 'up': end_pos = (cx, cy - zwaard_lengte)
            elif self.facing == 'down': end_pos = (cx, cy + zwaard_lengte)
            elif self.facing == 'left': end_pos = (cx - zwaard_lengte, cy)
            else: end_pos = (cx + zwaard_lengte, cy)

            if "Magisch Zwaard" in self.inventory:
                pygame.draw.line(surface, (0, 0, 200), (cx, cy), end_pos, 14)
                pygame.draw.line(surface, (0, 255, 255), (cx, cy), end_pos, 8)
                pygame.draw.line(surface, WHITE, (cx, cy), end_pos, 4)
                for _ in range(4):
                    vx = end_pos[0] + random.randint(-12, 12)
                    vy = end_pos[1] + random.randint(-12, 12)
                    pygame.draw.circle(surface, (0, 255, 255), (vx, vy), random.randint(2, 4))
            else:
                pygame.draw.line(surface, (150, 150, 150), (cx, cy), end_pos, 6) 
                pygame.draw.line(surface, WHITE, (cx, cy), end_pos, 2)  

class Enemy(Entity):
    def __init__(self, x, y, difficulty="Normal"):
        self.difficulty = difficulty
        mults = { "Easy": (0.75, 0.5), "Normal": (1.0, 1.0), "Hard": (1.5, 1.5), "Impossible": (2.5, 3.0) }
        self.hp_mult, self.dmg_mult = mults.get(difficulty, (1.0, 1.0))
        
        super().__init__(x, y, 50, 50, RED, 2, max_health=int(50 * self.hp_mult)) 
        
        self.visual_size = 80 
        self.attack_cooldown = 0
        self.current_anim_state = 'idle'
        self.frame_index = 0.0
        self.animation_speed = 0.1
        self.facing_right = True
        self.is_removable = False
        
        # Jouw Zwerm AI Variabelen
        self.ai_state = 'patrol' 
        self.patrol_target = None
        self.patrol_timer = 0
        self.last_known_pos = None
        self.investigate_timer = 0
        
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

    def update(self, walls, player=None, entities=None):
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
        if dist < 350: 
            can_see_player = True
            for wall in walls:
                if wall.rect.clipline(self.rect.center, player.rect.center):
                    can_see_player = False 
                    break
                    
        if can_see_player:
            self.ai_state = 'chase'
            self.last_known_pos = (player.rect.centerx, player.rect.centery)
            self.investigate_timer = 180 
        elif self.investigate_timer > 0:
            self.ai_state = 'investigate'
            self.investigate_timer -= 1
        else:
            self.ai_state = 'patrol'

        target_pos = None
        current_speed = self.speed

        if self.ai_state == 'chase': target_pos = (player.rect.centerx, player.rect.centery)
        elif self.ai_state == 'investigate':
            target_pos = self.last_known_pos
            if target_pos and math.hypot(self.x - target_pos[0], self.y - target_pos[1]) < 20:
                self.investigate_timer = 0
        elif self.ai_state == 'patrol':
            current_speed = self.speed * 0.4 
            self.patrol_timer += 1
            if self.patrol_target is None or math.hypot(self.x - self.patrol_target[0], self.y - self.patrol_target[1]) < 20 or self.patrol_timer > 120:
                self.patrol_target = (self.x + random.randint(-150, 150), self.y + random.randint(-150, 150))
                self.patrol_timer = 0
            target_pos = self.patrol_target

        dx, dy = 0, 0
        if target_pos and self.attack_timer == 0:
            is_moving = True
            self.path_timer += 1
            if self.path_timer >= 30 or not self.path:
                self.path_timer = 0
                start_tile = (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
                goal_tile = (int(target_pos[0] // TILE_SIZE), int(target_pos[1] // TILE_SIZE))
                self.path = get_path(start_tile, goal_tile, walls)

            if self.path:
                next_tile = self.path[0]
                target_x = next_tile[0] * TILE_SIZE + (TILE_SIZE // 2) - (self.width // 2)
                target_y = next_tile[1] * TILE_SIZE + (TILE_SIZE // 2) - (self.height // 2)
                dir_x, dir_y = target_x - self.x, target_y - self.y
                dist_to_target = math.hypot(dir_x, dir_y)
                
                if dist_to_target > current_speed:
                    dx = (dir_x / dist_to_target) * current_speed
                    dy = (dir_y / dist_to_target) * current_speed
                    self.facing_right = dx > 0
                else: self.path.pop(0)
            else:
                dir_x, dir_y = target_pos[0] - self.rect.centerx, target_pos[1] - self.rect.centery
                dist_to_target = math.hypot(dir_x, dir_y)
                if dist_to_target > 0:
                    dx = (dir_x / dist_to_target) * current_speed
                    dy = (dir_y / dist_to_target) * current_speed
                    self.facing_right = dx > 0
            
            # --- ZWERM LOGICA ---
            if entities and self.ai_state == 'chase':
                separation_dx, separation_dy = 0, 0
                for other in entities:
                    if isinstance(other, Enemy) and other != self and other.health > 0:
                        dist_to_other = math.hypot(self.x - other.x, self.y - other.y)
                        if 0 < dist_to_other < 60: 
                            separation_dx += (self.x - other.x) / dist_to_other
                            separation_dy += (self.y - other.y) / dist_to_other
                if separation_dx != 0 or separation_dy != 0:
                    dx += separation_dx * 2.5 
                    dy += separation_dy * 2.5
                    totale_snelheid = math.hypot(dx, dy)
                    if totale_snelheid > 0:
                        dx = (dx / totale_snelheid) * current_speed
                        dy = (dy / totale_snelheid) * current_speed

            self.move_and_collide(dx, dy, walls)

        if player and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            if not getattr(player, 'is_invincible', False):
                player.take_damage(int(10 * self.dmg_mult))
            self.attack_timer = 30; self.attack_cooldown = 90; is_moving = False

        if self.attack_timer > 0: self.current_anim_state = 'attack'
        elif is_moving and (dx != 0 or dy != 0): self.current_anim_state = 'walk'
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
            
        if not self.is_removable and self.health > 0 and not isinstance(self, Boss):
            self.draw_health_bar(surface, camera, offset_y=-20)

class Boss(Enemy):
    def __init__(self, x, y, difficulty="Normal"):
        super().__init__(x, y, difficulty) 
        self.max_health = int(500 * self.hp_mult)
        self.health = self.max_health
        self.speed = 1.5 
        self.width, self.height = 70, 70
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.visual_size = 200 
        
        self.special_cooldown, self.slam_timer, self.slam_radius = 180, 0, 120        
        self.just_spawned, self.trigger_slam_shake = True, False
        self.charge_cooldown = 240 
        self.charge_timer, self.charge_duration, self.charge_dx, self.charge_dy = 0, 0, 0, 0
        
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

    def update(self, walls, player=None, entities=None):
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
                if dist <= self.slam_radius and not getattr(player, 'is_invincible', False): 
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
            if self.charge_timer == 0: self.charge_duration = 15 
            return
            
        if self.charge_duration > 0:
            self.charge_duration -= 1
            self.current_anim_state = 'walk'
            self.move_and_collide(self.charge_dx, self.charge_dy, walls)
            
            if player and self.rect.colliderect(player.rect):
                if not getattr(player, 'is_invincible', False):
                    player.take_damage(int(25 * self.dmg_mult))
                self.trigger_slam_shake = True
                self.charge_duration = 0 
                self.attack_cooldown = 60 
            return

        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.attack_timer > 0: self.attack_timer -= 1
        
        is_moving = False
        can_see_player = False
        if dist < 450: 
            can_see_player = True
            for wall in walls:
                if wall.rect.clipline(self.rect.center, player.rect.center):
                    can_see_player = False 
                    break
                    
        if can_see_player:
            self.ai_state = 'chase'
            self.last_known_pos = (player.rect.centerx, player.rect.centery)
            self.investigate_timer = 180 
        elif self.investigate_timer > 0:
            self.ai_state = 'investigate'; self.investigate_timer -= 1
        else: self.ai_state = 'patrol'

        target_pos, current_speed = None, self.speed
        if self.ai_state == 'chase': target_pos = (player.rect.centerx, player.rect.centery)
        elif self.ai_state == 'investigate':
            target_pos = self.last_known_pos
            if target_pos and math.hypot(self.x - target_pos[0], self.y - target_pos[1]) < 20: self.investigate_timer = 0
        elif self.ai_state == 'patrol':
            current_speed = self.speed * 0.4 
            self.patrol_timer += 1
            if self.patrol_target is None or math.hypot(self.x - self.patrol_target[0], self.y - self.patrol_target[1]) < 20 or self.patrol_timer > 120:
                self.patrol_target = (self.x + random.randint(-150, 150), self.y + random.randint(-150, 150))
                self.patrol_timer = 0
            target_pos = self.patrol_target

        dx, dy = 0, 0
        if target_pos and self.attack_timer == 0:
            is_moving = True
            self.path_timer += 1
            if self.path_timer >= 30 or not self.path:
                self.path_timer = 0
                start_tile = (int(self.rect.centerx // TILE_SIZE), int(self.rect.centery // TILE_SIZE))
                goal_tile = (int(target_pos[0] // TILE_SIZE), int(target_pos[1] // TILE_SIZE))
                self.path = get_path(start_tile, goal_tile, walls)

            if self.path:
                next_tile = self.path[0]
                target_x = next_tile[0] * TILE_SIZE + (TILE_SIZE // 2) - (self.width // 2)
                target_y = next_tile[1] * TILE_SIZE + (TILE_SIZE // 2) - (self.height // 2)
                dir_x, dir_y = target_x - self.x, target_y - self.y
                dist_to_target = math.hypot(dir_x, dir_y)
                if dist_to_target > current_speed:
                    dx = (dir_x / dist_to_target) * current_speed; dy = (dir_y / dist_to_target) * current_speed
                    self.facing_right = dx > 0
                else: self.path.pop(0)
            else:
                dir_x, dir_y = target_pos[0] - self.rect.centerx, target_pos[1] - self.rect.centery
                dist_to_target = math.hypot(dir_x, dir_y)
                if dist_to_target > 0:
                    dx = (dir_x / dist_to_target) * current_speed; dy = (dir_y / dist_to_target) * current_speed
                    self.facing_right = dx > 0
                    
            if entities and self.ai_state == 'chase':
                separation_dx, separation_dy = 0, 0
                for other in entities:
                    if isinstance(other, Enemy) and other != self and other.health > 0:
                        dist_to_other = math.hypot(self.x - other.x, self.y - other.y)
                        if 0 < dist_to_other < 80: 
                            separation_dx += (self.x - other.x) / dist_to_other
                            separation_dy += (self.y - other.y) / dist_to_other
                if separation_dx != 0 or separation_dy != 0:
                    dx += separation_dx * 2.0; dy += separation_dy * 2.0
                    totale_snelheid = math.hypot(dx, dy)
                    if totale_snelheid > 0:
                        dx = (dx / totale_snelheid) * current_speed; dy = (dy / totale_snelheid) * current_speed

            self.move_and_collide(dx, dy, walls)

        if player and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            if not getattr(player, 'is_invincible', False):
                player.take_damage(int(15 * self.dmg_mult))
            self.attack_timer = 30; self.attack_cooldown = 90; is_moving = False

        if self.attack_timer > 0: self.current_anim_state = 'attack'
        elif is_moving and (dx != 0 or dy != 0): self.current_anim_state = 'walk'
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

# --- MATTIS Z'N EPISCHE WITTE ORC ---
class WhiteOrc(Boss):
    def __init__(self, x, y, difficulty="Normal"):
        super().__init__(x, y, difficulty)
        self.max_health = int(2000 * self.hp_mult)
        self.health = self.max_health
        self.speed = 2.5
        self.visual_size = 250 
        
        # 1. Jump aanval stats
        self.jump_cooldown = 300
        self.is_jumping = False
        self.jump_timer = 0
        self.jump_target_x = 0
        self.jump_target_y = 0
        
        # 2. Triangle Slam stats
        self.triangle_cooldown = 450
        self.is_charging_triangle = False
        self.triangle_timer = 0
        self.triangle_range = 300
        self.triangle_angle = 45

        self.animations = {'idle': [], 'walk': [], 'attack': [], 'death': [], 'jump': [], 'sprint': []}
        try:
            for state in ['idle', 'walk', 'attack', 'death', 'jump', 'sprint']:
                i = 0
                while True:
                    pad = os.path.join(PNG_DIR, "WhiteOrc PNG", f"white_{state}", f"{i}.png")
                    if not os.path.exists(pad): break
                    img = pygame.image.load(pad).convert_alpha()
                    img = pygame.transform.scale(img, (self.visual_size, self.visual_size))
                    self.animations[state].append(img)
                    i += 1
            if self.animations['idle']: self.image = self.animations['idle'][0]
        except Exception as e:
            print("Animatie Error Witte Orc:", e)
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((255, 255, 255)) 

    def update(self, walls, player=None, entities=None):
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
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.jump_cooldown > 0: self.jump_cooldown -= 1
        if self.triangle_cooldown > 0: self.triangle_cooldown -= 1

        # --- AANVAL 1: TRIANGLE SLAM ---
        if self.triangle_cooldown == 0 and dist < 250 and not self.is_jumping and self.slam_timer == 0 and self.charge_duration == 0:
            self.is_charging_triangle = True
            self.triangle_timer = 90 
            self.triangle_cooldown = 500
            self.current_anim_state = 'attack'
            self.frame_index = 0

        if self.is_charging_triangle:
            self.triangle_timer -= 1
            self.x += random.randint(-2, 2)
            
            if self.triangle_timer <= 0:
                self.is_charging_triangle = False
                self.trigger_slam_shake = True 
                
                angle_to_player = math.degrees(math.atan2(player.y - self.y, player.x - self.x))
                orc_angle = 0 if self.facing_right else 180
                angle_diff = abs((angle_to_player - orc_angle + 180) % 360 - 180)
                
                if dist < self.triangle_range and angle_diff < self.triangle_angle:
                    if not getattr(player, 'is_invincible', False):
                        player.take_damage(int(50 * self.dmg_mult))
            
            self._animate()
            return

        # --- AANVAL 2: JUMP ATTACK ---
        if self.jump_cooldown == 0 and dist > 150 and dist < 500 and self.slam_timer == 0 and self.charge_duration == 0 and not self.is_charging_triangle:
            self.is_jumping = True
            self.jump_timer = 45 
            self.jump_cooldown = 400
            self.jump_target_x = player.x
            self.jump_target_y = player.y
            self.current_anim_state = 'jump'
            self.frame_index = 0.0

        if self.is_jumping:
            self.jump_timer -= 1
            self.current_anim_state = 'jump'

            dx = (self.jump_target_x - self.x) * 0.1
            dy = (self.jump_target_y - self.y) * 0.1
            self.x += dx
            self.y += dy
            self.rect.topleft = (self.x, self.y)
            self.facing_right = dx > 0

            if self.jump_timer <= 0:
                self.is_jumping = False
                self.trigger_slam_shake = True 
                if dist < 160: 
                    if not getattr(player, 'is_invincible', False):
                        player.take_damage(int(45 * self.dmg_mult))
                self.attack_cooldown = 60
            
            self._animate()
            return

        # --- AANVAL 3: DASH / SPRINT ---
        if dist > 150 and dist < 400 and self.charge_cooldown == 0 and self.charge_timer == 0 and self.slam_timer == 0 and not self.is_jumping and not self.is_charging_triangle:
            self.charge_timer = 45 
            self.charge_cooldown = 300
            self.current_anim_state = 'idle'
            dir_x, dir_y = player.x - self.x, player.y - self.y
            if dist > 0:
                self.charge_dx = (dir_x / dist) * 16 
                self.charge_dy = (dir_y / dist) * 16
                self.facing_right = self.charge_dx > 0
            return

        if self.charge_timer > 0:
            self.charge_timer -= 1
            self.current_anim_state = 'idle'
            if self.charge_timer == 0:
                self.charge_duration = 20
            return

        if self.charge_duration > 0:
            self.charge_duration -= 1
            self.current_anim_state = 'sprint' 
            self.move_and_collide(self.charge_dx, self.charge_dy, walls)

            if player and self.rect.colliderect(player.rect):
                if not getattr(player, 'is_invincible', False):
                    player.take_damage(int(35 * self.dmg_mult))
                self.trigger_slam_shake = True
                self.charge_duration = 0
                self.attack_cooldown = 60
            
            self._animate()
            return

        super().update(walls, player, entities)

    def _animate(self):
        if self.animations.get(self.current_anim_state) and len(self.animations[self.current_anim_state]) > 0:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.current_anim_state]): 
                self.frame_index = 0.0
            self.image = self.animations[self.current_anim_state][int(self.frame_index)]
            if not self.facing_right: 
                self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, surface, camera):
        if getattr(self, 'is_charging_triangle', False):
            cx, cy = self.rect.centerx - camera.x, self.rect.centery - camera.y
            orc_angle = 0 if self.facing_right else 180
            
            p1 = (cx, cy)
            rad1 = math.radians(orc_angle - self.triangle_angle)
            rad2 = math.radians(orc_angle + self.triangle_angle)
            
            p2 = (cx + math.cos(rad1) * self.triangle_range, cy + math.sin(rad1) * self.triangle_range)
            p3 = (cx + math.cos(rad2) * self.triangle_range, cy + math.sin(rad2) * self.triangle_range)
            
            warn_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = int(100 + math.sin(pygame.time.get_ticks() / 100) * 50) 
            pygame.draw.polygon(warn_surf, (255, 0, 0, alpha), [p1, p2, p3])
            surface.blit(warn_surf, (0, 0))

        if getattr(self, 'is_jumping', False):
            shadow_surface = pygame.Surface((60, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, 100), (0, 0, 60, 20))
            surface.blit(shadow_surface, (self.x - camera.x + (self.width // 2) - 30, self.y - camera.y + self.height - 10))
            
            hoogte_in_lucht = math.sin((self.jump_timer / 45.0) * math.pi) * 120 
            
            if hasattr(self, 'image') and self.image:
                offset_x = (self.visual_size - self.width) // 2
                offset_y = (self.visual_size - self.height) // 2
                surface.blit(self.image, (self.x - camera.x - offset_x, self.y - camera.y - offset_y - int(hoogte_in_lucht)))
            return 
            
        super().draw(surface, camera)

class NPC(Entity):
    def __init__(self, x, y, level_index=0): 
        super().__init__(x, y, 40, 40, (128, 0, 128), 0, max_health=100)
        self.level_index = level_index
        self.is_talking = False 
        self.dialogue_pages = [] 
        self.current_page = 0    
        self.has_spoken = False 
        try:
            pad = os.path.join(PNG_DIR, "Different PNG", "wizard.png")
            if os.path.exists(pad):
                img = pygame.image.load(pad)
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        if self.is_talking and player:
            dist = math.hypot(self.x - player.x, self.y - player.y)
            if dist > 80: 
                self.is_talking = False

    def interact(self, player):
        if self.is_talking: return 
        
        self.has_spoken = True 
        self.is_talking = True
        self.current_page = 0
        
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
        if self.current_page < len(self.dialogue_pages) - 1:
            self.current_page += 1 
        else:
            self.is_talking = False 

    def draw(self, surface, camera):
        super().draw(surface, camera)
        font = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 20)
        
        if not self.has_spoken:
            t = pygame.time.get_ticks()
            bounce = math.sin(t / 200.0) * 5 
            text_surf = font.render("Praat met mij [E]!", True, GREEN, BLACK)
            text_rect = text_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 15 + bounce - camera.y)
            surface.blit(text_surf, text_rect)

        if self.is_talking and self.dialogue_pages:
            huidige_lijst = self.dialogue_pages[self.current_page]
            
            for i, regel in enumerate(huidige_lijst):
                text_surf = font.render(regel, True, YELLOW, BLACK)
                y_offset = (len(huidige_lijst) - i + 1) * 20
                text_rect = text_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 5 - y_offset - camera.y)
                surface.blit(text_surf, text_rect)
                
            spatie_surf = font_small.render("[SPATIE] Verder", True, (0, 255, 255), BLACK)
            spatie_rect = spatie_surf.get_rect(centerx=self.rect.centerx - camera.x, bottom=self.rect.top - 10 - camera.y)
            surface.blit(spatie_surf, spatie_rect)

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
        super().__init__(x, y, 0, 0, color, 1, 1) 
        self.text = text
        self.color = color
        self.timer = 45 
        self.is_removable = False
        self.font = pygame.font.Font(None, 36)
        self.x += random.randint(-15, 15)
        self.y += random.randint(-10, 10)

    def update(self, walls=None, player=None):
        self.y -= 1.5 
        self.timer -= 1
        if self.timer <= 0:
            self.is_removable = True

    def draw(self, surface, camera):
        text_surf = self.font.render(self.text, True, self.color)
        outline_surf = self.font.render(self.text, True, (0, 0, 0)) 
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            surface.blit(outline_surf, (draw_x + dx, draw_y + dy))
        surface.blit(text_surf, (draw_x, draw_y))
            
class PushableRock(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 44, 44, (139, 69, 19), speed=0, max_health=999) 
        try:
            pad = os.path.join(PNG_DIR, "Different PNG", "rots.png")
            if os.path.exists(pad):
                img = pygame.image.load(pad).convert_alpha()
                self.image = pygame.transform.scale(img, (self.width, self.height))
            else: raise Exception("No PNG")
        except:
            self.image = pygame.Surface((44, 44), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (120, 120, 120), (22, 22), 20) 
            pygame.draw.circle(self.image, (80, 80, 80), (22, 22), 20, 4) 
            pygame.draw.circle(self.image, (180, 180, 180), (12, 12), 6)  

    def update(self, walls=None, player=None, entities=None):
        pass 

    def move_rock(self, dx, dy, walls, player=None):
        oude_x, oude_y = self.x, self.y
        self.x += dx
        self.y += dy
        self.rect.topleft = (self.x, self.y)
        
        hitbox = self.rect.inflate(-4, -4) 
        for wall in walls:
            if hitbox.colliderect(wall.rect):
                self.x, self.y = oude_x, oude_y
                self.rect.topleft = (self.x, self.y)
                return False
        
        if player and hasattr(player, 'current_doors'):
            door_rects = [d.rect for d in player.current_doors]
            for door_rect in door_rects:
                if self.rect.colliderect(door_rect):
                    self.x, self.y = oude_x, oude_y
                    self.rect.topleft = (self.x, self.y)
                    return False
        return True

class PressurePlate(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, (150, 150, 150), speed=0, max_health=999)
        self.is_pressed = False
        self.image_up, self.image_down = None, None
        try:
            pad = os.path.join(PNG_DIR, "Different PNG", "plaat_op.png")
            if os.path.exists(pad):
                img = pygame.image.load(pad).convert_alpha()
                self.image_up = pygame.transform.scale(img, (40, 40))
            else: raise Exception("No PNG")
        except:
            self.image_up = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.rect(self.image_up, (80, 80, 80), (0, 0, 40, 40))
            pygame.draw.rect(self.image_up, (200, 200, 200), (6, 6, 28, 28))
            
        try:
            pad = os.path.join(PNG_DIR, "Different PNG", "plaat_neer.png")
            if os.path.exists(pad):
                img = pygame.image.load(pad).convert_alpha()
                self.image_down = pygame.transform.scale(img, (40, 40))
            else: raise Exception("No PNG")
        except:
            self.image_down = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.rect(self.image_down, (50, 50, 50), (0, 0, 40, 40))
            pygame.draw.rect(self.image_down, (100, 255, 100), (10, 10, 20, 20)) 
            pygame.draw.rect(self.image_down, (20, 100, 20), (10, 10, 20, 20), 2)
        
        self.image = self.image_up

    def update(self, walls=None, player=None, entities=None):
        pass

class Torch(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 30, 40, (139, 69, 19), speed=0, max_health=999)
        self.is_lit = False
        
        self.image_off = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image_off, (100, 50, 20), (10, 10, 10, 30)) 
        pygame.draw.circle(self.image_off, (50, 50, 50), (15, 10), 8) 
        
        self.image_on = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image_on, (100, 50, 20), (10, 10, 10, 30))
        pygame.draw.circle(self.image_on, (255, 100, 0), (15, 10), 12) 
        pygame.draw.circle(self.image_on, (255, 255, 0), (15, 10), 6)  
        
        self.image = self.image_off

    def update(self, walls=None, player=None):
        self.image = self.image_on if self.is_lit else self.image_off