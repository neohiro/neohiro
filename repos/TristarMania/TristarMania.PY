import pygame
import sys
import random
import math
import os
import time
from datetime import datetime
import numpy as np # Import the NumPy library

# --- Constants ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FULLSCREEN = True
FPS = 60
SPAWN_RATE = 120 # Spawn an obstacle every X frames
SAMPLE_RATE = 44100 # Standard audio sample rate for sound generation
LETTER_MAPPING = "HGFURSRQMLEDCBKIJPONAXYZWV" # Used for save/load codes

# --- Colors ---
DARK_BLUE = (15, 15, 30)
BLUE = (50, 50, 100)
LIGHT_BLUE = (150, 150, 200)
WHITE = (255, 255, 255)
MENU_TEXT_COLOR = (200, 200, 255)
HOVER_TEXT_COLOR = (255, 255, 255)
SLIDER_BG_COLOR = (70, 70, 70)
SLIDER_HANDLE_COLOR = (200, 200, 255)
SPACESHIP_COLOR = (255, 20, 147) # Bright neon pink
ENEMY_COLOR = (255, 50, 50)
NEUTRAL_COLOR = (50, 255, 50)
ROCK_COLOR = (150, 150, 150)
LASER_COLOR = (0, 255, 255)
LIFE_COLOR = (255, 50, 50)
EXPLOSION_COLORS = [(255, 255, 0), (255, 165, 0), (255, 69, 0), (255, 0, 0)]
FOG_COLOR = (30, 0, 40) # Deep nebula purple

# --- Cyberpunk Head / HUD Colors ---
CYBER_SKIN_COLOR = (170, 180, 190) # Pale synthetic skin
CYBER_SKIN_SHADOW = (100, 110, 120)
CYBER_ACCENT = (0, 255, 255) # Cyan glow
CYBER_EYE_RED = (255, 30, 30)
CYBER_METAL = (60, 65, 70)
CYBER_DARK_METAL = (30, 30, 35)
HUD_BG_COLOR = (5, 15, 25, 210) # Dark transparent blue
HUD_BORDER_COLOR = (0, 200, 255)
HUD_TEXT_COLOR = (180, 255, 230) # Minty bright text

# --- Helper function for sound generation ---
def sinc(x):
    if x == 0:
        return 1.0
    else:
        return math.sin(x) / x

# --- Parallax Star Class ---
class ParallaxStar:
    def __init__(self, screen_width, screen_height):
        self.x = random.randrange(0, screen_width)
        self.y = random.randrange(0, screen_height)
        self.size = random.randint(1, 2)
        self.color = (random.randint(40, 80), random.randint(40, 80), random.randint(80, 120)) 
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.parallax_factor = random.uniform(0.1, 0.3)

    def update(self, player_dx, player_dy):
        self.x -= player_dx * self.parallax_factor
        self.y -= player_dy * self.parallax_factor
        self.x %= self.screen_width
        self.y %= self.screen_height

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

# --- Starfield Animation Class ---
class Star:
    def __init__(self, screen_width, screen_height):
        self.x = random.randrange(0, screen_width)
        self.y = random.randrange(0, screen_height)
        self.size = random.randint(1, 3)
        self.speed = random.uniform(0.5, 2.0)
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        self.screen_width = screen_width
        self.screen_height = screen_height

    def update(self):
        self.y += self.speed
        if self.y > self.screen_height:
            self.y = 0
            self.x = random.randrange(0, self.screen_width)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

# --- Explosion Effect Classes ---
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(1, 5)
        self.angle = random.uniform(0, 2 * math.pi)
        self.vx = self.speed * math.cos(self.angle)
        self.vy = self.speed * math.sin(self.angle)
        self.lifespan = random.randint(20, 40)
        self.color = random.choice(EXPLOSION_COLORS)
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifespan -= 1
        if self.size > 0.1:
            self.size -= 0.1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

class Explosion:
    def __init__(self, x, y, num_particles=30):
        self.particles = [Particle(x, y) for _ in range(num_particles)]
        self.is_done = False

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.lifespan > 0 and p.size > 0]
        if not self.particles:
            self.is_done = True

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)

# --- Harvest Particle Class ---
class HarvestParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(2, 4)
        self.size = random.randint(2, 4)
        self.lifespan = 180 
        self.rect = pygame.Rect(self.x, self.y, self.size * 2, self.size * 2)

    def update(self, player_pos):
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += self.speed * (dx / dist)
            self.y += self.speed * (dy / dist)
        self.lifespan -= 1
        self.rect.center = (int(self.x), int(self.y))
        
    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size)

# --- Engine Trail Particle Class ---
class TrailParticle:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.size = random.randint(3, 6)
        spread = random.uniform(-0.5, 0.5)
        speed = random.uniform(2, 5)
        self.vx = -speed * math.cos(math.radians(angle) + spread)
        self.vy = -speed * math.sin(math.radians(angle) + spread)
        self.color = (0, 255, 255) 
        self.alpha = 255
        self.decay = 15

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= self.decay
        self.size -= 0.2
    
    def draw(self, screen):
        if self.alpha > 0 and self.size > 0:
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, int(self.alpha)), (int(self.size), int(self.size)), int(self.size))
            screen.blit(s, (self.x - self.size, self.y - self.size))

# --- Spaceship Class (Player) ---
class Spaceship:
    def __init__(self, screen_width, screen_height):
        self.x = screen_width / 2
        self.y = screen_height + 50 
        self.velocity = 0
        self.max_velocity = 5
        self.acceleration = 0.2
        self.deceleration = 0.1
        self.rotation_speed = 3
        self.direction = -90 
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = 20
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        self.invulnerable = False
        self.invulnerability_duration = 180 
        self.invulnerability_timer = 0
        self.blink = False
        self.trails = []
        
    def update(self):
        self.x += self.velocity * math.cos(math.radians(self.direction))
        self.y += self.velocity * math.sin(math.radians(self.direction))
        self.x %= self.screen_width
        self.y %= self.screen_height
        self.rect.center = (int(self.x), int(self.y))

        if self.invulnerable:
            self.invulnerability_timer -= 1
            if self.invulnerability_timer % 10 < 5:
                self.blink = True
            else:
                self.blink = False
            if self.invulnerability_timer <= 0:
                self.invulnerable = False
                self.blink = False
        
        for p in self.trails:
            p.update()
        self.trails = [p for p in self.trails if p.alpha > 0 and p.size > 0]
        
    def move_forward(self):
        self.velocity = min(self.max_velocity, self.velocity + self.acceleration)
        angle_rad = math.radians(self.direction)
        rear_x = self.x - self.size * math.cos(angle_rad)
        rear_y = self.y - self.size * math.sin(angle_rad)
        self.trails.append(TrailParticle(rear_x, rear_y, self.direction))
        
    def move_backward(self):
        self.velocity = max(-self.max_velocity, self.velocity - self.acceleration)
    
    def stop(self):
        if self.velocity > 0:
            self.velocity = max(0, self.velocity - self.deceleration)
        elif self.velocity < 0:
            self.velocity = min(0, self.velocity + self.deceleration)

    def rotate_left(self):
        self.direction -= self.rotation_speed
        
    def rotate_right(self):
        self.direction += self.rotation_speed
        
    def draw(self, screen):
        for p in self.trails:
            p.draw(screen)
        if self.blink:
            return 
        angle_rad = math.radians(self.direction)
        p1_x = self.x + self.size * math.cos(angle_rad)
        p1_y = self.y + self.size * math.sin(angle_rad)
        p2_x = self.x + self.size * math.cos(angle_rad + 2.5)
        p2_y = self.y + self.size * math.sin(angle_rad + 2.5)
        p3_x = self.x + self.size * math.cos(angle_rad - 2.5)
        p3_y = self.y + self.size * math.sin(angle_rad - 2.5)
        points = [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)]
        pygame.draw.polygon(screen, SPACESHIP_COLOR, points)
        
    def check_collision(self, other_rect):
        return self.rect.colliderect(other_rect)

    def respawn(self):
        self.x = self.screen_width / 2
        self.y = self.screen_height / 2
        self.velocity = 0
        self.invulnerable = True
        self.invulnerability_timer = self.invulnerability_duration

# --- Laser Class ---
class Laser:
    def __init__(self, x, y, direction, screen_width, screen_height, is_enemy_laser=False, level=1):
        self.x = x
        self.y = y
        self.direction = direction
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_enemy_laser = is_enemy_laser

        if is_enemy_laser:
            self.speed = 5
            self.color = ENEMY_COLOR
            self.thickness = 5
            self.length = 15
        else:
            self.speed = 10
            self.color = LASER_COLOR
            base_thickness = 5
            self.thickness = min(base_thickness + (level // 2), 25)
            self.length = 20 
        
        self.rect = pygame.Rect(self.x, self.y, self.thickness, self.thickness)
        self.angle = direction 
        
    def update(self):
        self.x += self.speed * math.cos(math.radians(self.direction))
        self.y += self.speed * math.sin(math.radians(self.direction))
        self.rect.center = (int(self.x), int(self.y))
        
    def draw(self, screen):
        laser_surf = pygame.Surface((self.length, self.thickness), pygame.SRCALPHA)
        pygame.draw.rect(laser_surf, self.color, (0, 0, self.length, self.thickness))
        rotated_laser = pygame.transform.rotate(laser_surf, -self.direction)
        new_rect = rotated_laser.get_rect(center=(int(self.x), int(self.y)))
        
        glow_size = max(self.length, self.thickness) * 0.6
        glow_surf = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
        glow_color = (*self.color, 50) 
        pygame.draw.circle(glow_surf, glow_color, (int(glow_size), int(glow_size)), int(glow_size))
        
        screen.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))
        screen.blit(rotated_laser, new_rect.topleft)
        
    def is_off_screen(self):
        return self.x < 0 or self.x > self.screen_width or self.y < 0 or self.y > self.screen_height

# --- Obstacle Classes ---
class SpaceRock:
    def __init__(self, screen_width, screen_height):
        self.size = random.randint(15, 40)
        self.x = random.randrange(self.size, screen_width - self.size)
        self.y = -self.size
        self.speed = random.uniform(1.0, 3.0)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        self.is_destroyed = False
        self.score_value = 10
        self.is_life_rock = True 
        
        self.image = pygame.Surface((self.size * 2 + 10, self.size * 2 + 10), pygame.SRCALPHA)
        self.points = []
        num_points = random.randint(7, 12)
        center = (self.size + 5, self.size + 5)
        for i in range(num_points):
            angle = math.radians((i / num_points) * 360)
            r = self.size * random.uniform(0.7, 1.2)
            px = center[0] + r * math.cos(angle)
            py = center[1] + r * math.sin(angle)
            self.points.append((px, py))
        
        pygame.draw.polygon(self.image, ROCK_COLOR, self.points)
        pygame.draw.polygon(self.image, (200, 200, 200), self.points, 2) 

        self.rotation = 0
        self.rot_speed = random.uniform(-2, 2)
        
    def update(self):
        self.y += self.speed
        self.rect.center = (int(self.x), int(self.y))
        self.rotation += self.rot_speed
        
    def draw(self, screen):
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        screen.blit(rotated_image, new_rect.topleft)
        
    def is_off_screen(self):
        return self.y > self.screen_height + self.size

class EnemySpaceship:
    def __init__(self, screen_width, screen_height, level):
        self.size = 20
        self.x = random.randrange(self.size, screen_width - self.size)
        self.y = random.randrange(-300, -50) 
        self.base_speed = random.uniform(1.5, 3.5)
        capped_level = min(level, 2)
        self.speed_multiplier = 1 + (capped_level - 1) * 0.2
        self.speed = self.base_speed * self.speed_multiplier
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        self.is_destroyed = False
        self.score_value = 50
        self.last_shot_time = pygame.time.get_ticks()

    def update(self, player_pos, level):
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.x += self.speed * (dx / dist)
            self.y += self.speed * (dy / dist)
        self.rect.center = (int(self.x), int(self.y))

    def can_shoot(self, current_time, level):
        if level < 3: return False
        shoot_cooldown = (1500 - (level - 3) * 50) * 2
        return current_time - self.last_shot_time > max(500, shoot_cooldown)

    def shoot(self, player_pos):
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        angle = math.degrees(math.atan2(dy, dx))
        new_laser = Laser(self.x, self.y, angle, self.screen_width, self.screen_height, is_enemy_laser=True)
        self.last_shot_time = pygame.time.get_ticks()
        return new_laser
    
    def draw(self, screen):
        points = [
            (self.x, self.y - self.size),
            (self.x + self.size, self.y),
            (self.x, self.y + self.size),
            (self.x - self.size, self.y)
        ]
        pygame.draw.polygon(screen, ENEMY_COLOR, points)
        
    def is_off_screen(self):
        return self.y > self.screen_height + self.size or self.x < -self.size or self.x > self.screen_width + self.size

class NeutralSpaceship:
    def __init__(self, screen_width, screen_height):
        self.size = 15
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.speed = random.uniform(1.0, 2.0)
        self.is_destroyed = False
        self.is_life_stealer = True
        
        side = random.randint(0, 3)
        buffer = self.size * 2
        
        if side == 0: # Top
            self.x = random.randrange(0, screen_width)
            self.y = -buffer
            self.direction = random.uniform(45, 135) 
        elif side == 1: # Right
            self.x = screen_width + buffer
            self.y = random.randrange(0, screen_height)
            self.direction = random.uniform(135, 225) 
        elif side == 2: # Bottom
            self.x = random.randrange(0, screen_width)
            self.y = screen_height + buffer
            self.direction = random.uniform(225, 315) 
        else: # Left
            self.x = -buffer
            self.y = random.randrange(0, screen_height)
            self.direction = random.uniform(-45, 45) 

        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        
    def update(self):
        self.x += self.speed * math.cos(math.radians(self.direction))
        self.y += self.speed * math.sin(math.radians(self.direction))
        self.rect.center = (int(self.x), int(self.y))
    
    def draw(self, screen):
        points = [
            (self.x, self.y - self.size),
            (self.x + self.size, self.y + self.size),
            (self.x - self.size, self.y + self.size)
        ]
        pygame.draw.polygon(screen, NEUTRAL_COLOR, points)
        
    def is_off_screen(self):
        margin = 100
        return (self.x < -margin or self.x > self.screen_width + margin or
                self.y < -margin or self.y > self.screen_height + margin)

# --- Boss Class ---
class Boss:
    def __init__(self, screen_width, screen_height, level):
        self.size = 100
        self.x = screen_width / 2
        self.y = -self.size
        self.speed = 0.5 
        
        base_hp = (10 + (level - 4) * 10)
        health_multiplier = 1.2 if level >= 8 else 2.0
        self.max_health = base_hp * health_multiplier
        self.health = self.max_health
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = pygame.Rect(self.x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        self.is_destroyed = False
        self.score_value = 0 
        self.last_shot_time = pygame.time.get_ticks()
        self.target_x = self.x
        self.target_y = self.y
        self.move_timer = 0 

    def update(self, player_pos):
        self.move_timer -= 1
        if self.move_timer <= 0:
            self.move_timer = random.randint(60, 180) 
            if random.random() < 0.6:
                self.target_x = player_pos[0]
                self.target_y = player_pos[1]
            else:
                self.target_x = random.randint(self.size, self.screen_width - self.size)
                self.target_y = random.randint(self.size, self.screen_height // 2)

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist != 0:
            self.x += self.speed * (dx / dist)
            self.y += self.speed * (dy / dist)
            
        self.rect.center = (int(self.x), int(self.y))

    def can_shoot(self, current_time, level):
        if level < 5: return False
        shoot_cooldown = max(500, 2000 - (level - 5) * 100)
        return current_time - self.last_shot_time > shoot_cooldown

    def shoot(self, player_pos):
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        angle = math.degrees(math.atan2(dy, dx))
        new_laser = Laser(self.x, self.y, angle, self.screen_width, self.screen_height, is_enemy_laser=True)
        self.last_shot_time = pygame.time.get_ticks()
        return new_laser

    def draw(self, screen):
        x, y = self.rect.topleft
        w, h = self.rect.size
        bevel = 15 
        color_top_light = (255, 120, 120)    
        color_bottom_shadow = (100, 20, 20)  
        color_side_mid = (180, 30, 30)       
        
        pygame.draw.polygon(screen, color_top_light, 
                            [(x, y), (x + w, y), (x + w - bevel, y + bevel), (x + bevel, y + bevel)])
        pygame.draw.polygon(screen, color_bottom_shadow, 
                            [(x, y + h), (x + w, y + h), (x + w - bevel, y + h - bevel), (x + bevel, y + h - bevel)])
        pygame.draw.polygon(screen, color_side_mid, 
                            [(x, y), (x, y + h), (x + bevel, y + h - bevel), (x + bevel, y + bevel)])
        pygame.draw.polygon(screen, color_side_mid, 
                            [(x + w, y), (x + w, y + h), (x + w - bevel, y + h - bevel), (x + w - bevel, y + bevel)])

        center_rect = pygame.Rect(x + bevel, y + bevel, w - 2 * bevel, h - 2 * bevel)
        pygame.draw.rect(screen, ENEMY_COLOR, center_rect)

        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 5
        core_radius = int((w // 6) + pulse)
        core_radius = max(5, core_radius)
        center_x, center_y = self.rect.center
        pygame.draw.circle(screen, (100, 0, 0), (center_x, center_y), core_radius)

        if self.health > 0:
            bg_rect = pygame.Rect(self.rect.left, self.rect.top - 20, self.rect.width, 10)
            pygame.draw.rect(screen, DARK_BLUE, bg_rect)
            health_percentage = self.health / self.max_health
            fg_rect = pygame.Rect(self.rect.left, self.rect.top - 20, self.rect.width * health_percentage, 10)
            pygame.draw.rect(screen, LIFE_COLOR, fg_rect)
            pygame.draw.rect(screen, WHITE, bg_rect, 1)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.is_destroyed = True

    def is_off_screen(self):
        return self.y > self.screen_height + self.size

# --- Black Hole Class ---
class BlackHole:
    def __init__(self, screen_width, screen_height, level):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.radius = 40 
        self.gravity_radius = 300 
        self.strength = 200 + (level * 15) 

        self.direction = random.choice([-1, 1])
        if self.direction == 1: 
            self.x = -self.radius
        else: 
            self.x = self.screen_width + self.radius
        
        self.y = random.randrange(self.radius, self.screen_height - self.radius)
        self.speed = 1.5
        
        # Diagonal movement logic
        self.vx = self.speed * self.direction
        # Add random vertical movement to make it move diagonally
        self.vy = random.uniform(-0.5, 0.5) * self.speed
        
        self.is_active = True
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
        
        if (self.direction == 1 and self.x > self.screen_width + self.radius * 2) or \
           (self.direction == -1 and self.x < -self.radius * 2) or \
           (self.y < -self.radius * 2) or (self.y > self.screen_height + self.radius * 2):
            self.is_active = False

    def draw(self, screen):
        gravity_surface = pygame.Surface((self.gravity_radius * 2, self.gravity_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(gravity_surface, (50, 0, 80, 80), (self.gravity_radius, self.gravity_radius), self.gravity_radius)
        screen.blit(gravity_surface, (self.x - self.gravity_radius, self.y - self.gravity_radius))
        
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.radius)

    def attract(self, obj):
        dx = self.x - obj.x
        dy = self.y - obj.y
        dist = math.hypot(dx, dy)

        if self.radius < dist < self.gravity_radius:
            pull_force = self.strength / (dist * 2)
            obj.x += pull_force * (dx / dist)
            obj.y += pull_force * (dy / dist)

# --- Nebula Event Class ---
class NebulaEvent:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.total_duration = 600 
        self.duration = self.total_duration
        self.fade_duration = 120
        self.active = True
        self.max_fog_alpha = 250
        
        self.fog_texture = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.fog_texture.fill((*FOG_COLOR, 245)) 
        
        cloud_brush = self._generate_gradient_brush(300, (30, 0, 40), 100) 
        for _ in range(25):
            x = random.randint(-100, self.screen_width)
            y = random.randint(-100, self.screen_height)
            self.fog_texture.blit(cloud_brush, (x, y))

        self.visibility_radius = 280 
        self.light_mask = pygame.Surface((self.visibility_radius * 2, self.visibility_radius * 2), pygame.SRCALPHA)
        
        self.main_brush = self._generate_gradient_brush(int(self.visibility_radius * 0.7), (0,0,0), 255)
        self.edge_brush_large = self._generate_gradient_brush(100, (0,0,0), 180)
        self.edge_brush_small = self._generate_gradient_brush(60, (0,0,0), 120)

        self.blobs = []
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(self.visibility_radius * 0.3, self.visibility_radius * 0.6)
            speed = random.uniform(0.02, 0.05) * random.choice([-1, 1])
            self.blobs.append([angle, dist, speed, random.uniform(0, 2 * math.pi)])

    def _generate_gradient_brush(self, radius, color, max_alpha):
        """Generates a surface with a radial gradient."""
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        step = 2
        for r in range(radius, 0, -step):
            alpha = int(max_alpha * ((1 - (r / radius)) ** 2))
            pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
        return surf

    def update(self):
        self.duration -= 1
        if self.duration <= 0:
            self.active = False

    def draw(self, screen, player_pos):
        time_elapsed = self.total_duration - self.duration
        fade_factor = 1.0
        
        if time_elapsed < self.fade_duration:
            fade_factor = time_elapsed / self.fade_duration
        elif self.duration < self.fade_duration:
            fade_factor = self.duration / self.fade_duration
            
        if fade_factor <= 0: return

        fog_layer = self.fog_texture.copy()
        
        if fade_factor < 1.0:
            fade_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(255 * (1-fade_factor)))) 
            fog_layer.blit(fade_surf, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

        self.light_mask.fill((0,0,0,0))
        cw, ch = self.visibility_radius, self.visibility_radius

        self.light_mask.blit(self.main_brush, (cw - self.main_brush.get_width()//2, ch - self.main_brush.get_height()//2))

        time_val = pygame.time.get_ticks() * 0.005
        
        for i, blob in enumerate(self.blobs):
            blob[0] += blob[2] 
            wobble = math.sin(time_val + blob[3]) * 20
            bx = cw + math.cos(blob[0]) * (blob[1] + wobble)
            by = ch + math.sin(blob[0]) * (blob[1] + wobble)
            
            if i % 2 == 0:
                self.light_mask.blit(self.edge_brush_large, (int(bx) - 50, int(by) - 50))
            else:
                self.light_mask.blit(self.edge_brush_small, (int(bx) - 30, int(by) - 30))

        dest_x = player_pos[0] - self.visibility_radius
        dest_y = player_pos[1] - self.visibility_radius
        
        fog_layer.blit(self.light_mask, (dest_x, dest_y), special_flags=pygame.BLEND_RGBA_SUB)
        
        for _ in range(5):
            line_y = random.randint(0, self.screen_height)
            line_h = random.randint(1, 4)
            pygame.draw.rect(fog_layer, (50, 255, 100, 80), (0, line_y, self.screen_width, line_h))
            
            rx = random.randint(0, self.screen_width)
            ry = random.randint(0, self.screen_height)
            rw = random.randint(20, 100)
            rh = random.randint(2, 10)
            pygame.draw.rect(fog_layer, (200, 255, 200, 60), (rx, ry, rw, rh))
            
        screen.blit(fog_layer, (0, 0))


# --- Main Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.clock = pygame.time.Clock()

        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT
        self.FULLSCREEN = FULLSCREEN
        self.FPS = FPS

        flags = (pygame.FULLSCREEN | pygame.SCALED) if self.FULLSCREEN else 0
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Tristar Mania")

        self.font = pygame.font.Font(None, 74)
        self.menu_font = pygame.font.Font(None, 60)
        self.small_font = pygame.font.Font(None, 40)
        self.score_font = pygame.font.Font(None, 50)
        self.life_font = pygame.font.Font(None, 50)
        self.leaderboard_font = pygame.font.Font(None, 45)
        self.speech_font = pygame.font.Font(None, 36)

        self.stars = [Star(self.SCREEN_WIDTH, self.SCREEN_HEIGHT) for _ in range(300)]
        self.parallax_stars = [ParallaxStar(self.SCREEN_WIDTH, self.SCREEN_HEIGHT) for _ in range(150)] 
        self.high_scores = [] # stores tuples: (name, score, level)
        self.volume = 0.5
        
        self.resolutions = [(1280, 720), (1600, 900), (1920, 1080), (3840, 2160)]
        self.current_resolution_index = 2
        
        self.keybinds = {
            "Move Up": pygame.K_w,
            "Move Down": pygame.K_s,
            "Move Left": pygame.K_a,
            "Move Right": pygame.K_d,
            "Shoot": pygame.K_SPACE 
        }
        self.remapping_key_for = None
        
        self.explosions = []
        self.music_is_playing = False 
        
        # Variables for the head animation
        self.head_blink_timer = 0
        self.head_blink_duration = 0.12 
        self.head_next_blink = time.time() + random.uniform(3, 8)
        self.head_is_blinking = False

        # --- Sound Effects ---
        laser_sound_list = [int(20000 * sinc(2 * math.pi * 440 * i / SAMPLE_RATE)) for i in range(SAMPLE_RATE // 10)]
        menu_click_sound_list = [int(15000 * math.sin(2 * math.pi * 880 * i / SAMPLE_RATE)) for i in range(SAMPLE_RATE // 20)]
        explosion_sound_list = [int(random.uniform(-1, 1) * 20000 * (1 - i / (SAMPLE_RATE // 4))) for i in range(SAMPLE_RATE // 4)]
        
        level_up_sound_list = []
        duration_samples = SAMPLE_RATE // 3
        for i in range(duration_samples):
            start_freq = 523.25
            end_freq = 1046.50
            current_freq = start_freq + (end_freq - start_freq) * (i / duration_samples)
            amplitude = 18000 * (1 - (i / duration_samples))
            sample = amplitude * math.sin(2 * math.pi * current_freq * i / SAMPLE_RATE)
            level_up_sound_list.append(int(sample))
        
        harvest_sound_list = []
        duration_samples = int(SAMPLE_RATE * 0.1) 
        for i in range(duration_samples):
            freq = 1500 + 500 * (i / duration_samples) 
            amplitude = 10000 * math.sin(math.pi * (i / duration_samples)) 
            sample = amplitude * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
            harvest_sound_list.append(int(sample))
        
        hurt_sound_list = []
        duration_samples = int(SAMPLE_RATE * 0.4) 
        frequency = 150 
        amplitude_envelope = 1.0 
        for i in range(duration_samples):
            amplitude_envelope = max(0, 1 - (i / duration_samples))
            sample = 15000 * amplitude_envelope * math.sin(2 * math.pi * frequency * i / SAMPLE_RATE)
            hurt_sound_list.append(int(sample))

        laser_sound_1d = np.array(laser_sound_list, dtype=np.int16)
        menu_click_sound_1d = np.array(menu_click_sound_list, dtype=np.int16)
        explosion_sound_1d = np.array(explosion_sound_list, dtype=np.int16)
        level_up_sound_1d = np.array(level_up_sound_list, dtype=np.int16)
        harvest_sound_1d = np.array(harvest_sound_list, dtype=np.int16)
        hurt_sound_1d = np.array(hurt_sound_list, dtype=np.int16)

        laser_sound_data = np.column_stack((laser_sound_1d, laser_sound_1d))
        menu_click_sound_data = np.column_stack((menu_click_sound_1d, menu_click_sound_1d))
        explosion_sound_data = np.column_stack((explosion_sound_1d, explosion_sound_1d))
        level_up_sound_data = np.column_stack((level_up_sound_1d, level_up_sound_1d))
        harvest_sound_data = np.column_stack((harvest_sound_1d, harvest_sound_1d))
        hurt_sound_data = np.column_stack((hurt_sound_1d, hurt_sound_1d))
        
        self.laser_sound = pygame.mixer.Sound(pygame.sndarray.make_sound(laser_sound_data))
        self.explosion_sound = pygame.mixer.Sound(pygame.sndarray.make_sound(explosion_sound_data))
        self.menu_click_sound = pygame.mixer.Sound(pygame.sndarray.make_sound(menu_click_sound_data))
        self.level_up_sound = pygame.mixer.Sound(pygame.sndarray.make_sound(level_up_sound_data))
        self.harvest_sound = pygame.mixer.Sound(pygame.sndarray.make_sound(harvest_sound_data))
        self.hurt_sound = pygame.mixer.Sound(pygame.sndarray.make_sound(hurt_sound_data))

        note_duration = int(SAMPLE_RATE * 0.5) 
        frequencies = [65.41, 49.00, 58.27, 43.65] 
        music_sound_list = []
        for freq in frequencies:
            for i in range(note_duration):
                amplitude = 12000 * (1 - (i / note_duration)) 
                sample = amplitude * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
                music_sound_list.append(int(sample))
        music_sound_1d = np.array(music_sound_list, dtype=np.int16)
        music_sound_data = np.column_stack((music_sound_1d, music_sound_1d))
        self.background_music = pygame.mixer.Sound(pygame.sndarray.make_sound(music_sound_data))

        self.all_sounds = [self.laser_sound, self.explosion_sound, self.menu_click_sound, self.level_up_sound, self.harvest_sound, self.hurt_sound, self.background_music]
        self.update_volumes()

    def play_background_music(self):
        if not self.music_is_playing:
            self.background_music.play(loops=-1)
            self.music_is_playing = True

    def stop_background_music(self):
        self.background_music.stop()
        self.music_is_playing = False

    def update_volumes(self):
        for sound in self.all_sounds:
            sound.set_volume(self.volume)

    def draw_text(self, text, font, color, surface, x, y, center=True):
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        if center:
            textrect.center = (x, y)
        else:
            textrect.x = x
            textrect.y = y
        surface.blit(textobj, textrect)
        return textobj, textrect

    def draw_lifebar(self, current_lives, max_lives, surface):
        bar_width = 30
        bar_height = 15
        bar_spacing = 10
        
        start_x = 15
        start_y = 15
        
        current_color = LIFE_COLOR
        if current_lives == 1:
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                current_color = WHITE
        
        for i in range(max_lives):
            bar_rect = pygame.Rect(start_x + i * (bar_width + bar_spacing), start_y, bar_width, bar_height)
            color = current_color if i < current_lives else DARK_BLUE
            pygame.draw.rect(surface, color, bar_rect)
            pygame.draw.rect(surface, WHITE, bar_rect, 2) 

    def animate_background(self, surface, player_dx=0, player_dy=0):
        surface.fill(DARK_BLUE)
        for p_star in self.parallax_stars:
            p_star.update(player_dx, player_dy)
            p_star.draw(surface)
        for star in self.stars:
            star.update()
            star.draw(surface)
            
    def draw_pause_symbol(self):
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        bar_width = 30
        bar_height = 100
        spacing = 20
        total_width = (bar_width * 2) + spacing
        center_x = self.SCREEN_WIDTH // 2
        center_y = self.SCREEN_HEIGHT // 2
        left_bar_rect = pygame.Rect(center_x - total_width // 2, center_y - bar_height // 2, bar_width, bar_height)
        right_bar_rect = pygame.Rect(center_x - total_width // 2 + bar_width + spacing, center_y - bar_height // 2, bar_width, bar_height)
        pygame.draw.rect(self.screen, WHITE, left_bar_rect)
        pygame.draw.rect(self.screen, WHITE, right_bar_rect)
        
    def draw_pause_menu(self, event):
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        menu_items = ["Resume", "Save Game", "Load Game", "Exit to Menu"]
        item_spacing = 80
        start_y = self.SCREEN_HEIGHT // 2
        exit_game = False
        resume_game = False
        load_game = False
        save_game = False 
        for i, item in enumerate(menu_items):
            x = self.SCREEN_WIDTH // 2
            y = start_y + i * item_spacing
            text_surface = self.menu_font.render(item, True, MENU_TEXT_COLOR)
            text_rect = text_surface.get_rect(center=(x, y))
            if text_rect.collidepoint(pygame.mouse.get_pos()):
                text_surface = self.menu_font.render(item, True, HOVER_TEXT_COLOR)
                if event and event.type == pygame.MOUSEBUTTONDOWN:
                    self.menu_click_sound.play()
                    if item == "Resume": resume_game = True
                    elif item == "Save Game": save_game = True
                    elif item == "Load Game": load_game = True
                    elif item == "Exit to Menu": exit_game = True
            self.screen.blit(text_surface, text_rect)
        return resume_game, load_game, exit_game, save_game
    
    # --- Cyberpunk Head Logic ---
    def draw_head(self, surface, center_x, center_y, mouse_pos, talking_active):
        """Draws a cybernetic/scifi head with a visor and implants."""
        current_time = time.time()

        # 1. Neck (Mechanical/Cables)
        pygame.draw.rect(surface, CYBER_DARK_METAL, (center_x - 30, center_y + 100, 60, 120))
        # Draw some cable lines on the neck
        for i in range(3):
            lx = center_x - 15 + i*15
            pygame.draw.line(surface, CYBER_METAL, (lx, center_y+100), (lx, center_y+160), 4)

        # 2. Face Shape (Base - Pale/Metallic)
        face_rect = pygame.Rect(center_x - 105, center_y - 130, 210, 280)
        pygame.draw.ellipse(surface, CYBER_SKIN_SHADOW, face_rect.inflate(4,4))
        pygame.draw.ellipse(surface, CYBER_SKIN_COLOR, face_rect)

        # 3. Headset / Cybernetic Ears
        pygame.draw.rect(surface, CYBER_DARK_METAL, (center_x - 130, center_y - 40, 40, 80), border_radius=10) # Left
        pygame.draw.rect(surface, CYBER_DARK_METAL, (center_x + 90, center_y - 40, 40, 80), border_radius=10)  # Right
        # Antenna
        pygame.draw.line(surface, CYBER_METAL, (center_x + 110, center_y - 40), (center_x + 110, center_y - 100), 2)
        if int(current_time * 2) % 2 == 0: # Blink light on antenna
            pygame.draw.circle(surface, CYBER_ACCENT, (center_x + 110, center_y - 100), 3)

        # 4. Tech Helmet / Hair
        pygame.draw.ellipse(surface, CYBER_DARK_METAL, (center_x - 110, center_y - 150, 220, 160)) 
        # Redraw Face lower half to keep jaw shape
        pygame.draw.arc(surface, CYBER_SKIN_COLOR, face_rect, math.pi, 2*math.pi, 100)
        # Helmet visor rim
        pygame.draw.arc(surface, CYBER_METAL, (center_x - 105, center_y - 150, 210, 150), 0, math.pi, 10)

        # 5. Eyes and Implants calculation
        # Handle Blinking logic
        if not self.head_is_blinking and current_time > self.head_next_blink:
            self.head_is_blinking = True
            self.head_next_blink = current_time + self.head_blink_duration
        elif self.head_is_blinking and current_time > self.head_next_blink:
            self.head_is_blinking = False
            self.head_next_blink = current_time + random.uniform(3, 8)

        eye_y = center_y - 30
        left_eye_x = center_x - 50
        right_eye_x = center_x + 50
        eye_radius = 18 
        
        # Calculate Pupil Look Direction
        mx, my = mouse_pos
        dx = (mx - center_x) / (self.SCREEN_WIDTH / 2) * 5
        dy = (my - center_y) / (self.SCREEN_HEIGHT / 2) * 5
        dx = max(-5, min(5, dx))
        dy = max(-5, min(5, dy))

        # --- RIGHT EYE: NORMAL CYBERNETIC (Blue) ---
        if self.head_is_blinking:
             pygame.draw.line(surface, CYBER_SKIN_SHADOW, (right_eye_x - 20, eye_y), (right_eye_x + 20, eye_y), 4)
        else:
            pygame.draw.circle(surface, (200, 220, 230), (right_eye_x, eye_y), eye_radius)
            pygame.draw.circle(surface, CYBER_ACCENT, (right_eye_x + int(dx), eye_y + int(dy)), 7)
            
        # --- LEFT EYE: TACTICAL VISOR / IMPLANT (Red) ---
        # Draw a metal housing around the left eye area
        pygame.draw.rect(surface, CYBER_METAL, (left_eye_x - 25, eye_y - 20, 50, 40), border_radius=5)
        # Glowing Red Lens
        pygame.draw.circle(surface, CYBER_EYE_RED, (left_eye_x, eye_y), 12)
        # Lens Reflection
        pygame.draw.circle(surface, (255, 150, 150), (left_eye_x - 4, eye_y - 4), 3)
        # Scanning Line in Visor
        scan_y = eye_y - 10 + (int(current_time * 20) % 20)
        pygame.draw.line(surface, (255, 100, 100), (left_eye_x - 10, scan_y), (left_eye_x + 10, scan_y), 1)

        # 6. Face Details / Lines
        # Circuit lines on cheeks
        pygame.draw.line(surface, CYBER_SKIN_SHADOW, (center_x + 60, center_y + 30), (center_x + 90, center_y + 20), 2)
        pygame.draw.line(surface, CYBER_SKIN_SHADOW, (center_x + 60, center_y + 40), (center_x + 85, center_y + 35), 2)
        
        # 7. Mouth (Robotic/Stern)
        if talking_active:
             mouth_open_amount = (math.sin(current_time * 15) + 1) * 2
        else:
             mouth_open_amount = 0
             
        mouth_y = center_y + 65
        pygame.draw.rect(surface, (50, 40, 40), (center_x - 20, mouth_y, 40, 4 + mouth_open_amount))
        # Jaw lines vertical
        pygame.draw.line(surface, CYBER_SKIN_SHADOW, (center_x - 20, mouth_y + 15), (center_x - 20, mouth_y + 40), 2)
        pygame.draw.line(surface, CYBER_SKIN_SHADOW, (center_x + 20, mouth_y + 15), (center_x + 20, mouth_y + 40), 2)


    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            w, _ = font.size(test_line)
            if w < max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        return lines

    def briefing_screen(self):
        full_text = "Welcome, pilot. You are assigned to protect this sector. Avoid hitting any green tristars travelling in your sector, traffic is going to increase rapidly. If you need to power up, find some asteroids nearby & shoot them. Good luck!"
        
        # HUD Layout
        bubble_w = 700
        bubble_h = 350
        bubble_x = self.SCREEN_WIDTH // 2 - bubble_w // 2 + 100
        bubble_y = self.SCREEN_HEIGHT // 2 - 200
        
        head_x = 300
        head_y = self.SCREEN_HEIGHT - 300
        
        text_char_index = 0
        last_char_time = pygame.time.get_ticks()
        char_delay = 40 # ms per char
        
        running = True
        skip_text = False
        
        # Create a transparent surface for the HUD
        hud_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)

        while running:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    if text_char_index < len(full_text):
                        text_char_index = len(full_text)
                        skip_text = True
                    else:
                        running = False
            
            # Update Text typewriter effect
            if not skip_text and text_char_index < len(full_text):
                if current_time - last_char_time > char_delay:
                    text_char_index += 1
                    last_char_time = current_time
            
            self.animate_background(self.screen)
            
            # --- Draw HUD Panel ---
            hud_surface.fill((0,0,0,0)) # Clear
            
            # Main HUD Background (Organic/Tech shape)
            hud_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
            pygame.draw.rect(hud_surface, HUD_BG_COLOR, hud_rect, border_radius=15)
            
            # Tech Borders (Corners only)
            corner_len = 30
            # Top Left
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x, bubble_y), (bubble_x + corner_len, bubble_y), 3)
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x, bubble_y), (bubble_x, bubble_y + corner_len), 3)
            # Top Right
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x + bubble_w, bubble_y), (bubble_x + bubble_w - corner_len, bubble_y), 3)
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x + bubble_w, bubble_y), (bubble_x + bubble_w, bubble_y + corner_len), 3)
            # Bottom Left
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x, bubble_y + bubble_h), (bubble_x + corner_len, bubble_y + bubble_h), 3)
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x, bubble_y + bubble_h), (bubble_x, bubble_y + bubble_h - corner_len), 3)
            # Bottom Right
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x + bubble_w, bubble_y + bubble_h), (bubble_x + bubble_w - corner_len, bubble_y + bubble_h), 3)
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, (bubble_x + bubble_w, bubble_y + bubble_h), (bubble_x + bubble_w, bubble_y + bubble_h - corner_len), 3)
            
            # Scanlines
            for y in range(bubble_y, bubble_y + bubble_h, 4):
                pygame.draw.line(hud_surface, (0, 200, 255, 20), (bubble_x, y), (bubble_x + bubble_w, y), 1)
            
            # Connection Line (Transmission signal)
            start_pos = (head_x + 50, head_y - 120)
            mid_pos = (bubble_x - 30, bubble_y + bubble_h // 2)
            end_pos = (bubble_x, bubble_y + bubble_h // 2)
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, start_pos, mid_pos, 2)
            pygame.draw.line(hud_surface, HUD_BORDER_COLOR, mid_pos, end_pos, 2)
            pygame.draw.circle(hud_surface, HUD_BORDER_COLOR, start_pos, 4)
            
            # Blit HUD surface
            self.screen.blit(hud_surface, (0,0))

            # Draw Head
            is_talking = text_char_index < len(full_text)
            self.draw_head(self.screen, head_x, head_y, mouse_pos, is_talking)
            
            # Render Text
            current_visible_text = full_text[:text_char_index]
            lines = self.wrap_text(current_visible_text, self.speech_font, bubble_w - 60)
            
            for i, line in enumerate(lines):
                text_surf = self.speech_font.render(line, True, HUD_TEXT_COLOR)
                # Add a slight shadow/glow to text
                shadow_surf = self.speech_font.render(line, True, (0, 50, 50))
                self.screen.blit(shadow_surf, (bubble_x + 32, bubble_y + 32 + i * 40))
                self.screen.blit(text_surf, (bubble_x + 30, bubble_y + 30 + i * 40))
            
            # Draw "Click to continue" prompt if finished
            if text_char_index >= len(full_text):
                 if (current_time // 500) % 2 == 0:
                     prompt_surf = self.small_font.render("Click to continue...", True, CYBER_ACCENT)
                     self.screen.blit(prompt_surf, (bubble_x + bubble_w - 280, bubble_y + bubble_h - 40))

            pygame.display.flip()
            self.clock.tick(self.FPS)

    def title_screen(self):
        title_text = "Tristar Mania"
        fade_alpha = 0
        running = True
        start_time = pygame.time.get_ticks()
        while running:
            if running and (pygame.time.get_ticks() - start_time > 3000):
                self.menu_click_sound.play()
                running = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self.menu_click_sound.play()
                    running = False
                    break 
            self.animate_background(self.screen)
            self.draw_text(title_text, self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)
            if fade_alpha < 255: fade_alpha += 5
            fade_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
            fade_surface.fill(DARK_BLUE)
            fade_surface.set_alpha(255 - fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def video_settings_menu(self):
        pygame.mouse.set_visible(True) 
        video_items = ["Fullscreen: ", "Resolution: ", "Back"]
        item_spacing = 100
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if fullscreen_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.FULLSCREEN = not self.FULLSCREEN
                        flags = (pygame.FULLSCREEN | pygame.SCALED) if self.FULLSCREEN else 0
                        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), flags)
                    elif resolution_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.current_resolution_index = (self.current_resolution_index + 1) % len(self.resolutions)
                        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = self.resolutions[self.current_resolution_index]
                        flags = (pygame.FULLSCREEN | pygame.SCALED) if self.FULLSCREEN else 0
                        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), flags)
                        self.stars = [Star(self.SCREEN_WIDTH, self.SCREEN_HEIGHT) for _ in range(300)]
                        self.parallax_stars = [ParallaxStar(self.SCREEN_WIDTH, self.SCREEN_HEIGHT) for _ in range(150)]
                    elif back_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        running = False
            self.animate_background(self.screen)
            start_y = self.SCREEN_HEIGHT // 2 - (len(video_items) * item_spacing) // 2
            self.draw_text("Video Settings", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, start_y - 100)
            fullscreen_text = f"Fullscreen: {'ON' if self.FULLSCREEN else 'OFF'}"
            _, fullscreen_rect = self.draw_and_get_rect(fullscreen_text, self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y)
            current_res = f"{self.resolutions[self.current_resolution_index][0]}x{self.resolutions[self.current_resolution_index][1]}"
            resolution_text = f"Resolution: {current_res}"
            _, resolution_rect = self.draw_and_get_rect(resolution_text, self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + item_spacing)
            _, back_rect = self.draw_and_get_rect("Back", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + 2 * item_spacing)
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def draw_and_get_rect(self, text, font, color, hover_color, x, y):
        mx, my = pygame.mouse.get_pos()
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        if text_rect.collidepoint((mx, my)):
            text_surface = font.render(text, True, hover_color)
        self.screen.blit(text_surface, text_rect)
        return text_surface, text_rect

    def audio_settings_menu(self):
        pygame.mouse.set_visible(True) 
        item_spacing = 100
        start_y = self.SCREEN_HEIGHT // 2 - (2 * item_spacing) // 2
        slider_x = self.SCREEN_WIDTH // 2 - 150
        slider_y = start_y
        slider_width = 300
        slider_height = 20
        handle_width = 20
        running = True
        dragging_slider = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if handle_rect.collidepoint(event.pos):
                        dragging_slider = True
                    if back_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        running = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragging_slider:
                        self.menu_click_sound.play() 
                        dragging_slider = False
                elif event.type == pygame.MOUSEMOTION and dragging_slider:
                    mouse_x, _ = event.pos
                    new_volume = (mouse_x - slider_x) / slider_width
                    self.volume = max(0, min(1, new_volume))
                    self.update_volumes()
            self.animate_background(self.screen)
            self.draw_text("Audio Settings", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, start_y - 100)
            slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
            pygame.draw.rect(self.screen, SLIDER_BG_COLOR, slider_rect, border_radius=5)
            handle_x = slider_x + self.volume * slider_width - handle_width / 2
            handle_rect = pygame.Rect(handle_x, slider_y - 5, handle_width, slider_height + 10)
            pygame.draw.rect(self.screen, SLIDER_HANDLE_COLOR, handle_rect, border_radius=5)
            self.draw_text(f"Volume: {int(self.volume * 100)}%", self.small_font, WHITE, self.screen, slider_x + slider_width + 100, slider_y + 10)
            _, back_rect = self.draw_and_get_rect("Back", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + item_spacing)
            pygame.display.flip()
            self.clock.tick(self.FPS)
            
    def controls_settings_menu(self):
        pygame.mouse.set_visible(True) 
        item_spacing = 100
        running = True
        while running:
            self.animate_background(self.screen)
            start_y = self.SCREEN_HEIGHT // 2 - (len(self.keybinds) * item_spacing) // 2
            self.draw_text("Controls Settings", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, start_y - 100)
            control_rects = {}
            for i, (action, key) in enumerate(self.keybinds.items()):
                key_name = pygame.key.name(key).upper()
                if key == pygame.K_SPACE:
                    key_name = "SPACEBAR"
                text = f"{action}: {key_name}"
                _, rect = self.draw_and_get_rect(text, self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + i * item_spacing)
                control_rects[action] = rect
            _, back_rect = self.draw_and_get_rect("Back", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + len(self.keybinds) * item_spacing)
            if self.remapping_key_for:
                self.draw_text("Press any key...", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)
            pygame.display.flip()
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.remapping_key_for:
                    if event.type == pygame.KEYDOWN:
                        self.menu_click_sound.play()
                        self.keybinds[self.remapping_key_for] = event.key
                        self.remapping_key_for = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if back_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        running = False
                    else:
                        for action, rect in control_rects.items():
                            if rect.collidepoint(event.pos):
                                self.menu_click_sound.play()
                                self.remapping_key_for = action
                                break
    def options_menu(self):
        options_items = ["Video", "Audio", "Controls", "Back"]
        item_spacing = 100
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if video_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.video_settings_menu()
                    elif audio_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.audio_settings_menu()
                    elif controls_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.controls_settings_menu()
                    elif back_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        running = False
            self.animate_background(self.screen)
            start_y = self.SCREEN_HEIGHT // 2 - (len(options_items) * item_spacing) // 2
            self.draw_text("Options", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, start_y - 100)
            _, video_rect = self.draw_and_get_rect("Video", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y)
            _, audio_rect = self.draw_and_get_rect("Audio", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + item_spacing)
            _, controls_rect = self.draw_and_get_rect("Controls", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + 2 * item_spacing)
            _, back_rect = self.draw_and_get_rect("Back", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, start_y + 3 * item_spacing)
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def load_game_menu(self):
        pygame.mouse.set_visible(True)
        input_code = ""
        running = True
        while running:
            self.animate_background(self.screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        input_code = input_code[:-1]
                    elif event.key == pygame.K_RETURN:
                        if len(input_code) == 4:
                            level = self.code_to_level(input_code)
                            self.menu_click_sound.play()
                            self.start_game_animation(start_level=level)
                            return 
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        if len(input_code) < 4 and event.unicode.upper() in LETTER_MAPPING:
                             input_code += event.unicode.upper()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        return
                    if start_rect.collidepoint(event.pos) and len(input_code) == 4:
                         level = self.code_to_level(input_code)
                         self.menu_click_sound.play()
                         self.start_game_animation(start_level=level)
                         return
            self.draw_text("LOAD GAME", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 150)
            self.draw_text("Enter 4-Letter Code:", self.menu_font, MENU_TEXT_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50)
            box_width = 300
            box_height = 80
            box_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - box_width // 2, self.SCREEN_HEIGHT // 2 + 50 - box_height // 2, box_width, box_height)
            pygame.draw.rect(self.screen, SLIDER_BG_COLOR, box_rect)
            pygame.draw.rect(self.screen, WHITE, box_rect, 2) 
            self.draw_text(input_code, self.font, LIGHT_BLUE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50)
            if len(input_code) == 4:
                 _, start_rect = self.draw_and_get_rect("START", self.menu_font, NEUTRAL_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 150)
            else:
                 start_rect = pygame.Rect(0,0,0,0) 
            _, back_rect = self.draw_and_get_rect("Back", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 100)
            pygame.display.flip()
            self.clock.tick(self.FPS)
            
    def main_menu(self):
        pygame.mouse.set_visible(True) 
        menu_items = ["New Game", "Load Game", "Leaderboards", "Options", "Exit"]
        item_spacing = 100
        running = True
        while running:
            self.play_background_music() 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if new_game_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.start_game_animation()
                    elif load_game_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.load_game_menu()
                    elif leaderboard_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.leaderboard_menu()
                    elif options_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        self.options_menu()
                    elif exit_rect.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
            self.animate_background(self.screen)
            self.draw_text("Tristar Mania", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 250)
            self.draw_text("Main Menu", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 150)
            menu_start_y = self.SCREEN_HEIGHT // 2
            _, new_game_rect = self.draw_and_get_rect("New Game", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, menu_start_y)
            _, load_game_rect = self.draw_and_get_rect("Load Game", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, menu_start_y + item_spacing)
            _, leaderboard_rect = self.draw_and_get_rect("Leaderboards", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, menu_start_y + 2 * item_spacing)
            _, options_rect = self.draw_and_get_rect("Options", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, menu_start_y + 3 * item_spacing)
            _, exit_rect = self.draw_and_get_rect("Exit", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, menu_start_y + 4 * item_spacing)
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def leaderboard_menu(self):
        pygame.mouse.set_visible(True) 
        running = True
        while running:
            self.animate_background(self.screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_rect.collidepoint(event.pos):
                        self.menu_click_sound.play()
                        return 
            self.draw_text("LEADERBOARD", self.font, LIGHT_BLUE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 200)
            for i, entry in enumerate(self.high_scores):
                # Unpack tuple: name, score, level
                name, score, level = entry
                self.draw_text(f"{i + 1}. {name} - {score} (Lvl {level})", self.small_font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 100 + i * 40)
            _, back_rect = self.draw_and_get_rect("Back", self.menu_font, MENU_TEXT_COLOR, HOVER_TEXT_COLOR, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 100)
            pygame.display.flip()
            self.clock.tick(self.FPS)
    
    def level_to_code(self, level):
        offset = 100000 
        encoded_level = level + offset
        code_chars = []
        for _ in range(4):
            encoded_level, remainder = divmod(encoded_level, 26)
            code_chars.append(LETTER_MAPPING[remainder])
        return ''.join(reversed(code_chars))

    def code_to_level(self, code):
        offset = 100000
        if len(code) != 4:
            return 1 
        value = 0
        for char in code:
            if char not in LETTER_MAPPING:
                return 1 
            value = value * 26 + LETTER_MAPPING.index(char)
        decoded_level = value - offset
        return max(1, decoded_level)

    def save_game_screen(self, level):
        pygame.mouse.set_visible(True) 
        save_code = self.level_to_code(level)
        running = True
        while running:
            self.animate_background(self.screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.menu_click_sound.play()
                    return 
            self.draw_text("SAVE CODE", self.font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 150)
            self.draw_text(save_code, self.font, LIGHT_BLUE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)
            self.draw_text("Write this code down to load this level later.", self.small_font, MENU_TEXT_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 100)
            self.draw_text("Click to return to the menu", self.small_font, MENU_TEXT_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50)
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def enter_name_screen(self, score, level):
        pygame.mouse.set_visible(True)
        input_name = ""
        running = True
        while running:
            self.animate_background(self.screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        input_name = input_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        if len(input_name) > 0:
                            self.menu_click_sound.play()
                            # Save score here
                            self.high_scores.append((input_name, score, level))
                            # Sort by score (index 1), descending
                            self.high_scores.sort(key=lambda x: x[1], reverse=True)
                            self.high_scores = self.high_scores[:5]
                            self.game_over_screen(score, level)
                            return
                    elif event.key == pygame.K_ESCAPE:
                        # Save with default name if escaped
                        self.high_scores.append(("Player", score, level))
                        self.high_scores.sort(key=lambda x: x[1], reverse=True)
                        self.high_scores = self.high_scores[:5]
                        self.game_over_screen(score, level)
                        return
                    else:
                        if len(input_name) < 10 and event.unicode.isprintable():
                            input_name += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN:
                     if len(input_name) > 0:
                        self.menu_click_sound.play()
                        self.high_scores.append((input_name, score, level))
                        self.high_scores.sort(key=lambda x: x[1], reverse=True)
                        self.high_scores = self.high_scores[:5]
                        self.game_over_screen(score, level)
                        return

            self.draw_text("GAME OVER", self.font, ENEMY_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 150)
            self.draw_text("Enter Your Name:", self.menu_font, MENU_TEXT_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50)
            
            box_width = 400
            box_height = 80
            box_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - box_width // 2, self.SCREEN_HEIGHT // 2 + 50 - box_height // 2, box_width, box_height)
            pygame.draw.rect(self.screen, SLIDER_BG_COLOR, box_rect)
            pygame.draw.rect(self.screen, WHITE, box_rect, 2) 
            
            self.draw_text(input_name, self.font, LIGHT_BLUE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50)
            self.draw_text("Press Enter to Submit", self.small_font, MENU_TEXT_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 150)
            
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def game_over_screen(self, final_score, final_level):
        pygame.mouse.set_visible(True) 
        if final_score < 0: final_score = 0
        save_code = self.level_to_code(final_level)
        running = True
        while running:
            self.animate_background(self.screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.menu_click_sound.play()
                    return 
            self.draw_text("GAME OVER", self.font, ENEMY_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 200)
            self.draw_text(f"Your Score: {final_score}", self.menu_font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 130)
            self.draw_text(f"Level Reached: {final_level}", self.menu_font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 90)
            self.draw_text(f"Level Code: {save_code}", self.menu_font, LIGHT_BLUE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 30)
            self.draw_text("LEADERBOARD", self.leaderboard_font, LIGHT_BLUE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 10)
            for i, entry in enumerate(self.high_scores):
                name, score, level = entry
                self.draw_text(f"{i + 1}. {name} - {score} (Lvl {level})", self.small_font, WHITE, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 60 + i * 40)
            self.draw_text("Click to return to menu", self.small_font, MENU_TEXT_COLOR, self.screen, self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50)
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def take_screenshot(self):
        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
        save_dir = os.path.join(pictures_dir, "TristarMania")
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except OSError:
                save_dir = "."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        full_path = os.path.join(save_dir, filename)
        pygame.image.save(self.screen, full_path)
        print(f"Screenshot saved to: {full_path}")

    def start_game_animation(self, start_level=1):
        self.stop_background_music() 
        display_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        spaceship = Spaceship(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        is_paused = False
        frame_counter = 0
        level = start_level
        score = int((start_level - 1) * (600 + 100 * start_level)) if start_level > 1 else 0
        score_for_next_level = int(level * (600 + 100 * level))
        initial_lives = 4 + (start_level - 1)
        lives = initial_lives
        max_lives = initial_lives
        boss_spawned_this_level = False 
        rocks = []
        enemies = []
        neutrals = []
        bosses = [] 
        player_lasers = []
        enemy_lasers = []
        harvest_particles = []
        black_hole = None
        black_hole_timer = random.randint(20 * self.FPS, 40 * self.FPS)
        nebula = None
        nebula_timer = random.randint(60 * self.FPS, 120 * self.FPS) 
        shake_offset = [0, 0]
        shake_timer = 0
        level_up_timer = 0
        
        pygame.mouse.set_visible(False) 
        while spaceship.y > self.SCREEN_HEIGHT / 3:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            angle_rad = math.radians(spaceship.direction)
            rear_x = spaceship.x - spaceship.size * math.cos(angle_rad)
            rear_y = spaceship.y - spaceship.size * math.sin(angle_rad)
            spaceship.trails.append(TrailParticle(rear_x, rear_y, spaceship.direction))
            for p in spaceship.trails:
                p.update()
            spaceship.trails = [p for p in spaceship.trails if p.alpha > 0 and p.size > 0]
            current_dy = -spaceship.max_velocity 
            self.animate_background(self.screen, player_dx=0, player_dy=current_dy)
            spaceship.y -= spaceship.max_velocity
            spaceship.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(self.FPS)
        
        running = True
        while running:
            event = None
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.menu_click_sound.play()
                        is_paused = not is_paused
                    if e.key == pygame.K_F12 or e.key == pygame.K_PRINTSCREEN:
                        self.take_screenshot()
                    if not is_paused and e.key == self.keybinds["Shoot"]:
                        self.laser_sound.play()
                        new_laser = Laser(spaceship.x, spaceship.y, spaceship.direction, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, level=level)
                        player_lasers.append(new_laser)
                event = e
            
            if not is_paused:
                pygame.mouse.set_visible(False)
                keys = pygame.key.get_pressed()
                if keys[self.keybinds["Move Up"]] or keys[pygame.K_UP]: spaceship.move_forward()
                elif keys[self.keybinds["Move Down"]] or keys[pygame.K_DOWN]: spaceship.move_backward()
                else: spaceship.stop()
                if keys[self.keybinds["Move Left"]] or keys[pygame.K_LEFT]: spaceship.rotate_left()
                if keys[self.keybinds["Move Right"]] or keys[pygame.K_RIGHT]: spaceship.rotate_right()
                
                black_hole_timer -= 1
                if not bosses and black_hole is None and black_hole_timer <= 0:
                    black_hole = BlackHole(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, level)
                    black_hole_timer = random.randint(30 * self.FPS, 60 * self.FPS)

                if black_hole:
                    black_hole.update()
                    if not black_hole.is_active: black_hole = None
                    else:
                        all_attractable_objects = [spaceship] + rocks + enemies + neutrals + bosses + player_lasers + enemy_lasers + harvest_particles
                        for obj in all_attractable_objects:
                            black_hole.attract(obj)

                if not nebula:
                    nebula_timer -= 1
                    if nebula_timer <= 0:
                        nebula = NebulaEvent(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
                        nebula_timer = random.randint(300 * self.FPS, 600 * self.FPS) 
                else:
                    nebula.update()
                    if not nebula.active: nebula = None

                spaceship.update()

                frame_counter += 1
                if frame_counter % SPAWN_RATE == 0:
                    obstacle_type = random.choice(["rock", "enemy", "neutral"])
                    if obstacle_type == "rock": rocks.append(SpaceRock(self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
                    elif obstacle_type == "enemy": enemies.append(EnemySpaceship(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, level))
                    elif obstacle_type == "neutral":
                        spawn_count = 1 + int(level / 2) 
                        for _ in range(spawn_count):
                            neutrals.append(NeutralSpaceship(self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
                
                if level >= 4 and not boss_spawned_this_level and not bosses:
                    num_bosses = 2 if level >= 8 else 1
                    for _ in range(num_bosses):
                        new_boss = Boss(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, level)
                        if num_bosses > 1:
                            new_boss.x = random.randint(100, self.SCREEN_WIDTH - 100)
                            new_boss.rect.centerx = int(new_boss.x)
                        bosses.append(new_boss)
                    boss_spawned_this_level = True

                for rock in rocks: rock.update()
                for enemy in enemies:
                    enemy.update((spaceship.x, spaceship.y), level)
                    if enemy.can_shoot(pygame.time.get_ticks(), level):
                        self.laser_sound.play()
                        enemy_lasers.append(enemy.shoot((spaceship.x, spaceship.y)))
                for neutral in neutrals: neutral.update()
                for boss in bosses:
                    boss.update((spaceship.x, spaceship.y))
                    if boss.can_shoot(pygame.time.get_ticks(), level):
                        self.laser_sound.play()
                        enemy_lasers.append(boss.shoot((spaceship.x, spaceship.y)))
                for laser in player_lasers: laser.update()
                for laser in enemy_lasers: laser.update()

                for explosion in self.explosions: explosion.update()
                self.explosions = [exp for exp in self.explosions if not exp.is_done]
                
                for particle in harvest_particles:
                    particle.update((spaceship.x, spaceship.y))
                harvest_particles = [p for p in harvest_particles if p.lifespan > 0]

            angle_rad = math.radians(spaceship.direction)
            p_dx = spaceship.velocity * math.cos(angle_rad)
            p_dy = spaceship.velocity * math.sin(angle_rad)
            self.animate_background(display_surface, p_dx, p_dy)
            
            if black_hole: black_hole.draw(display_surface)
            if not spaceship.invulnerable: spaceship.draw(display_surface)

            for rock in rocks: rock.draw(display_surface)
            for enemy in enemies: enemy.draw(display_surface)
            for neutral in neutrals: neutral.draw(display_surface)
            for boss in bosses: boss.draw(display_surface)
            for laser in player_lasers: laser.draw(display_surface)
            for laser in enemy_lasers: laser.draw(display_surface)
            for explosion in self.explosions: explosion.draw(display_surface)
            for particle in harvest_particles: particle.draw(display_surface)
            if spaceship.invulnerable: spaceship.draw(display_surface)
            if nebula: nebula.draw(display_surface, (spaceship.x, spaceship.y))

            if not is_paused:
                if black_hole:
                    collections_to_check = [rocks, enemies, neutrals, player_lasers, enemy_lasers, harvest_particles]
                    for collection in collections_to_check:
                        for item in collection[:]:
                            if math.hypot(item.x - black_hole.x, item.y - black_hole.y) < black_hole.radius:
                                self.explosions.append(Explosion(item.x, item.y, num_particles=5))
                                if item in collection: collection.remove(item)
                    if not spaceship.invulnerable and math.hypot(spaceship.x - black_hole.x, spaceship.y - black_hole.y) < black_hole.radius:
                        self.hurt_sound.play()
                        shake_timer = 20 
                        self.explosions.append(Explosion(spaceship.rect.centerx, spaceship.rect.centery, num_particles=50))
                        lives -= 1
                        if lives <= 0:
                            self.enter_name_screen(score, level)
                            return
                        else: spaceship.respawn()
                
                if not spaceship.invulnerable:
                    player_collided_physically = False
                    for rock in rocks[:]:
                        if spaceship.check_collision(rock.rect):
                            self.hurt_sound.play()
                            shake_timer = 20 
                            self.explosions.append(Explosion(rock.rect.centerx, rock.rect.centery))
                            lives -= 1
                            if rock in rocks: rocks.remove(rock)
                            player_collided_physically = True
                            break
                    if not player_collided_physically:
                        for enemy in enemies[:]:
                            if spaceship.check_collision(enemy.rect):
                                self.hurt_sound.play()
                                shake_timer = 20 
                                self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery))
                                lives -= 1
                                if enemy in enemies: enemies.remove(enemy)
                                player_collided_physically = True
                                break
                    if not player_collided_physically:
                        for boss in bosses[:]:
                            if spaceship.check_collision(boss.rect):
                                self.hurt_sound.play()
                                shake_timer = 30 
                                self.explosions.append(Explosion(spaceship.rect.centerx, spaceship.rect.centery, num_particles=50))
                                lives -= 2  
                                player_collided_physically = True
                                break 
                    if player_collided_physically:
                        if lives <= 0:
                            self.enter_name_screen(score, level)
                            return
                        else: spaceship.respawn()
                    
                    if not spaceship.invulnerable:
                        for laser in enemy_lasers[:]:
                            if spaceship.check_collision(laser.rect):
                                self.hurt_sound.play()
                                shake_timer = 20
                                self.explosions.append(Explosion(laser.rect.centerx, laser.rect.centery))
                                lives -= 1
                                if laser in enemy_lasers: enemy_lasers.remove(laser)
                                if lives <= 0:
                                    self.enter_name_screen(score, level)
                                    return
                                break 

                for p_laser in player_lasers[:]:
                    hit_laser = False
                    for e_laser in enemy_lasers[:]:
                        if p_laser.rect.colliderect(e_laser.rect):
                            self.explosions.append(Explosion((p_laser.x + e_laser.x)/2, (p_laser.y + e_laser.y)/2, num_particles=10))
                            if e_laser in enemy_lasers: enemy_lasers.remove(e_laser)
                            hit_laser = True
                            break 
                    if hit_laser:
                        if p_laser in player_lasers: player_lasers.remove(p_laser)
                        continue 

                for laser in player_lasers[:]:
                    collided = False
                    for rock in rocks[:]:
                        if laser.rect.colliderect(rock.rect):
                            self.explosion_sound.play()
                            self.explosions.append(Explosion(rock.rect.centerx, rock.rect.centery))
                            score += rock.score_value
                            if laser in player_lasers: player_lasers.remove(laser)
                            if rock in rocks: rocks.remove(rock)
                            if rock.is_life_rock:
                                self.harvest_sound.play()
                                for _ in range(10): harvest_particles.append(HarvestParticle(rock.rect.centerx, rock.rect.centery))
                            if lives < max_lives: lives += 1
                            collided = True
                            break
                    if collided: continue
                    for enemy in enemies[:]:
                        if laser.rect.colliderect(enemy.rect):
                            self.explosion_sound.play()
                            self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery))
                            score += enemy.score_value
                            if laser in player_lasers: player_lasers.remove(laser)
                            if enemy in enemies: enemies.remove(enemy)
                            collided = True
                            break
                    if collided: continue
                    for neutral in neutrals[:]:
                        if laser.rect.colliderect(neutral.rect):
                            self.explosion_sound.play()
                            shake_timer = 20 
                            self.explosions.append(Explosion(neutral.rect.centerx, neutral.rect.centery))
                            if laser in player_lasers: player_lasers.remove(laser)
                            if neutral in neutrals: neutrals.remove(neutral)
                            self.hurt_sound.play()
                            lives -= 1
                            if lives <= 0:
                                self.enter_name_screen(score, level)
                                return
                            collided = True 
                            break
                    if collided: continue
                    for boss in bosses[:]:
                        if laser.rect.colliderect(boss.rect):
                            self.explosions.append(Explosion(laser.x, laser.y, num_particles=15))
                            if laser in player_lasers: player_lasers.remove(laser)
                            boss.take_damage(1)
                            if boss.is_destroyed:
                                self.explosion_sound.play()
                                shake_timer = 30 
                                self.explosions.append(Explosion(boss.rect.centerx, boss.rect.centery, num_particles=100))
                                score += boss.score_value 
                                if boss in bosses: bosses.remove(boss)
                            collided = True
                            break
                        
                for particle in harvest_particles[:]:
                    if spaceship.check_collision(particle.rect):
                        score += 5
                        if particle in harvest_particles: harvest_particles.remove(particle)

                if score >= score_for_next_level:
                    level += 1
                    level_up_timer = 60 
                    self.level_up_sound.play()
                    max_lives += 1
                    lives += 1
                    boss_spawned_this_level = False
                    score_for_next_level = int(level * (600 + 100 * level))

                rocks = [rock for rock in rocks if not rock.is_off_screen()]
                enemies = [enemy for enemy in enemies if not enemy.is_off_screen()]
                neutrals = [n for n in neutrals if not n.is_off_screen()] 
                bosses = [boss for boss in bosses if not boss.is_off_screen()] 
                player_lasers = [laser for laser in player_lasers if not laser.is_off_screen()]
                enemy_lasers = [laser for laser in enemy_lasers if not laser.is_off_screen()]

            if level_up_timer > 0:
                level_up_timer -= 1
                font_scale = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() * 0.02)
                popup_text = "LEVEL UP!"
                y_offset = -50 * (1 - (level_up_timer / 60))
                self.draw_text(popup_text, self.font, EXPLOSION_COLORS[0], display_surface, self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2 + y_offset)

            shake_x, shake_y = 0, 0
            if shake_timer > 0:
                shake_timer -= 1
                shake_amount = 10 if shake_timer > 30 else 5
                shake_x = random.randint(-shake_amount, shake_amount)
                shake_y = random.randint(-shake_amount, shake_amount)
            self.screen.blit(display_surface, (shake_x, shake_y))

            self.draw_lifebar(lives, max_lives, self.screen)
            self.draw_text(f"Score: {score}", self.score_font, WHITE, self.screen, 15, 60, center=False)
            self.draw_text(f"Level: {level}", self.score_font, WHITE, self.screen, 15, 105, center=False)

            if is_paused:
                pygame.mouse.set_visible(True)
                resume_game, load_game, exit_game, save_game = self.draw_pause_menu(event)
                if resume_game: is_paused = False
                elif save_game:
                    self.save_game_screen(level)
                    is_paused = True
                elif load_game:
                    self.load_game_menu()
                    return
                elif exit_game: return

            pygame.display.flip()
            self.clock.tick(self.FPS)

if __name__ == "__main__":
    game = Game()
    game.title_screen()
    game.briefing_screen()
    game.main_menu()