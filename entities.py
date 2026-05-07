# -*- coding: utf-8 -*-
"""
entities.py (Nu MET Boss, én MET Traps!)
"""

import pygame
import math
import os
from settings import *

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
        if hasattr(self, 'image') and self.image:
            surface.blit(self.image, draw_pos)
        else:
            pygame.draw.rect(surface, self.color, (*draw_pos, self.width, self.height))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50, BLUE, 5, max_health=100)
        self.inventory = [] 
        self.frame_index = 0.0      
        self.animation_speed = 0.2
        self.facing = 'down'        
        self.is_moving = False
        
        # Nieuwe eigenschappen voor Level 4!
        self.is_blocking = False
        self.spell_cooldown = 0 
        
        self.animations = {'up': [], 'down': [], 'left': [], 'right': []}
        try:
            for direction in ['up', 'down', 'left', 'right']:
                i = 0
                while os.path.exists(f"{direction}/{i}.png"):
                    img = pygame.image.load(f"{direction}/{i}.png").convert_alpha()
                    img = pygame.transform.scale(img, (self.width, self.height))
                    self.animations[direction].append(img)
                    i += 1
            if self.animations['down']: self.image = self.animations['down'][0] 
        except: self.image = None
        
        self.sword_img = None
        try:
            huidige_map = os.path.dirname(os.path.abspath(__file__))
            sword_pad = os.path.join(huidige_map, "sword.png")
            if os.path.exists(sword_pad):
                img = pygame.image.load(sword_pad).convert_alpha()
                self.sword_img = pygame.transform.scale(img, (60, 60))
        except: pass

    def take_damage(self, amount): 
        # Als je aan het blocken bent, krijg je GEEN SCHADE!
        if self.is_blocking:
            return 
        self.health -= amount

    def attack(self, enemies, walls): 
        if self.is_blocking: return # Je kan niet slaan en blocken tegelijk
        self.attack_timer = 15 
        for enemy in enemies:
            dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if dist < 90: 
                if "Magisch Zwaard" in self.inventory: enemy.health -= 40
                else: enemy.health -= 20
                
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

    def update(self, walls: list, player=None):
        if self.attack_timer > 0: self.attack_timer -= 1
        if self.spell_cooldown > 0: self.spell_cooldown -= 1
        
        keys = pygame.key.get_pressed()
        self.is_moving = False 

        # BLOCK LOGICA
        if keys[pygame.K_LSHIFT] and "Schild" in self.inventory:
            self.is_blocking = True
            dx, dy = 0, 0 # Je kan niet lopen terwijl je blockt
        else:
            self.is_blocking = False
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -self.speed; self.facing = 'left'; self.is_moving = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = self.speed; self.facing = 'right'; self.is_moving = True
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -self.speed; self.facing = 'up'; self.is_moving = True
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = self.speed; self.facing = 'down'; self.is_moving = True

        if dx != 0:
            self.x += dx
            self.rect.topleft = (self.x, self.y)
            hitbox = self.rect.inflate(-15, -15)
            for wall in walls:
                if hitbox.colliderect(wall.rect):
                    self.x -= dx; self.rect.topleft = (self.x, self.y)

        if dy != 0:
            self.y += dy
            self.rect.topleft = (self.x, self.y)
            hitbox = self.rect.inflate(-15, -15)
            for wall in walls:
                if hitbox.colliderect(wall.rect):
                    self.y -= dy; self.rect.topleft = (self.x, self.y)

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
        
        # Teken het blauwe krachtveld als we blocken!
        if self.is_blocking:
            pygame.draw.circle(surface, (0, 191, 255), (cx, cy), 35, 4)
            pygame.draw.circle(surface, (0, 191, 255, 100), (cx, cy), 35) # Lichtblauwe gloed
        
        if self.attack_timer > 0 and not self.is_blocking:
            if "Magisch Zwaard" in self.inventory and self.sword_img:
                base_angles = {'right': 0, 'up': 90, 'left': 180, 'down': 270}
                base_angle = base_angles[self.facing]
                progress = self.attack_timer / 15.0 
                swing_angle = progress * 120 - 60
                total_angle = base_angle + swing_angle
                image_rotation = total_angle - 45
                
                rotated_sword = pygame.transform.rotate(self.sword_img, image_rotation)
                distance = 35 
                offset_x = math.cos(math.radians(total_angle)) * distance
                offset_y = -math.sin(math.radians(total_angle)) * distance 
                
                sword_rect = rotated_sword.get_rect(center=(cx + offset_x, cy + offset_y))
                surface.blit(rotated_sword, sword_rect)
            else:
                zwaard_lengte = 60 if "Magisch Zwaard" in self.inventory else 40
                if self.facing == 'up': end_pos = (cx, cy - zwaard_lengte)
                elif self.facing == 'down': end_pos = (cx, cy + zwaard_lengte)
                elif self.facing == 'left': end_pos = (cx - zwaard_lengte, cy)
                else: end_pos = (cx + zwaard_lengte, cy)
                pygame.draw.line(surface, (150, 150, 150), (cx, cy), end_pos, 6) 
                pygame.draw.line(surface, (255, 255, 255), (cx, cy), end_pos, 2)  

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50, RED, 2, max_health=50) 
        self.visual_size = 80 
        self.patrol_timer = 0
        self.patrol_direction = 1
        self.attack_cooldown = 0
        self.current_anim_state = 'idle'
        self.frame_index = 0.0
        self.animation_speed = 0.1
        self.facing_right = True
        self.is_removable = False
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'death': []}
        try:
            for state in ['idle', 'walk', 'attack', 'death']:
                i = 0
                while os.path.exists(f"goblin_{state}/{i}.png"):
                    img = pygame.image.load(f"goblin_{state}/{i}.png")
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
        ai_state = 'chase' if dist < 300 else 'patrol'

        if ai_state == 'chase' and self.attack_timer == 0:
            is_moving = True
            
            dx = 0
            if self.x < player.x: dx = self.speed; self.facing_right = True
            elif self.x > player.x: dx = -self.speed; self.facing_right = False
            
            if dx != 0:
                self.x += dx
                self.rect.topleft = (self.x, self.y)
                hitbox = self.rect.inflate(-15, -15) 
                for wall in walls:
                    if hitbox.colliderect(wall.rect):
                        self.x -= dx
                        self.rect.topleft = (self.x, self.y)
                        break
            
            dy = 0
            if self.y < player.y: dy = self.speed
            elif self.y > player.y: dy = -self.speed
            
            if dy != 0:
                self.y += dy
                self.rect.topleft = (self.x, self.y)
                hitbox = self.rect.inflate(-15, -15)
                for wall in walls:
                    if hitbox.colliderect(wall.rect):
                        self.y -= dy
                        self.rect.topleft = (self.x, self.y)
                        break

        if player and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            player.take_damage(10); self.attack_timer = 30; self.attack_cooldown = 90; is_moving = False

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
            
            draw_x = self.x - camera.x - offset_x
            draw_y = self.y - camera.y - offset_y
            surface.blit(self.image, (draw_x, draw_y))
        else:
            draw_pos = (self.x - camera.x, self.y - camera.y)
            pygame.draw.rect(surface, self.color, (*draw_pos, self.width, self.height))
            
        if not self.is_removable and self.health > 0:
            self.draw_health_bar(surface, camera, offset_y=-30) 

class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 500  
        self.max_health = 500
        self.speed = 1     
        
        self.width = 70
        self.height = 70
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.visual_size = 200 
        
        # --- SPECIALE AANVAL (AARDBEVING SLAM) ---
        self.special_cooldown = 180  # 3 seconden rust tussen speciale aanvallen
        self.slam_timer = 0          # De timer voor het "opladen" van de aanval
        self.slam_radius = 120       # Hoe groot de gevaren-cirkel is
        
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'death': []}
        try:
            for state in ['idle', 'walk', 'attack', 'death']:
                i = 0
                while os.path.exists(f"boss_{state}/{i}.png"):
                    img = pygame.image.load(f"boss_{state}/{i}.png")
                    img = pygame.transform.scale(img, (self.visual_size, self.visual_size))
                    self.animations[state].append(img)
                    i += 1
            if self.animations['idle']: self.image = self.animations['idle'][0]
        except: self.image = None

    def update(self, walls, player=None):
        # 1. Dood animatie
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

        # 2. Speciale Aanval Logica (Aardbeving)
        if self.special_cooldown > 0: 
            self.special_cooldown -= 1

        # Als hij dichtbij de speler is, zijn cooldown is 0, start met opladen!
        if dist < self.slam_radius and self.special_cooldown == 0 and self.slam_timer == 0:
            self.slam_timer = 60 # 1 seconde lang stilstaan en opladen (60 frames)
            self.special_cooldown = 240 # Pas over 4 seconden mag hij weer springen
            self.current_anim_state = 'attack'
            self.frame_index = 0.0

        # Als hij aan het opladen is...
        if self.slam_timer > 0:
            self.slam_timer -= 1
            self.current_anim_state = 'attack'
            
            if self.animations['attack']:
                self.frame_index += (self.animation_speed * 0.5) 
                if self.frame_index >= len(self.animations['attack']): self.frame_index = 0.0
                self.image = self.animations['attack'][int(self.frame_index)]
                if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)

            # Vlak voor het einde van het opladen (frame 5): BOOM!
            if self.slam_timer == 5: 
                if dist <= self.slam_radius:
                    player.take_damage(25) # 25 Schade in één klap!
            
            return # BELANGRIJK: Stop de update hier, hij mag niet lopen tijdens zijn Slam!

        # 3. Normale loop logica (De baas rent achter je aan als hij niet aan het slaan is)
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.attack_timer > 0: self.attack_timer -= 1
        
        is_moving = False
        ai_state = 'chase' if dist < 400 else 'patrol'

        if ai_state == 'chase' and self.attack_timer == 0:
            is_moving = True
            
            dx = 0
            if self.x < player.x: dx = self.speed; self.facing_right = True
            elif self.x > player.x: dx = -self.speed; self.facing_right = False
            
            if dx != 0:
                self.x += dx
                self.rect.topleft = (self.x, self.y)
                hitbox = self.rect.inflate(-15, -15) 
                for wall in walls:
                    if hitbox.colliderect(wall.rect):
                        self.x -= dx
                        self.rect.topleft = (self.x, self.y)
                        break
            
            dy = 0
            if self.y < player.y: dy = self.speed
            elif self.y > player.y: dy = -self.speed
            
            if dy != 0:
                self.y += dy
                self.rect.topleft = (self.x, self.y)
                hitbox = self.rect.inflate(-15, -15)
                for wall in walls:
                    if hitbox.colliderect(wall.rect):
                        self.y -= dy
                        self.rect.topleft = (self.x, self.y)
                        break

        # Normale kleine aanval (als hij je per ongeluk aanraakt)
        if player and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            player.take_damage(10); self.attack_timer = 30; self.attack_cooldown = 90; is_moving = False

        if self.attack_timer > 0: self.current_anim_state = 'attack'
        elif is_moving: self.current_anim_state = 'walk'
        else: self.current_anim_state = 'idle'

        if self.animations[self.current_anim_state]:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.current_anim_state]): self.frame_index = 0.0
            self.image = self.animations[self.current_anim_state][int(self.frame_index)]
            if not self.facing_right: self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, surface, camera):
        # 1. Teken EERST de gevaarlijke rode cirkel (zodat hij onder de Troll ligt)
        if self.slam_timer > 0:
            cx = self.x - camera.x + (self.width // 2)
            cy = self.y - camera.y + (self.height // 2)
            
            # Bereken hoe groot de oranje waarschuwingslijn moet zijn
            progress = 1.0 - (self.slam_timer / 60.0)
            current_radius = int(self.slam_radius * progress)
            
            # Teken de transparante waarschuwingszone
            warning_surface = pygame.Surface((self.slam_radius*2, self.slam_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(warning_surface, (255, 0, 0, 60), (self.slam_radius, self.slam_radius), self.slam_radius) # Rode achtergrond
            pygame.draw.circle(warning_surface, (255, 100, 0, 200), (self.slam_radius, self.slam_radius), current_radius, 4) # Groeiende oranje rand
            
            surface.blit(warning_surface, (cx - self.slam_radius, cy - self.slam_radius))

        # 2. Teken de baas zelf (bovenop de rode cirkel)
        super().draw(surface, camera)

class NPC(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, (128, 0, 128), 0, max_health=100)
        self.quest_state = 'start'
        self.message = ""
        self.talk_timer = 0 
        try:
            if os.path.exists("wizard.png"):
                img = pygame.image.load("wizard.png")
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        if self.talk_timer > 0: self.talk_timer -= 1

    def interact(self, player):
        self.talk_timer = 180 
        if self.quest_state == 'start':
            self.message = "Goblins bewaken de kist! Versla ze allemaal, pak de sleutel en kom terug!"
            self.quest_state = 'waiting'
        elif self.quest_state == 'waiting':
            if "Gouden Sleutel" in player.inventory:
                self.message = "Geweldig! De Uitgang (Bruine Deur) is nu geopend! Succes!"
                player.inventory.remove("Gouden Sleutel")
                player.inventory.append("Kasteel Toegang") 
                self.quest_state = 'done'
            else:
                self.message = "Versla alle Goblins zodat de kist opent, en breng me de sleutel!"
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
        self.item_name = item_name
        self.is_picked_up = False
        self.frames = []
        self.frame_index = 0.0
        self.animation_speed = 0.2
        self.is_opening = False
        self.is_open = False
        try:
            i = 0
            while os.path.exists(f"kist/{i}.png"):
                img = pygame.image.load(f"kist/{i}.png")
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
                self.is_opening = False
                self.is_open = True
                if player and not self.is_picked_up:
                    player.inventory.append(self.item_name)
                    self.is_picked_up = True
            if self.frames: self.image = self.frames[int(self.frame_index)]

class Potion(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, (255, 20, 147), 0, max_health=1)
        self.is_picked_up = False
        try:
            if os.path.exists("potion.png"):
                img = pygame.image.load("potion.png")
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except: pass

    def update(self, walls=None, player=None):
        if player and self.rect.colliderect(player.rect) and not self.is_picked_up:
            if player.health < player.max_health:
                player.health += 30 
                if player.health > player.max_health: player.health = player.max_health
                self.is_picked_up = True

# --- HIER IS DE VERLOREN TRAP KLASSE WEER TERUG! ---
class Trap(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, (100, 100, 100), 0, max_health=1)
        self.damage_cooldown = 0
        self.is_active = True  
        self.timer = 0         
        self.switch_time = 90  
        
        self.image_active = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image_active, (60, 60, 60), (0, 0, 40, 40)) 
        for i in range(4): 
            pygame.draw.polygon(self.image_active, (200, 0, 0), [(i*10, 40), (i*10+5, 10), (i*10+10, 40)])
            
        self.image_safe = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image_safe, (60, 60, 60), (0, 0, 40, 40)) 
        for i in range(4): 
            pygame.draw.circle(self.image_safe, (20, 20, 20), (i*10 + 5, 20), 4)

        self.image = self.image_active

    def update(self, walls=None, player=None):
        self.timer += 1
        if self.timer >= self.switch_time:
            self.timer = 0
            self.is_active = not self.is_active 
            if self.is_active: self.image = self.image_active
            else: self.image = self.image_safe

        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
            
        if self.is_active and player and self.rect.colliderect(player.rect):
            if self.damage_cooldown == 0:
                player.take_damage(20)
                self.damage_cooldown = 60

class Fireball(Entity):
    def __init__(self, x, y, facing):
        super().__init__(x, y, 20, 20, (255, 100, 0), 12, 1) # Super snel (12 speed)
        self.facing = facing
        self.is_removable = False
        
        # Teken een coole oranje/gele vuurbal
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 69, 0), (10, 10), 10) # Buitenkant oranje
        pygame.draw.circle(self.image, (255, 255, 0), (10, 10), 5)  # Binnenkant geel

    def update(self, walls=None, player=None):
        # Vlieg in de juiste richting
        if self.facing == 'up': self.y -= self.speed
        elif self.facing == 'down': self.y += self.speed
        elif self.facing == 'left': self.x -= self.speed
        elif self.facing == 'right': self.x += self.speed
        
        self.rect.topleft = (self.x, self.y)
        
        # Breek kapot als hij een muur of gesloten deur raakt
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                self.is_removable = True
                return