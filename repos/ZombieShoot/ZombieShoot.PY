import pygame
import random
import math
import numpy as np
import sys

# --- Game Constants ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARK_RED = (139, 0, 0)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255) # Brighter color for the Gatling gun
NEON_CYAN = (0, 255, 255)  # The new color for the power-up
BARRIER_COLOR = BLACK # Changed from bright white to black for obstacles
BLOOD_RED = (180, 0, 0)  # A deep red for blood particles
NUKE_GREEN = (50, 205, 50) # New color for the nuke power-up


# New colors for the floor with eight gradients
FLOOR_GRAY_1 = (20, 20, 20)
FLOOR_GRAY_2 = (40, 40, 40)
FLOOR_GRAY_3 = (60, 60, 60)
FLOOR_GRAY_4 = (80, 80, 80)
FLOOR_GRAY_5 = (100, 100, 100)
FLOOR_GRAY_6 = (120, 120, 120)
FLOOR_GRAY_7 = (140, 140, 140)
FLOOR_COLORS = [FLOOR_GRAY_1, FLOOR_GRAY_2, FLOOR_GRAY_3, FLOOR_GRAY_4, FLOOR_GRAY_5, FLOOR_GRAY_6, FLOOR_GRAY_7]


# Hexagon dimensions
HEX_SIDE = 60
# Recalculated based on a proper hex grid
HEX_WIDTH = HEX_SIDE * 2
HEX_HEIGHT = int(HEX_SIDE * math.sqrt(3))

# --- Initialize Pygame ---
pygame.init()
pygame.mixer.init() # Initialize the mixer for sound
# Set the game to run in fullscreen mode and get dimensions after initialization
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Python Zombie Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)

# Global variables for top scores and audio settings
top_scores = []
global_volume = 0.5
is_muted = False
# Default keybinds, now a global dictionary
keybinds = {
    'move_up': pygame.K_w,
    'move_down': pygame.K_s,
    'move_left': pygame.K_a,
    'move_right': pygame.K_d
}


# --- Sound Generation ---
def generate_sound(frequency, duration, volume):
    """
    Generates a sound wave and returns a Pygame Sound object.
    frequency: The frequency of the sine wave in Hz.
    duration: The duration of the sound in milliseconds.
    volume: The volume (0.0 to 1.0).
    
    This version has a corrected calculation for the sound's volume envelope
    to prevent the ValueError from mismatched array sizes.
    """
    sample_rate = 44100
    n_samples = int(round(duration * sample_rate / 1000))
    
    # Define a simple fade-in/out length (e.g., 10% of the total duration)
    fade_len = int(n_samples * 0.1)
    
    # Calculate the length of the sustained (middle) portion
    sustain_len = n_samples - (fade_len * 2)
    
    # Handle cases where the sound is too short for a fade
    if sustain_len < 0:
        fade_len = n_samples // 2
        sustain_len = 0
    
    # Generate the fade-in, sustain, and fade-out arrays
    fade_in = np.linspace(0, 1, fade_len)
    sustain = np.ones(sustain_len)
    fade_out = np.linspace(1, 0, n_samples - fade_len - sustain_len) # Correct length calculation
    
    # Concatenate them to create the full volume envelope array
    full_arr = np.concatenate([fade_in, sustain, fade_out])
    
    buf = np.zeros((n_samples, 2), dtype=np.int16)
    max_sample = 32767
    
    # Generate the sine wave
    sine_wave = np.sin(2 * np.pi * np.arange(n_samples) * frequency / sample_rate)
    
    # Multiply the sine wave by the volume envelope
    scaled_wave = np.array(sine_wave * max_sample * volume * full_arr, dtype=np.int16)
    
    for channel in range(2):
        buf[:, channel] = scaled_wave
    
    sound = pygame.sndarray.make_sound(buf)
    return sound

# Generate our sound effects internally
shoot_sound = generate_sound(500, 50, 0.25) # The volume has been lowered from 0.375 to 0.25
hit_sound = generate_sound(300, 100, 0.3)
zombie_death_sound = generate_sound(150, 200, 0.6)
hurt_sound = generate_sound(100, 150, 0.8) # New sound effect for losing health
powerup_sound = generate_sound(800, 100, 0.5)  # New sound for health power-up
nuke_sound = generate_sound(900, 1000, 0.8)  # New sound for the nuke power-up

# Main menu melody notes and their durations in milliseconds
# Frequencies for a simple C major scale starting from middle C
C4 = 261.63
E4 = 329.63
G4 = 392.00
A4 = 440.00
C5 = 523.25
NOTES = {
    'C4': C4,
    'E4': E4,
    'G4': G4,
    'A4': A4,
    'C5': C5,
}

# The melody is represented as a list of (note_name, duration) tuples
MELODY = [
    ('C4', 300), ('E4', 300), ('G4', 300),
    ('G4', 600),
    ('E4', 300), ('C4', 300),
    ('C5', 300),
    ('A4', 600),
    ('G4', 300), ('E4', 300), ('C4', 300),
    ('C4', 1000)
]

# Create a list to hold the generated sound objects for the melody
melody_sounds = []
for note, duration in MELODY:
    if note in NOTES:
        sound = generate_sound(NOTES[note], duration, global_volume/3)  # PATCHED
        melody_sounds.append((sound, duration))


# --- Classes ---
class Player(pygame.sprite.Sprite):
    """
    Represents the player character.
    Handles movement, health, and shooting.
    """
    def __init__(self):
        super().__init__()
        # Create a visually improved circular player icon
        self.image = pygame.Surface([50, 50], pygame.SRCALPHA)
        # Outer darker ring for depth
        pygame.draw.circle(self.image, (0, 0, 139), (25, 25), 25)
        # Main blue body
        pygame.draw.circle(self.image, BLUE, (25, 25), 22)
        # Inner lighter circle for a 3D effect
        pygame.draw.circle(self.image, (100, 100, 255), (25, 25), 15)
        
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed = 5
        self.health = 100
        self.max_health = 100
        # New attributes for weapon upgrade
        self.current_weapon = 'pistol' # pistol, machine_gun, gatling_gun
        self.last_shot_time = 0
        self.fire_rate = 500 # milliseconds between shots (for pistol)
        # Create a weapon instance and add it to a list
        self.weapons = pygame.sprite.Group()
        self.pistol = Pistol(self)
        self.weapons.add(self.pistol)

    def update(self):
        """
        Updates player position based on key presses.
        Now uses the global keybinds dictionary for movement.
        """
        keys = pygame.key.get_pressed()
        # Movement with WASD
        if keys[keybinds['move_left']] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[keybinds['move_right']] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[keybinds['move_up']] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[keybinds['move_down']] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed
            
        # Movement with Arrow Keys
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

        self.weapons.update(self.rect.center, pygame.mouse.get_pos())


    def draw(self):
        """
        Draws the player on the screen.
        """
        screen.blit(self.image, self.rect)
        self.weapons.draw(screen)

    def shoot(self, mouse_pos, all_sprites, bullets):
        """
        Creates a new bullet instance and adds it to the bullet group.
        Fires only if the fire rate cooldown has passed.
        """
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.fire_rate:
            shoot_sound.play()
            direction = math.atan2(mouse_pos[1] - self.rect.centery, mouse_pos[0] - self.rect.centerx)
            # Change bullet color based on weapon
            if self.current_weapon == 'machine_gun':
                bullet_color = YELLOW
            elif self.current_weapon == 'gatling_gun':
                bullet_color = MAGENTA
            else:
                bullet_color = RED

            bullet = Bullet(self.rect.center, direction, bullet_color)
            all_sprites.add(bullet)
            bullets.add(bullet)
            self.last_shot_time = current_time
        
    def restore_health(self, amount):
        """
        Restores player's health up to the maximum.
        """
        self.health = min(self.max_health, self.health + amount)


class Pistol(pygame.sprite.Sprite):
    """
    Represents the player's weapon, which follows the player and aims at the cursor.
    Its appearance changes as the weapon is upgraded.
    """
    def __init__(self, player):
        super().__init__()
        self.player = player

        # --- Create surfaces for each weapon level with improved detail ---
        # Level 1: Pistol
        self.pistol_image = pygame.Surface([20, 10], pygame.SRCALPHA)
        pygame.draw.rect(self.pistol_image, (80, 80, 80), (0, 0, 20, 8))   # Main body
        pygame.draw.rect(self.pistol_image, (50, 50, 50), (3, 6, 5, 4))    # Handle
        
        # Level 2: Machine Gun (larger and more detailed)
        self.machine_gun_image = pygame.Surface([30, 15], pygame.SRCALPHA)
        pygame.draw.rect(self.machine_gun_image, (80, 80, 80), (0, 0, 30, 10)) # Main body
        pygame.draw.rect(self.machine_gun_image, (50, 50, 50), (5, 8, 7, 7))  # Handle
        pygame.draw.rect(self.machine_gun_image, (100, 100, 100), (0, 0, 30, 2)) # Top rail

        # Level 3: Gatling Gun (largest and most detailed)
        self.gatling_gun_image = pygame.Surface([45, 22], pygame.SRCALPHA)
        pygame.draw.rect(self.gatling_gun_image, (80, 80, 80), (0, 0, 45, 18)) # Main body
        pygame.draw.rect(self.gatling_gun_image, (50, 50, 50), (10, 15, 10, 7)) # Handle
        # Simulate multiple barrels
        pygame.draw.rect(self.gatling_gun_image, (100, 100, 100), (0, 0, 45, 4))
        pygame.draw.rect(self.gatling_gun_image, (100, 100, 100), (0, 7, 45, 4))
        pygame.draw.rect(self.gatling_gun_image, (100, 100, 100), (0, 14, 45, 4))
        
        # Start with the pistol image as the base
        self.original_image = self.pistol_image
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=self.player.rect.center)
    
    def update(self, player_pos, mouse_pos):
        """
        Update the position, rotation, and appearance of the weapon.
        """
        # Select the correct weapon image based on the player's current weapon
        if self.player.current_weapon == 'machine_gun':
            self.original_image = self.machine_gun_image
        elif self.player.current_weapon == 'gatling_gun':
            self.original_image = self.gatling_gun_image
        else: # Default to pistol
            self.original_image = self.pistol_image

        # Update position to follow the player
        self.rect.center = player_pos
        
        # Calculate the angle to the mouse cursor
        dx = mouse_pos[0] - self.rect.centerx
        dy = mouse_pos[1] - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))
        
        # Rotate the image and update the rect to match
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)


class Zombie(pygame.sprite.Sprite):
    """
    Represents a zombie enemy.
    Moves towards the player and has a subtle pulsating animation.
    """
    def __init__(self, initial_health):
        super().__init__()
        # Create a more detailed, layered zombie icon
        self.original_image = pygame.Surface([40, 40], pygame.SRCALPHA)
        pygame.draw.circle(self.original_image, (0, 80, 0), (20, 20), 20)  # Darker outer ring
        pygame.draw.circle(self.original_image, GREEN, (20, 20), 17) # Main green body
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        
        # Variables for the pulsating animation
        self.pulse_timer = 0
        self.pulse_speed = random.uniform(1.5, 3)

        # Spawn zombie at a random position outside the screen
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = -50
        elif side == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = SCREEN_HEIGHT + 50
        elif side == 'left':
            self.rect.x = -50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
        else: # side == 'right'
            self.rect.x = SCREEN_WIDTH + 50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)

        # Zombies start slow and speed up when hit
        self.speed = random.uniform(0.5, 1.5)
        self.health = initial_health

    def update(self, player_rect):
        """
        Moves the zombie towards the player and applies a pulsating visual effect.
        """
        # Pulsating effect
        self.pulse_timer += self.pulse_speed * 0.1
        scale = 1.0 + math.sin(self.pulse_timer) * 0.05  # Pulse by 5%
        center = self.rect.center
        self.image = pygame.transform.scale(self.original_image, (int(40 * scale), int(40 * scale)))
        self.rect = self.image.get_rect(center=center)

        # Movement
        dx = player_rect.x - self.rect.x
        dy = player_rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += self.speed * dx / dist
            self.rect.y += self.speed * dy / dist
            
    def speed_up(self, amount):
        """
        Increases the zombie's speed, capped at the player's speed.
        """
        self.speed += amount
        if self.speed > 5: # Player's speed is 5
            self.speed = 5

    def draw(self):
        """
        Draws the zombie on the screen.
        """
        screen.blit(self.image, self.rect)

class WanderingZombie(Zombie):
    """
    A zombie that wanders aimlessly on the screen.
    Used for the background of the menu.
    """
    def __init__(self):
        super().__init__(initial_health=1) # A wandering zombie has minimal health
        self.speed = random.uniform(0.5, 1.5)
        # Give a random direction at the start
        self.vel_x = random.uniform(-1, 1) * self.speed
        self.vel_y = random.uniform(-1, 1) * self.speed
        
        # Reset position to a random edge of the screen
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = -50
        elif side == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = SCREEN_HEIGHT + 50
        elif side == 'left':
            self.rect.x = -50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
        else: # side == 'right'
            self.rect.x = SCREEN_WIDTH + 50
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
    
    def update(self):
        """
        Moves the zombie and resets its position if it goes off-screen.
        Does not call parent update to avoid pulsing and seeking player.
        """
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Reset zombie if it goes off screen
        if self.rect.right < -50 or self.rect.left > SCREEN_WIDTH + 50 or \
           self.rect.bottom < -50 or self.rect.top > SCREEN_HEIGHT + 50:
            self.__init__() # Re-initialize to a new random position and direction

class Bullet(pygame.sprite.Sprite):
    """
    Represents a bullet fired by the player, with a glow effect.
    """
    def __init__(self, pos, direction, color):
        super().__init__()
        self.image = pygame.Surface([14, 14], pygame.SRCALPHA)
        
        # Create a semi-transparent glow effect
        glow_color = (min(color[0]+50, 255), min(color[1]+50, 255), min(color[2]+50, 255), 100)
        pygame.draw.circle(self.image, glow_color, (7, 7), 7)
        
        # Draw the solid bullet core
        pygame.draw.circle(self.image, color, (7, 7), 4)

        self.rect = self.image.get_rect(center=pos)
        self.speed = 10
        self.vel_x = self.speed * math.cos(direction)
        self.vel_y = self.speed * math.sin(direction)

    def update(self):
        """
        Moves the bullet and kills it if it goes off-screen.
        """
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or \
           self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw(self):
        """
        Draws the bullet on the screen.
        """
        screen.blit(self.image, self.rect)
        
class PowerUp(pygame.sprite.Sprite):
    """
    Represents a health-restoring power-up with a first-aid cross symbol.
    """
    def __init__(self, barriers_group):
        super().__init__()
        self.image = pygame.Surface([20, 20], pygame.SRCALPHA)
        # Main body of the power-up
        pygame.draw.circle(self.image, NEON_CYAN, (10, 10), 10)
        # White first-aid cross
        pygame.draw.rect(self.image, WHITE, (8, 3, 4, 14)) # Vertical bar
        pygame.draw.rect(self.image, WHITE, (3, 8, 14, 4)) # Horizontal bar

        self.rect = self.image.get_rect()
        
        # Keep generating a position until it doesn't collide with a barrier
        while True:
            self.rect.center = (random.randint(50, SCREEN_WIDTH - 50), random.randint(50, SCREEN_HEIGHT - 50))
            if not pygame.sprite.spritecollide(self, barriers_group, False):
                break
        
    def update(self):
        # The power-up doesn't move, so this method is empty.
        pass

class NukePowerUp(pygame.sprite.Sprite):
    """
    Represents a nuke power-up. When shot, it kills all zombies.
    It blinks to draw attention.
    """
    def __init__(self, barriers_group):
        super().__init__()
        self.image = pygame.Surface([25, 25], pygame.SRCALPHA)
        # Draw the main body with a letter 'N' for Nuke
        pygame.draw.circle(self.image, NUKE_GREEN, (12, 12), 12)
        n_font = pygame.font.Font(None, 24)
        n_text = n_font.render("N", True, WHITE)
        n_rect = n_text.get_rect(center=(12, 12))
        self.image.blit(n_text, n_rect)
        
        self.rect = self.image.get_rect()
        
        # Keep generating a position until it doesn't collide with a barrier
        while True:
            self.rect.center = (random.randint(50, SCREEN_WIDTH - 50), random.randint(50, SCREEN_HEIGHT - 50))
            if not pygame.sprite.spritecollide(self, barriers_group, False):
                break
        
        self.last_blink_time = pygame.time.get_ticks()
        self.blink_interval = 250  # milliseconds
        self.is_visible = True

    def update(self):
        """
        Handles the blinking effect of the power-up.
        """
        now = pygame.time.get_ticks()
        if now - self.last_blink_time > self.blink_interval:
            self.is_visible = not self.is_visible
            self.last_blink_time = now
        
        # Set alpha to be visible or invisible
        if self.is_visible:
            self.image.set_alpha(255)
        else:
            self.image.set_alpha(0)
        
class Particle:
    """
    Represents a single particle for a visual effect.
    """
    def __init__(self, pos, color):
        self.pos = list(pos)
        self.color = color
        self.velocity = [random.uniform(-3, 3), random.uniform(-3, 3)]
        self.lifespan = random.randint(10, 30)
        self.size = 5

    def update(self):
        # Update particle position
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        # Decrease lifespan
        self.lifespan -= 1
        # Decrease size slightly for a fading effect
        self.size = max(0, self.size - 0.2)

    def draw(self, screen_surface):
        if self.lifespan > 0 and self.size > 0:
            pygame.draw.circle(screen_surface, self.color, (int(self.pos[0]), int(self.pos[1])), int(self.size))

class BloodStain(pygame.sprite.Sprite):
    """
    A persistent sprite for a blood stain on the floor.
    It appears when a zombie is shot.
    """
    def __init__(self, pos):
        super().__init__()
        self.size = random.randint(5, 15)
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLOOD_RED, (self.size, self.size), self.size)
        self.rect = self.image.get_rect(center=pos)
        self.creation_time = pygame.time.get_ticks()

    def update(self):
        # Blood stains do not move, but could be set to fade over time
        pass

class Barrier(pygame.sprite.Sprite):
    """
    Represents a barrier that blocks movement.
    """
    def __init__(self, pos):
        super().__init__()
        self.width = random.randint(50, 200)
        self.height = random.randint(50, 200)
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(BARRIER_COLOR)
        self.rect = self.image.get_rect(topleft=pos)
        self.draw_3d_effect() # Now calls this once on creation

    def draw_3d_effect(self):
        # The lighter color for the inner rectangle
        lighter_color = (60, 60, 60)
        # The new darker color for the inner relief
        darker_color = (30, 30, 30)

        # Draw the lighter gray rectangle first
        inner_rect = pygame.Rect(5, 5, self.width - 10, self.height - 10)
        pygame.draw.rect(self.image, lighter_color, inner_rect)

        # Draw the new darker gray rectangle on top of the lighter one
        darker_rect = pygame.Rect(10, 10, self.width - 20, self.height - 20)
        pygame.draw.rect(self.image, darker_color, darker_rect)

# --- Helper Functions ---
def draw_floor_background():
    """
    Draws a tiled hexagonal floor pattern on the screen.
    This version uses a correct alignment algorithm for flat-topped hexagons
    and eight shades of gray for the tiles.
    """
    hex_radius = HEX_SIDE
    hex_width = hex_radius * 2
    hex_height = hex_radius * math.sqrt(3)
    
    # A smaller radius for the inner hexagon to create a 3D effect
    inner_hex_radius = hex_radius * 0.95 

    # Calculate number of hexes to draw
    num_cols = int(SCREEN_WIDTH / (hex_width * 0.75)) + 2
    num_rows = int(SCREEN_HEIGHT / hex_height) + 2

    for row in range(num_rows):
        for col in range(num_cols):
            # Calculate the center of the hexagon
            x_pos = col * hex_width * 0.75
            y_pos = row * hex_height
            
            # Apply offset for every other column
            if col % 2 != 0:
                y_pos += hex_height / 2

            # Determine color based on a more robust pattern
            # The (row * 2 + col) % 7 pattern provides a better distribution for hex grids.
            color_index = (row * 2 + col) % 7
            color = FLOOR_COLORS[color_index]

            # Vertices for a flat-topped hexagon
            vertices = [
                (x_pos + hex_radius, y_pos),
                (x_pos + hex_radius * 0.5, y_pos + hex_height * 0.5),
                (x_pos - hex_radius * 0.5, y_pos + hex_height * 0.5),
                (x_pos - hex_radius, y_pos),
                (x_pos - hex_radius * 0.5, y_pos - hex_height * 0.5),
                (x_pos + hex_radius * 0.5, y_pos - hex_height * 0.5),
            ]
            
            pygame.draw.polygon(screen, color, vertices)

            # --- Draw the smaller, lighter inner hexagon for 3D relief ---
            # Get the lighter color
            lighter_color_index = min(color_index + 1, len(FLOOR_COLORS) - 1)
            lighter_color = FLOOR_COLORS[lighter_color_index]
            
            inner_vertices = [
                (x_pos + inner_hex_radius, y_pos),
                (x_pos + inner_hex_radius * 0.5, y_pos + inner_hex_radius * math.sqrt(3) * 0.5),
                (x_pos - inner_hex_radius * 0.5, y_pos + inner_hex_radius * math.sqrt(3) * 0.5),
                (x_pos - inner_hex_radius, y_pos),
                (x_pos - inner_hex_radius * 0.5, y_pos - inner_hex_radius * math.sqrt(3) * 0.5),
                (x_pos + inner_hex_radius * 0.5, y_pos - inner_hex_radius * math.sqrt(3) * 0.5),
            ]
            
            pygame.draw.polygon(screen, lighter_color, inner_vertices)

# --- Menu Functions ---
def show_start_menu():
    """
    Displays the game's main menu, with New Game, Options, Leaderboards, and Quit buttons.
    """
    menu_running = True
    
    # Create a group for the zombies wandering in the background
    wandering_zombies = pygame.sprite.Group()
    for _ in range(5):
        wandering_zombies.add(WanderingZombie())

    # Play the main menu melody
    current_note = 0
    start_time = pygame.time.get_ticks()

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if new_game_rect.collidepoint(event.pos):
                    return "new_game"
                if options_rect.collidepoint(event.pos):
                    return "options_menu"
                if leaderboards_rect.collidepoint(event.pos):
                    return "leaderboards_menu"
                if quit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
        
        # Play the main menu melody
        now = pygame.time.get_ticks()
        if now - start_time > melody_sounds[current_note][1]:
            start_time = now
            current_note += 1
            if current_note >= len(melody_sounds):
                current_note = 0 # Loop the melody
            melody_sounds[current_note][0].play()

        # Draw the tiled floor background first
        draw_floor_background()
        
        # Draw zombies in the background
        wandering_zombies.update()
        wandering_zombies.draw(screen)

        # Draw the menu text and buttons on top
        title_text = large_font.render("ZOMBIE SHOOT", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        new_game_text = font.render("New Game", True, WHITE)
        new_game_rect = new_game_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        
        options_text = font.render("Options", True, WHITE)
        options_rect = options_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        leaderboards_text = font.render("Leaderboards", True, WHITE)
        leaderboards_rect = leaderboards_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

        quit_text = font.render("Quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))

        screen.blit(new_game_text, new_game_rect)
        screen.blit(options_text, options_rect)
        screen.blit(leaderboards_text, leaderboards_rect)
        screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()

def show_options_menu():
    """
    Displays the options menu with buttons for Audio and Controls.
    """
    options_running = True
    while options_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if audio_rect.collidepoint(event.pos):
                    return "audio_menu"
                if controls_rect.collidepoint(event.pos):
                    return "controls_menu"
                if back_rect.collidepoint(event.pos):
                    return "start_menu"

        draw_floor_background()

        # Title
        title_text = large_font.render("OPTIONS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        # Audio button
        audio_text = font.render("Audio", True, WHITE)
        audio_rect = audio_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(audio_text, audio_rect)
        
        # Controls button
        controls_text = font.render("Controls", True, WHITE)
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(controls_text, controls_rect)

        # Back button
        back_text = font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)

        pygame.display.flip()

def show_audio_menu():
    global global_volume, is_muted, shoot_sound, hit_sound, zombie_death_sound, hurt_sound, powerup_sound, nuke_sound
    audio_running = True
    slider_dragging = False

    slider_x = SCREEN_WIDTH // 2 - 100
    slider_y = SCREEN_HEIGHT // 2 - 50
    slider_width = 200
    slider_height = 20
    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)

    mute_button_x = SCREEN_WIDTH // 2 - 100
    mute_button_y = SCREEN_HEIGHT // 2
    mute_button_width = 200
    mute_button_height = 50
    mute_button_rect = pygame.Rect(mute_button_x, mute_button_y, mute_button_width, mute_button_height)

    while audio_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if slider_rect.collidepoint(event.pos):
                    slider_dragging = True
                if mute_button_rect.collidepoint(event.pos):
                    is_muted = not is_muted
                    if is_muted:
                        shoot_sound.set_volume(0)
                        hit_sound.set_volume(0)
                        zombie_death_sound.set_volume(0)
                        hurt_sound.set_volume(0)
                        powerup_sound.set_volume(0)
                        nuke_sound.set_volume(0)
                        for sound, _ in melody_sounds:
                            sound.set_volume(0)
                    else:
                        shoot_sound.set_volume(global_volume)
                        hit_sound.set_volume(global_volume)
                        zombie_death_sound.set_volume(global_volume)
                        hurt_sound.set_volume(global_volume)
                        powerup_sound.set_volume(global_volume)
                        nuke_sound.set_volume(global_volume)
                        for sound, _ in melody_sounds:
                            sound.set_volume(global_volume)
                if back_rect.collidepoint(event.pos):
                    return "options_menu"

            if event.type == pygame.MOUSEBUTTONUP:
                slider_dragging = False

            if event.type == pygame.MOUSEMOTION and slider_dragging:
                mouse_x = event.pos[0]
                slider_knob_x = max(slider_x, min(mouse_x, slider_x + slider_width))
                global_volume = (slider_knob_x - slider_x) / slider_width
                shoot_sound.set_volume(global_volume)
                hit_sound.set_volume(global_volume)
                zombie_death_sound.set_volume(global_volume)
                hurt_sound.set_volume(global_volume)
                powerup_sound.set_volume(global_volume)
                nuke_sound.set_volume(global_volume)
                for sound, _ in melody_sounds:
                    sound.set_volume(global_volume)
                is_muted = (global_volume == 0)

        draw_floor_background()
        title_text = large_font.render("AUDIO", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        volume_text = font.render("Volume", True, WHITE)
        volume_rect = volume_text.get_rect(center=(SCREEN_WIDTH // 2, slider_y - 25))
        screen.blit(volume_text, volume_rect)
        pygame.draw.rect(screen, (100, 100, 100), slider_rect)
        slider_knob_x = slider_x + (global_volume * slider_width)
        pygame.draw.circle(screen, GREEN, (int(slider_knob_x), slider_y + slider_height // 2), 10)

        mute_button_text = font.render("Mute" if not is_muted else "Unmute", True, WHITE)
        pygame.draw.rect(screen, (50, 50, 50), mute_button_rect)
        screen.blit(mute_button_text, mute_button_text.get_rect(center=mute_button_rect.center))

        back_text = font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)

        pygame.display.flip()


def show_controls_menu():
    """
    Displays the controls menu with a list of keybindings, now with remapping.
    """
    global keybinds
    controls_running = True
    remap_mode = False
    current_key_to_remap = None
    
    # Calculate button positions
    button_y_start = SCREEN_HEIGHT // 2 - 100
    button_spacing = 60
    button_width = 100
    button_height = 40
    
    # Define a list of actions and their button positions
    actions = [
        ('move_up', "Move Up"),
        ('move_down', "Move Down"),
        ('move_left', "Move Left"),
        ('move_right', "Move Right")
    ]
    
    action_rects = {}

    while controls_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and not remap_mode:
                if back_rect.collidepoint(event.pos):
                    return "options_menu"
                # Check if a remap button was clicked
                for action, rect in action_rects.items():
                    if rect.collidepoint(event.pos):
                        remap_mode = True
                        current_key_to_remap = action
            
            # If in remap mode, wait for a key press
            if event.type == pygame.KEYDOWN and remap_mode:
                if event.key not in keybinds.values():
                    keybinds[current_key_to_remap] = event.key
                    remap_mode = False
                    current_key_to_remap = None
                else:
                    # Inform the user the key is already in use
                    # A small message box or console message is fine for now
                    print("Key is already in use!")

        draw_floor_background()

        # Title
        title_text = large_font.render("CONTROLS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        # Display the current keybindings and change buttons
        for i, (key_action, key_text) in enumerate(actions):
            # Display action text
            action_label = font.render(f'{key_text}:', True, WHITE)
            action_rect = action_label.get_rect(center=(SCREEN_WIDTH // 2 - 100, button_y_start + i * button_spacing))
            screen.blit(action_label, action_rect)

            # Display the currently bound key
            current_key_name = pygame.key.name(keybinds[key_action]).upper()
            key_name_label = font.render(current_key_name, True, YELLOW)
            key_name_rect = key_name_label.get_rect(center=(SCREEN_WIDTH // 2, button_y_start + i * button_spacing))
            screen.blit(key_name_label, key_name_rect)

            # Draw the Change button
            change_button_rect = pygame.Rect(
                SCREEN_WIDTH // 2 + 50,
                button_y_start + i * button_spacing - button_height // 2,
                button_width,
                button_height
            )
            pygame.draw.rect(screen, (50, 50, 50), change_button_rect, border_radius=10)
            change_text = font.render("Change", True, WHITE)
            change_text_rect = change_text.get_rect(center=change_button_rect.center)
            screen.blit(change_text, change_text_rect)
            action_rects[key_action] = change_button_rect
        
        # Display shooting control, which is not remappable
        shoot_text = font.render("Shoot: Left Mouse Button", True, WHITE)
        shoot_rect = shoot_text.get_rect(center=(SCREEN_WIDTH // 2, button_y_start + len(actions) * button_spacing + 20))
        screen.blit(shoot_text, shoot_rect)

        # Prompt for key change
        if remap_mode:
            prompt_text = font.render(f"Press a new key for '{current_key_to_remap.replace('_', ' ').title()}'", True, MAGENTA)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
            screen.blit(prompt_text, prompt_rect)

        # Back button
        back_text = font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)

        pygame.display.flip()

def show_pause_menu():
    """
    Displays the pause menu with Resume and Main Menu buttons.
    """
    pause_running = True
    while pause_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_rect.collidepoint(event.pos):
                    return "resume"
                if main_menu_rect.collidepoint(event.pos):
                    return "start_menu"

        # Draw the tiled floor background first
        draw_floor_background()

        # Draw a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Draw the menu text and buttons
        pause_text = large_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(pause_text, pause_rect)

        resume_text = font.render("Resume", True, WHITE)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        
        main_menu_text = font.render("Main Menu", True, WHITE)
        main_menu_rect = main_menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        screen.blit(resume_text, resume_rect)
        screen.blit(main_menu_text, main_menu_rect)

        pygame.display.flip()
        
def show_game_over_screen(final_score):
    """
    Displays the game over screen with the final score and top scores.
    """
    global top_scores
    top_scores.append(final_score)
    top_scores.sort(reverse=True)
    top_scores = top_scores[:5] # Keep only the top 5 scores

    game_over_running = True
    while game_over_running:
        draw_floor_background()
        
        # Game Over Title
        game_over_text = large_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(game_over_text, game_over_rect)

        # Final Score
        final_score_text = font.render(f"Final Score: {final_score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(final_score_text, final_score_rect)

        # Top Scores
        top_scores_title = font.render("Top Scores:", True, WHITE)
        top_scores_title_rect = top_scores_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(top_scores_title, top_scores_title_rect)
        
        for i, score in enumerate(top_scores):
            score_text = font.render(f"{i + 1}. {score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30 + i * 30))
            screen.blit(score_text, score_rect)

        # Return to Menu Button
        return_text = font.render("Return to Menu", True, WHITE)
        return_rect = return_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(return_text, return_rect)

        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if return_rect.collidepoint(event.pos):
                    return "start_menu"
                    
def show_leaderboards():
    """
    Displays the leaderboards with the top scores.
    """
    global top_scores
    leaderboards_running = True
    while leaderboards_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    return "start_menu"

        draw_floor_background()

        # Title
        title_text = large_font.render("LEADERBOARDS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        # Display top scores
        for i, score in enumerate(top_scores):
            score_text = font.render(f"{i + 1}. {score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 + i * 40))
            screen.blit(score_text, score_rect)
        
        # Back button
        back_text = font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(back_text, back_rect)

        pygame.display.flip()
        
def show_controls_dialogue():
    """
    Displays a dialogue explaining the game controls.
    """
    dialogue_running = True
    
    # Get key names from the keybinds dictionary
    move_up_key = pygame.key.name(keybinds['move_up']).upper()
    move_down_key = pygame.key.name(keybinds['move_down']).upper()
    move_left_key = pygame.key.name(keybinds['move_left']).upper()
    move_right_key = pygame.key.name(keybinds['move_right']).upper()

    # Create text surfaces for each control
    controls_title = large_font.render("Controls", True, WHITE)
    
    control_texts = [
        f"{move_up_key} - Move Up",
        f"{move_left_key} - Move Left",
        f"{move_down_key} - Move Down",
        f"{move_right_key} - Move Right",
        "Arrow Keys also work for movement",
        "Mouse - Aim",
        "Left Click - Shoot"
    ]
    
    control_surfs = [font.render(text, True, WHITE) for text in control_texts]

    while dialogue_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Any key press or mouse click will advance the dialogue
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return

        draw_floor_background()
        
        # Display the title
        title_rect = controls_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
        screen.blit(controls_title, title_rect)
        
        # Display each control line
        for i, surf in enumerate(control_surfs):
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 + i * 40))
            screen.blit(surf, rect)
        
        # Hint to the player how to continue
        hint_text = font.render("Press any key or click to continue", True, YELLOW)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 240))
        screen.blit(hint_text, hint_rect)

        pygame.display.flip()

def show_dialogue():
    """
    Displays a story dialogue before the game starts.
    """
    dialogue_running = True
    dialogue_text = "This is it... last man standing. Let's show these zombies what humanity is made of!"
    dialogue_surf = font.render(dialogue_text, True, WHITE)
    dialogue_rect = dialogue_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    while dialogue_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Any key press or mouse click will advance the dialogue
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return

        draw_floor_background()
        screen.blit(dialogue_surf, dialogue_rect)
        
        # Hint to the player how to continue
        hint_text = font.render("Press any key or click to continue", True, YELLOW)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(hint_text, hint_rect)

        pygame.display.flip()
        
def main_game_loop():
    """
    Contains the main game logic and drawing loop.
    """
    # Show the controls dialogue first
    show_controls_dialogue()
    # Show the story dialogue before starting the game
    show_dialogue()

    # --- Sprite Groups ---
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    powerups = pygame.sprite.Group() # New group for power-ups
    nuke_powerups = pygame.sprite.Group() # Group for the nuke power-up
    barriers = pygame.sprite.Group() # New group for barriers
    particles = [] # A list to hold the new particle effects
    blood_stains = pygame.sprite.Group() # Group for blood stains on the floor

    # --- Game Variables ---
    player = Player()
    all_sprites.add(player)
    # Add the player's pistol to the sprite group so it can be drawn
    all_sprites.add(player.pistol)
    score = 0
    last_zombie_spawn_time = pygame.time.get_ticks()
    zombie_spawn_rate = 1250 # in milliseconds, changed from 1000
    last_powerup_spawn_time = pygame.time.get_ticks()
    powerup_spawn_rate = 15000 # in milliseconds, a new power-up every 15 seconds
    last_nuke_spawn_time = pygame.time.get_ticks()
    nuke_spawn_rate = 30000 # 30 seconds, less frequent than health power-up
    is_game_over = False
    is_paused = False # New state variable for pausing the game
    is_shooting = False # New state variable to track if the mouse button is held down
    damage_flash_timer = 0 # Timer for the red screen flash effect
    nuke_shockwave = None # Dictionary to manage the nuke explosion visual

    # Generate a random number of barriers and place them on the screen
    num_barriers = random.randint(3, 7)
    for _ in range(num_barriers):
        while True:
            # Pick a random position for the new barrier
            x = random.randint(50, SCREEN_WIDTH - 250)
            y = random.randint(50, SCREEN_HEIGHT - 250)
            new_barrier = Barrier((x, y))
            
            # Check for overlaps with other barriers and the player's starting position
            # This is a simple but effective way to ensure no overlaps
            overlap = False
            if pygame.sprite.spritecollide(new_barrier, barriers, False):
                overlap = True
            
            # Also ensure it doesn't spawn too close to the player
            player_start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 100, 200, 200)
            if new_barrier.rect.colliderect(player_start_rect):
                overlap = True

            if not overlap:
                all_sprites.add(new_barrier)
                barriers.add(new_barrier)
                break

    # --- Main Game Loop ---
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Check for escape key to toggle pause
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                is_paused = not is_paused
            
            # Track if the mouse button is pressed for rapid fire
            if not is_paused and not is_game_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left mouse button
                        is_shooting = True
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        is_shooting = False
        
        # --- Game Logic ---
        if not is_game_over and not is_paused:
            # Store the old max health to calculate the increase
            old_max_health = player.max_health
            
            # Incrementally increase max health based on score (10 HP per 250 points)
            player.max_health = 100 + (score // 250) * 10
            
            # If max health has increased, add the difference to the current health
            if player.max_health > old_max_health:
                player.health += player.max_health - old_max_health
            
            # Check for score thresholds to upgrade gun and increase fire rate
            if score >= 1250 and player.current_weapon != 'gatling_gun':
                player.current_weapon = 'gatling_gun'
                player.fire_rate = 65  # Base fire rate for gatling gun
            elif score >= 500 and player.current_weapon == 'pistol':
                player.current_weapon = 'machine_gun'
                player.fire_rate = 125 # Base fire rate for machine gun
            
            # Increase fire rate progressively based on score tiers
            if player.current_weapon == 'machine_gun':
                score_past_upgrade = score - 500
                fire_rate_modifier = score_past_upgrade // 400
                player.fire_rate = max(60, 125 - fire_rate_modifier * 10)
            elif player.current_weapon == 'gatling_gun':
                score_past_upgrade = score - 1250
                fire_rate_modifier = score_past_upgrade // 400
                player.fire_rate = max(25, 65 - fire_rate_modifier * 5)


            # Fire the weapon if the player is holding the mouse button
            if is_shooting:
                player.shoot(pygame.mouse.get_pos(), all_sprites, bullets)

            # Store the player's old position before updating
            player_old_rect = player.rect.copy()
            
            # Update player and zombies separately to avoid the TypeError
            player.update()
            zombies.update(player.rect)
            bullets.update()
            powerups.update()
            nuke_powerups.update() # Update the nuke power-up (for blinking)
            
            # Update and clean up particles
            for particle in particles:
                particle.update()
            particles = [p for p in particles if p.lifespan > 0]
            
            # Collision detection for player and barriers
            if pygame.sprite.spritecollide(player, barriers, False):
                player.rect = player_old_rect
            
            # Collision detection for zombies and barriers
            for zombie in zombies:
                if pygame.sprite.spritecollide(zombie, barriers, False):
                    # For a simple bounce, reverse the movement direction
                    zombie.rect.x -= zombie.speed
                    zombie.rect.y -= zombie.speed

            # Spawn new zombies
            now = pygame.time.get_ticks()
            if now - last_zombie_spawn_time > zombie_spawn_rate:
                zombie_health = 1 + (score // 100) # Difficulty scales with score
                new_zombie = Zombie(zombie_health)
                all_sprites.add(new_zombie)
                zombies.add(new_zombie)
                last_zombie_spawn_time = now
                # Increase difficulty over time by reducing spawn rate
                zombie_spawn_rate = max(400, zombie_spawn_rate - 2)

            # Spawn a new power-up if one isn't on screen
            now = pygame.time.get_ticks()
            if len(powerups) == 0 and now - last_powerup_spawn_time > powerup_spawn_rate:
                new_powerup = PowerUp(barriers)
                all_sprites.add(new_powerup)
                powerups.add(new_powerup)
                last_powerup_spawn_time = now

            # Spawn a new nuke power-up
            if len(nuke_powerups) == 0 and now - last_nuke_spawn_time > nuke_spawn_rate:
                new_nuke = NukePowerUp(barriers)
                all_sprites.add(new_nuke)
                nuke_powerups.add(new_nuke)
                last_nuke_spawn_time = now

            # Check for collisions between bullets and zombies, and bullets and barriers
            # Bullets are destroyed on impact with either
            pygame.sprite.groupcollide(bullets, barriers, True, False)
            hits = pygame.sprite.groupcollide(zombies, bullets, False, True)
            for zombie, bullet_hit_list in hits.items():
                hit_sound.play() # Play sound on hit
                zombie.health -= len(bullet_hit_list)
                # Speed up the zombie when it's hit
                zombie.speed_up(0.5)

                # Create blood stain and particles when a zombie is hit
                blood_stain = BloodStain(zombie.rect.center)
                blood_stains.add(blood_stain)
                
                # A smaller burst of particles for a single hit
                for _ in range(5): 
                    particles.append(Particle(zombie.rect.center, BLOOD_RED))

                if zombie.health <= 0:
                    zombie_death_sound.play() # Play sound on zombie death
                    # Create a larger burst of particles when the zombie is destroyed
                    for _ in range(20):
                        particles.append(Particle(zombie.rect.center, GREEN))
                    zombie.kill()
                    score += 10
                    
            # Check for collisions between bullets and power-ups
            powerup_hits = pygame.sprite.groupcollide(powerups, bullets, True, True)
            if powerup_hits:
                powerup_sound.play() # Play a sound when the power-up is hit
                player.restore_health(25) # Restore 25 health

            # Check for collisions between bullets and nuke power-ups
            nuke_hits = pygame.sprite.groupcollide(nuke_powerups, bullets, True, True)
            if nuke_hits:
                nuke_sound.play() # Play the nuke sound
                # Get nuke position for shockwave effect
                nuke_pos = list(nuke_hits.keys())[0].rect.center
                nuke_shockwave = {'pos': nuke_pos, 'radius': 0, 'max_radius': 400, 'speed': 25}
                # Kill all zombies on screen
                zombie_death_sound.play() # Play a sound for the effect
                for zombie in zombies:
                    # Create death particles for each zombie
                    for _ in range(20):
                        particles.append(Particle(zombie.rect.center, GREEN))
                    zombie.kill()
                    score += 10 # Give score for each zombie killed

            # Check for collisions between player and zombies
            player_hits = pygame.sprite.spritecollide(player, zombies, True)
            if player_hits:
                # Calculate damage based on score (player's level)
                # Base damage is 25, reduced by 1 for every 100 score points, with a minimum of 5.
                damage_taken = max(5, 25 - (score // 100))
                player.health -= damage_taken
                hurt_sound.play() # Play the hurt sound effect
                damage_flash_timer = 5 # Flash the screen for 5 frames
                if player.health <= 0:
                    is_game_over = True

        # --- Drawing ---
        draw_floor_background()

        # Draw blood stains first so they are on the lowest layer
        blood_stains.draw(screen)

        # Draw barriers
        barriers.draw(screen)
        
        # Draw all other sprites including player, and enemies
        zombies.draw(screen)
        all_sprites.draw(screen)
        
        # Draw the particles after all sprites
        for particle in particles:
            particle.draw(screen)

        # Draw the nuke shockwave effect if it's active
        if nuke_shockwave:
            pygame.draw.circle(screen, WHITE, nuke_shockwave['pos'], int(nuke_shockwave['radius']), 8)
            nuke_shockwave['radius'] += nuke_shockwave['speed']
            if nuke_shockwave['radius'] > nuke_shockwave['max_radius']:
                nuke_shockwave = None
        
        # Draw the damage flash effect if active
        if damage_flash_timer > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((255, 0, 0, 100))
            screen.blit(flash_surface, (0, 0))
            damage_flash_timer -= 1
        
        # --- HUD Drawing ---
        # Create a semi-transparent panel for the HUD
        hud_panel = pygame.Surface((200, 100), pygame.SRCALPHA)
        hud_panel.fill((50, 50, 50, 150))
        screen.blit(hud_panel, (5, 5))

        # Health bar drawing
        if player.health > 75: health_color = GREEN
        elif player.health > 50: health_color = (255, 255, 0) # Yellow
        elif player.health > 25: health_color = (255, 165, 0) # Orange
        else: health_color = RED

        health_bar_rect_bg = pygame.Rect(10, 10, 150, 20)
        pygame.draw.rect(screen, (50, 50, 50), health_bar_rect_bg, border_radius=5)
        health_bar_width = (player.health / player.max_health) * 150
        health_bar_rect = pygame.Rect(10, 10, health_bar_width, 20)
        pygame.draw.rect(screen, health_color, health_bar_rect, border_radius=5)
        
        # Display score and weapon info on the HUD
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 40))
        weapon_name = player.current_weapon.replace('_', ' ').title()
        weapon_surf = font.render(f'Weapon: {weapon_name}', True, WHITE)
        screen.blit(weapon_surf, (10, 70))
        
        if is_game_over:
            # Return final score to main loop
            return score
        
        # If the game is paused, display the pause menu
        if is_paused:
            action = show_pause_menu()
            if action == "resume":
                is_paused = False
            elif action == "start_menu":
                return "start_menu"

        pygame.display.flip()

        # --- Frame Rate Control ---
        clock.tick(60)

    # This part is technically unreachable in this version, but good practice
    return score

# --- Main Program Entry ---
if __name__ == "__main__":
    current_screen = "start_menu"
    while True:
        if current_screen == "start_menu":
            action = show_start_menu()
            if action == "new_game":
                current_screen = "game"
            elif action == "options_menu":
                current_screen = "options"
            elif action == "leaderboards_menu":
                current_screen = "leaderboards"
        elif current_screen == "options":
            action = show_options_menu()
            if action == "start_menu":
                current_screen = "start_menu"
            elif action == "audio_menu":
                current_screen = "audio"
            elif action == "controls_menu":
                current_screen = "controls"
        elif current_screen == "audio":
            action = show_audio_menu()
            if action == "options_menu":
                current_screen = "options"
        elif current_screen == "controls":
            action = show_controls_menu()
            if action == "options_menu":
                current_screen = "options"
        elif current_screen == "leaderboards":
            action = show_leaderboards()
            if action == "start_menu":
                current_screen = "start_menu"
        elif current_screen == "game":
            result = main_game_loop()
            if result == "start_menu":
                current_screen = "start_menu"
            else:
                final_score = result
                current_screen = show_game_over_screen(final_score)