import pygame
import random
import sys
import numpy as np

# --- Sound Generation ---
def generate_sound(frequency=440, duration=0.1, sample_rate=44100):
    """Generates a pygame.Sound object with a simple tone and fade-out at max volume."""
    num_samples = int(duration * sample_rate)
    time_array = np.linspace(0, duration, num_samples, False)
    
    # Generate sine wave
    tone = np.sin(frequency * time_array * 2 * np.pi)
    
    # Simple linear fade-out to prevent clicking noise
    fade_out = np.linspace(1, 0, num_samples)
    audio = tone * fade_out
    
    # Scale to 16-bit integer values
    audio = (audio * 32767).astype(np.int16)
    
    # Pygame sound requires a stereo signal (2 channels)
    stereo_audio = np.zeros((num_samples, 2), dtype=np.int16)
    stereo_audio[:, 0] = audio
    stereo_audio[:, 1] = audio
    
    return pygame.sndarray.make_sound(stereo_audio)

# --- Constants ---
# Screen dimensions are now set in the Tetris class for fullscreen mode
PLAY_WIDTH = 300  # meaning 300 // 10 = 30 width per block
PLAY_HEIGHT = 600  # meaning 600 // 20 = 20 height per block
BLOCK_SIZE = 30

# TOP_LEFT_X and Y are now calculated dynamically in the Tetris class

# --- Theme Colors ---
COLOR_BACKGROUND = (10, 10, 25)
COLOR_GRID = (40, 50, 80)
COLOR_BORDER = (40, 255, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_TITLE = (40, 255, 255)
COLOR_TITLE_GLOW = (170, 0, 255)
COLOR_BUTTON_INACTIVE = (20, 30, 80)
COLOR_BUTTON_ACTIVE = (40, 60, 150)
COLOR_BUTTON_TEXT = (255, 255, 255)


# --- Shapes ---
S = [['.....',
      '.....',
      '..00.',
      '.00..',
      '.....'],
     ['.....',
      '..0.',
      '..00.',
      '...0.',
      '.....']]

Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0.',
      '.00.',
      '.0...',
      '.....']]

I = [['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '0000.',
      '.....',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

shapes = [S, Z, I, O, J, L, T]
# Neon-style colors for the pieces
shape_colors = [(57, 255, 20), (255, 40, 40), (40, 255, 255), (255, 255, 40),
                (255, 165, 40), (40, 40, 255), (170, 0, 255)]

# --- Leaderboard (Temporary) ---
leaderboard = []

# --- Classes ---
class Piece:
    """Represents a Tetris piece."""
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = shape_colors[shapes.index(shape)]
        self.rotation = 0

class Particle:
    """Represents a single particle for effects."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, 1) # Bias upwards
        self.size = random.randint(3, 6)
        self.lifespan = random.randint(25, 60) # In frames
        self.gravity = 0.1

    def update(self):
        """Updates the particle's state."""
        self.lifespan -= 1
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.size -= 0.1 # Shrink over time

    def draw(self, surface):
        """Draws the particle."""
        if self.is_alive:
            pygame.draw.rect(surface, self.color, (self.x, self.y, self.size, self.size))

    @property
    def is_alive(self):
        """Checks if the particle should still be active."""
        return self.lifespan > 0 and self.size > 0

class Tetris:
    """Main class to handle the game logic and state."""
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption('Tetris')
        
        # Center the play area on the screen
        self.top_left_x = (self.width - PLAY_WIDTH) // 2
        self.top_left_y = (self.height - PLAY_HEIGHT) // 2

        self.game_state = 'main_menu'
        self.font = pygame.font.SysFont('consolas', 30)
        self.large_font = pygame.font.SysFont('consolas', 60, bold=True)
        self.small_font = pygame.font.SysFont('consolas', 20)
        
        # Options menu state and audio settings
        self.options_menu_state = 'main'
        self.master_volume = 0.5  # Volume from 0.0 to 1.0

        self.load_sounds()
        self.init_stars()
        self.star_speed_multiplier = 1.0
        
        self.reset_game()
        
    def load_sounds(self):
        """Generates and loads all sound effects into a dictionary."""
        self.sounds = {
            'move': generate_sound(200, 0.05),
            'rotate': generate_sound(300, 0.05),
            'drop': generate_sound(150, 0.1),
            'clear_line': generate_sound(600, 0.3),
            'clear_tetris': generate_sound(800, 0.5), # For 4 lines
            'game_over': generate_sound(100, 0.8),
            'click': generate_sound(400, 0.08),
            'pause': generate_sound(250, 0.15)
        }

    def play_sound(self, sound_name):
        """Plays a sound from the sounds dictionary with the master volume."""
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]
            sound.set_volume(self.master_volume)
            sound.play()

    def init_stars(self):
        """Initializes the starfield for the animated background."""
        self.stars = []
        for _ in range(250):  # Number of stars
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            speed = random.uniform(0.5, 1.5)  # Each star has its own base speed
            color_val = random.randint(50, 150)
            color = (color_val, color_val, color_val)
            self.stars.append([x, y, size, speed, color])

    def draw_and_update_stars(self):
        """Draws and updates the starfield background."""
        self.screen.fill(COLOR_BACKGROUND)
        for star in self.stars:
            # Update star position
            star[1] += star[3] * self.star_speed_multiplier
            
            # If star goes off-screen, reset it to the top
            if star[1] > self.height:
                star[1] = 0
                star[0] = random.randint(0, self.width)
            
            # Draw the star
            pygame.draw.rect(self.screen, star[4], (star[0], star[1], star[2], star[2]))

    def reset_game(self):
        """Resets the game state for a new game."""
        self.grid = self.create_grid()
        self.locked_positions = {}
        self.change_piece = False
        self.run = True
        self.current_piece = self.get_shape()
        self.next_piece = self.get_shape()
        self.clock = pygame.time.Clock()
        self.fall_time = 0
        self.fall_speed = 0.27
        self.level_time = 0
        self.score = 0
        self.last_score = 0
        self.player_name = ""
        self.particles = [] # List to hold active particles

    def create_grid(self, locked_positions={}):
        """Creates the game grid."""
        grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                if (x, y) in locked_positions:
                    c = locked_positions[(x, y)]
                    grid[y][x] = c
        return grid

    def convert_shape_format(self, shape):
        """Converts the shape format for easier processing."""
        positions = []
        format = shape.shape[shape.rotation % len(shape.shape)]

        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    positions.append((shape.x + j, shape.y + i))

        for i, pos in enumerate(positions):
            positions[i] = (pos[0] - 2, pos[1] - 4)
        return positions

    def valid_space(self, shape):
        """Checks if the piece is in a valid position."""
        accepted_pos = [[(j, i) for j in range(10) if self.grid[i][j] == (0,0,0)] for i in range(20)]
        accepted_pos = [j for sub in accepted_pos for j in sub]

        formatted = self.convert_shape_format(shape)

        for pos in formatted:
            if pos not in accepted_pos:
                if pos[1] > -1:
                    return False
        return True

    def check_lost(self, positions):
        """Checks if the game is over."""
        for pos in positions:
            x, y = pos
            if y < 1:
                return True
        return False

    def get_shape(self):
        """Returns a new random piece."""
        return Piece(5, 0, random.choice(shapes))
    
    def draw_glowing_text(self, text, font, main_color, glow_color, center_pos):
        """Draws text with a glowing effect."""
        text_surf_glow = font.render(text, True, glow_color)
        offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]
        for dx, dy in offsets:
            text_rect_glow = text_surf_glow.get_rect(center=(center_pos[0] + dx, center_pos[1] + dy))
            self.screen.blit(text_surf_glow, text_rect_glow)
            
        text_surf_main = font.render(text, True, main_color)
        text_rect_main = text_surf_main.get_rect(center=center_pos)
        self.screen.blit(text_surf_main, text_rect_main)

    def draw_grid(self, surface):
        """Draws the grid lines."""
        for i in range(21):
            pygame.draw.line(surface, COLOR_GRID, (self.top_left_x, self.top_left_y + i * BLOCK_SIZE),
                             (self.top_left_x + PLAY_WIDTH, self.top_left_y + i * BLOCK_SIZE), 1)
        for j in range(11):
            pygame.draw.line(surface, COLOR_GRID, (self.top_left_x + j * BLOCK_SIZE, self.top_left_y),
                             (self.top_left_x + j * BLOCK_SIZE, self.top_left_y + PLAY_HEIGHT), 1)

    def draw_block(self, surface, color, x, y):
        """Draws a single block with a modern, beveled look."""
        darker_color = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
        pygame.draw.rect(surface, darker_color, (x, y, BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(surface, color, (x + 2, y + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4))
    
    def emit_particles(self, x, y, color, count=15):
        """Emits a burst of particles from a specific location."""
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
            
    def manage_particles(self):
        """Updates and draws all particles, removing dead ones."""
        alive_particles = []
        for p in self.particles:
            p.update()
            if p.is_alive:
                p.draw(self.screen)
                alive_particles.append(p)
        self.particles = alive_particles

    def clear_rows(self, grid, locked):
        """Clears completed rows, triggers particles, and returns the number of cleared rows."""
        inc = 0
        ind = -1
        for i in range(len(grid) - 1, -1, -1):
            row = grid[i]
            if (0,0,0) not in row:
                inc += 1
                ind = i
                
                # Emit particles for the cleared row
                for j in range(len(row)):
                    px = self.top_left_x + j * BLOCK_SIZE + BLOCK_SIZE // 2
                    py = self.top_left_y + i * BLOCK_SIZE + BLOCK_SIZE // 2
                    self.emit_particles(px, py, grid[i][j])
                
                for j in range(len(row)):
                    try:
                        del locked[(j, i)]
                    except:
                        continue
                        
        if inc > 0:
            if inc == 4:
                self.play_sound('clear_tetris')
            else:
                self.play_sound('clear_line')

            for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
                x, y = key
                if y < ind:
                    newKey = (x, y + inc)
                    locked[newKey] = locked.pop(key)
        return inc
    
    def update_score(self, nscore):
        """Updates the score."""
        self.score += nscore
        if self.score > self.get_high_score():
            self.save_high_score(self.score)

    def get_high_score(self):
        """Gets the high score from file and the current session's leaderboard."""
        file_high_score = 0
        try:
            with open("highscore.txt", "r") as f:
                file_high_score = int(f.read())
        except (FileNotFoundError, ValueError):
            file_high_score = 0
            
        leaderboard_high_score = 0
        if leaderboard:
            leaderboard_high_score = max(score for _, score in leaderboard)

        return max(file_high_score, leaderboard_high_score)

    def save_high_score(self, score):
        """Saves the high score to a file."""
        with open("highscore.txt", "w") as f:
            f.write(str(score))


    def draw_next_shape(self, shape, surface):
        """Draws the next shape on the side."""
        label = self.font.render('Next Shape', 1, COLOR_TEXT)

        sx = self.top_left_x + PLAY_WIDTH + 50
        sy = self.top_left_y + 100
        format = shape.shape[shape.rotation % len(shape.shape)]

        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    self.draw_block(surface, shape.color, sx + j * BLOCK_SIZE, sy + i * BLOCK_SIZE)
        
        surface.blit(label, (sx + 10, sy - 40))

    def draw_window(self, surface, grid, score=0):
        """Draws the main game window."""
        self.draw_and_update_stars()
        
        self.draw_glowing_text('TETRIS', self.large_font, COLOR_TITLE, COLOR_TITLE_GLOW, (self.width / 2, 50))

        # Current Score
        label = self.font.render('Score: ' + str(score), 1, COLOR_TEXT)
        sx = self.top_left_x + PLAY_WIDTH + 50
        sy = self.top_left_y + 350
        surface.blit(label, (sx, sy))
        
        # High Score (split into two lines)
        high_score_text_label = self.font.render('High Score', 1, COLOR_TEXT)
        high_score_value_label = self.font.render(str(self.get_high_score()), 1, COLOR_TEXT)
        
        # Position the labels on the left side, centered in the available space
        sx_center = self.top_left_x / 2
        sy_start = self.top_left_y + 200

        # Draw "High Score" text
        surface.blit(high_score_text_label, (sx_center - high_score_text_label.get_width() / 2, sy_start))

        # Draw the score number below the text
        surface.blit(high_score_value_label, (sx_center - high_score_value_label.get_width() / 2, sy_start + 40))

        # Draw grid and pieces
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j] != (0,0,0):
                    self.draw_block(surface, grid[i][j], self.top_left_x + j * BLOCK_SIZE, self.top_left_y + i * BLOCK_SIZE)

        self.draw_grid(surface)
        pygame.draw.rect(surface, COLOR_BORDER, (self.top_left_x, self.top_left_y, PLAY_WIDTH, PLAY_HEIGHT), 4)
        
        self.manage_particles()

    def game_loop(self):
        """The main game loop."""
        self.grid = self.create_grid(self.locked_positions)

        self.fall_time += self.clock.get_rawtime()
        self.level_time += self.clock.get_rawtime()
        self.clock.tick()

        if self.level_time / 1000 > 5:
            self.level_time = 0
            if self.fall_speed > 0.12:
                self.fall_speed -= 0.005

        if self.fall_time / 1000 >= self.fall_speed:
            self.fall_time = 0
            self.current_piece.y += 1
            if not (self.valid_space(self.current_piece)) and self.current_piece.y > 0:
                self.current_piece.y -= 1
                self.change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False
                pygame.display.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.current_piece.x -= 1
                    if not self.valid_space(self.current_piece):
                        self.current_piece.x += 1
                    else:
                        self.play_sound('move')
                elif event.key == pygame.K_RIGHT:
                    self.current_piece.x += 1
                    if not self.valid_space(self.current_piece):
                        self.current_piece.x -= 1
                    else:
                        self.play_sound('move')
                elif event.key == pygame.K_DOWN:
                    self.current_piece.y += 1
                    if not self.valid_space(self.current_piece):
                        self.current_piece.y -= 1
                    else:
                        self.play_sound('move')
                elif event.key == pygame.K_UP:
                    self.current_piece.rotation += 1
                    if not self.valid_space(self.current_piece):
                        self.current_piece.rotation -= 1
                    else:
                        self.play_sound('rotate')
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    self.play_sound('pause')
                    self.game_state = 'pause'

        shape_pos = self.convert_shape_format(self.current_piece)

        for i in range(len(shape_pos)):
            x, y = shape_pos[i]
            if y > -1:
                self.grid[y][x] = self.current_piece.color

        if self.change_piece:
            for pos in shape_pos:
                p = (pos[0], pos[1])
                self.locked_positions[p] = self.current_piece.color
            self.current_piece = self.next_piece
            self.next_piece = self.get_shape()
            self.change_piece = False
            cleared_rows = self.clear_rows(self.grid, self.locked_positions)
            self.score += cleared_rows * 10
            if cleared_rows > 0:
                self.play_sound('drop')


        self.draw_window(self.screen, self.grid, self.score)
        self.draw_next_shape(self.next_piece, self.screen)
        pygame.display.update()

        if self.check_lost(self.locked_positions):
            self.play_sound('game_over')
            self.last_score = self.score
            self.game_state = 'game_over'

    def draw_button(self, text, x, y, width, height, inactive_color, active_color, border_radius=10):
        """Draws a button, highlighting it on hover."""
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        
        is_hovered = x + width > mouse[0] > x and y + height > mouse[1] > y
        
        if is_hovered:
            pygame.draw.rect(self.screen, active_color, (x, y, width, height), border_radius=border_radius)
        else:
            pygame.draw.rect(self.screen, inactive_color, (x, y, width, height), border_radius=border_radius)
        
        pygame.draw.rect(self.screen, COLOR_BORDER, (x, y, width, height), 2, border_radius=border_radius)


        text_surf = self.font.render(text, True, COLOR_BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=((x + (width / 2)), (y + (height / 2))))
        self.screen.blit(text_surf, text_rect)
        
        return is_hovered and click[0] == 1


    def main_menu(self):
        """Displays the main menu."""
        button_width, button_height = 220, 50
        center_x = self.width / 2 - button_width / 2
        center_y = self.height / 2
        
        play_button_rect = pygame.Rect(center_x, center_y - 80, button_width, button_height)
        leaderboard_button_rect = pygame.Rect(center_x, center_y - 10, button_width, button_height)
        options_button_rect = pygame.Rect(center_x, center_y + 60, button_width, button_height)
        quit_button_rect = pygame.Rect(center_x, center_y + 130, button_width, button_height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if play_button_rect.collidepoint(event.pos):
                        self.play_sound('click')
                        self.start_game()
                    if leaderboard_button_rect.collidepoint(event.pos):
                        self.play_sound('click')
                        self.show_leaderboard()
                    if options_button_rect.collidepoint(event.pos):
                        self.play_sound('click')
                        self.show_options()
                    if quit_button_rect.collidepoint(event.pos):
                        self.play_sound('click')
                        pygame.time.wait(200) # Wait for sound to play
                        self.quit_game()

        self.draw_and_update_stars()
        self.draw_glowing_text('TETRIS', self.large_font, COLOR_TITLE, COLOR_TITLE_GLOW, (self.width / 2, self.height * 0.25))

        # Draw buttons
        self.draw_button("Play", play_button_rect.x, play_button_rect.y, play_button_rect.width, play_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        self.draw_button("Leaderboard", leaderboard_button_rect.x, leaderboard_button_rect.y, leaderboard_button_rect.width, leaderboard_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        self.draw_button("Options", options_button_rect.x, options_button_rect.y, options_button_rect.width, options_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        self.draw_button("Quit", quit_button_rect.x, quit_button_rect.y, quit_button_rect.width, quit_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        
        pygame.display.update()

    def start_game(self):
        self.reset_game()
        self.game_state = 'playing'

    def show_leaderboard(self):
        self.game_state = 'leaderboard'

    def show_options(self):
        self.game_state = 'options'

    def quit_game(self):
        self.run = False
        pygame.quit()
        sys.exit()

    def leaderboard_screen(self):
        """Displays the leaderboard."""
        back_button_rect = pygame.Rect(self.width / 2 - 100, self.height - 100, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if back_button_rect.collidepoint(event.pos):
                        self.play_sound('click')
                        self.back_to_menu()
        
        self.draw_and_update_stars()
        title = self.large_font.render('Leaderboard', 1, COLOR_TEXT)
        self.screen.blit(title, (self.width / 2 - title.get_width() / 2, 80))

        sorted_leaderboard = sorted(leaderboard, key=lambda x: x[1], reverse=True)

        y_offset = 180
        for i, (name, score) in enumerate(sorted_leaderboard[:10]):
            entry = self.font.render(f"{i + 1}. {name}: {score}", 1, COLOR_TEXT)
            self.screen.blit(entry, (self.width / 2 - entry.get_width() / 2, y_offset))
            y_offset += 40

        self.draw_button("Back", back_button_rect.x, back_button_rect.y, back_button_rect.width, back_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        
        pygame.display.update()

    def options_screen(self):
        """Displays the options menu and its submenus."""
        if self.options_menu_state == 'main':
            self.main_options_submenu()
        elif self.options_menu_state == 'audio':
            self.audio_options_submenu()
        elif self.options_menu_state == 'controls':
            self.controls_options_submenu()

    def main_options_submenu(self):
        """The main options menu with buttons for submenus."""
        button_width, button_height = 220, 50
        center_x = self.width / 2 - button_width / 2
        
        audio_button_rect = pygame.Rect(center_x, 250, button_width, button_height)
        controls_button_rect = pygame.Rect(center_x, 320, button_width, button_height)
        back_button_rect = pygame.Rect(self.width / 2 - 100, self.height - 100, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False; pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if audio_button_rect.collidepoint(event.pos):
                    self.play_sound('click')
                    self.options_menu_state = 'audio'
                elif controls_button_rect.collidepoint(event.pos):
                    self.play_sound('click')
                    self.options_menu_state = 'controls'
                elif back_button_rect.collidepoint(event.pos):
                    self.play_sound('click')
                    self.back_to_menu()
        
        self.draw_and_update_stars()
        title = self.large_font.render('Options', 1, COLOR_TEXT)
        self.screen.blit(title, (self.width / 2 - title.get_width() / 2, 150))

        self.draw_button("Audio", audio_button_rect.x, audio_button_rect.y, audio_button_rect.width, audio_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        self.draw_button("Controls", controls_button_rect.x, controls_button_rect.y, controls_button_rect.width, controls_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        self.draw_button("Back", back_button_rect.x, back_button_rect.y, back_button_rect.width, back_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        
        pygame.display.update()

    def audio_options_submenu(self):
        """Menu for changing audio volume."""
        back_button_rect = pygame.Rect(self.width / 2 - 100, self.height - 100, 200, 50)
        
        volume_bar_width = 300
        volume_bar_x = self.width / 2 - volume_bar_width / 2
        volume_bar_y = self.height / 2
        # Make the hitbox taller for easier clicking
        volume_bar_hitbox = pygame.Rect(volume_bar_x, volume_bar_y - 10, volume_bar_width, 40) 
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False; pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button_rect.collidepoint(mouse_pos):
                    self.play_sound('click')
                    self.options_menu_state = 'main'
        
        # Handle volume bar click/drag outside the event loop to allow holding the mouse down
        if mouse_pressed[0] and volume_bar_hitbox.collidepoint(mouse_pos):
            click_x = mouse_pos[0]
            new_volume = (click_x - volume_bar_x) / volume_bar_width
            self.master_volume = max(0.0, min(1.0, new_volume))

        self.draw_and_update_stars()
        title = self.large_font.render('Audio Settings', 1, COLOR_TEXT)
        self.screen.blit(title, (self.width / 2 - title.get_width() / 2, 150))
        
        # Drawing the volume slider
        volume_bar_height = 20
        # Bar background
        pygame.draw.rect(self.screen, COLOR_BUTTON_INACTIVE, (volume_bar_x, volume_bar_y, volume_bar_width, volume_bar_height), border_radius=5)
        # Current volume level
        current_volume_width = volume_bar_width * self.master_volume
        pygame.draw.rect(self.screen, COLOR_BUTTON_ACTIVE, (volume_bar_x, volume_bar_y, current_volume_width, volume_bar_height), border_radius=5)
        
        volume_text = self.font.render(f"Master Volume: {int(self.master_volume * 100)}%", 1, COLOR_TEXT)
        self.screen.blit(volume_text, (self.width / 2 - volume_text.get_width() / 2, volume_bar_y - 50))
        
        self.draw_button("Back", back_button_rect.x, back_button_rect.y, back_button_rect.width, back_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        
        pygame.display.update()

    def controls_options_submenu(self):
        """Menu for displaying game controls."""
        back_button_rect = pygame.Rect(self.width / 2 - 100, self.height - 100, 200, 50)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False; pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button_rect.collidepoint(event.pos):
                    self.play_sound('click')
                    self.options_menu_state = 'main'

        self.draw_and_update_stars()
        title = self.large_font.render('Controls', 1, COLOR_TEXT)
        self.screen.blit(title, (self.width / 2 - title.get_width() / 2, 150))
        
        controls_text = [
            "Left Arrow : Move Left",
            "Right Arrow: Move Right",
            "Down Arrow : Move Down",
            "Up Arrow   : Rotate",
            "Escape/P   : Pause"
        ]
        
        y_offset = 280
        for line in controls_text:
            text = self.font.render(line, 1, COLOR_TEXT)
            self.screen.blit(text, (self.width / 2 - text.get_width() / 2, y_offset))
            y_offset += 40
            
        self.draw_button("Back", back_button_rect.x, back_button_rect.y, back_button_rect.width, back_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        pygame.display.update()

    def pause_screen(self):
        """Displays the pause menu."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 10, 25, 200)) # Semi-transparent dark blue
        self.screen.blit(overlay, (0, 0))

        resume_button_rect = pygame.Rect(self.width / 2 - 100, self.height / 2 - 50, 200, 50)
        menu_button_rect = pygame.Rect(self.width / 2 - 100, self.height / 2 + 20, 200, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    self.resume_game()
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if resume_button_rect.collidepoint(event.pos):
                        self.resume_game()
                    elif menu_button_rect.collidepoint(event.pos):
                        self.play_sound('click')
                        self.back_to_menu()

        title = self.large_font.render('Paused', 1, COLOR_TEXT)
        self.screen.blit(title, (self.width / 2 - title.get_width() / 2, 200))

        self.draw_button("Resume", resume_button_rect.x, resume_button_rect.y, resume_button_rect.width, resume_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)
        self.draw_button("Main Menu", menu_button_rect.x, menu_button_rect.y, menu_button_rect.width, menu_button_rect.height, COLOR_BUTTON_INACTIVE, COLOR_BUTTON_ACTIVE)

        pygame.display.update()

    def resume_game(self):
        self.play_sound('pause')
        self.game_state = 'playing'

    def back_to_menu(self):
        self.game_state = 'main_menu'
        self.options_menu_state = 'main' # Reset state when leaving options

    def game_over_screen(self):
        """Displays the game over screen and handles name input."""
        while self.game_state == 'game_over':
            self.draw_and_update_stars()
            title = self.large_font.render('Game Over', 1, (255, 40, 40))
            self.screen.blit(title, (self.width / 2 - title.get_width() / 2, self.height * 0.2))

            score_text = self.font.render(f'Your Score: {self.last_score}', 1, COLOR_TEXT)
            self.screen.blit(score_text, (self.width / 2 - score_text.get_width() / 2, self.height * 0.35))
            
            prompt_text = self.font.render('Enter your name:', 1, COLOR_TEXT)
            self.screen.blit(prompt_text, (self.width / 2 - prompt_text.get_width() / 2, self.height * 0.45))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.play_sound('click')
                        # If a name was entered, add it to the leaderboard.
                        if self.player_name:
                            leaderboard.append((self.player_name, self.last_score))
                        # Always return to menu, even if no name was entered.
                        self.player_name = ""
                        self.back_to_menu()
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    else:
                        # Only add characters that are valid and printable
                        if len(self.player_name) < 10 and event.unicode.isprintable():
                            self.player_name += event.unicode
            
            input_box = pygame.Rect(self.width / 2 - 150, self.height * 0.55, 300, 50)
            pygame.draw.rect(self.screen, COLOR_BUTTON_INACTIVE, input_box, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_BORDER, input_box, 2, border_radius=10)
            
            # Only render the text if the player_name string is not empty.
            if self.player_name:
                name_surface = self.font.render(self.player_name, True, COLOR_TEXT)
                self.screen.blit(name_surface, (input_box.x + 10, input_box.y + 10))
            
            info_text = self.small_font.render('Press Enter to submit', 1, (180, 180, 180))
            self.screen.blit(info_text, (self.width / 2 - info_text.get_width() / 2, self.height * 0.65))

            pygame.display.update()

    def run_game(self):
        """Main function to run the entire game application."""
        while self.run:
            if self.game_state == 'main_menu':
                self.star_speed_multiplier = 1.0 # Full speed in menus
                self.main_menu()
            elif self.game_state == 'playing':
                self.star_speed_multiplier = 0.2 # Slow during gameplay
                self.game_loop()
            elif self.game_state == 'leaderboard':
                self.star_speed_multiplier = 1.0
                self.leaderboard_screen()
            elif self.game_state == 'options':
                self.star_speed_multiplier = 1.0
                self.options_screen()
            elif self.game_state == 'pause':
                # No star update here to keep the game screen frozen
                self.pause_screen()
            elif self.game_state == 'game_over':
                self.star_speed_multiplier = 0.5 # Medium speed for game over
                self.game_over_screen()

if __name__ == '__main__':
    game = Tetris()
    game.run_game()
