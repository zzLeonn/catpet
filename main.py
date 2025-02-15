import pygame
import sys
import win32api
import win32con
import win32gui
import random
import os

# Initialize Pygame
pygame.init()

# Get screen size
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Create borderless window
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.display.set_caption("Desktop Cat")

# Set window properties
hwnd = pygame.display.get_wm_info()["window"]
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)

# Configuration
SCALE_FACTOR = 3
WALK_SPEED = 1
RUN_SPEED = WALK_SPEED + 2
EVENT_INTERVAL = 3000

# Improved sprite sheet loader with error handling
def load_spritesheet(image_path, frame_width, num_frames, flip=False):
    try:
        sheet = pygame.image.load(image_path).convert_alpha()
        print(f"Loaded {image_path}: {sheet.get_width()}x{sheet.get_height()}")  # Debugging
        frame_height = sheet.get_height()
        
        # Validate sheet dimensions
        if frame_width * num_frames > sheet.get_width():
            raise ValueError(f"Sprite sheet {image_path} too narrow for {num_frames} frames of width {frame_width}")
            
        frames = []
        for i in range(num_frames):
            # Create subsurface with integer coordinates
            frame_rect = pygame.Rect(int(i * frame_width), 0, int(frame_width), frame_height)
            frame = sheet.subsurface(frame_rect)
            scaled_frame = pygame.transform.scale(
                frame,
                (int(frame_width * SCALE_FACTOR), int(frame_height * SCALE_FACTOR))
            )
            if flip:
                scaled_frame = pygame.transform.flip(scaled_frame, True, False)
            frames.append(scaled_frame)
        return frames
    except Exception as e:
        print(f"Error loading {image_path}: {str(e)}")
        return [pygame.Surface((50*SCALE_FACTOR, 50*SCALE_FACTOR), pygame.SRCALPHA)]

# Load all animations with corrected frame sizes
animations = {
    "idle": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Idle.png"), 50, 10),
    "walk_right": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Walk.png"), 50, 8),
    "walk_left": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Walk.png"), 50, 8, flip=True),
    "run_right": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Run.png"), 50, 8),
    "run_left": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Run.png"), 50, 8, flip=True),
    "sit": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Sitting.png"), 50, 1),
    "stretch": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Stretching.png"), 50, 13),
    "sleep": [
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Sleeping1.png"), 50, 1)[0],
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Sleeping2.png"), 50, 1)[0]
    ],
    "lick": (
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Licking 1.png"), 50, 5) +
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Licking 2.png"), 50, 5)
    ),
    # Corrected meow animations (200px width per frame, 4 frames total)
    "meow_right": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Meow.png"), 200, 4),
    "meow_left": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Meow.png"), 200, 4, flip=True),
    # VFX animation (48px width per frame, 3 frames total)
    "meow_vfx": load_spritesheet(os.path.join("assets", "sprites", "Meow-VFX.png"), 48, 3)
}

# State management
current_state = "idle"
current_frame = 0
frame_counter = 0
animation_speed = 10
pet_rect = animations["idle"][0].get_rect(center=(screen_width//2, screen_height//2))
dragging = False
facing_direction = "right"

# VFX state
vfx_active = False
vfx_frame = 0
vfx_frame_counter = 0
vfx_rect = None

# Event system
event_timer = pygame.time.get_ticks()
active_event = None
move_direction = None
special_duration = 0
special_start = 0

events = [
    ("idle", 10, False),
    ("walk", 25, False),
    ("run", 15, False),
    ("sit", 25, True),
    ("stretch", 20, True),
    ("sleep", 15, True),
    ("lick", 15, True),
    ("meow", 10, True)
]

def get_random_event(exclude=None):
    """Get a random event, optionally excluding certain events."""
    filtered_events = [e for e in events if e[0] != exclude]
    total = sum(weight for _, weight, _ in filtered_events)
    r = random.uniform(0, total)
    upto = 0
    for event, weight, _ in filtered_events:
        if upto + weight >= r:
            return event
        upto += weight
    return "idle"

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60)
    current_time = pygame.time.get_ticks()
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if pet_rect.collidepoint(mouse_pos):
                special_duration = 0
                dragging = True
                if mouse_pos[0] < pet_rect.centerx:
                    current_state = "walk_right"
                    facing_direction = "right"
                else:
                    current_state = "walk_left"
                    facing_direction = "left"
                current_frame = 0
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            current_state = "idle"
            current_frame = 0
        elif event.type == pygame.MOUSEMOTION and dragging:
            rel_x = event.rel[0]
            pet_rect.move_ip(event.rel)
            pet_rect.x = max(0, min(pet_rect.x, screen_width - pet_rect.width))
            pet_rect.y = max(0, min(pet_rect.y, screen_height - pet_rect.height))
            
            if rel_x > 0:
                current_state = "walk_right"
                facing_direction = "right"
            elif rel_x < 0:
                current_state = "walk_left"
                facing_direction = "left"

    # Random event logic
    if not dragging and current_time - event_timer > EVENT_INTERVAL and special_duration == 0:
        active_event = get_random_event()
        event_timer = current_time
        
        if active_event == "walk":
            current_state = "walk_right" if random.choice([True, False]) else "walk_left"
            move_direction = "right" if "right" in current_state else "left"
            facing_direction = move_direction
        elif active_event == "run":
            current_state = "run_right" if random.choice([True, False]) else "run_left"
            move_direction = "right" if "right" in current_state else "left"
            facing_direction = move_direction
        elif active_event == "sit":
            current_state = "sit"
            special_duration = random.randint(2000, 8000)
            special_start = current_time
        elif active_event == "stretch":
            current_state = "stretch"
            special_duration = len(animations["stretch"]) * animation_speed * 16
            special_start = current_time
        elif active_event == "sleep":
            current_state = "sleep"
            special_duration = random.randint(2000, 10000)
            special_start = current_time
            current_frame = random.randint(0, 1)
        elif active_event == "lick":
            current_state = "lick"
            special_duration = len(animations["lick"]) * animation_speed * 16
            special_start = current_time
        elif active_event == "meow":
            current_state = "meow_right" if facing_direction == "right" else "meow_left"
            special_duration = len(animations[current_state]) * animation_speed * 16
            special_start = current_time
            
            # Activate VFX
            vfx_active = True
            vfx_frame = 0
            vfx_frame_counter = 0
            vfx_image = animations["meow_vfx"][0]
            vfx_width = vfx_image.get_width()
            vfx_height = vfx_image.get_height()
            
            if facing_direction == "right":
                vfx_x = pet_rect.right - vfx_width//2
            else:
                vfx_x = pet_rect.left - vfx_width//2
                
            vfx_y = pet_rect.centery - vfx_height//2
            vfx_rect = pygame.Rect(vfx_x, vfx_y, vfx_width, vfx_height)
        
        current_frame = 0

    # Handle special durations
    if special_duration > 0:
        if current_time - special_start > special_duration:
            special_duration = 0
            current_state = "idle"
            current_frame = 0
        elif active_event in ["sit", "sleep"]:
            frame_counter = 0

    # Autonomous movement
    if not dragging and special_duration == 0:
        if active_event in ["walk", "run"]:
            speed = RUN_SPEED if active_event == "run" else WALK_SPEED
            prev_x = pet_rect.x
            
            if move_direction == "right":
                pet_rect.x += speed
                if pet_rect.right > screen_width:
                    pet_rect.x = screen_width - pet_rect.width
                    active_event = get_random_event(exclude="walk")
                    current_state = active_event
                    current_frame = 0
            else:
                pet_rect.x -= speed
                if pet_rect.left < 0:
                    pet_rect.x = 0
                    active_event = get_random_event(exclude="walk")
                    current_state = active_event
                    current_frame = 0
            
            if pet_rect.x == prev_x:
                active_event = get_random_event(exclude="walk")
                current_state = active_event
                current_frame = 0

    # Animation logic
    if (special_duration == 0 or active_event == "stretch") and not vfx_active:
        frame_counter += 1
        if frame_counter >= animation_speed:
            current_frame = (current_frame + 1) % len(animations[current_state])
            frame_counter = 0
            
            if active_event == "stretch" and current_frame == 0:
                special_duration = 0
                current_state = "idle"

    # Update VFX animation
    if vfx_active:
        vfx_frame_counter += 1
        if vfx_frame_counter >= animation_speed:
            vfx_frame += 1
            vfx_frame_counter = 0
            if vfx_frame >= len(animations["meow_vfx"]):
                vfx_active = False
                vfx_frame = 0


    # Update display
    screen.fill((0, 0, 0))
    screen.blit(animations[current_state][current_frame], pet_rect)
    if vfx_active:
        screen.blit(animations["meow_vfx"][vfx_frame], vfx_rect)
    pygame.display.flip()

pygame.quit()
sys.exit()