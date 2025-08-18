import pygame
import os

class Player:
    def __init__(self, human_sprite_instance, initial_x, initial_y, tile_size, tile_render_scale):
        self.human_sprite = human_sprite_instance
        self.x = initial_x  # Player's current X position in tile units
        self.y = initial_y  # Player's current Y position in tile units
        self.tile_size = tile_size # Size of a single map tile (e.g., 8 pixels)
        self.tile_render_scale = tile_render_scale # Scale factor for rendering map tiles (e.g., 4x)

        self.current_direction = 'down'
        self.is_moving = False
        self.animation_frame_index = 0
        self.animation_speed = 8 # frames per second for player animation (used for idle animation)

        # For tile-based movement
        self.target_x = initial_x
        self.target_y = initial_y
        self.movement_start_time = 0
        self.movement_duration = 416 # milliseconds to move one tile (25% faster)

        # Pixel position for rendering (interpolated during movement)
        self.current_pixel_x = self.x * self.tile_size * self.tile_render_scale
        self.current_pixel_y = self.y * self.tile_size * self.tile_render_scale

        self.last_movement_key = None # Stores the key that initiated the last movement
        self.next_movement_key = None # Stores the next movement key if pressed while moving

    def _start_movement(self, key):
        self.is_moving = True
        self.movement_start_time = pygame.time.get_ticks()
        
        # Store current tile position as start for interpolation
        self.start_x = self.x
        self.start_y = self.y

        # Calculate target tile
        if key == pygame.K_DOWN:
            self.current_direction = 'down'
            self.target_y += 2
        elif key == pygame.K_UP:
            self.current_direction = 'up'
            self.target_y -= 2
        elif key == pygame.K_LEFT:
            self.current_direction = 'left'
            self.target_x -= 2
        elif key == pygame.K_RIGHT:
            self.current_direction = 'right'
            self.target_x += 2
        
        # Ensure target is within map bounds (add map boundary checks later)
        # For now, just prevent moving off the current tile if no actual move happened
        if self.target_x == self.x and self.target_y == self.y:
            self.is_moving = False # No actual move, so not moving
            self.animation_frame_index = 0 # Reset to facing frame

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if not self.is_moving: # Only allow new movement if not already moving
                self.last_movement_key = event.key # Store the key that initiated this movement
                self._start_movement(event.key) # Call helper to start movement
            else: # If already moving, store the new key press as the next movement
                # Only buffer directional keys
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    self.next_movement_key = event.key

        elif event.type == pygame.KEYUP:
            # For Pokemon style movement, key up doesn't stop movement mid-tile.
            # Movement completes on its own.
            # If the released key was the last movement key, clear it.
            if event.key == self.last_movement_key:
                self.last_movement_key = None

    def update(self):
        current_time = pygame.time.get_ticks()
        if self.is_moving:
            elapsed_time = current_time - self.movement_start_time
            progress = min(1.0, elapsed_time / self.movement_duration)

            # Interpolate pixel position for smooth camera movement and sprite drawing
            # The player sprite is 64x64, map tiles are 8x8 (rendered 32x32)
            # So, moving one tile means moving 32 pixels.
            # This should be the size of a single map tile in pixels after rendering scale
            tile_pixel_size = self.tile_size * self.tile_render_scale # This is 32

            self.current_pixel_x = self.start_x * tile_pixel_size + (self.target_x - self.start_x) * tile_pixel_size * progress
            self.current_pixel_y = self.start_y * tile_pixel_size + (self.target_y - self.start_y) * tile_pixel_size * progress

            # Update animation frame based on movement progress
            # For a 2-frame animation, divide movement duration into 2 segments
            current_animation_frames = self.human_sprite.get_animation(self.current_direction)
            # Update animation frame based on movement progress
            # For a 4-frame animation, divide movement duration into 4 segments
            current_animation_frames = self.human_sprite.get_animation(self.current_direction)
            if current_animation_frames and len(current_animation_frames) == 4:
                frame_segment_duration = self.movement_duration / 4
                self.animation_frame_index = int(elapsed_time / frame_segment_duration) % 4
            else:
                # Fallback if animation frames are not 4 or don't exist
                self.animation_frame_index = 0 

            if progress >= 1.0:
                # Movement finished, snap to target tile
                self.x = self.target_x
                self.y = self.target_y
                self.is_moving = False
                self.animation_frame_index = 0 # Reset to facing frame
                # Ensure pixel position is exactly on the new tile
                self.current_pixel_x = self.x * tile_pixel_size
                self.current_pixel_y = self.y * tile_pixel_size

                # Check for buffered next movement first
                if self.next_movement_key is not None:
                    self.last_movement_key = self.next_movement_key # Use the buffered key
                    self.next_movement_key = None # Clear the buffer
                    self._start_movement(self.last_movement_key)
                else:
                    # If no buffered movement, check if the last movement key is still pressed for continuous movement
                    keys = pygame.key.get_pressed()
                    if self.last_movement_key is not None and keys[self.last_movement_key]:
                        # If the key is still pressed, start a new movement in that direction
                        self._start_movement(self.last_movement_key)
        else:
            # If not moving, ensure pixel position is snapped to current tile
            tile_pixel_size = self.tile_size * self.tile_render_scale
            self.current_pixel_x = self.x * tile_pixel_size
            self.current_pixel_y = self.y * tile_pixel_size
            self.animation_frame_index = 0 # Ensure facing frame when idle

    def get_current_sprite(self):
        if self.is_moving:
            current_animation_frames = self.human_sprite.get_animation(self.current_direction)
            if current_animation_frames:
                return current_animation_frames[self.animation_frame_index]
            else:
                return self.human_sprite.get_sprite(f'facing_{self.current_direction}')
        else:
            return self.human_sprite.get_sprite(f'facing_{self.current_direction}')

    def get_pixel_position(self):
        return self.current_pixel_x, self.current_pixel_y

    def get_tile_position(self):
        return self.x, self.y