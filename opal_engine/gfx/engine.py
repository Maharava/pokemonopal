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
# TILE_RENDER_SCALE: The scaling factor for rendering tiles (e.g., 2 for 2x, 4 for 4x).
TILE_RENDER_SCALE = 4

# Game Boy Color screen dimensions in tiles
GBC_SCREEN_WIDTH_TILES = 20 # 160 pixels / 8 pixels per tile
GBC_SCREEN_HEIGHT_TILES = 18 # 144 pixels / 8 pixels per tile

# Colors
BLACK = (0, 0, 0)

def get_palettes(file_path):
    """
    Reads palette data from a .pal file and returns a dictionary of palettes.
    Each palette is a list of RGB color tuples.

    The .pal files contain lines like:
    RGB 31 31 31; WHITE
    RGB 0 0 0; BLACK

    Args:
        file_path (str): The absolute path to the .pal file.

    Returns:
        dict: A dictionary where keys are palette names (e.g., 'GRAY', 'RED')
              and values are lists of RGB color tuples.
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
    Reads the tile palette mapping from an assembly file (e.g., kanto_palette_map.asm).
    This file defines which palette to use for each tile ID.

    Args:
        file_path (str): The absolute path to the _palette_map.asm file.

    Returns:
        list: A list where the index is the tile ID and the value is the palette name string.
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

    Args:
        map_name (str): The uppercase name of the map (e.g., "PALLET_TOWN").
        project_root (str): The absolute path to the project's root directory.

    Returns:
        tuple: A tuple containing (width_in_blocks, height_in_blocks).
    """
    # Temporary override for PALLET_TOWN based on user's observation
    if map_name == "PALLET_TOWN":
        print(f"Overriding dimensions for {map_name}: 5x18 blocks (20 tiles wide)")
        return 5, 18

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
    print(f"Warning: Map dimensions not found for {map_name}. Defaulting to 10, 9.")
    print(f"get_map_dimensions returning default: 10, 9")
    return 10, 9 # Default to Pallet Town dimensions if not found or error

def load_tileset_tiles(tileset_image, palette):
    """
    Pre-renders all 8x8 tiles from a PIL Image tileset into Pygame Surfaces.
    Each tile is scaled by TILE_RENDER_SCALE and has the given palette applied.

    Args:
        tileset_image (PIL.Image.Image): The loaded tileset image (e.g., from a PNG).
        palette (list): The palette (list of RGB tuples) to apply to the tile surfaces.

    Returns:
        list: A list of Pygame Surface objects, each representing a pre-rendered tile.
    """
    pre_rendered_tiles = []
    tileset_width_tiles = tileset_image.width // TILE_SIZE
    tileset_height_tiles = tileset_image.height // TILE_SIZE

    for tile_y in range(tileset_height_tiles):
        for tile_x in range(tileset_width_tiles):
            # Create a new Pygame surface for each tile, scaled by TILE_RENDER_SCALE
            tile_surface = pygame.Surface((TILE_SIZE * TILE_RENDER_SCALE, TILE_SIZE * TILE_RENDER_SCALE), depth=8)
            tile_surface.set_palette(palette)

            # Extract the 8x8 tile region from the PIL image
            for y_pixel in range(TILE_SIZE):
                for x_pixel in range(TILE_SIZE):
                    # Get grayscale value from the tileset image
                    # The tileset_image is assumed to be grayscale for palette mapping
                    grayscale_value = tileset_image.getpixel((tile_x * TILE_SIZE + x_pixel, tile_y * TILE_SIZE + y_pixel))
                    
                    # Map grayscale to one of the 4 palette indices (0-3)
                    if grayscale_value < 64:
                        palette_index = 0
                    elif grayscale_value < 128:
                        palette_index = 1
                    elif grayscale_value < 192:
                        palette_index = 2
                    else:
                        palette_index = 3
                    
                    # Draw TILE_RENDER_SCALE x TILE_RENDER_SCALE pixel block for each source pixel to achieve scaling
                    for sy in range(TILE_RENDER_SCALE):
                        for sx in range(TILE_RENDER_SCALE):
                            tile_surface.set_at((x_pixel * TILE_RENDER_SCALE + sx, y_pixel * TILE_RENDER_SCALE + sy), palette_index)
            pre_rendered_tiles.append(tile_surface)
    return pre_rendered_tiles

def load_animated_tiles_from_png(filepath, palette):
    """
    Loads animated tile frames from a PNG file using Pygame's image loading.
    Assumes the PNG contains multiple 8x8 tile frames stacked vertically.
    Converts RGBA image data to Pygame surfaces and applies the given palette.

    Args:
        filepath (str): The absolute path to the animated tiles PNG file.
        palette (list): The palette (list of RGB tuples) to apply to the tile surfaces.

    Returns:
        list: A list of Pygame Surface objects, each representing an animated tile frame.
    """
    tiles = []
    try:
        # Load the image using Pygame
        img_surface = pygame.image.load(filepath).convert_alpha() # Use convert_alpha for transparency

        # Iterate through the image, extracting 8x8 tile frames
        for i in range(img_surface.get_height() // TILE_SIZE):
            # Create a sub-surface for each 8x8 tile frame
            tile_rect = pygame.Rect(0, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            source_tile_surface = img_surface.subsurface(tile_rect).copy() # .copy() is important to make it independent

            # Create a new 8-bit surface for the scaled tile
            scaled_tile_surface = pygame.Surface((TILE_SIZE * TILE_RENDER_SCALE, TILE_SIZE * TILE_RENDER_SCALE), depth=8)
            scaled_tile_surface.set_palette(palette)

            # Blit the source tile onto the 8-bit surface. This performs the color reduction.
            # Use SRCALPHA flag to handle transparency correctly during blitting.
            scaled_tile_surface.blit(pygame.transform.scale(source_tile_surface, (TILE_SIZE * TILE_RENDER_SCALE, TILE_SIZE * TILE_RENDER_SCALE)), (0, 0))
            
            tiles.append(scaled_tile_surface)
    except pygame.error as e:
        print(f"Error loading animated tiles from {filepath}: {e}")
    return tiles

def load_player_sprite(filepath, palette):
    """
    Loads the player sprite from a PNG file, scales it, and applies the given palette.
    Assumes the player sprite is 16x16 pixels in the source PNG.

    Args:
        filepath (str): The absolute path to the player sprite PNG file.
        palette (list): The palette (list of RGB tuples) to apply to the sprite surface.

    Returns:
        pygame.Surface: The scaled and palettized player sprite surface.
    """
    try:
        # Load the image using Pygame
        img_surface = pygame.image.load(filepath).convert_alpha() # Use convert_alpha for transparency

        # Create a new 8-bit surface for the scaled sprite
        scaled_sprite_surface = pygame.Surface((16 * TILE_RENDER_SCALE, 16 * TILE_RENDER_SCALE), depth=8)
        scaled_sprite_surface.set_palette(palette)

        # Blit the source image onto the 8-bit surface. This performs the color reduction.
        scaled_sprite_surface.blit(pygame.transform.scale(img_surface, (16 * TILE_RENDER_SCALE, 16 * TILE_RENDER_SCALE)), (0, 0))
        return scaled_sprite_surface
    except pygame.error as e:
        print(f"Error loading player sprite from {filepath}: {e}")
        return None

def get_tileset_info(map_name, project_root):
    """
    Reads data/maps/maps.asm to find the tileset, metatiles, and palette map for a given map.
    This function is crucial for dynamically loading the correct visual assets for each map.

    Args:
        map_name (str): The uppercase name of the map (e.g., "REDS_HOUSE_2F").
        project_root (str): The absolute path to the project's root directory.

    Returns:
        tuple: A tuple containing (tileset_png_path, metatiles_bin_path, palette_map_asm_path).
               Returns (None, None, None) if maps.asm is not found or tileset info is missing.
    """
    maps_asm_path = os.path.join(project_root, 'data', 'maps', 'maps.asm')
    tileset_constant = None

    try:
        with open(maps_asm_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Look for lines defining map properties, e.g., "map RedsHouse2F, TILESET_PLAYERS_HOUSE, ..."
                # The comparison is case-insensitive and handles underscores in map_name
                if line.startswith('map') and map_name.replace("_", "").lower() in line.lower():
                    parts = line.split(',')
                    tileset_constant = parts[1].strip()
                    print(f"Found tileset_constant for {map_name}: {tileset_constant}")
                    break
    except FileNotFoundError:
        print(f"Error: maps.asm not found at {maps_asm_path}")
        return None, None, None

    if tileset_constant is None:
        print(f"Error: Tileset information not found for map {map_name} in maps.asm. Defaulting to Kanto.")
        # Default to Kanto tileset if information is not found
        return (
            os.path.join(project_root, 'gfx', 'tilesets', 'kanto.png'),
            os.path.join(project_root, 'data', 'tilesets', 'kanto_metatiles.bin'),
            os.path.join(project_root, 'gfx', 'tilesets', 'kanto_palette_map.asm')
        )

    # Extract the base name from the tileset constant (e.g., "TILESET_PLAYERS_HOUSE" -> "players_house")
    tileset_base_name = tileset_constant.replace('TILESET_', '').lower()

    # Construct the full paths to the tileset PNG, metatiles BIN, and palette map ASM
    tileset_png_path = os.path.join(project_root, 'gfx', 'tilesets', f'{tileset_base_name}.png')
    metatiles_bin_path = os.path.join(project_root, 'data', 'tilesets', f'{tileset_base_name}_metatiles.bin')
    palette_map_asm_path = os.path.join(project_root, 'gfx', 'tilesets', f'{tileset_base_name}_palette_map.asm')

    print(f"get_tileset_info returning PNG: {tileset_png_path}")
    print(f"get_tileset_info returning BIN: {metatiles_bin_path}")
    print(f"get_tileset_info returning PALETTE_MAP: {palette_map_asm_path}")

    return tileset_png_path, metatiles_bin_path, palette_map_asm_path

def render_game_frame(screen, map_surface, player_sprite, camera_x, camera_y, VIEW_PIXEL_WIDTH, VIEW_PIXEL_HEIGHT, MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT, map_width_blocks, map_height_blocks, block_ids, metatile_data, day_palettes, tile_palette_map, water_animation_frames, flower_animation_frames_cgb, player_x, player_y, animation_timer, pre_rendered_tiles):
    """
    Renders a single frame of the game, including the map and player sprite.

    Args:
        screen (pygame.Surface): The main display surface.
        map_surface (pygame.Surface): The surface representing the entire map.
        player_sprite (pygame.Surface): The player's sprite surface.
        camera_x (int): The X-coordinate of the camera's top-left corner on the map_surface.
        camera_y (int): The Y-coordinate of the camera's top-left corner on the map_surface.
        VIEW_PIXEL_WIDTH (int): The width of the view area in pixels.
        VIEW_PIXEL_HEIGHT (int): The height of the view area in pixels.
        MAP_PIXEL_WIDTH (int): The total width of the map in pixels.
        MAP_PIXEL_HEIGHT (int): The total height of the map in pixels.
        map_width_blocks (int): The width of the map in blocks.
        map_height_blocks (int): The height of the map in blocks.
        block_ids (bytes): Raw data representing the map's block layout.
        metatile_data (bytes): Raw data defining how metatiles are composed of tiles.
        tileset_image (PIL.Image.Image): The loaded tileset image.
        day_palettes (dict): Dictionary of loaded palettes.
        tile_palette_map (list): Mapping of tile IDs to palette names.
        water_animation_frames (list): List of Pygame Surfaces for water animation.
        flower_animation_frames_cgb (list): List of Pygame Surfaces for flower animation.
        player_x (int): Player's X-coordinate in tile units.
        player_y (int): Player's Y-coordinate in tile units.
        animation_timer (int): Timer for controlling animation frames.
    """
    # Clear the map surface for the new frame
    map_surface.fill(BLACK)

    # --- Render Map onto map_surface ---
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
                            # This uses the tile_palette_map (e.g., players_house_palette_map.asm)
                            # to get the palette name, and then looks up the actual colors in day_palettes (from bg_tiles.pal)
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
                                # For static tiles, use the pre-rendered surface
                                current_tile_surface = pre_rendered_tiles[tile_id]
                                # Ensure the correct palette is applied to the pre-rendered tile if it changes (e.g., day/night cycle)
                                # For now, we assume a single palette for static tiles, set during pre-rendering.
                                # If dynamic palette changes are needed, this will require more complex handling.
                                current_tile_surface.set_palette(palette)

                            # Calculate the position to blit the tile onto the map_surface
                            # This position is scaled by TILE_RENDER_SCALE because the tiles themselves are larger
                            screen_x = (block_x * BLOCK_WIDTH + tile_x) * TILE_SIZE * TILE_RENDER_SCALE
                            screen_y = (block_y * BLOCK_HEIGHT + tile_y) * TILE_SIZE * TILE_RENDER_SCALE

                            # Blit (draw) the tile surface onto the map_surface
                            if current_tile_surface:
                                map_surface.blit(current_tile_surface, (screen_x, screen_y))

    # --- Render Player Sprite ---
    # Calculate player's pixel position on the map_surface
    # Player coordinates (player_x, player_y) are in tile units, so multiply by TILE_SIZE * TILE_RENDER_SCALE for pixel position
    player_pixel_x = player_x * TILE_SIZE * TILE_RENDER_SCALE
    player_pixel_y = player_y * TILE_SIZE * TILE_RENDER_SCALE
    map_surface.blit(player_sprite, (player_pixel_x, player_pixel_y))

    # Blit the camera's view from the map_surface to the actual screen
    # This creates the scrolling effect if the map is larger than the view.
    # The third argument (pygame.Rect) defines the sub-rectangle of map_surface to blit.
    # Calculate the offset to center the map on the screen if it's smaller than the view.
    # This ensures maps smaller than the view area are centered, not just top-left aligned.
    offset_x = max(0, (VIEW_PIXEL_WIDTH - MAP_PIXEL_WIDTH) // 2)
    offset_y = max(0, (VIEW_PIXEL_HEIGHT - MAP_PIXEL_HEIGHT) // 2)
    screen.blit(map_surface, (offset_x, offset_y), pygame.Rect(camera_x, camera_y, VIEW_PIXEL_WIDTH, VIEW_PIXEL_HEIGHT))

    # Update the full display Surface to the screen
    pygame.display.flip()

def main(map_name_from_arg):
    """
    Main function to initialize Pygame, load assets, and render the map.

    Args:
        map_name (str): The uppercase name of the map to load (e.g., "PALLET_TOWN", "REDS_HOUSE_2F").
    """
    # Determine the project root directory based on the script's location
    # This allows the script to be run from any directory within the project.
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Get map dimensions dynamically from map_constants.asm
    # Use the uppercase version for map_constants.asm lookup
    map_name_for_lookup = map_name_from_arg.upper()
    map_width_blocks, map_height_blocks = get_map_dimensions(map_name_for_lookup, project_root)

    # Calculate the full map dimensions in pixels (the "larger canvas" where the entire map is drawn)
    # These dimensions are scaled by TILE_RENDER_SCALE to accommodate the scaled tiles.
    MAP_PIXEL_WIDTH = map_width_blocks * BLOCK_WIDTH * TILE_SIZE * TILE_RENDER_SCALE 
    MAP_PIXEL_HEIGHT = map_height_blocks * BLOCK_HEIGHT * TILE_SIZE * TILE_RENDER_SCALE 

    # Calculate the actual display window dimensions (the "view size" that the user sees).
    # These dimensions are fixed to the Game Boy Color's effective resolution (scaled by TILE_RENDER_SCALE).
    VIEW_PIXEL_WIDTH = GBC_SCREEN_WIDTH_TILES * TILE_SIZE * TILE_RENDER_SCALE
    VIEW_PIXEL_HEIGHT = GBC_SCREEN_HEIGHT_TILES * TILE_SIZE * TILE_RENDER_SCALE 

    # Initialize Pygame
    pygame.init()
    # Set up the display window with the fixed view dimensions
    screen = pygame.display.set_mode((VIEW_PIXEL_WIDTH, VIEW_PIXEL_HEIGHT))
    # Print calculated and actual screen sizes for debugging/verification
    print(f"Calculated VIEW_PIXEL_WIDTH: {VIEW_PIXEL_WIDTH}")
    print(f"Calculated VIEW_PIXEL_HEIGHT: {VIEW_PIXEL_HEIGHT}")
    print(f"Actual screen size: {screen.get_size()}")
    # Set the window title dynamically based on the loaded map name
    pygame.display.set_caption(f"Opal Engine - {map_name_for_lookup.replace('_', ' ').title()}")

    # Create a surface for the entire map (the "larger canvas")
    # All map tiles and sprites are drawn onto this surface first.
    map_surface = pygame.Surface((MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT), depth=8)

    # --- Load Assets ---
    # Get dynamic paths for tileset, metatiles, and palette map based on the map_name
    tileset_png_path, metatiles_bin_path, palette_map_asm_path = get_tileset_info(map_name_for_lookup, project_root)

    # If tileset information is not found, exit the game
    if tileset_png_path is None:
        pygame.quit()
        return

    # Assign the dynamically determined paths to variables used for loading
    tileset_path = tileset_png_path
    metatiles_path = metatiles_bin_path
    # This variable name is a remnant, but now correctly holds the dynamic palette map path
    kanto_palette_map_path = palette_map_asm_path 
    
    # Dynamically construct the map file path (e.g., "PalletTown.blk" from "PALLET_TOWN")
    # The map_name is converted to a format matching the .blk filenames (e.g., REDS_HOUSE_2F -> RedsHouse2F.blk)
    # Convert map_name_from_arg (e.g., "PALLET_TOWN") to PascalCase (e.g., "PalletTown")
    # This handles names like "REDS_HOUSE_2F" -> "RedsHouse2F"
    pascal_case_map_name = "".join([s.capitalize() for s in map_name_from_arg.lower().split('_')])
    map_filename = f'{pascal_case_map_name}.blk'
    map_path = os.path.join(project_root, 'maps', map_filename)
    
    # Path to the general background palette file (contains various palettes like DAY, NITE, GRAY, etc.)
    bg_palette_path = os.path.join(project_root, 'gfx', 'tilesets', 'bg_tiles.pal')

    try:
        # Print paths being used for asset loading for debugging/verification
        print(f"Loading tileset from: {tileset_path}")
        print(f"Loading metatiles from: {metatiles_path}")
        print(f"Loading palette map from: {kanto_palette_map_path}")
        
        # Load the main tileset image (e.g., kanto.png or players_house.png)
        tileset_image = Image.open(tileset_path)
        # Load background palettes from bg_tiles.pal
        day_palettes = get_palettes(bg_palette_path)
        # Load tile-to-palette mapping from the dynamically determined palette map ASM file
        tile_palette_map = get_tile_palette_map(palette_map_asm_path)
        # Set the palette for the entire map surface using the 'GRAY' palette from bg_tiles.pal
        map_surface.set_palette(day_palettes['GRAY']) 

        # Pre-render all static tiles from the tileset
        pre_rendered_tiles = load_tileset_tiles(tileset_image, day_palettes['GRAY']) 

        # Load animated tile frames for water and flowers (these are universal assets)
        water_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'water', 'water.png')
        water_animation_frames = load_animated_tiles_from_png(water_png_path, day_palettes['GRAY'])

        flower_cgb_1_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'flower', 'cgb_1.png')
        flower_cgb_2_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'flower', 'cgb_2.png')
        flower_animation_frames_cgb = load_animated_tiles_from_png(flower_cgb_1_png_path, day_palettes['GRAY']) + \
                                      load_animated_tiles_from_png(flower_cgb_2_png_path, day_palettes['GRAY'])

        # Load player sprite and apply the 'GRAY' palette
        player_sprite_path = os.path.join(project_root, 'gfx', 'sprites', 'chris.png')
        player_sprite = load_player_sprite(player_sprite_path, day_palettes['GRAY'])
        if player_sprite is None:
            pygame.quit()
            return

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

    # Player position in tile coordinates (e.g., 0,0 is top-left tile of the map)
    # For REDS_HOUSE_2F (4x4 blocks), a good starting point might be the center.
    # A block is 4x4 tiles, so a 4x4 block map is 16x16 tiles.
    # Center tile would be (8, 8).
    player_x = (map_width_blocks * BLOCK_WIDTH) // 2
    player_y = (map_height_blocks * BLOCK_HEIGHT) // 2

    # Game loop variables
    running = True
    animation_timer = 0 # Controls animation speed
    frame_counter = 0 # Used to slow down animation updates

    # Calculate camera position to center the view on the player
    # The player is 16x16 pixels, so we subtract half its size to truly center
    # The camera should follow the player, but not go off the map edges.
    player_pixel_x = player_x * TILE_SIZE * TILE_RENDER_SCALE
    player_pixel_y = player_y * TILE_SIZE * TILE_RENDER_SCALE

    camera_x = max(0, min(player_pixel_x + (16 * TILE_RENDER_SCALE // 2) - (VIEW_PIXEL_WIDTH // 2), MAP_PIXEL_WIDTH - VIEW_PIXEL_WIDTH))
    camera_y = max(0, min(player_pixel_y + (16 * TILE_RENDER_SCALE // 2) - (VIEW_PIXEL_HEIGHT // 2), MAP_PIXEL_HEIGHT - VIEW_PIXEL_HEIGHT))

    # --- Main Game Loop ---
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Render the current game frame
        render_game_frame(screen, map_surface, player_sprite, camera_x, camera_y, VIEW_PIXEL_WIDTH, VIEW_PIXEL_HEIGHT, MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT, map_width_blocks, map_height_blocks, block_ids, metatile_data, day_palettes, tile_palette_map, water_animation_frames, flower_animation_frames_cgb, player_x, player_y, animation_timer, pre_rendered_tiles)

if __name__ == "__main__":
    # This block runs when the script is executed directly
    if len(sys.argv) > 1:
        # If a command-line argument is provided, use it as the map name
        map_name_arg = sys.argv[1] # Keep original casing
    else:
        # Otherwise, default to "PALLET_TOWN"
        map_name_arg = "PALLET_TOWN"
        print(f"No map name provided. Defaulting to {map_name_arg}.")
    # Call the main function with the determined map name
    main(map_name_arg)