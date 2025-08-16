import pygame
import os
import re
from PIL import Image

# Constants
TILE_SIZE = 8
BLOCK_WIDTH = 4
BLOCK_HEIGHT = 4
MAP_WIDTH_BLOCKS = 10
MAP_HEIGHT_BLOCKS = 9

SCREEN_WIDTH = MAP_WIDTH_BLOCKS * BLOCK_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT_BLOCKS * BLOCK_HEIGHT * TILE_SIZE

# Colors
BLACK = (0, 0, 0)

def get_palettes(file_path):
    palettes = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if "RGB" in line and not line.startswith(';'):
                parts = line.split(';')
                palette_name = parts[-1].strip().upper()
                numbers = re.findall(r'\d+', parts[0])
                colors = []
                for i in range(0, len(numbers), 3):
                    r = int(numbers[i]) * 8
                    g = int(numbers[i+1]) * 8
                    b = int(numbers[i+2]) * 8
                    colors.append((r, g, b))
                palettes[palette_name] = colors[::-1]
    return palettes

def get_tile_palette_map(file_path):
    tile_palette_map = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('tilepal'):
                parts = line.split(',')
                for part in parts[1:]:
                    tile_palette_map.append(part.strip().upper())
    return tile_palette_map

# Helper function to load animated tiles from a PNG file
def load_animated_tiles_from_png(filepath):
    tiles = []
    try:
        img = Image.open(filepath).convert("RGBA")
        for i in range(img.height // TILE_SIZE):
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE), depth=8)
            for y in range(TILE_SIZE):
                for x in range(TILE_SIZE):
                    r, g, b, a = img.getpixel((x, i * TILE_SIZE + y))
                    if a == 0:
                        # Transparent, so use color 0
                        palette_index = 0
                    else:
                        # Map grayscale to one of the 4 palette colors
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

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Opal Engine - Pallet Town")

    # Load assets
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tileset_path = os.path.join(project_root, 'gfx', 'tilesets', 'kanto.png')
    metatiles_path = os.path.join(project_root, 'data', 'tilesets', 'kanto_metatiles.bin')
    map_path = os.path.join(project_root, 'maps', 'PalletTown.blk')
    bg_palette_path = os.path.join(project_root, 'gfx', 'tilesets', 'bg_tiles.pal')
    kanto_palette_map_path = os.path.join(project_root, 'gfx', 'tilesets', 'kanto_palette_map.asm')

    try:
        tileset_image = Image.open(tileset_path)
        day_palettes = get_palettes(bg_palette_path)
        tile_palette_map = get_tile_palette_map(kanto_palette_map_path)

        # Load animation frames
        water_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'water', 'water.png')
        water_animation_frames = load_animated_tiles_from_png(water_png_path)

        flower_cgb_1_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'flower', 'cgb_1.png')
        flower_cgb_2_png_path = os.path.join(project_root, 'gfx', 'tilesets', 'flower', 'cgb_2.png')
        flower_animation_frames_cgb = load_animated_tiles_from_png(flower_cgb_1_png_path) + \
                                      load_animated_tiles_from_png(flower_cgb_2_png_path)

    except (IOError, FileNotFoundError) as e:
        print(f"Error loading assets: {e}")
        return

    # Read map block data
    with open(map_path, 'rb') as f:
        block_ids = f.read()

    # Read metatile data
    with open(metatiles_path, 'rb') as f:
        metatile_data = f.read()

    running = True
    animation_timer = 0 # Initialize animation timer
    frame_counter = 0 # Initialize frame counter
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BLACK)

        frame_counter = (frame_counter + 1) % 4 # Increment frame counter (0, 1, 2, 3)
        if frame_counter == 0: # Only update animation_timer every 4 frames
            animation_timer = (animation_timer + 1) % 8

        # Render map
        for block_y in range(MAP_HEIGHT_BLOCKS):
            for block_x in range(MAP_WIDTH_BLOCKS):
                block_index = block_y * MAP_WIDTH_BLOCKS + block_x
                if block_index < len(block_ids):
                    block_id = block_ids[block_index]
                    
                    metatile_index = block_id * (BLOCK_WIDTH * BLOCK_HEIGHT)
                    metatile = metatile_data[metatile_index:metatile_index + (BLOCK_WIDTH * BLOCK_HEIGHT)]

                    for tile_y in range(BLOCK_HEIGHT):
                        for tile_x in range(BLOCK_WIDTH):
                            tile_index_in_metatile = tile_y * BLOCK_WIDTH + tile_x
                            if tile_index_in_metatile < len(metatile):
                                tile_id = metatile[tile_index_in_metatile]

                                palette_name = tile_palette_map[tile_id]
                                palette = day_palettes[palette_name]

                                current_tile_surface = None

                                if tile_id == 20 and water_animation_frames: # Water tile (0x14)
                                    frame_index = (animation_timer // 2) % 4
                                    current_tile_surface = water_animation_frames[frame_index]
                                    current_tile_surface.set_palette(palette)

                                elif tile_id == 3 and flower_animation_frames_cgb: # Flower tile (0x03)
                                    frame_index = (animation_timer // 2) % 2
                                    current_tile_surface = flower_animation_frames_cgb[frame_index]
                                    current_tile_surface.set_palette(palette)

                                else:
                                    # Existing logic for static tiles (from kanto.png)
                                    current_tile_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), depth=8)
                                    current_tile_surface.set_palette(palette)

                                    tileset_x = (tile_id % (tileset_image.width // TILE_SIZE)) * TILE_SIZE
                                    tileset_y = (tile_id // (tileset_image.width // TILE_SIZE)) * TILE_SIZE

                                    for y_pixel in range(TILE_SIZE):
                                        for x_pixel in range(TILE_SIZE):
                                            grayscale_value = tileset_image.getpixel((tileset_x + x_pixel, tileset_y + y_pixel))
                                            if grayscale_value < 64:
                                                palette_index = 0
                                            elif grayscale_value < 128:
                                                palette_index = 1
                                            elif grayscale_value < 192:
                                                palette_index = 2
                                            else:
                                                palette_index = 3
                                            current_tile_surface.set_at((x_pixel, y_pixel), palette_index)

                                screen_x = (block_x * BLOCK_WIDTH + tile_x) * TILE_SIZE
                                screen_y = (block_y * BLOCK_HEIGHT + tile_y) * TILE_SIZE

                                if current_tile_surface: # Only blit if a surface was created
                                    screen.blit(current_tile_surface, (screen_x, screen_y))


        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
