import pygame
import os
import re
import sys
from PIL import Image

# Constants
# TILE_SIZE: The size of a single tile in pixels (e.g., 8x8 pixels).
TILE_SIZE = 8
# BLOCK_WIDTH: The number of tiles horizontally in a metatile block.
BLOCK_WIDTH = 4
# BLOCK_HEIGHT: The number of tiles vertically in a metatile block.
BLOCK_HEIGHT = 4

# Colors
BLACK = (0, 0, 0)

def get_palettes(file_path):
    """
    Reads palette data from a .pal file and returns a dictionary of palettes.
    Each palette is a list of RGB color tuples.

    The .pal files contain lines like:
    RGB 31 31 31; WHITE
    RGB 0 0 0; BLACK
    """
    palettes = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Look for lines containing "RGB" and not starting with a comment (;)
            if "RGB" in line and not line.startswith(';'):
                parts = line.split(';')
                # The palette name is the last part, converted to uppercase
                palette_name = parts[-1].strip().upper()
                # Extract all numbers (R, G, B values) from the first part of the line
                numbers = re.findall(r'\d+', parts[0])
                colors = []
                # Iterate through the numbers, taking 3 at a time for R, G, B
                for i in range(0, len(numbers), 3):
                    # Convert RGB values (0-31) to (0-255) by multiplying by 8
                    r = int(numbers[i]) * 8
                    g = int(numbers[i+1]) * 8
                    b = int(numbers[i+2]) * 8
                    colors.append((r, g, b))
                # Store the palette, reversing the colors as per the original implementation's requirement
                palettes[palette_name] = colors[::-1]
    return palettes

def get_tile_palette_map(file_path):
    """
    Reads the tile palette mapping from an assembly file.
    This file defines which palette to use for each tile ID.
    """
    tile_palette_map = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Look for lines starting with 'tilepal'
            if line.startswith('tilepal'):
                parts = line.split(',')
                # The actual palette names start from the second part
                for part in parts[1:]:
                    tile_palette_map.append(part.strip().upper())
    return tile_palette_map

def get_map_dimensions(map_name, project_root):
    """
    Reads the map dimensions (width and height in blocks) from map_constants.asm.
    This allows the engine to dynamically size the display for any given map.
    """
    map_constants_path = os.path.join(project_root, 'constants', 'map_constants.asm')
    try:
        with open(map_constants_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Find the line defining the map's constants, e.g., "map_const PALLET_TOWN, 10, 9"
                if line.startswith('map_const') and map_name in line:
                    parts = line.split(',')
                    # Extract width (second part) and height (third part, before any comment)
                    width = int(parts[1].strip())
                    height = int(parts[2].split(';')[0].strip())
                    return width, height
    except FileNotFoundError:
        print(f"Error: map_constants.asm not found at {map_constants_path}")
    print(f"Warning: Map dimensions not found for {map_name}. Defaulting to 10x9 (Pallet Town size).")
    return 10, 9 # Default to Pallet Town dimensions if not found or error

def load_animated_tiles_from_png(filepath):
    """
    Loads animated tile frames from a PNG file.
    Assumes the PNG contains multiple 8x8 tile frames stacked vertically.
    Converts RGBA image data to Pygame surfaces with 8-bit depth,
    mapping grayscale values to a 4-color palette (indices 0-3).
    """
    tiles = []
    try:
        img = Image.open(filepath).convert("RGBA")
        # Iterate through the image, extracting 8x8 tile frames
        for i in range(img.height // TILE_SIZE):
            # Create a new Pygame surface for each tile frame
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE), depth=8)
            for y in range(TILE_SIZE):
                for x in range(TILE_SIZE):
                    r, g, b, a = img.getpixel((x, i * TILE_SIZE + y))
                    if a == 0:
                        # If transparent, use palette index 0
                        palette_index = 0
                    else:
                        # Map grayscale value to one of the 4 palette indices
                        grayscale = (r + g + b) // 3
                        if grayscale < 64:
                            palette_index = 0
                        elif grayscale < 128:
                            palette_index = 1
                        elif grayscale < 192:
                            palette_index = 2
                        else:
                            palette_index = 3
                    surface.set_at((x, y), palette_index)
            tiles.append(surface)
    except FileNotFoundError:
        print(f"Error: PNG file not found at {filepath}")
    return tiles

def main(map_name):
    """
    Main function to initialize Pygame, load assets, and render the map.
    """
    # Determine the project root directory based on the script's location
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Get map dimensions dynamically
    map_width_blocks, map_height_blocks = get_map_dimensions(map_name, project_root)

    # Calculate screen dimensions based on map size and tile/block constants
    SCREEN_WIDTH = map_width_blocks * BLOCK_WIDTH * TILE_SIZE
    SCREEN_HEIGHT = map_height_blocks * BLOCK_HEIGHT * TILE_SIZE

    # Initialize Pygame
    pygame.init()
    # Set up the display window with calculated dimensions
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Set the window title
    pygame.display.set_caption(f"Opal Engine - {map_name.replace('_', ' ').title()}")

    # --- Load Assets ---
    # Paths to various game assets
    tileset_path = os.path.join(project_root, 'gfx', 'tilesets', 'kanto.png')
    metatiles_path = os.path.join(project_root, 'data', 'tilesets', 'kanto_metatiles.bin')
    
    # Dynamically construct the map file path (e.g., "PalletTown.blk" from "PALLET_TOWN")
    map_filename = f'{map_name.replace("_", "").title()}.blk'
    map_path = os.path.join(project_root, 'maps', map_filename)
    
    bg_palette_path = os.path.join(project_root, 'gfx', 'tilesets', 'bg_tiles.pal')
    kanto_palette_map_path = os.path.join(project_root, 'gfx', 'tilesets', 'kanto_palette_map.asm')

    try:
        # Load the main tileset image (e.g., kanto.png)
        tileset_image = Image.open(tileset_path)
        # Load background palettes
        day_palettes = get_palettes(bg_palette_path)
        # Load tile-to-palette mapping
        tile_palette_map = get_tile_palette_map(kanto_palette_map_path)

        # Load animated tile frames for water and flowers
        water_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'water', 'water.png')
        water_animation_frames = load_animated_tiles_from_png(water_png_path)

        flower_cgb_1_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'flower', 'cgb_1.png')
        flower_cgb_2_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'flower', 'cgb_2.png')
        flower_animation_frames_cgb = load_animated_tiles_from_png(flower_cgb_1_png_path) + \
                                      load_animated_tiles_from_png(flower_cgb_2_png_path)

    except (IOError, FileNotFoundError) as e:
        print(f"Error loading assets: {e}")
        return

    # --- Read Map Data ---
    try:
        # Read the map's block IDs from the .blk file
        with open(map_path, 'rb') as f:
            block_ids = f.read()
    except FileNotFoundError:
        print(f"Error: Map file not found at {map_path}. Please ensure the map name is correct and the .blk file exists.")
        pygame.quit()
        return

    # Read metatile data (defines how blocks are composed of tiles)
    with open(metatiles_path, 'rb') as f:
        metatile_data = f.read()

    # Game loop variables
    running = True
    animation_timer = 0 # Controls animation speed
    frame_counter = 0 # Used to slow down animation updates

    # --- Main Game Loop ---
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear the screen
        screen.fill(BLACK)

        # Update animation frames
        # The frame_counter increments every loop, but animation_timer only updates every 4 frames
        # This slows down the animation to be visible
        frame_counter = (frame_counter + 1) % 4
        if frame_counter == 0:
            animation_timer = (animation_timer + 1) % 8

        # --- Render Map ---
        # Iterate through each block in the map
        for block_y in range(map_height_blocks):
            for block_x in range(map_width_blocks):
                # Calculate the index of the current block in the block_ids data
                block_index = block_y * map_width_blocks + block_x
                if block_index < len(block_ids):
                    block_id = block_ids[block_index]
                    
                    # Get the metatile data for the current block_id
                    metatile_index = block_id * (BLOCK_WIDTH * BLOCK_HEIGHT)
                    metatile = metatile_data[metatile_index:metatile_index + (BLOCK_WIDTH * BLOCK_HEIGHT)]

                    # Iterate through each tile within the current metatile block
                    for tile_y in range(BLOCK_HEIGHT):
                        for tile_x in range(BLOCK_WIDTH):
                            tile_index_in_metatile = tile_y * BLOCK_WIDTH + tile_x
                            if tile_index_in_metatile < len(metatile):
                                tile_id = metatile[tile_index_in_metatile]

                                # Determine the palette to use for the current tile
                                palette_name = tile_palette_map[tile_id]
                                palette = day_palettes[palette_name]

                                current_tile_surface = None

                                # Handle animated water tiles (tile_id 20)
                                if tile_id == 20 and water_animation_frames:
                                    # Select the current animation frame for water
                                    frame_index = (animation_timer // 2) % 4
                                    current_tile_surface = water_animation_frames[frame_index]
                                    current_tile_surface.set_palette(palette)

                                # Handle animated flower tiles (tile_id 3)
                                elif tile_id == 3 and flower_animation_frames_cgb:
                                    # Select the current animation frame for flowers
                                    frame_index = (animation_timer // 2) % 2
                                    current_tile_surface = flower_animation_frames_cgb[frame_index]
                                    current_tile_surface.set_palette(palette)

                                else:
                                    # Logic for static tiles (from kanto.png)
                                    # Create a new surface for the tile
                                    current_tile_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), depth=8)
                                    current_tile_surface.set_palette(palette)

                                    # Calculate the position of the tile within the main tileset image
                                    tileset_x = (tile_id % (tileset_image.width // TILE_SIZE)) * TILE_SIZE
                                    tileset_y = (tile_id // (tileset_image.width // TILE_SIZE)) * TILE_SIZE

                                    # Copy pixel data from the tileset image to the tile surface
                                    for y_pixel in range(TILE_SIZE):
                                        for x_pixel in range(TILE_SIZE):
                                            # Get grayscale value from the tileset image
                                            grayscale_value = tileset_image.getpixel((tileset_x + x_pixel, tileset_y + y_pixel))
                                            # Map grayscale to one of the 4 palette indices
                                            if grayscale_value < 64:
                                                palette_index = 0
                                            elif grayscale_value < 128:
                                                palette_index = 1
                                            elif grayscale_value < 192:
                                                palette_index = 2
                                            else:
                                                palette_index = 3
                                            current_tile_surface.set_at((x_pixel, y_pixel), palette_index)

                                # Calculate the screen position to blit the tile
                                screen_x = (block_x * BLOCK_WIDTH + tile_x) * TILE_SIZE
                                screen_y = (block_y * BLOCK_HEIGHT + tile_y) * TILE_SIZE

                                # Blit (draw) the tile surface onto the main screen
                                if current_tile_surface:
                                    screen.blit(current_tile_surface, (screen_x, screen_y))

        # Update the full display Surface to the screen
        pygame.display.flip()

    # Quit Pygame when the loop ends
    pygame.quit()

if __name__ == "__main__":
    # This block runs when the script is executed directly
    if len(sys.argv) > 1:
        # If a command-line argument is provided, use it as the map name
        map_name_arg = sys.argv[1].upper()
    else:
        # Otherwise, default to "PALLET_TOWN"
        map_name_arg = "PALLET_TOWN"
        print(f"No map name provided. Defaulting to {map_name_arg}.")
    # Call the main function with the determined map name
    main(map_name_arg)
