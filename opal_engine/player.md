# Player Sprite and Movement Implementation Plan

## Goal
To load the 2nd floor of Red's house (or any other small map) with black space around it, display a player sprite, enable player movement with appropriate collision detection, and simulate Pokémon-style movement (tile-based, step-by-step).

## Phase 1: Player Sprite Loading and Display
1.  **Player Sprite Asset:** Identify or create a placeholder player sprite (e.g., a simple square or a basic character sprite).
    *   Need to determine the sprite sheet format (e.g., multiple frames for animation, different directions).
    *   Load the sprite sheet using PIL and convert to Pygame surfaces, similar to how animated tiles are loaded.
2.  **Initial Player Position:** Define a starting position for the player on the map (e.g., center of the view, or a specific tile).
3.  **Rendering Player:** Blit the player sprite onto the `map_surface` at its current position *after* the map tiles have been rendered.

## Phase 2: Basic Movement (Tile-based)
1.  **Input Handling:** Detect arrow key presses (Up, Down, Left, Right) using Pygame's event system.
2.  **Movement Logic:**
    *   Implement tile-based movement: when a key is pressed, the player attempts to move one tile in that direction.
    *   Introduce a movement state (e.g., `idle`, `moving`) to prevent continuous movement while a key is held down.
    *   Consider animation for movement (e.g., walking frames).
3.  **Player Position Update:** Update the player's logical tile coordinates (e.g., `player_x`, `player_y`).
4.  **Camera Follow (Future Consideration):** For larger maps, the camera will eventually need to follow the player. For now, the player will move within the fixed camera view.

## Phase 3: Collision Detection
1.  **Map Collision Data:** Determine how to get collision information for each tile on the map.
    *   This likely involves reading additional data associated with the map or metatiles (e.g., a collision layer or flags in metatile definitions).
    *   Need to investigate the original assembly project for how collision is handled (e.g., `collision_constants.asm`, `data/collision/`).
2.  **Collision Check:** Before moving the player to a new tile, check if the target tile is walkable.
    *   If not walkable, prevent movement.

## Phase 4: Pokémon-style Movement (Step-by-step animation)
1.  **Smooth Movement:** Instead of instantly jumping to the next tile, animate the player's movement smoothly over a short duration (e.g., a few frames).
    *   This involves interpolating the player's pixel position between the start and end tiles.
2.  **Animation Frames:** Use different sprite frames for walking animations (e.g., left foot forward, right foot forward).

## Phase 5: Integrating with Map Renderer
1.  **Refactor `map_renderer.py`:** The `map_renderer.py` will primarily be responsible for rendering the map and handling the camera. The player logic will be separate.
2.  **Main Game Loop:** A higher-level `main.py` (or similar) will orchestrate the game loop, calling `map_renderer` to draw the map and then drawing the player on top.

## Assets to Investigate
*   `gfx/player/` (if exists, for player sprites)
*   `constants/collision_constants.asm`
*   `data/collision/`
*   `data/sprites/` (for player sprite definition)

## Initial Map for Testing
*   `REDS_HOUSE_2F` (or `PLAYERS_HOUSE_2F` if that's the correct name for Red's house 2F in Pallet Town). Need to confirm the exact map name from `map_constants.asm` and the corresponding `.blk` file.

## Action Items
1.  Confirm the exact map name for Red's House 2F.
2.  Locate player sprite assets or create a placeholder.
3.  Investigate collision data format.
4.  Start implementing Phase 1 in `map_renderer.py` (for now, will move to separate player module later).