
import pygame

class HumanSprite:
    """
    A class to load, process, and manage character sprite animations from a sprite sheet.

    This class assumes a specific sprite sheet layout:
    - It contains 6 tiles arranged vertically in a single column.
    - Each tile is 16x16 pixels.
    - The order of tiles from top to bottom is:
        0: Facing Down
        1: Facing Up
        2: Facing Left
        3: Stepping Down
        4: Stepping Up
        5: Stepping Left

    The class handles transparency (making white backgrounds transparent) and generates
    animation sequences for different directions.
    """

    TILE_SIZE = 16  # Each sprite tile is 16x16 pixels

    def __init__(self, sprite_sheet_path: str, palette: list):
        """
        Initializes the HumanSprite by loading the sprite sheet, processing it,
        and preparing animation frames.

        Args:
            sprite_sheet_path (str): The absolute path to the sprite sheet image file (e.g., 'chris.png').
            palette (list): The palette (list of RGB tuples) to apply to the sprite surfaces.
        """
        self.sprite_sheet_path = sprite_sheet_path
        self.palette = palette # Store the palette
        self.sprites = {}  # Dictionary to store individual sprite surfaces
        self.animations = {}  # Dictionary to store animation sequences

        self._load_and_process_sprite_sheet()
        self._generate_animations()

    def _load_and_process_sprite_sheet(self):
        """
        Loads the sprite sheet image, converts it to a format suitable for Pygame,
        sets the white background to be transparent, and extracts individual sprite tiles.
        """
        try:
            # Load the sprite sheet image
            # .convert_alpha() is used to ensure the image has an alpha channel for transparency.
            sprite_sheet = pygame.image.load(self.sprite_sheet_path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading sprite sheet {self.sprite_sheet_path}: {e}")
            return

        # Set the white color (RGB: 255, 255, 255) as the transparent color.
        # This will make any pure white pixels in the sprite sheet transparent.
        # The (0, 0, 0) argument is a flag for RLEACCEL, which can speed up blitting
        # for images with a single transparent color.
        sprite_sheet.set_colorkey((255, 255, 255), pygame.RLEACCEL)

        # Extract individual 16x16 tiles from the sprite sheet.
        # The sprite sheet is assumed to be a single column of 6 tiles.
        # We create a new Surface for each tile to ensure it's independent.
        scale_factor = 4 # Scale 16x16 sprites to 64x64
        scaled_size = (self.TILE_SIZE * scale_factor, self.TILE_SIZE * scale_factor)

        # Helper function to process and store a single sprite
        def process_sprite(subsurface_rect):
            original_subsurface = sprite_sheet.subsurface(subsurface_rect)
            scaled_surface_rgba = pygame.transform.scale(original_subsurface, scaled_size)

            # Create an 8-bit surface for palette application
            # Use SRCALPHA flag to preserve transparency during blit
            eight_bit_surface = pygame.Surface(scaled_size, depth=8)
            eight_bit_surface.set_palette(self.palette)
            eight_bit_surface.blit(scaled_surface_rgba, (0, 0))
            return eight_bit_surface

        self.sprites['facing_down'] = process_sprite((0, 0 * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))
        self.sprites['facing_up'] = process_sprite((0, 1 * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))
        self.sprites['facing_left'] = process_sprite((0, 2 * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))
        self.sprites['stepping_down'] = process_sprite((0, 3 * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))
        self.sprites['stepping_up'] = process_sprite((0, 4 * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))
        self.sprites['stepping_left'] = process_sprite((0, 5 * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))

        # Generate mirrored sprites for 'facing_right' and 'stepping_right'.
        # pygame.transform.flip(surface, flip_x, flip_y)
        # We flip horizontally (flip_x=True) and not vertically (flip_y=False).
        self.sprites['facing_right'] = pygame.transform.flip(self.sprites['facing_left'], True, False)
        self.sprites['stepping_right'] = pygame.transform.flip(self.sprites['stepping_left'], True, False)

    def _generate_animations(self):
        """
        Generates the animation sequences for different directions based on the
        extracted sprite tiles.

        The animation sequence for walking is typically a 4-frame cycle:
        [Facing, Step1, Facing, Step2]
        Where Step2 is often a mirrored version of Step1 to create a natural walking cycle.
        """
        # Animation for moving down (4-frame cycle)
        self.animations['down'] = [
            self.sprites['facing_down'],
            self.sprites['stepping_down'],
            self.sprites['facing_down'],
            pygame.transform.flip(self.sprites['stepping_down'], True, False) # Mirrored step
        ]

        # Animation for moving up (4-frame cycle)
        self.animations['up'] = [
            self.sprites['facing_up'],
            self.sprites['stepping_up'],
            self.sprites['facing_up'],
            pygame.transform.flip(self.sprites['stepping_up'], True, False) # Mirrored step
        ]

        # Animation for moving left (4-frame cycle)
        self.animations['left'] = [
            self.sprites['facing_left'],
            self.sprites['stepping_left'],
            self.sprites['facing_left'],
            self.sprites['stepping_left'] # No mirroring for left
        ]

        # Animation for moving right (4-frame cycle)
        self.animations['right'] = [
            self.sprites['facing_right'],
            self.sprites['stepping_right'],
            self.sprites['facing_right'],
            self.sprites['stepping_right'] # No mirroring for right
        ]

    def get_sprite(self, name: str) -> pygame.Surface:
        """
        Returns a specific static sprite by its name.

        Args:
            name (str): The name of the sprite (e.g., 'facing_down', 'facing_up').

        Returns:
            pygame.Surface: The requested sprite surface.
        """
        return self.sprites.get(name)

    def get_animation(self, direction: str) -> list[pygame.Surface]:
        """
        Returns the animation sequence for a given direction.

        Args:
            direction (str): The direction of the animation (e.g., 'down', 'up', 'left', 'right').

        Returns:
            list[pygame.Surface]: A list of sprite surfaces representing the animation frames.
        """
        return self.animations.get(direction)

# Example Usage (for testing purposes, not part of the class itself)
# To run this example, you would need a 'chris.png' file in the same directory
# as this script, or provide its full path.
#
# if __name__ == "__main__":
#     pygame.init()
#
#     # Set up a display for demonstration
#     screen_width, screen_height = 320, 240
#     screen = pygame.display.set_mode((screen_width, screen_height))
#     pygame.display.set_caption("Human Sprite Animation Demo")
#
#     # IMPORTANT: Replace 'chris.png' with the actual path to your sprite sheet.
#     # For this example, we assume 'chris.png' is in the same directory as human_sprite.py
#     # In a real application, you would pass the correct path.
#     sprite_sheet_file = "chris.png" # Or "C:/path/to/your/chris.png"
#
#     # Create an instance of HumanSprite
#     player_sprite = HumanSprite(sprite_sheet_file)
#
#     # Get animation frames
#     down_animation = player_sprite.get_animation('down')
#     up_animation = player_sprite.get_animation('up')
#     left_animation = player_sprite.get_animation('left')
#     right_animation = player_sprite.get_animation('right')
#
#     if down_animation and up_animation and left_animation and right_animation:
#         print("Animations loaded successfully!")
#         print(f"Down animation frames: {len(down_animation)}")
#         print(f"Up animation frames: {len(up_animation)}")
#         print(f"Left animation frames: {len(left_animation)}")
#         print(f"Right animation frames: {len(right_animation)}")
#
#         # You can now use these animation lists to draw frames on the screen
#         # based on game logic (e.g., player movement, animation speed).
#         # For example, to display the first frame of the down animation:
#         # screen.blit(down_animation[0], (screen_width // 2 - player_sprite.TILE_SIZE // 2,
#         #                                  screen_height // 2 - player_sprite.TILE_SIZE // 2))
#         # pygame.display.flip()
#
#         # Simple animation loop for demonstration
#         current_frame_index = 0
#         animation_speed = 10 # frames per second for animation
#         clock = pygame.time.Clock()
#         running = True
#         current_animation = down_animation # Start with down animation
#
#         while running:
#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     running = False
#                 elif event.type == pygame.KEYDOWN:
#                     if event.key == pygame.K_DOWN:
#                         current_animation = down_animation
#                     elif event.key == pygame.K_UP:
#                         current_animation = up_animation
#                     elif event.key == pygame.K_LEFT:
#                         current_animation = left_animation
#                     elif event.key == pygame.K_RIGHT:
#                         current_animation = right_animation
#
#             screen.fill((0, 0, 0)) # Clear screen with black
#
#             # Update frame index for animation
#             current_frame_index = (current_frame_index + 1) % len(current_animation)
#             current_frame = current_animation[current_frame_index]
#
#             # Draw the current frame in the center of the screen
#             screen.blit(current_frame, (screen_width // 2 - player_sprite.TILE_SIZE // 2,
#                                         screen_height // 2 - player_sprite.TILE_SIZE // 2))
#
#             pygame.display.flip()
#             clock.tick(animation_speed) # Control animation speed
#
#     else:
#         print("Failed to load animations. Check sprite sheet path and content.")
#
#     pygame.quit()
