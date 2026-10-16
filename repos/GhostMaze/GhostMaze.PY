#
# A Pygame 2D RPG prototype with a start menu, character movement,
# a simple dungeon with enemies and NPCs, and life points.
#
import pygame
import sys
import numpy as np
import random
import math

# --- Initialization ---
pygame.init()
pygame.mixer.init() # Initialize the sound mixer

# --- Constants ---
SCREEN_INFO = pygame.display.Info()
SCREEN_WIDTH = SCREEN_INFO.current_w
SCREEN_HEIGHT = SCREEN_INFO.current_h
# Calculate TILE_SIZE dynamically to fit the screen
# UPDATED: TILE_SIZE now ensures the dungeon grid perfectly fits the screen.
TILE_SIZE = SCREEN_WIDTH // 30
HORIZONTAL_TILES = SCREEN_WIDTH // TILE_SIZE
VERTICAL_TILES = SCREEN_HEIGHT // TILE_SIZE
PLAYER_SIZE = TILE_SIZE // 2 # New constant for smaller player size
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
WALL_COLOR = (100, 100, 100)
FLOOR_COLOR = (50, 50, 50)
FLOOR_TILE_SIZE = TILE_SIZE // 2 # NEW: Size of the individual floor tiles
FLOOR_COLOR_2 = (40, 40, 40) # NEW: Second color for the checkerboard pattern
PLAYER_COLOR = (255, 0, 0)
NPC_COLOR = (0, 0, 255)
ENEMY_COLOR = (200, 50, 50) # Red color for enemies
ENEMY_HIT_COLOR = (255, 255, 255) # NEW: White flash when enemy is hit
BOSS_COLOR = (240, 240, 240) # NEW: Ghostly white for the boss
BASE_ENEMY_DAMAGE = 15 # NEW: Base damage inflicted by enemies
BOSS_DAMAGE = 40 # NEW: Damage inflicted by the boss
DAMAGE_SCALING_PER_LEVEL = 5 # NEW: Extra damage per player level
HAMMER_HEAD_COLOR = (192, 192, 192) # NEW: Silver for the hammer head
HAMMER_HANDLE_COLOR = (139, 69, 19) # NEW: Brown for the hammer handle
FOOTSTEP_COLOR = (30, 30, 30) # NEW: Color for footsteps
TORCH_COLOR = (255, 255, 0)
DOOR_COLOR = (139, 69, 19) # SaddleBrown for the door
KEY_COLOR = (255, 215, 0) # Gold for the key
LIFE_BAR_COLOR = (0, 255, 0) # Green for life bar
LIFE_BAR_BG_COLOR = (255, 0, 0) # Red for life bar background
STAMINA_BAR_COLOR = (0, 191, 255) # Deep Sky Blue
STAMINA_BAR_BG_COLOR = (25, 25, 25) # Dark gray

# NEW POWER-UP COLORS
FOG_CLEAR_COLOR = (128, 0, 128) # Purple
ENEMY_BOMB_COLOR = (255, 255, 255) # White
HEAL_COLOR = (0, 255, 0) # Green
CYAN_COLOR = (0, 255, 255) # NEW: For level up effect

# --- Game States ---
GAME_STATES = {
    "MENU": 0,
    "GAME": 1,
    "DIALOGUE": 2,
    "GAME_OVER": 3,
    "OPTIONS": 4, # New state for the options menu
    "AUDIO_OPTIONS": 5, # New state for audio options
    "CONTROLS_OPTIONS": 6, # New state for controls options
    "PAUSED": 7, # New state for the pause menu
    "REBINDING_KEY": 8, # New state for key re-binding
    "LEADERBOARD": 9, # NEW state for the leaderboard menu
    "STORY": 10, # NEW state for story screens
}

# Create the display in fullscreen mode
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("My Story-Driven RPG")
clock = pygame.time.Clock()

# Set initial game state to the menu
current_state = GAME_STATES["MENU"]
current_level = 1
player_score = 0 # NEW: Initialize player's score
player_level = 1 # NEW: Initialize player's level
LEVEL_UP_THRESHOLD = 500 # NEW: Score needed to level up
score_at_last_level_up = 0 # NEW: Tracks score when last level up occurred

# --- Text and Fonts ---
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 40)
dialogue_font = pygame.font.Font(None, 24)

# --- Keybindings Dictionary ---
# A dictionary to hold the current keybindings.
# This makes it easy to change them dynamically.
KEY_BINDINGS = {
    "move_up": pygame.K_w,
    "move_down": pygame.K_s,
    "move_left": pygame.K_a,
    "move_right": pygame.K_d,
    "sprint": pygame.K_LSHIFT,
    "interact": pygame.K_SPACE,
}

# Variable to track which key is being re-bound
rebind_target = None

# --- Story and Dialogue ---
# NEW: Define a list of story events that occur at specific levels
STORY_EVENTS = {
    1: ("You awaken in a dark dungeon, a forgotten hero. Your mission: find the lost artifacts of power to save the kingdom from an ancient evil. You must venture through the dungeons to find them.",
        "Use '" + pygame.key.name(KEY_BINDINGS["move_up"]).upper() + "', '" + pygame.key.name(KEY_BINDINGS["move_left"]).upper() + "', '" + pygame.key.name(KEY_BINDINGS["move_down"]).upper() + "', '" + pygame.key.name(KEY_BINDINGS["move_right"]).upper() + "' or arrow keys to move, '" + pygame.key.name(KEY_BINDINGS["sprint"]).upper() + "' to sprint, and '" + pygame.key.name(KEY_BINDINGS["interact"]).upper() + "' to interact with objects and characters, slash enemies and break through walls."),
    2: ("A strange glow emanates from a distant room. You feel a surge of energy. Could one of the artifacts be near?", "Hammer through walls to make life easier."),
    4: ("The path ahead is guarded by a powerful enemy. You'll need all your wits and strength to overcome this challenge. The artifacts are within your grasp!", "Defeat the boss to unlock the door."),
    6: ("This seems to never end... the challenge is one that continues. Find all artifacts and stay alive!", "Powerups and NPCs are there to help!"),
    8: ("The path ahead is guarded by a powerful enemy. You'll need all your wits and strength to overcome this challenge. The artifacts are within your grasp!", "Defeat the boss to unlock the door."),
    12: ("A strange glow emanates from a distant room. You feel a surge of energy. Could one of the artifacts be near?", "Defeat the boss to unlock the door."),
    16: ("A strange glow emanates from a distant room. You feel a surge of energy. Could one of the artifacts be near? Or another enemy?", "Defeat the boss to unlock the door.")
}


# NEW: Define the NPC dialogue list
NPC_DIALOGUES = [
    "I have been waiting for someone like you! Good you brought a hammer. A key is needed to open the magic door, and I can help you with some of your life points.",
    "The way forward is magically locked, but a key is hidden somewhere in this labyrinth. Interacting with me will also heal you a bit.",
    "Only those with a magic key may pass. I can't come with you, but I can restore your vitality.",
    "A locked magic door blocks your path. You must find a key to unlock it. I can feel your strength returning just by talking to me.",
    "Be careful, the magic key is guarded! But don't worry, I'll patch you up if you get hurt."
]

# --- Audio Settings ---
music_volume = 0.5 # Initial volume level (0.0 to 1.0)
is_muted = False # Flag to check if the game is muted
pygame.mixer.music.set_volume(music_volume)

# --- Sound Effects ---
def generate_unlock_sound():
    """Generates a simple 'unlock' sound effect using two short tones."""
    sample_rate = 44100
    duration = 0.2 # duration in seconds
    frequency1 = 880 # A5
    frequency2 = 1320 # E6

    # Create time arrays for two parts of the sound
    t1 = np.linspace(0., duration, int(sample_rate * duration / 2), False)
    t2 = np.linspace(0., duration, int(sample_rate * duration / 2), False)

    # Generate sine waves for each part
    tone1 = 0.5 * np.sin(2 * np.pi * frequency1 * t1)
    tone2 = 0.5 * np.sin(2 * np.pi * frequency2 * t2)

    # Combine the tones
    sound_data = np.concatenate((tone1, tone2))

    # Scale to 16-bit integer format and convert to bytes
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    
    # Create the Pygame Sound object
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_damage_sound():
    """Generates a low, quick tone for taking damage."""
    sample_rate = 44100
    duration = 0.1
    frequency = 100 # Low frequency for a 'thud' sound
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_collect_sound():
    """Generates a high, pleasant tone for collecting items."""
    sample_rate = 44100
    duration = 0.1
    frequency = 1000 # High frequency
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())
    
def generate_dialogue_sound():
    """Generates a soft, quick 'pop' for dialogue."""
    sample_rate = 44100
    duration = 0.05
    frequency = 500
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    sound_data = 0.3 * np.sin(2 * np.pi * frequency * t) * np.exp(-t * 20) # A little decay
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_game_over_sound():
    """Generates a long, descending tone for game over."""
    sample_rate = 44100
    duration = 1.5
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    # Descending frequency from 400Hz to 100Hz
    frequency = 400 * np.exp(-t / 0.5) + 100
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_level_up_sound():
    """Generates a short, ascending tone for leveling up."""
    sample_rate = 44100
    duration = 0.5
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    # Ascending frequency from 200Hz to 800Hz
    frequency = 200 * np.exp(t * 2)
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())
    
def generate_footstep_sound():
    """Generates a simple, percussive footstep sound."""
    sample_rate = 44100
    duration = 0.8
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    # A short, decaying low frequency tone
    sound_data = 0.2 * np.sin(2 * np.pi * 150 * t) * np.exp(-t * 100)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_hammer_swing_sound():
    """Generates a 'swoosh' sound for the hammer swing."""
    sample_rate = 44100
    duration = 0.2
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    # White noise
    noise = np.random.uniform(-0.5, 0.5, len(t))
    # Apply an envelope to shape the noise into a swoosh
    envelope = np.exp(-t * 20)
    sound_data = noise * envelope
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_enemy_hit_sound():
    """Generates a short, sharp sound for hitting an enemy."""
    sample_rate = 44100
    duration = 0.1
    frequency = 600
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    # A decaying sine wave to make a 'hit' sound
    sound_data = 0.4 * np.sin(2 * np.pi * frequency * t) * np.exp(-t * 50)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_wall_destroy_sound():
    """Generates a crumbling/crashing sound for wall destruction."""
    sample_rate = 44100
    duration = 0.5
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    
    # Generate white noise for the crumble/static effect
    noise = np.random.uniform(-1, 1, len(t))
    
    # Create a decay envelope to make it sound like an impact that fades
    envelope = np.exp(-t * 15)
    
    # Generate a low-frequency rumble to add weight to the sound
    rumble = 0.5 * np.sin(2 * np.pi * 60 * t) # A 60Hz rumble
    
    # Combine the sounds: mix the noise and rumble, then shape with the envelope
    sound_data = (noise * 0.5 + rumble) * envelope
    
    # Normalize the audio to prevent clipping (volume too loud)
    if np.max(np.abs(sound_data)) > 0:
        sound_data /= np.max(np.abs(sound_data))
    
    # Scale to 16-bit integer format for Pygame
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_menu_melody():
    """Generates a simple low-bass melody loop for menus."""
    sample_rate = 44100
    bpm = 100
    note_duration = 60 / bpm
    
    # A simple, low bassline (A2, G2, C2, E2)
    notes = [110.0, 98.0, 65.4, 82.4] 
    
    melody_data = []
    
    for freq in notes:
        t = np.linspace(0., note_duration, int(sample_rate * note_duration), False)
        # Create a sine wave with a decay envelope to sound like a bass pluck
        note_data = 0.3 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 5)
        melody_data.append(note_data)
        
    # Concatenate all note data into one array
    full_melody_data = np.concatenate(melody_data)
    
    # Scale to 16-bit integer format and convert to bytes
    sound_data_int16 = (full_melody_data * 32767).astype(np.int16)
    
    # Create the Pygame Sound object
    return pygame.mixer.Sound(sound_data_int16.tobytes())

# Generate the sounds once at the start
unlock_sound = generate_unlock_sound()
damage_sound = generate_damage_sound()
collect_sound = generate_collect_sound()
dialogue_sound = generate_dialogue_sound()
game_over_sound = generate_game_over_sound()
level_up_sound = generate_level_up_sound()
footstep_sound = generate_footstep_sound()
hammer_swing_sound = generate_hammer_swing_sound()
enemy_hit_sound = generate_enemy_hit_sound()
wall_destroy_sound = generate_wall_destroy_sound() # NEW: Wall destruction sound
menu_melody_sound = generate_menu_melody()

# --- Sound Player Helper ---
def play_sound(sound):
    """Plays a sound effect, respecting the global volume and mute settings."""
    global music_volume, is_muted
    if not is_muted:
        sound.set_volume(music_volume)
        sound.play()

# --- Game Classes ---

class Footstep(pygame.sprite.Sprite):
    """A single fading footstep particle."""
    def __init__(self, x, y):
        super().__init__()
        self.size = PLAYER_SIZE // 4
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.image.fill(FOOTSTEP_COLOR)
        self.rect = self.image.get_rect(center=(x, y))
        self.lifespan = 60  # Lasts for 1 second at 60 FPS
        self.initial_lifespan = 60

    def update(self):
        """Fades the footstep out and then removes it."""
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return
        
        # Calculate new alpha based on remaining lifespan
        alpha = int(255 * (self.lifespan / self.initial_lifespan))
        self.image.set_alpha(alpha)


class Particle(pygame.sprite.Sprite):
    """A single particle for special effects."""
    def __init__(self, x, y, color, particle_type):
        super().__init__()
        self.x = x
        self.y = y
        self.color = color
        self.type = particle_type

        if self.type == 'explosion':
            self.size = random.randint(2, 6)
            self.vx = random.uniform(-3, 3)
            self.vy = random.uniform(-3, 3)
            self.lifespan = random.randint(20, 40)
        elif self.type == 'healing':
            self.size = random.randint(4, 8)
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-2, -0.5) # Move upwards
            self.lifespan = random.randint(30, 50)

        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
    def update(self):
        """Updates the particle's position and lifespan."""
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return

        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)

        # Fade out effect for the last 20 frames of life
        if self.lifespan < 20:
            alpha = int(255 * (self.lifespan / 20))
            self.image.set_alpha(alpha)

class Hammer(pygame.sprite.Sprite):
    """Represents the player's hammer."""
    def __init__(self, player):
        super().__init__()
        self.player = player
        
        # Create the hammer image
        self.original_image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE * 2), pygame.SRCALPHA)
        handle_rect = pygame.Rect(PLAYER_SIZE * 0.4, PLAYER_SIZE * 0.5, PLAYER_SIZE * 0.2, PLAYER_SIZE * 1.5)
        head_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE * 0.5)
        pygame.draw.rect(self.original_image, HAMMER_HANDLE_COLOR, handle_rect)
        pygame.draw.rect(self.original_image, HAMMER_HEAD_COLOR, head_rect)
        
        self.image = self.original_image
        self.rect = self.image.get_rect(midbottom=self.player.rect.center)
        
        self.swinging = False
        self.swing_angle = 0
        self.swing_duration = 15  # in frames
        self.swing_timer = 0
        self.swing_speed = 12 # degrees per frame

    def update(self):
        """Updates the hammer's position and rotation."""
        if self.swinging:
            self.swing_timer -= 1
            if self.swing_timer <= 0:
                self.swinging = False
                self.swing_angle = 0
            else:
                # The swing animation
                self.swing_angle -= self.swing_speed
        else:
            # When not swinging, keep it pointed in the player's direction
            self.swing_angle = self.player.direction.angle_to(pygame.math.Vector2(0, -1))

        # Rotate the hammer
        self.image = pygame.transform.rotate(self.original_image, self.swing_angle)
        
        # Position the hammer relative to the player
        # The offset vector moves the hammer out in front of the player
        offset = self.player.direction.normalize() * (PLAYER_SIZE * 0.75)
        self.rect = self.image.get_rect(center=self.player.rect.center + offset)

    def swing(self):
        """Initiates a hammer swing."""
        if not self.swinging:
            play_sound(hammer_swing_sound)
            self.swinging = True
            self.swing_timer = self.swing_duration
            # Start the swing from an offset angle based on player direction
            self.swing_angle = self.player.direction.angle_to(pygame.math.Vector2(0, -1)) + 45

class Player(pygame.sprite.Sprite):
    """Represents the player character."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill(PLAYER_COLOR)
        # Center the player within the tile they spawned on
        self.rect = self.image.get_rect(center=(x + TILE_SIZE/2, y + TILE_SIZE/2))
        self.base_speed = 5 # Increased from 4 to 5 for slightly faster movement
        self.sprint_speed = self.base_speed * 1.75 # Sprint speed is 1.75x base speed
        self.has_key = False
        self.base_life_points = 100
        self.max_life_points = self.base_life_points
        self.life_points = self.max_life_points
        self.invulnerable_timer = 0
        self.is_flashing = False
        self.inventory = [] # New list to store collected power-ups
        
        # New stamina system attributes
        self.base_stamina = 100
        self.max_stamina = self.base_stamina
        self.stamina = self.max_stamina
        self.stamina_drain_rate = 1.5 # How much stamina is lost per frame while sprinting
        self.stamina_recharge_rate = 1 # How much stamina is gained per frame when not sprinting
        self.is_sprinting = False

        # NEW: Player direction and hammer
        self.direction = pygame.math.Vector2(0, -1) # Default facing up
        self.hammer = Hammer(self)

    def update(self, dx, dy, walls, doors):
        """
        Update player position with collision detection that allows sliding.
        This function now checks for collisions with both walls and locked doors.
        It also handles stamina drain and recharge.
        """
        # Update stamina based on action
        if self.is_sprinting and self.stamina > 0:
            self.stamina -= self.stamina_drain_rate
            if self.stamina < 0:
                self.stamina = 0
                self.is_sprinting = False # Stop sprinting if stamina runs out
        else:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_recharge_rate)
        
        # Determine the current speed
        current_speed = self.sprint_speed if self.is_sprinting and self.stamina > 0 else self.base_speed

        # Normalize diagonal movement to prevent faster movement
        if dx != 0 and dy != 0:
            dx /= 1.414
            dy /= 1.414
        
        # Apply the determined speed to the movement vectors
        new_dx = dx * current_speed
        new_dy = dy * current_speed
        
        # NEW: Update player direction based on movement input
        if dx != 0 or dy != 0:
            self.direction.x = dx
            self.direction.y = dy

        # Move only in the x-direction first
        self.rect.x += new_dx

        # Check for collision with walls and locked doors after x-movement
        for wall_dict in walls:
            wall_rect = wall_dict['rect']
            if self.rect.colliderect(wall_rect):
                if new_dx > 0: # Moving right
                    self.rect.right = wall_rect.left
                if new_dx < 0: # Moving left
                    self.rect.left = wall_rect.right
        for door in doors:
            if door.locked and self.rect.colliderect(door.rect):
                if new_dx > 0:
                    self.rect.right = door.rect.left
                if new_dx < 0:
                    self.rect.left = door.rect.right

        # Move only in the y-direction next
        self.rect.y += new_dy

        # Check for collision with walls and locked doors after y-movement
        for wall_dict in walls:
            wall_rect = wall_dict['rect']
            if self.rect.colliderect(wall_rect):
                if new_dy > 0: # Moving down
                    self.rect.bottom = wall_rect.top
                if new_dy < 0: # Moving up
                    self.rect.top = wall_rect.bottom
        for door in doors:
            if door.locked and self.rect.colliderect(door.rect):
                if new_dy > 0:
                    self.rect.bottom = door.rect.top
                if new_dy < 0:
                    self.rect.top = door.rect.bottom

        # Check for screen boundary collision
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)


        # Update invulnerability timer
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
            # Flash the player to indicate invulnerability
            if self.invulnerable_timer % 10 < 5:
                self.image.fill(WHITE)
            else:
                self.image.fill(PLAYER_COLOR)
        else:
            self.image.fill(PLAYER_COLOR)

        # NEW: Update the hammer's state
        self.hammer.update()


class NPC(pygame.sprite.Sprite):
    """Represents a non-player character."""
    def __init__(self, x, y, dialogue, patrol_range=20):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(NPC_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.dialogue = dialogue
        self.speed = 1
        
        # Define the patrol area for slight movement
        self.patrol_start = (x, y)
        self.patrol_end = (x + patrol_range, y + patrol_range)

        # Choose a random initial movement direction for both axes
        self.move_direction_x = random.choice([-1, 1])
        self.move_direction_y = random.choice([-1, 1])
    
    def update(self):
        """Update the NPC's position within its patrol area."""
        self.rect.x += self.speed * self.move_direction_x
        self.rect.y += self.speed * self.move_direction_y

        # Reverse direction if hitting horizontal boundaries
        if self.rect.x > self.patrol_end[0] or self.rect.x < self.patrol_start[0]:
            self.move_direction_x *= -1
        # Reverse direction if hitting vertical boundaries
        if self.rect.y > self.patrol_end[1] or self.rect.y < self.patrol_start[1]:
            self.move_direction_y *= -1

class Door(pygame.sprite.Sprite):
    """Represents a door that can transition to another level."""
    def __init__(self, x, y, locked=True):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(DOOR_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.locked = locked

class Key(pygame.sprite.Sprite):
    """Represents a key that can be collected."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE * 0.5, TILE_SIZE * 0.5)) # Changed size
        self.image.fill(KEY_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    """Represents a moving enemy with smarter AI."""
    def __init__(self, x, y, patrol_range, speed):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(ENEMY_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        
        # Define the patrol area
        self.patrol_start_x = x
        self.patrol_end_x = x + patrol_range
        self.patrol_start_y = y
        self.patrol_end_y = y + patrol_range
        
        # Choose a random initial movement direction for both axes
        self.move_direction_x = random.choice([-1, 1])
        self.move_direction_y = random.choice([-1, 1])
        
        # Enemy health and state
        self.max_life_points = 3
        self.life_points = self.max_life_points
        self.invulnerable_timer = 0
        
        # NEW: AI properties
        self.aggro_radius = TILE_SIZE * 3 # The distance at which the enemy will start chasing the player

    def take_damage(self, amount):
        """Reduces the enemy's life points if not invulnerable."""
        if self.invulnerable_timer == 0:
            self.life_points -= amount
            play_sound(enemy_hit_sound)
            self.invulnerable_timer = 30 # 30 frames of invulnerability
            
    def update(self, player):
        """
        Update the enemy's position. It will patrol its area until the player
        gets close, at which point it will chase the player.
        """
        player_pos = pygame.math.Vector2(player.rect.center)
        enemy_pos = pygame.math.Vector2(self.rect.center)
        distance_to_player = player_pos.distance_to(enemy_pos)

        # --- AI Logic: Chase or Patrol ---
        if distance_to_player < self.aggro_radius:
            # CHASE MODE: Move towards the player
            # **BUG FIX**: Only normalize if the distance is greater than zero
            if distance_to_player > 0:
                direction = (player_pos - enemy_pos).normalize()
                self.rect.x += direction.x * self.speed
                self.rect.y += direction.y * self.speed
        else:
            # PATROL MODE: Move within the defined patrol area
            self.rect.x += self.speed * self.move_direction_x
            self.rect.y += self.speed * self.move_direction_y
            
            # Reverse direction if hitting horizontal boundaries
            if self.rect.x >= self.patrol_end_x or self.rect.x <= self.patrol_start_x:
                self.move_direction_x *= -1
                self.rect.x = max(self.patrol_start_x, min(self.rect.x, self.patrol_end_x))

            # Reverse direction if hitting vertical boundaries
            if self.rect.y >= self.patrol_end_y or self.rect.y <= self.patrol_start_y:
                self.move_direction_y *= -1
                self.rect.y = max(self.patrol_start_y, min(self.rect.y, self.patrol_end_y))
            
        # Update invulnerability and flashing
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
            # Flash the enemy to indicate being hit
            if self.invulnerable_timer % 10 < 5:
                self.image.fill(ENEMY_HIT_COLOR)
            else:
                self.image.fill(ENEMY_COLOR)
        else:
            self.image.fill(ENEMY_COLOR)

class Boss(pygame.sprite.Sprite):
    """Represents a powerful boss enemy."""
    def __init__(self, x, y):
        super().__init__()
        self.original_size = TILE_SIZE * 2
        self.image = pygame.Surface((self.original_size, self.original_size))
        self.image.fill(BOSS_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2.1 # Slower but relentless
        self.max_life_points = 7
        self.life_points = self.max_life_points
        self.invulnerable_timer = 0
        self.damage = BOSS_DAMAGE

    def take_damage(self, amount):
        """Reduces the boss's life points if not invulnerable."""
        if self.invulnerable_timer == 0:
            self.life_points -= amount
            play_sound(enemy_hit_sound) # Reuse hit sound
            self.invulnerable_timer = 30 # 0.5 seconds of invulnerability

    def update(self, player):
        """The boss always chases the player."""
        player_pos = pygame.math.Vector2(player.rect.center)
        boss_pos = pygame.math.Vector2(self.rect.center)
        distance_to_player = player_pos.distance_to(boss_pos)

        # Always chase the player
        if distance_to_player > 0:
            direction = (player_pos - boss_pos).normalize()
            self.rect.x += direction.x * self.speed
            self.rect.y += direction.y * self.speed

        # Update invulnerability and flashing
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
            # Flash the boss to indicate being hit
            if self.invulnerable_timer % 10 < 5:
                self.image.fill(ENEMY_HIT_COLOR)
            else:
                self.image.fill(BOSS_COLOR)
        else:
            self.image.fill(BOSS_COLOR)
            
class Torch(pygame.sprite.Sprite):
    """Represents a static torch light source."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2))
        self.image.fill(TORCH_COLOR)
        self.rect = self.image.get_rect(center=(x, y))

class PowerUp(pygame.sprite.Sprite):
    """Represents a collectible power-up."""
    def __init__(self, x, y, color, type):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE * 0.5, TILE_SIZE * 0.5)) # Changed size
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.type = type

# --- Particle Emitter ---
def create_particles(x, y, color, count, particle_type):
    """Spawns a number of particles at a given position."""
    for _ in range(count):
        particle = Particle(x, y, color, particle_type)
        particle_group.add(particle)

# --- Dungeon Generation ---
def _is_valid_spawn_pos(x, y, layout, padding=1):
    """Checks if a position is a valid floor tile with padding."""
    # Check if the tile is within bounds
    if not (0 < y < len(layout) - 1 and 0 < x < len(layout[0]) - 1):
        return False
    # Check if the tile is a floor
    if layout[y][x] != 0:
        return False
    # Check for padding
    for dy in range(-padding, padding + 1):
        for dx in range(-padding, dx + 1):
            if layout[y + dy][x + dx] != 0:
                return False
    return True


def _generate_simple_dungeon(width, height):
    """Generates a simple, empty square dungeon."""
    layout = [[1 for _ in range(width)] for _ in range(height)]
    # Create the floor, now a complete border
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            layout[y][x] = 0
    return layout

def _generate_maze_dungeon(width, height):
    """
    Generates a maze using a simplified randomized depth-first search (DFS).
    This algorithm inherently creates a "perfect" maze, which means it is
    fully interconnected with no loops or inaccessible areas.
    """
    # Initialize the grid with walls everywhere
    layout = [[1 for _ in range(width)] for _ in range(height)]
    stack = []
    
    # Start at a random even-numbered cell within the inner grid
    # We use a 2-step increment to ensure we are always on a cell we can "carve" from
    start_x = random.randrange(1, width - 1, 2)
    start_y = random.randrange(1, height - 1, 2)
    
    layout[start_y][start_x] = 0
    stack.append((start_x, start_y))

    while stack:
        current_x, current_y = stack.pop()
        
        # Define possible neighbors to move to (2 steps away)
        neighbors = []
        if current_x > 1: neighbors.append((current_x - 2, current_y))
        if current_x < width - 2: neighbors.append((current_x + 2, current_y))
        if current_y > 1: neighbors.append((current_x, current_y - 2))
        if current_y < height - 2: neighbors.append((current_x, current_y + 2))

        unvisited_neighbors = []
        for nx, ny in neighbors:
            # Check if the neighbor is a wall (hasn't been visited yet)
            if layout[ny][nx] == 1:
                unvisited_neighbors.append((nx, ny))

        if unvisited_neighbors:
            stack.append((current_x, current_y))
            next_x, next_y = random.choice(unvisited_neighbors)
            
            # Carve a path to the neighbor
            wall_x = current_x + (next_x - current_x) // 2
            wall_y = current_y + (next_y - current_y) // 2
            layout[wall_y][wall_x] = 0
            layout[next_y][next_x] = 0
            
            stack.append((next_x, next_y))
            
    # Explicitly set the border to be walls to ensure a contained maze.
    for y in range(height):
        layout[y][0] = 1  # Left edge
        layout[y][width - 1] = 1  # Right edge
    for x in range(width):
        layout[0][x] = 1  # Top edge
        layout[height - 1][x] = 1  # Bottom edge
            
    return layout

def _create_open_spaces(layout, width, height, num_spaces=3, min_size=3, max_size=6):
    """
    Randomly carves out large, open spaces within the maze.
    This helps break up the winding paths and creates more open areas.
    By anchoring new rooms to existing floor tiles, this function ensures
    that all carved rooms are connected to the main maze path, preventing
    the creation of unreachable areas.
    """
    for _ in range(num_spaces):
        # Find all floor tiles to ensure the new room connects to an existing path.
        floor_tiles = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if layout[y][x] == 0:
                    floor_tiles.append((x, y))
        
        # If there's no floor to connect to, we can't add a room.
        if not floor_tiles:
            return

        # Choose a random size for the new room
        space_width = random.randint(min_size, max_size)
        space_height = random.randint(min_size, max_size)

        # Pick a random existing floor tile as an "anchor"
        anchor_x, anchor_y = random.choice(floor_tiles)
        
        # Determine the top-left corner of the new room so that it overlaps
        # with the anchor tile. This guarantees connectivity.
        x_start = random.randint(anchor_x - space_width + 1, anchor_x)
        y_start = random.randint(anchor_y - space_height + 1, anchor_y)
        
        # Clamp the coordinates to ensure the room stays within the dungeon boundaries.
        x_start = max(1, x_start)
        y_start = max(1, y_start)
        x_start = min(x_start, width - space_width - 1)
        y_start = min(y_start, height - space_height - 1)

        # Carve out the room area by setting tiles to 0 (floor).
        for y in range(y_start, y_start + space_height):
            for x in range(x_start, x_start + space_width):
                # Final check to stay within the inner walls
                if 1 <= x < width - 1 and 1 <= y < height - 1:
                    layout[y][x] = 0

def generate_dungeon(level):
    """Generates a full dungeon with all objects based on the level."""
    width = HORIZONTAL_TILES
    height = VERTICAL_TILES

    # Check if it's a boss level
    is_boss_level = (level % 4 == 0) and level > 0

    if level == 1:
        layout = _generate_simple_dungeon(width, height)
    else:
        layout = _generate_maze_dungeon(width, height)
        _create_open_spaces(layout, width, height)

    floor_tiles = [(x, y) for y in range(1, height - 1) for x in range(1, width - 1) if layout[y][x] == 0]

    player_spawn_pos = None
    npcs_to_spawn = []
    keys_to_spawn = []
    power_ups_to_spawn = []
    enemies_to_spawn = []
    torches_to_spawn = []
    bosses_to_spawn = []

    # --- UNIFIED SPAWNING LOGIC ---
    # Determine how many unique positions we need for essential items.
    # Regular level: player, key, npc, 3 power-ups = 6
    # Boss level: player, npc, 3 power-ups, boss = 6
    num_essential_items = 6

    if len(floor_tiles) < num_essential_items:
        chosen_positions = random.sample(floor_tiles, len(floor_tiles))
    else:
        chosen_positions = random.sample(floor_tiles, num_essential_items)

    positions_to_assign = list(chosen_positions)
    def get_pos():
        return positions_to_assign.pop(0) if positions_to_assign else None

    # Assign positions to all items
    player_spawn_pos = get_pos()
    npc_pos = get_pos()
    heal_pos = get_pos()
    enemy_bomb_pos = get_pos()
    fog_clear_pos = get_pos()
    
    # The final essential item is either a key (on normal levels) or a boss
    if is_boss_level:
        key_pos = None
        boss_pos = get_pos()
    else:
        key_pos = get_pos()
        boss_pos = None

    if player_spawn_pos is None:
        player_spawn_pos = (width // 2, height // 2)

    # Remove the used tiles from the available pool for other spawns
    floor_tiles = [tile for tile in floor_tiles if tile not in chosen_positions]
    
    # Create the objects based on their assigned positions
    if npc_pos: npcs_to_spawn.append({"pos": npc_pos, "dialogue": random.choice(NPC_DIALOGUES), "patrol_range": 20})
    if key_pos: keys_to_spawn.append({"pos": key_pos})
    if heal_pos: power_ups_to_spawn.append({"pos": heal_pos, "type": "heal"})
    if enemy_bomb_pos: power_ups_to_spawn.append({"pos": enemy_bomb_pos, "type": "enemy_bomb"})
    if fog_clear_pos: power_ups_to_spawn.append({"pos": fog_clear_pos, "type": "fog_clear"})
    if boss_pos: bosses_to_spawn.append({"pos": boss_pos})

    # Spawn enemies (now on all levels, including boss levels)
    num_enemies = min(level * 2, len(floor_tiles))
    enemy_patrol_range = 50 + 25 * level
    enemy_speed = 2 + 0.5 * level
    for _ in range(num_enemies):
        if not floor_tiles: break
        enemy_pos = random.choice(floor_tiles)
        floor_tiles.remove(enemy_pos)
        enemies_to_spawn.append({"pos": enemy_pos, "patrol_range": enemy_patrol_range, "speed": enemy_speed})

    # Spawn torches (now on all levels, including boss levels)
    num_torches = 7
    for _ in range(num_torches):
        if not floor_tiles: break
        torch_pos = random.choice(floor_tiles)
        floor_tiles.remove(torch_pos)
        torches_to_spawn.append({"pos": torch_pos})

    # --- Door Placement (remains the same) ---
    door_pos = None
    wall_tiles = [(x, y) for y in range(height) for x in range(width) if layout[y][x] == 1 and (y in [0, height-1] or x in [0, width-1])]
    
    if wall_tiles:
        door_pos = random.choice(wall_tiles)
    else:
        door_pos = (width - 1, height // 2)

    layout[door_pos[1]][door_pos[0]] = 0
    if door_pos[1] == 0 and height > 1: layout[1][door_pos[0]] = 0
    elif door_pos[1] == height - 1 and height > 1: layout[height - 2][door_pos[0]] = 0
    elif door_pos[0] == 0 and width > 1: layout[door_pos[1]][1] = 0
    elif door_pos[0] == width - 1 and width > 1: layout[door_pos[1]][width - 2] = 0

    return {
        "layout": layout,
        "npcs": npcs_to_spawn,
        "enemies": enemies_to_spawn,
        "torches": torches_to_spawn,
        "doors": [{"pos": door_pos, "locked": True}],
        "keys": keys_to_spawn,
        "power_ups": power_ups_to_spawn,
        "player_spawn_pos": player_spawn_pos,
        "bosses": bosses_to_spawn
    }

# NEW FOG OF WAR GLOBAL VARIABLES
# Use the same tile counts to ensure consistency
TILE_GRID_WIDTH = HORIZONTAL_TILES
TILE_GRID_HEIGHT = VERTICAL_TILES
visited_tiles = np.zeros((TILE_GRID_HEIGHT, TILE_GRID_WIDTH), dtype=bool)


def load_map(map_data):
    """Loads a new map from the generated map data."""
    global player, walls, npcs, torches, active_dialogue, keys, doors, enemies, bosses, visited_tiles, power_ups, particle_group, footstep_group
    
    # Reset game objects for the new map
    walls = []
    npcs = pygame.sprite.Group()
    torches = pygame.sprite.Group()
    doors = pygame.sprite.Group()
    keys = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bosses = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    particle_group.empty() # Clear particles on new level
    footstep_group.empty() # Clear footsteps on new level
    active_dialogue = None
    
    # Reset visited tiles for the new map
    visited_tiles = np.zeros((TILE_GRID_HEIGHT, TILE_GRID_WIDTH), dtype=bool)

    # Populate walls from map layout
    for row_idx, row in enumerate(map_data["layout"]):
        for col_idx, cell in enumerate(row):
            if cell == 1:
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE
                rect_height = TILE_SIZE
                # For the last row, stretch the wall's height to fill the remaining screen space.
                # This prevents a gap from forming between the dungeon and the bottom of the screen.
                if row_idx == len(map_data["layout"]) - 1:
                    rect_height = SCREEN_HEIGHT - y
                wall_rect = pygame.Rect(x, y, TILE_SIZE, rect_height)
                # MODIFIED: Walls are now dictionaries with increased health
                walls.append({'rect': wall_rect, 'health': 5, 'hit_timer': 0})

    # Place player at the specified spawn position
    spawn_pos = (map_data["player_spawn_pos"][0] * TILE_SIZE, map_data["player_spawn_pos"][1] * TILE_SIZE)
    # The player object is now initialized in the main function
    if player:
        player.rect.center = (spawn_pos[0] + TILE_SIZE/2, spawn_pos[1] + TILE_SIZE/2)
        player.has_key = False # Reset key on new map
        player.life_points = player.max_life_points # Reset life points to new max
        player.inventory = [] # Reset inventory
        player.stamina = player.max_stamina # Refill stamina on new level
    else:
        player = Player(spawn_pos[0], spawn_pos[1])

    # Create NPCs from map data
    for npc_data in map_data["npcs"]:
        npcs.add(NPC(npc_data["pos"][0] * TILE_SIZE, npc_data["pos"][1] * TILE_SIZE, npc_data["dialogue"], npc_data["patrol_range"]))

    # Create enemies from map data
    for enemy_data in map_data["enemies"]:
        enemies.add(Enemy(enemy_data["pos"][0] * TILE_SIZE, enemy_data["pos"][1] * TILE_SIZE, enemy_data["patrol_range"], enemy_data["speed"]))

    # Create bosses from map data
    for boss_data in map_data.get("bosses", []):
        bosses.add(Boss(boss_data["pos"][0] * TILE_SIZE, boss_data["pos"][1] * TILE_SIZE))

    # Create torches from map data
    for torch_data in map_data["torches"]:
        torches.add(Torch(torch_data["pos"][0] * TILE_SIZE + TILE_SIZE // 2, torch_data["pos"][1] * TILE_SIZE + TILE_SIZE // 2))

    # Create keys from map data
    for key_data in map_data["keys"]:
        keys.add(Key(key_data["pos"][0] * TILE_SIZE, key_data["pos"][1] * TILE_SIZE))
    
    # Create doors from map data
    for door_data in map_data["doors"]:
        door_x = door_data["pos"][0] * TILE_SIZE
        door_y = door_data["pos"][1] * TILE_SIZE
        
        # Create a door instance with default size
        new_door = Door(door_x, door_y, door_data["locked"])

        # If the door is on the last row, stretch its height to match the walls
        if door_data["pos"][1] == len(map_data["layout"]) - 1:
            door_height = SCREEN_HEIGHT - door_y
            new_door.image = pygame.Surface((TILE_SIZE, door_height))
            new_door.image.fill(DOOR_COLOR)
            new_door.rect = new_door.image.get_rect(topleft=(door_x, door_y))
        
        doors.add(new_door)

    # Create power-ups from map data
    for pu_data in map_data["power_ups"]:
        color = None
        if pu_data["type"] == "heal":
            color = HEAL_COLOR
        elif pu_data["type"] == "enemy_bomb":
            color = ENEMY_BOMB_COLOR
        elif pu_data["type"] == "fog_clear":
            color = FOG_CLEAR_COLOR
        if color:
            power_ups.add(PowerUp(pu_data["pos"][0] * TILE_SIZE, pu_data["pos"][1] * TILE_SIZE, color, pu_data["type"]))


# Initial map load
current_dungeon_data = generate_dungeon(current_level)
# Add the 'player' and other group variable initializations here.
player = None
particle_group = pygame.sprite.Group()
footstep_group = pygame.sprite.Group()
bosses = pygame.sprite.Group()
load_map(current_dungeon_data)

# --- Leaderboard Data ---
leaderboard = []

def add_to_leaderboard(score, level):
    """Adds a new score and level to the temporary leaderboard and keeps it sorted."""
    global leaderboard
    leaderboard.append({"score": score, "level": level})
    # Sort in descending order by score
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    # Keep only the top 10 scores
    leaderboard = leaderboard[:10]

# --- Functions for drawing different screens ---

def get_key_name(key_code):
    """Converts a pygame key code to a readable string."""
    return pygame.key.name(key_code).upper()

def draw_menu(menu_entities_group):
    """Draws the main menu screen."""
    screen.fill(BLACK)
    
    # NEW: Draw the floating menu entities for ambience
    menu_entities_group.draw(screen)
    
    # Title text
    title_text = font.render("Ghost Maze: A Hero's Journey", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)
    
    # Start button text
    start_text = small_font.render("Start Game", True, WHITE)
    start_rect = start_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    
    # Options button text (new)
    options_text = small_font.render("Options", True, WHITE)
    options_rect = options_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 70))
    
    # Leaderboard button (NEW)
    leaderboard_text = small_font.render("Leaderboard", True, WHITE)
    leaderboard_rect = leaderboard_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 140))

    # Quit button text (new)
    quit_text = small_font.render("Quit Game", True, WHITE)
    quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 210))
    
    # Simple button logic: change color on hover
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw Start button
    start_button_color = GREEN if start_rect.inflate(20, 10).collidepoint(mouse_pos) else DARK_GREEN
    pygame.draw.rect(screen, start_button_color, start_rect.inflate(20, 10), border_radius=10)
    screen.blit(start_text, start_rect)
    
    # Draw Options button
    options_button_color = GREEN if options_rect.inflate(20, 10).collidepoint(mouse_pos) else DARK_GREEN
    pygame.draw.rect(screen, options_button_color, options_rect.inflate(20, 10), border_radius=10)
    screen.blit(options_text, options_rect)
    
    # Draw Leaderboard button
    leaderboard_button_color = GREEN if leaderboard_rect.inflate(20, 10).collidepoint(mouse_pos) else DARK_GREEN
    pygame.draw.rect(screen, leaderboard_button_color, leaderboard_rect.inflate(20, 10), border_radius=10)
    screen.blit(leaderboard_text, leaderboard_rect)

    # Draw Quit button
    quit_button_color = GREEN if quit_rect.inflate(20, 10).collidepoint(mouse_pos) else DARK_GREEN
    pygame.draw.rect(screen, quit_button_color, quit_rect.inflate(20, 10), border_radius=10)
    screen.blit(quit_text, quit_rect)

def draw_options_menu():
    """Draws the options menu screen."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("Options", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)

    # Audio button
    audio_text = small_font.render("Audio", True, WHITE)
    audio_rect = audio_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
    audio_button_color = GREEN if audio_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, audio_button_color, audio_rect.inflate(20, 10), border_radius=10)
    screen.blit(audio_text, audio_rect)

    # Controls button
    controls_text = small_font.render("Controls", True, WHITE)
    controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    controls_button_color = GREEN if controls_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, controls_button_color, controls_rect.inflate(20, 10), border_radius=10)
    screen.blit(controls_text, controls_rect)

    # Back button
    back_text = small_font.render("Back", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
    back_button_color = GREEN if back_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, back_button_color, back_rect.inflate(20, 10), border_radius=10)
    screen.blit(back_text, back_rect)

def draw_audio_menu():
    """Draws a placeholder for the audio settings menu."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("Audio Settings", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)

    # Volume Slider
    slider_width = 300
    slider_height = 20
    slider_x = SCREEN_WIDTH / 2 - slider_width / 2
    slider_y = SCREEN_HEIGHT / 2 - 50
    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
    
    # Draw slider background
    pygame.draw.rect(screen, DARK_GREEN, slider_rect, border_radius=5)
    
    # Draw the current volume level bar
    volume_bar_width = slider_width * music_volume
    volume_bar_rect = pygame.Rect(slider_x, slider_y, volume_bar_width, slider_height)
    pygame.draw.rect(screen, GREEN, volume_bar_rect, border_radius=5)
    
    # Draw the slider handle
    handle_x = slider_x + volume_bar_width
    handle_rect = pygame.Rect(handle_x - 5, slider_y - 5, 10, slider_height + 10)
    pygame.draw.rect(screen, WHITE, handle_rect)
    
    # Volume text
    volume_text = small_font.render(f"Volume: {int(music_volume * 100)}%", True, WHITE)
    volume_rect = volume_text.get_rect(center=(SCREEN_WIDTH / 2, slider_y - 30))
    screen.blit(volume_text, volume_rect)

    # Mute button
    mute_text_str = "Unmute" if is_muted else "Mute"
    mute_text = small_font.render(mute_text_str, True, WHITE)
    mute_rect = mute_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30))
    mute_button_color = GREEN if mute_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, mute_button_color, mute_rect.inflate(20, 10), border_radius=10)
    screen.blit(mute_text, mute_rect)

    # Back button
    back_text = small_font.render("Back", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100))
    back_button_color = GREEN if back_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, back_button_color, back_rect.inflate(20, 10), border_radius=10)
    screen.blit(back_text, back_rect)


def draw_controls_menu():
    """Draws the controls settings menu with rebindable keys."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("Controls", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)
    
    # Display the keybinding options
    key_y_start = SCREEN_HEIGHT / 2 - 100
    button_x_start = SCREEN_WIDTH / 2 + 50
    
    for i, (action, key_code) in enumerate(KEY_BINDINGS.items()):
        # Action label
        action_name = action.replace('_', ' ').title()
        action_text = small_font.render(action_name, True, WHITE)
        action_rect = action_text.get_rect(right=SCREEN_WIDTH / 2 - 10, centery=key_y_start + i * 50)
        screen.blit(action_text, action_rect)
        
        # Key button
        key_name = get_key_name(key_code)
        key_text = small_font.render(key_name, True, WHITE)
        
        # Check if this is the key currently being re-bound
        if rebind_target == action:
            key_text = small_font.render("Press a key...", True, WHITE)
            key_button_color = (150, 150, 150) # Gray color to show it's active
        else:
            key_button_color = GREEN if pygame.Rect(button_x_start, action_rect.y - 10, 150, 40).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
        
        key_rect = key_text.get_rect(left=button_x_start, centery=action_rect.centery)
        key_button_rect = key_rect.inflate(20, 10)
        pygame.draw.rect(screen, key_button_color, key_button_rect, border_radius=10)
        screen.blit(key_text, key_rect)

    # Back button
    back_text = small_font.render("Back", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150 + 50))
    back_button_color = GREEN if back_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, back_button_color, back_rect.inflate(20, 10), border_radius=10)
    screen.blit(back_text, back_rect)

def draw_leaderboard():
    """Draws the leaderboard screen."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("Leaderboard", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 8))
    screen.blit(title_text, title_rect)
    
    # Display the scores
    if not leaderboard:
        placeholder_text = small_font.render("No scores yet. Play to get on the board!", True, WHITE)
        placeholder_rect = placeholder_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        screen.blit(placeholder_text, placeholder_rect)
    else:
        y_pos = SCREEN_HEIGHT / 4
        rank_text = small_font.render("Rank    Score    Level", True, WHITE)
        rank_rect = rank_text.get_rect(center=(SCREEN_WIDTH / 2, y_pos))
        screen.blit(rank_text, rank_rect)
        y_pos += 40

        for i, entry in enumerate(leaderboard):
            score_line = f"{i+1}.      {entry['score']}      {entry['level']}"
            score_text = small_font.render(score_line, True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH / 2, y_pos + i * 40))
            screen.blit(score_text, score_rect)
    
    # Back button
    back_text = small_font.render("Back", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50))
    back_button_color = GREEN if back_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, back_button_color, back_rect.inflate(20, 10), border_radius=10)
    screen.blit(back_text, back_rect)

def draw_story_screen(text_lines):
    """Draws a full-screen story message with two lines of text."""
    screen.fill(BLACK)
    
    # Draw a rectangle for the text box
    text_box_rect = pygame.Rect(SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.3, SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.4)
    text_box_color = (20, 20, 20, 150)
    text_box_surface = pygame.Surface(text_box_rect.size, pygame.SRCALPHA)
    text_box_surface.fill(text_box_color)
    screen.blit(text_box_surface, text_box_rect.topleft)
    pygame.draw.rect(screen, WHITE, text_box_rect, 5, border_radius=10)

    # Wrap and render the story text
    story_text = text_lines[0]
    controls_text = text_lines[1]
    
    wrapped_story_text = wrap_text(story_text, dialogue_font, text_box_rect.width - 20)
    wrapped_controls_text = wrap_text(controls_text, dialogue_font, text_box_rect.width - 20)

    line_y = text_box_rect.top + 50
    for line in wrapped_story_text:
        line_surface = dialogue_font.render(line, True, WHITE)
        line_rect = line_surface.get_rect(center=(SCREEN_WIDTH / 2, line_y))
        screen.blit(line_surface, line_rect)
        line_y += 30

    # Add a separator line if both text lines are present
    if story_text and controls_text:
        line_y += 10
        pygame.draw.line(screen, WHITE, (text_box_rect.left + 20, line_y), (text_box_rect.right - 20, line_y))
        line_y += 20
        
    for line in wrapped_controls_text:
        line_surface = dialogue_font.render(line, True, WHITE)
        line_rect = line_surface.get_rect(center=(SCREEN_WIDTH / 2, line_y))
        screen.blit(line_surface, line_rect)
        line_y += 30


    # "Continue" prompt
    continue_text = small_font.render("Press any key to continue...", True, (200, 200, 200))
    continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.8))
    screen.blit(continue_text, continue_rect)

def wrap_text(text, font, max_width):
    """Wraps text to fit within a maximum width."""
    lines = []
    if not text:
        return lines
        
    words = text.split(' ')
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_width, _ = font.size(' '.join(current_line))
        if line_width > max_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    return lines

def draw_game_over():
    """Draws the game over screen."""
    screen.fill(BLACK)
    game_over_text = font.render("Game Over", True, (255, 0, 0))
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))
    screen.blit(game_over_text, game_over_rect)
    
    # Display the final score
    score_text = small_font.render(f"Final Score: {player_score}", True, WHITE)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
    screen.blit(score_text, score_rect)

    # Display the leaderboard (NEW)
    leaderboard_title = small_font.render("Leaderboard", True, WHITE)
    leaderboard_title_rect = leaderboard_title.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(leaderboard_title, leaderboard_title_rect)

    if not leaderboard:
        # This case should not happen if the score is added correctly before drawing this screen, but it's a good fallback
        pass
    else:
        for i, entry in enumerate(leaderboard[:5]): # Show top 5 on game over screen
            score_line = f"{i+1}. Score: {entry['score']} - Level: {entry['level']}"
            score_text = small_font.render(score_line, True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50 + i * 30))
            screen.blit(score_text, score_rect)

    restart_text = small_font.render("Press R to Restart", True, WHITE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 250))
    screen.blit(restart_text, restart_rect)
    
def draw_pause_menu():
    """Draws the pause menu screen as a semi-transparent overlay."""
    # Create a semi-transparent surface
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) # Black with 150/255 opacity
    screen.blit(overlay, (0, 0))

    # Title text
    title_text = font.render("Paused", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))
    screen.blit(title_text, title_rect)

    # Resume button
    resume_text = small_font.render("Resume", True, WHITE)
    resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    resume_button_color = GREEN if resume_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, resume_button_color, resume_rect.inflate(20, 10), border_radius=10)
    screen.blit(resume_text, resume_rect)

    # Exit to Main Menu button
    exit_text = small_font.render("Exit to Main Menu", True, WHITE)
    exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))
    exit_button_color = GREEN if exit_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, exit_button_color, exit_rect.inflate(20, 10), border_radius=10)
    screen.blit(exit_text, exit_rect)

def draw_floor():
    """Draws a tiled floor pattern on the screen."""
    screen.fill(FLOOR_COLOR)
    for y in range(0, SCREEN_HEIGHT, FLOOR_TILE_SIZE):
        for x in range(0, SCREEN_WIDTH, FLOOR_TILE_SIZE):
            # Create a checkerboard pattern
            if (x // FLOOR_TILE_SIZE + y // FLOOR_TILE_SIZE) % 2 == 0:
                pygame.draw.rect(screen, FLOOR_COLOR_2, (x, y, FLOOR_TILE_SIZE, FLOOR_TILE_SIZE))

def draw_game():
    """Draws the main game screen with dungeon, player, and NPCs."""
    # Draw the dungeon floor
    draw_floor()

    # NEW: Draw the footsteps
    footstep_group.draw(screen)
    
    # Draw the dungeon walls
    for wall_dict in walls:
        # If the wall was recently hit, make it flash white
        color = ENEMY_HIT_COLOR if wall_dict['hit_timer'] > 0 else WALL_COLOR
        pygame.draw.rect(screen, color, wall_dict['rect'])

    # Draw the doors, keys, and enemies
    doors.draw(screen)
    keys.draw(screen)
    enemies.draw(screen)
    bosses.draw(screen)
    power_ups.draw(screen)

    # Draw the player and NPCs
    npcs.draw(screen)
    screen.blit(player.image, player.rect)
    # NEW: Draw the hammer
    screen.blit(player.hammer.image, player.hammer.rect)
    
    # NEW: Draw particles
    particle_group.draw(screen)

    # --- Optimized Lighting Effect ---
    # Create a light mask with a transparent background
    light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    # Add a global ambient light that makes the unlit areas not completely dark
    ambient_light_level = 50 # Adjust as needed, from 0 to 255
    light_mask.fill((0, 0, 0, 255 - ambient_light_level))
    
    # Define a radius for the light sources
    light_radius = 200

    # Draw a light circle for each light source
    light_sources = [(s.rect.centerx, s.rect.centery) for s in torches]
    # The player also emits light
    light_sources.append(player.rect.center)
    
    for light_x, light_y in light_sources:
        # Create a surface for a single light gradient
        light_surface = pygame.Surface((light_radius * 2, light_radius * 2), pygame.SRCALPHA)
        # Create a gradient effect
        for i in range(light_radius, 0, -1):
            alpha = 255 - (i / light_radius) * 255
            pygame.draw.circle(light_surface, (255, 255, 255, alpha), (light_radius, light_radius), i)
        
        # Blit the light surface onto the main light mask using a blend mode
        light_mask.blit(light_surface, (light_x - light_radius, light_y - light_radius), special_flags=pygame.BLEND_RGBA_SUB)

    # Apply the final light mask to the screen
    screen.blit(light_mask, (0, 0))

    # --- Fog of War Effect ---
    # Create the fog surface, starting as a solid black overlay
    fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    fog_surface.fill(BLACK) # Start with a completely opaque black
    
    # Define colors for blending
    fog_color_seen_alpha = (0, 0, 0, 100) # Changed from 150 to 100 for a less dark effect
    
    # Convert player's position to tile coordinates
    player_tile_x = player.rect.centerx // TILE_SIZE
    player_tile_y = player.rect.centery // TILE_SIZE
    view_radius_tiles = 3 

    # Mark tiles around the player as visited
    for y_offset in range(-view_radius_tiles, view_radius_tiles + 1):
        for x_offset in range(-view_radius_tiles, view_radius_tiles + 1):
            tile_x = player_tile_x + x_offset
            tile_y = player_tile_y + y_offset
            
            # Check for valid grid coordinates
            if 0 <= tile_x < TILE_GRID_WIDTH and 0 <= tile_y < TILE_GRID_HEIGHT:
                # Mark as visited only if it's within a circle from the player's center
                dist_sq = (tile_x - player_tile_x)**2 + (tile_y - player_tile_y)**2
                if dist_sq <= view_radius_tiles**2:
                    visited_tiles[tile_y, tile_x] = True

    # Use a transparent color to "cut out" the fog
    cutout_color = (0, 0, 0, 0)

    for y in range(TILE_GRID_HEIGHT):
        for x in range(TILE_GRID_WIDTH):
            fog_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if visited_tiles[y, x]:
                # Draw a semi-transparent rectangle on the fog surface
                pygame.draw.rect(fog_surface, fog_color_seen_alpha, fog_rect)

    # Create a clear circle around the player to represent their immediate view
    player_view_radius_pixels = view_radius_tiles * TILE_SIZE
    # Create a transparent circle to "cut out" the current view
    pygame.draw.circle(fog_surface, cutout_color, player.rect.center, player_view_radius_pixels)

    # Blit the fog of war surface onto the screen
    screen.blit(fog_surface, (0, 0))

    # Draw the life bar
    bar_width = 200
    bar_height = 20
    bar_x = 10
    bar_y = 10
    pygame.draw.rect(screen, LIFE_BAR_BG_COLOR, (bar_x, bar_y, bar_width, bar_height))
    # Calculate the life bar width based on the percentage of max life points
    current_life_width = (player.life_points / player.max_life_points) * bar_width
    pygame.draw.rect(screen, LIFE_BAR_COLOR, (bar_x, bar_y, current_life_width, bar_height))
    life_text = small_font.render(f"HP: {player.life_points}", True, WHITE)
    screen.blit(life_text, (bar_x + bar_width + 10, bar_y - 5))
    
    # Draw the stamina bar
    stamina_bar_x = 10
    stamina_bar_y = bar_y + bar_height + 10
    pygame.draw.rect(screen, STAMINA_BAR_BG_COLOR, (stamina_bar_x, stamina_bar_y, bar_width, bar_height))
    current_stamina_width = (player.stamina / player.max_stamina) * bar_width
    pygame.draw.rect(screen, STAMINA_BAR_COLOR, (stamina_bar_x, stamina_bar_y, current_stamina_width, bar_height))
    stamina_text = small_font.render(f"Stamina: {int(player.stamina)}", True, WHITE)
    screen.blit(stamina_text, (stamina_bar_x + bar_width + 10, stamina_bar_y - 5))

    # Draw the score
    score_text = small_font.render(f"Score: {player_score}", True, WHITE)
    score_rect = score_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
    screen.blit(score_text, score_rect)

    # NEW: Draw the level
    level_text = small_font.render(f"Level: {player_level}", True, WHITE)
    level_rect = level_text.get_rect(topright=(SCREEN_WIDTH - 10, score_rect.bottom + 5))
    screen.blit(level_text, level_rect)
    
    # Draw the inventory section
    inventory_x = stamina_bar_x
    inventory_y = stamina_bar_y + bar_height + 10 # Position it below the stamina bar
    
    # Draw a container for the inventory
    inventory_size = 50
    inventory_spacing = 10
    num_slots = 4
    total_inventory_width = (inventory_size + inventory_spacing) * num_slots - inventory_spacing
    
    # Draw each slot
    for i in range(num_slots):
        slot_rect = pygame.Rect(inventory_x + i * (inventory_size + inventory_spacing), inventory_y, inventory_size, inventory_size)
        pygame.draw.rect(screen, WALL_COLOR, slot_rect, 2) # Draw a border for each slot

    # Draw the key icon if the player has the key
    if player.has_key:
        key_icon_rect = pygame.Rect(inventory_x, inventory_y, inventory_size, inventory_size)
        pygame.draw.rect(screen, KEY_COLOR, key_icon_rect)
    
    # Draw collected power-ups
    for i, item_type in enumerate(player.inventory):
        color = None
        if item_type == "heal":
            color = HEAL_COLOR
        elif item_type == "enemy_bomb":
            color = ENEMY_BOMB_COLOR
        elif item_type == "fog_clear":
            color = FOG_CLEAR_COLOR
        if color:
            item_rect = pygame.Rect(inventory_x + (i + 1) * (inventory_size + inventory_spacing), inventory_y, inventory_size, inventory_size)
            pygame.draw.rect(screen, color, item_rect)

def draw_dialogue(text):
    """Draws a dialogue box at the bottom of the screen."""
    # Semi-transparent background
    dialogue_box = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
    dialogue_box.fill((0, 0, 0, 150))
    
    # Dialogue text
    dialogue_text = dialogue_font.render(text, True, WHITE)
    dialogue_rect = dialogue_text.get_rect(center=(SCREEN_WIDTH / 2, 50))
    
    dialogue_box.blit(dialogue_text, dialogue_rect)
    screen.blit(dialogue_box, (0, SCREEN_HEIGHT - 100))

# --- Main Game Loop ---
def main():
    global current_state, active_dialogue, current_map_key, walls, npcs, torches, doors, player, keys, enemies, bosses, current_level, current_dungeon_data, power_ups, visited_tiles, rebind_target, KEY_BINDINGS, music_volume, is_muted, player_score, player_level, score_at_last_level_up, leaderboard, particle_group, footstep_group
    
    # --- NEW: Menu Animation Entities ---
    menu_entities = pygame.sprite.Group()
    # Create a few enemies
    for _ in range(3):
        # Spawn them at random heights, off-screen to the left or right
        start_x = random.choice([-200, SCREEN_WIDTH + 200])
        enemy = Enemy(start_x, random.randint(0, SCREEN_HEIGHT), 0, 0)
        # Set a speed. If starting from the right, make it negative.
        enemy.speed = random.uniform(1.5, 3.5) * (-1 if start_x > SCREEN_WIDTH else 1)
        menu_entities.add(enemy)
    # Create a boss
    boss_start_x = random.choice([-400, SCREEN_WIDTH + 400])
    boss = Boss(boss_start_x, random.randint(0, SCREEN_HEIGHT))
    boss.speed = 1.2 * (-1 if boss_start_x > SCREEN_WIDTH else 1) # Boss is slower
    menu_entities.add(boss)

    running = True
    
    # Store the last unmuted volume level
    last_volume = music_volume
    
    # Timer for footstep creation
    footstep_timer = 0
    
    # Define which states are considered 'menu' states
    menu_states = [
        GAME_STATES["MENU"],
        GAME_STATES["OPTIONS"],
        GAME_STATES["AUDIO_OPTIONS"],
        GAME_STATES["CONTROLS_OPTIONS"],
        GAME_STATES["REBINDING_KEY"],
        GAME_STATES["LEADERBOARD"]
    ]
    
    while running:
        # --- Menu Melody Logic ---
        if current_state in menu_states:
            if not is_muted:
                # Set volume and play if not already playing
                pygame.mixer.Channel(1).set_volume(music_volume)
                if not pygame.mixer.Channel(1).get_busy():
                    pygame.mixer.Channel(1).play(menu_melody_sound, -1) # Loop indefinitely
            else:
                # Stop the music if muted
                pygame.mixer.Channel(1).stop()
        else:
            # If not in a menu state, stop the melody
            pygame.mixer.Channel(1).stop()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if current_state == GAME_STATES["MENU"]:
                    start_text_rect = small_font.render("Start Game", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                    start_button_rect = start_text_rect.inflate(20, 10)
                    
                    options_text_rect = small_font.render("Options", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 70))
                    options_button_rect = options_text_rect.inflate(20, 10)
                    
                    leaderboard_text_rect = small_font.render("Leaderboard", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 140))
                    leaderboard_button_rect = leaderboard_text_rect.inflate(20, 10)

                    quit_text_rect = small_font.render("Quit Game", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 210))
                    quit_button_rect = quit_text_rect.inflate(20, 10)
                    
                    if start_button_rect.collidepoint(mouse_pos):
                        print("Starting game...")
                        # Reset game state for a new game
                        current_level = 1
                        player_score = 0
                        player_level = 1
                        score_at_last_level_up = 0
                        current_dungeon_data = generate_dungeon(current_level)
                        load_map(current_dungeon_data)
                        
                        # NEW: Check for story event on level 1
                        if current_level in STORY_EVENTS:
                            current_state = GAME_STATES["STORY"]
                        else:
                            current_state = GAME_STATES["GAME"]
                        continue
                    elif options_button_rect.collidepoint(mouse_pos):
                        print("Opening options menu...")
                        current_state = GAME_STATES["OPTIONS"]
                        continue
                    elif leaderboard_button_rect.collidepoint(mouse_pos):
                        print("Opening leaderboard...")
                        current_state = GAME_STATES["LEADERBOARD"]
                        continue
                    elif quit_button_rect.collidepoint(mouse_pos):
                        running = False
                elif current_state == GAME_STATES["OPTIONS"]:
                    audio_text_rect = small_font.render("Audio", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
                    audio_button_rect = audio_text_rect.inflate(20, 10)
                    
                    controls_text_rect = small_font.render("Controls", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                    controls_button_rect = controls_text_rect.inflate(20, 10)
                    
                    back_text_rect = small_font.render("Back", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
                    back_button_rect = back_text_rect.inflate(20, 10)
                    
                    if audio_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["AUDIO_OPTIONS"]
                        continue
                    elif controls_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["CONTROLS_OPTIONS"]
                        continue
                    elif back_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["MENU"]
                        continue
                elif current_state == GAME_STATES["AUDIO_OPTIONS"]:
                    back_text_rect = small_font.render("Back", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100))
                    back_button_rect = back_text_rect.inflate(20, 10)
                    
                    # Volume Slider
                    slider_width = 300
                    slider_height = 20
                    slider_x = SCREEN_WIDTH / 2 - slider_width / 2
                    slider_y = SCREEN_HEIGHT / 2 - 50
                    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
                    
                    # Mute button
                    mute_text_rect = small_font.render("Mute", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30))
                    mute_button_rect = mute_text_rect.inflate(20, 10)
                    
                    if slider_rect.collidepoint(mouse_pos):
                        # Calculate new volume based on mouse position
                        new_volume = (mouse_pos[0] - slider_x) / slider_width
                        music_volume = max(0, min(1, new_volume))
                        pygame.mixer.music.set_volume(music_volume)
                        pygame.mixer.Channel(0).set_volume(music_volume) # Also set channel volume
                        is_muted = False # Unmute if the slider is adjusted
                        last_volume = music_volume
                    elif mute_button_rect.collidepoint(mouse_pos):
                        is_muted = not is_muted
                        if is_muted:
                            pygame.mixer.music.set_volume(0)
                            pygame.mixer.Channel(0).set_volume(0) # Also mute the footstep channel
                        else:
                            pygame.mixer.music.set_volume(last_volume)
                            pygame.mixer.Channel(0).set_volume(last_volume) # Also unmute the footstep channel
                    elif back_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["OPTIONS"]
                        continue
                elif current_state == GAME_STATES["CONTROLS_OPTIONS"]:
                    back_text_rect = small_font.render("Back", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 200))
                    
                    # Handle clicks on the keybinding buttons
                    key_y_start = SCREEN_HEIGHT / 2 - 100
                    button_x_start = SCREEN_WIDTH / 2 + 50
                    
                    rebinding_clicked = False
                    for i, (action, key_code) in enumerate(KEY_BINDINGS.items()):
                        key_rect = small_font.render(get_key_name(key_code), True, WHITE).get_rect(left=button_x_start, centery=key_y_start + i * 50)
                        key_button_rect = key_rect.inflate(20, 10)
                        if key_button_rect.collidepoint(mouse_pos):
                            rebind_target = action
                            current_state = GAME_STATES["REBINDING_KEY"]
                            rebinding_clicked = True
                            break
                    if rebinding_clicked:
                        continue

                    back_button_rect = back_text_rect.inflate(20, 10)
                    if back_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["OPTIONS"]
                        continue
                elif current_state == GAME_STATES["LEADERBOARD"]:
                    back_text_rect = small_font.render("Back", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50))
                    back_button_rect = back_text_rect.inflate(20, 10)
                    if back_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["MENU"]
                        continue
                elif current_state == GAME_STATES["PAUSED"]:
                    resume_text_rect = small_font.render("Resume", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                    resume_button_rect = resume_text_rect.inflate(20, 10)
                    
                    exit_text_rect = small_font.render("Exit to Main Menu", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))
                    exit_button_rect = exit_text_rect.inflate(20, 10)
                    
                    if resume_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["GAME"]
                        continue
                    elif exit_button_rect.collidepoint(mouse_pos):
                        # Reset all game state variables
                        current_level = 1
                        player_score = 0
                        player_level = 1
                        score_at_last_level_up = 0
                        
                        # The player object will be recreated in load_map when the new game starts
                        player = None
                        current_dungeon_data = generate_dungeon(current_level)
                        load_map(current_dungeon_data)
                        
                        current_state = GAME_STATES["MENU"]
                        continue

            elif event.type == pygame.KEYDOWN:
                if current_state == GAME_STATES["REBINDING_KEY"]:
                    # Re-bind the key
                    if rebind_target:
                        KEY_BINDINGS[rebind_target] = event.key
                        rebind_target = None
                        current_state = GAME_STATES["CONTROLS_OPTIONS"]
                        continue
                elif event.key == pygame.K_ESCAPE:
                    if current_state == GAME_STATES["GAME"]:
                        current_state = GAME_STATES["PAUSED"]
                        continue
                    elif current_state == GAME_STATES["PAUSED"]:
                        current_state = GAME_STATES["GAME"]
                        continue
                    elif current_state == GAME_STATES["GAME_OVER"]:
                        running = False
                elif current_state == GAME_STATES["STORY"]:
                    current_state = GAME_STATES["GAME"]
                    continue
                elif current_state == GAME_STATES["DIALOGUE"]:
                    # Press any key to exit dialogue
                    active_dialogue = None
                    current_state = GAME_STATES["GAME"]
                    continue
                elif current_state == GAME_STATES["GAME_OVER"]:
                    if event.key == pygame.K_r:
                        # Restart the game from level 1
                        current_level = 1
                        player_score = 0
                        player_level = 1
                        score_at_last_level_up = 0
                        player = None # Reset player object
                        current_dungeon_data = generate_dungeon(current_level)
                        load_map(current_dungeon_data)
                        current_state = GAME_STATES["MENU"]
                        continue
                elif current_state == GAME_STATES["GAME"]:
                    if event.key == KEY_BINDINGS["interact"]:
                        # Swing hammer is an independent combat action.
                        player.hammer.swing()
                        
                        # Create an interaction rect for non-combat interactions.
                        interaction_rect = player.rect.inflate(TILE_SIZE // 2, TILE_SIZE // 2)

                        # --- BUG FIX: Prioritized Interaction Logic ---
                        # This structure ensures only one interaction (NPC, Key, Power-up, Door)
                        # happens per key press, preventing the bug where the key and door
                        # could be interacted with simultaneously.

                        # Check for an NPC to talk to.
                        collided_npc = None
                        for npc in npcs:
                            if interaction_rect.colliderect(npc.rect):
                                collided_npc = npc
                                break
                        
                        # Check for a key to pick up. This requires direct collision with the player.
                        key_to_collect = pygame.sprite.spritecollideany(player, keys)

                        # Check for a power-up to pick up. This requires direct collision.
                        power_up_to_collect = pygame.sprite.spritecollideany(player, power_ups)

                        # 1. NPC interaction has the highest priority.
                        if collided_npc:
                            player.life_points = min(player.max_life_points, player.life_points + 20)
                            create_particles(player.rect.centerx, player.rect.centery, HEAL_COLOR, 15, 'healing')
                            active_dialogue = f"{collided_npc.dialogue} You feel better. HP is now {player.life_points}/{player.max_life_points}."
                            current_state = GAME_STATES["DIALOGUE"]
                            play_sound(dialogue_sound)
                            continue
                        
                        # 2. Key collection is next. This ensures the key is in the player's
                        # possession before any door interaction can be attempted on a later key press.
                        elif key_to_collect:
                            keys.remove(key_to_collect)
                            player.has_key = True
                            player_score += 100
                            active_dialogue = "You found a key! It might open something."
                            current_state = GAME_STATES["DIALOGUE"]
                            play_sound(collect_sound)
                            continue

                        # 3. Power-up collection follows.
                        elif power_up_to_collect:
                            if power_up_to_collect.type == "heal":
                                player.life_points = min(player.max_life_points, player.life_points + 50)
                                create_particles(player.rect.centerx, player.rect.centery, HEAL_COLOR, 15, 'healing')
                                player_score += 50
                                active_dialogue = f"You used a healing potion! HP restored to {player.life_points}/{player.max_life_points}."
                            elif power_up_to_collect.type == "enemy_bomb":
                                player_score += 75
                                for enemy in enemies:
                                    create_particles(enemy.rect.centerx, enemy.rect.centery, ENEMY_COLOR, 30, 'explosion')
                                enemies.empty()
                                active_dialogue = "All enemies have been vanquished!"
                            elif power_up_to_collect.type == "fog_clear":
                                player_score += 25
                                visited_tiles.fill(True)
                                active_dialogue = "The fog of war has been lifted!"
                            
                            # Add the power-up to inventory and remove it from the map.
                            player.inventory.append(power_up_to_collect.type)
                            power_ups.remove(power_up_to_collect)
                            current_state = GAME_STATES["DIALOGUE"]
                            play_sound(collect_sound)
                            continue

                        # 4. Door interaction is the last resort.
                        else:
                            door_interacted = False
                            for door in doors:
                                # Check for collision with a locked door.
                                if door.locked and interaction_rect.colliderect(door.rect):
                                    if player.has_key:
                                        door.locked = False
                                        player.has_key = False # Use the key.
                                        play_sound(unlock_sound)
                                        active_dialogue = "The door is now unlocked. You can pass."
                                        current_state = GAME_STATES["DIALOGUE"]
                                    else:
                                        active_dialogue = "The door is locked. You need a key."
                                        current_state = GAME_STATES["DIALOGUE"]
                                    # Only interact with the first door found.
                                    door_interacted = True
                                    break
                            if door_interacted:
                                continue
            
            elif event.type == pygame.KEYUP:
                if event.key == KEY_BINDINGS["sprint"]:
                    player.is_sprinting = False
                # Stop footstep sound when movement keys are released
                if event.key in [KEY_BINDINGS["move_up"], KEY_BINDINGS["move_down"], KEY_BINDINGS["move_left"], KEY_BINDINGS["move_right"], pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    if not any(pygame.key.get_pressed()[k] for k in [KEY_BINDINGS["move_up"], KEY_BINDINGS["move_down"], KEY_BINDINGS["move_left"], KEY_BINDINGS["move_right"], pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]):
                        pygame.mixer.Channel(0).stop()

        if current_state == GAME_STATES["MENU"]:
            # --- NEW: Menu Animation Logic ---
            for entity in menu_entities:
                # Move the entity
                entity.rect.x += entity.speed

                # If entity goes off-screen, reset its position on the opposite side
                if entity.speed > 0 and entity.rect.left > SCREEN_WIDTH: # Moving right
                    entity.rect.right = 0
                    entity.rect.y = random.randint(0, SCREEN_HEIGHT - entity.rect.height)
                elif entity.speed < 0 and entity.rect.right < 0: # Moving left
                    entity.rect.left = SCREEN_WIDTH
                    entity.rect.y = random.randint(0, SCREEN_HEIGHT - entity.rect.height)
            draw_menu(menu_entities)
        elif current_state == GAME_STATES["OPTIONS"]:
            draw_options_menu()
        elif current_state == GAME_STATES["AUDIO_OPTIONS"]:
            draw_audio_menu()
        elif current_state == GAME_STATES["CONTROLS_OPTIONS"]:
            draw_controls_menu()
        elif current_state == GAME_STATES["REBINDING_KEY"]:
            draw_controls_menu() # Keep drawing the controls menu
        elif current_state == GAME_STATES["LEADERBOARD"]:
            draw_leaderboard()
        elif current_state == GAME_STATES["STORY"]:
            draw_story_screen(STORY_EVENTS.get(current_level, ("", "")))
        elif current_state == GAME_STATES["PAUSED"]:
            draw_game() # Draw the game screen first
            draw_pause_menu() # Then draw the overlay on top
        elif current_state == GAME_STATES["GAME"]:
            # Player input
            keys_pressed = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            # Check for sprinting key and sufficient stamina
            if keys_pressed[KEY_BINDINGS["sprint"]] and player.stamina > 0:
                player.is_sprinting = True
            else:
                player.is_sprinting = False

            # Check for movement using both WASD and arrow keys
            if keys_pressed[KEY_BINDINGS["move_up"]] or keys_pressed[pygame.K_UP]:
                dy -= 1
            if keys_pressed[KEY_BINDINGS["move_down"]] or keys_pressed[pygame.K_DOWN]:
                dy += 1
            if keys_pressed[KEY_BINDINGS["move_left"]] or keys_pressed[pygame.K_LEFT]:
                dx -= 1
            if keys_pressed[KEY_BINDINGS["move_right"]] or keys_pressed[pygame.K_RIGHT]:
                dx += 1
                
            # Play or stop footstep sound based on movement
            if dx != 0 or dy != 0:
                if not pygame.mixer.Channel(0).get_busy():
                    if not is_muted:
                        pygame.mixer.Channel(0).set_volume(music_volume)
                        pygame.mixer.Channel(0).play(footstep_sound, -1) # Play on a loop
                # Create footsteps
                footstep_timer += 1
                if footstep_timer > 10:
                    footstep_group.add(Footstep(player.rect.centerx, player.rect.centery))
                    footstep_timer = 0
            else:
                pygame.mixer.Channel(0).stop()
                footstep_timer = 0 # Reset timer when not moving

            player.update(dx, dy, walls, doors)

            # Update enemies, NPCs, walls, particles, and footsteps
            enemies.update(player)
            bosses.update(player)
            npcs.update()
            particle_group.update()
            footstep_group.update()
            for wall_dict in walls:
                if wall_dict['hit_timer'] > 0:
                    wall_dict['hit_timer'] -= 1

            # Hammer attack collision
            if player.hammer.swinging:
                # Check for collision between the hammer and enemies
                enemies_hit = pygame.sprite.spritecollide(player.hammer, enemies, False)
                for enemy in enemies_hit:
                    enemy.take_damage(1)
                
                # Check for collision between the hammer and bosses
                bosses_hit = pygame.sprite.spritecollide(player.hammer, bosses, False)
                for boss in bosses_hit:
                    boss.take_damage(1)

                # NEW: Check for collision between the hammer and walls
                for wall_dict in walls[:]: # Iterate a copy for safe removal
                    if wall_dict['hit_timer'] == 0 and player.hammer.rect.colliderect(wall_dict['rect']):
                        wall_dict['health'] -= 1
                        wall_dict['hit_timer'] = player.hammer.swing_duration
                        
                        if wall_dict['health'] <= 0:
                            create_particles(wall_dict['rect'].centerx, wall_dict['rect'].centery, WALL_COLOR, 20, 'explosion')
                            walls.remove(wall_dict)
                            player_score += 10 # Small reward
                            play_sound(wall_destroy_sound) # Play destruction sound
                        else:
                            play_sound(enemy_hit_sound) # Play hit sound

            # Check for dead enemies and remove them
            for enemy in list(enemies): # Iterate over a copy to allow removal
                if enemy.life_points <= 0:
                    player_score += 150 # Award points for defeating an enemy
                    create_particles(enemy.rect.centerx, enemy.rect.centery, ENEMY_COLOR, 30, 'explosion')
                    enemies.remove(enemy)

            # Check for dead bosses
            for boss in list(bosses):
                if boss.life_points <= 0:
                    player_score += 1000
                    create_particles(boss.rect.centerx, boss.rect.centery, BOSS_COLOR, 100, 'explosion')
                    
                    # Spawn a key at the boss's location
                    keys.add(Key(boss.rect.x, boss.rect.y))
                    
                    bosses.remove(boss)
                    # The door is no longer automatically unlocked. The player must collect the key.

            # Check for enemy/boss collision with player
            if player.invulnerable_timer == 0:
                collided_with = None
                damage_to_take = 0

                enemy_collision = pygame.sprite.spritecollideany(player, enemies)
                if enemy_collision:
                    collided_with = enemy_collision
                    damage_to_take = BASE_ENEMY_DAMAGE + (player_level * DAMAGE_SCALING_PER_LEVEL)
                
                boss_collision = pygame.sprite.spritecollideany(player, bosses)
                if boss_collision:
                    collided_with = boss_collision
                    damage_to_take = boss_collision.damage
                
                if collided_with:
                    player.life_points -= damage_to_take
                    play_sound(damage_sound)
                    player.invulnerable_timer = 60
                    if player.life_points <= 0:
                        play_sound(game_over_sound)
                        add_to_leaderboard(player_score, player_level)
                        current_state = GAME_STATES["GAME_OVER"]
            
            # Check for door transition
            for door in doors:
                if not door.locked and player.rect.colliderect(door.rect):
                    player_score += 200 # NEW: Reward for progressing to a new dungeon
                    play_sound(level_up_sound)
                    current_level += 1
                    current_dungeon_data = generate_dungeon(current_level)
                    load_map(current_dungeon_data)
                    # NEW: Check for a story event on the new level
                    if current_level in STORY_EVENTS:
                        current_state = GAME_STATES["STORY"]
            
            # Check for level up
            if player_score >= player_level * LEVEL_UP_THRESHOLD:
                player_level += 1
                player.max_life_points += 25  # Increase max HP
                player.max_stamina += 10 # Increase max stamina
                player.life_points = player.max_life_points  # Fully heal on level up
                player.stamina = player.max_stamina # Refill stamina
                # NEW: Create a cyan particle effect for leveling up
                create_particles(player.rect.centerx, player.rect.centery, CYAN_COLOR, 25, 'healing')
                play_sound(level_up_sound)

            # Draw everything
            draw_game()

        elif current_state == GAME_STATES["DIALOGUE"]:
            draw_game()
            draw_dialogue(active_dialogue)
        
        elif current_state == GAME_STATES["GAME_OVER"]:
            draw_game_over()

        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()