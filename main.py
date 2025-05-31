import pygame
import sys
import win32api
import win32con
import win32gui
import random
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    filename='desktop_pet.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_error(error_msg):
    """Log errors with traceback information"""
    logging.error(error_msg)
    logging.error(traceback.format_exc())
    print(f"ERROR: {error_msg}")

# Initialize Pygame
try:
    pygame.init()
except Exception as e:
    log_error(f"Pygame initialization failed: {str(e)}")
    sys.exit(1)

# Get screen size
try:
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
except Exception as e:
    log_error(f"Failed to get screen info: {str(e)}")
    screen_width, screen_height = 1920, 1080  # Default to common resolution

# Create placeholder surface for missing assets
def create_placeholder_surface(width, height):
    """Create a visible placeholder for missing assets"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, (255, 0, 0, 128), surface.get_rect(), 2)
    pygame.draw.line(surface, (255, 0, 0, 128), (0, 0), (width, height), 2)
    pygame.draw.line(surface, (255, 0, 0, 128), (width, 0), (0, height), 2)
    font = pygame.font.SysFont(None, 20)
    text = font.render("Missing Asset", True, (255, 255, 255, 200))
    surface.blit(text, (5, height//2 - 10))
    return surface

# Create borderless window
try:
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
    pygame.display.set_caption("Desktop Cat")
    
    # Set window properties
    hwnd = pygame.display.get_wm_info()["window"]
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                         win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                          win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | 
                          win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 0, 
                                      win32con.LWA_COLORKEY)
except Exception as e:
    log_error(f"Window setup failed: {str(e)}")
    print("Falling back to standard window")
    try:
        screen = pygame.display.set_mode((800, 600))
    except Exception as e:
        log_error(f"Fallback window creation failed: {str(e)}")
        sys.exit(1)

# Configuration
SCALE_FACTOR = 3
WALK_SPEED = 1
RUN_SPEED = WALK_SPEED + 2
EVENT_INTERVAL = 3000
ANIMATION_SPEEDS = {
    "idle": 10,
    "walk": 8,
    "run": 6,
    "sit": 10,
    "stretch": 8,
    "sleep": 15,
    "lick": 8,
    "meow": 8
}
DEFAULT_PLACEHOLDER = create_placeholder_surface(50*SCALE_FACTOR, 50*SCALE_FACTOR)

def load_spritesheet(image_path, frame_width, frame_height, num_frames, flip=False):
    """Load and process sprite sheets with comprehensive error handling"""
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File not found: {image_path}")
            
        # Load the image
        sheet = pygame.image.load(image_path)
        if not sheet.get_alpha():
            sheet = sheet.convert_alpha()
        
        # Validate dimensions
        if sheet.get_width() < frame_width * num_frames:
            raise ValueError(
                f"Sheet width {sheet.get_width()} too small for {num_frames} frames "
                f"of width {frame_width} (needed {frame_width * num_frames})"
            )
            
        if sheet.get_height() < frame_height:
            raise ValueError(
                f"Sheet height {sheet.get_height()} too small for frame height {frame_height}"
            )
        
        # Process frames
        frames = []
        for i in range(num_frames):
            try:
                frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                frame = sheet.subsurface(frame_rect)
                scaled_frame = pygame.transform.scale(
                    frame, 
                    (int(frame_width * SCALE_FACTOR), int(frame_height * SCALE_FACTOR))
                )
                if flip:
                    scaled_frame = pygame.transform.flip(scaled_frame, True, False)
                frames.append(scaled_frame)
            except Exception as frame_error:
                log_error(f"Error processing frame {i} in {image_path}: {str(frame_error)}")
                frames.append(create_placeholder_surface(
                    frame_width * SCALE_FACTOR, 
                    frame_height * SCALE_FACTOR
                ))
        return frames
        
    except Exception as e:
        log_error(f"Error loading {image_path}: {str(e)}")
        # Return placeholders for all requested frames
        return [create_placeholder_surface(
            frame_width * SCALE_FACTOR, 
            frame_height * SCALE_FACTOR
        ) for _ in range(num_frames)]

def validate_animations(animations):
    """Ensure all required animations are present and valid"""
    required_anims = ["idle", "walk_right", "walk_left"]
    valid = True
    
    for anim_name in required_anims:
        if anim_name not in animations:
            log_error(f"Missing required animation: {anim_name}")
            valid = False
        elif not animations[anim_name]:
            log_error(f"Empty animation list for: {anim_name}")
            animations[anim_name] = [DEFAULT_PLACEHOLDER]
            valid = False
    
    # Check all animations have at least one frame
    for name, frames in animations.items():
        if not frames:
            log_error(f"Animation {name} has no frames")
            animations[name] = [DEFAULT_PLACEHOLDER]
            valid = False
            
    return valid

# Load animations (without blink animation)
animations = {
    "idle": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Idle.png"), 50, 50, 10),
    "walk_right": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Walk.png"), 50, 50, 8),
    "walk_left": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Walk.png"), 50, 50, 8, flip=True),
    "run_right": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Run.png"), 50, 50, 8),
    "run_left": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Run.png"), 50, 50, 8, flip=True),
    "sit": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Sitting.png"), 50, 50, 1),
    "stretch": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Stretching.png"), 50, 50, 13),
    "sleep": [
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Sleeping1.png"), 50, 50, 1)[0],
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Sleeping2.png"), 50, 50, 1)[0]
    ],
    "lick": (
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Licking 1.png"), 50, 50, 5) +
        load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Licking 2.png"), 50, 50, 5)
    ),
    "meow_right": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Meow.png"), 50, 50, 4),
    "meow_left": load_spritesheet(os.path.join("assets", "sprites", "Cat-5-Meow.png"), 50, 50, 4, flip=True),
    "meow_vfx_right": load_spritesheet(os.path.join("assets", "sprites", "Meow-VFX.png"), 16, 16, 3),
    "meow_vfx_left": load_spritesheet(os.path.join("assets", "sprites", "Meow-VFX.png"), 16, 16, 3, flip=True)
}

# Validate animations
if not validate_animations(animations):
    log_error("Critical animation validation failed - some features may not work")

# State management
class PetState:
    def __init__(self):
        self.current = "idle"
        self.facing = "right"
        self.frame = 0
        self.frame_counter = 0
        
    def change(self, new_state):
        if new_state != self.current:
            self.current = new_state
            self.frame = 0
            self.frame_counter = 0
            
            # Update facing direction based on state name
            if "right" in new_state:
                self.facing = "right"
            elif "left" in new_state:
                self.facing = "left"
                
    def get_frame(self):
        """Safely get the current animation frame"""
        try:
            if self.current in animations and animations[self.current]:
                return animations[self.current][self.frame % len(animations[self.current])]
        except Exception as e:
            log_error(f"Error getting frame for {self.current}: {str(e)}")
        return DEFAULT_PLACEHOLDER

pet_state = PetState()
pet_rect = animations["idle"][0].get_rect(center=(screen_width//2, screen_height//2))
dragging = False

# VFX state
vfx_active = False
vfx_state = "meow_vfx_right"
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
    ("meow", 15, True)
]

def get_random_event(exclude=None):
    """Select a random event based on weighted probabilities"""
    try:
        filtered_events = [e for e in events if e[0] != exclude]
        total = sum(weight for _, weight, _ in filtered_events)
        r = random.uniform(0, total)
        upto = 0
        for event, weight, _ in filtered_events:
            if upto + weight >= r:
                return event
            upto += weight
        return "idle"
    except Exception as e:
        log_error(f"Error in get_random_event: {str(e)}")
        return "idle"

# Main loop
clock = pygame.time.Clock()
running = True
last_time = pygame.time.get_ticks()

while running:
    try:
        current_time = pygame.time.get_ticks()
        dt = current_time - last_time
        last_time = current_time
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if pet_rect.collidepoint(mouse_pos):
                    special_duration = 0
                    dragging = True
                    pet_state.change("walk_right" if mouse_pos[0] < pet_rect.centerx else "walk_left")
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                pet_state.change("idle")
            elif event.type == pygame.MOUSEMOTION and dragging:
                rel_x = event.rel[0]
                pet_rect.move_ip(event.rel)
                pet_rect.x = max(0, min(pet_rect.x, screen_width - pet_rect.width))
                pet_rect.y = max(0, min(pet_rect.y, screen_height - pet_rect.height))
                if rel_x > 0:
                    pet_state.change("walk_right")
                elif rel_x < 0:
                    pet_state.change("walk_left")

        # Random event logic
        if not dragging and current_time - event_timer > EVENT_INTERVAL and special_duration == 0:
            active_event = get_random_event()
            event_timer = current_time
            
            if active_event == "walk":
                move_direction = "right" if random.choice([True, False]) else "left"
                pet_state.change(f"walk_{move_direction}")
            elif active_event == "run":
                move_direction = "right" if random.choice([True, False]) else "left"
                pet_state.change(f"run_{move_direction}")
            elif active_event == "sit":
                pet_state.change("sit")
                special_duration = random.randint(2000, 8000)
                special_start = current_time
            elif active_event == "stretch":
                pet_state.change("stretch")
                special_duration = len(animations["stretch"]) * ANIMATION_SPEEDS["stretch"] * 16
                special_start = current_time
            elif active_event == "sleep":
                pet_state.change("sleep")
                special_duration = random.randint(2000, 10000)
                special_start = current_time
                pet_state.frame = random.randint(0, 1)
            elif active_event == "lick":
                pet_state.change("lick")
                special_duration = len(animations["lick"]) * ANIMATION_SPEEDS["lick"] * 16
                special_start = current_time
            elif active_event == "meow":
                state_name = f"meow_{pet_state.facing}"
                pet_state.change(state_name)
                vfx_state = f"meow_vfx_{pet_state.facing}"
                
                # Activate VFX
                vfx_active = True
                vfx_frame = 0
                vfx_frame_counter = 0
                try:
                    vfx_image = animations[vfx_state][0]
                    vfx_width = vfx_image.get_width()
                    vfx_height = vfx_image.get_height()
                    
                    if pet_state.facing == "right":
                        vfx_x = pet_rect.right - vfx_width//2
                    else:
                        vfx_x = pet_rect.left - vfx_width//2
                        
                    vfx_rect = pygame.Rect(vfx_x, pet_rect.centery - vfx_height//2, vfx_width, vfx_height)
                except Exception as e:
                    log_error(f"Error setting up VFX: {str(e)}")
                    vfx_active = False

        # Handle special durations
        if special_duration > 0:
            if current_time - special_start > special_duration:
                special_duration = 0
                pet_state.change("idle")
            elif active_event in ["sit", "sleep"]:
                pet_state.frame_counter = 0

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
                        pet_state.change(active_event)
                else:
                    pet_rect.x -= speed
                    if pet_rect.left < 0:
                        pet_rect.x = 0
                        active_event = get_random_event(exclude="walk")
                        pet_state.change(active_event)
                
                if pet_rect.x == prev_x:
                    active_event = get_random_event(exclude="walk")
                    pet_state.change(active_event)

        # Animation logic
        if special_duration == 0 or active_event == "stretch":
            pet_state.frame_counter += dt
            
            # Get animation speed for current state
            anim_speed = ANIMATION_SPEEDS.get(
                active_event if active_event in ANIMATION_SPEEDS else pet_state.current.split('_')[0],
                ANIMATION_SPEEDS["idle"]
            )
            
            if pet_state.frame_counter > 1000 / anim_speed:
                pet_state.frame = (pet_state.frame + 1) % len(animations.get(pet_state.current, [1]))
                pet_state.frame_counter = 0
                
                # Handle stretch animation completion
                if active_event == "stretch" and pet_state.frame == 0:
                    special_duration = 0
                    pet_state.change("idle")

        # Update VFX animation
        if vfx_active:
            vfx_frame_counter += dt
            if vfx_frame_counter > 1000 / ANIMATION_SPEEDS["meow"]:
                vfx_frame += 1
                vfx_frame_counter = 0
                if vfx_frame >= len(animations.get(vfx_state, [1])):
                    vfx_active = False
                    vfx_frame = 0

        # Update display
        screen.fill((0, 0, 0))
        screen.blit(pet_state.get_frame(), pet_rect)
        
        if vfx_active:
            try:
                if vfx_state in animations and vfx_frame < len(animations[vfx_state]):
                    screen.blit(animations[vfx_state][vfx_frame], vfx_rect)
            except Exception as e:
                log_error(f"Error drawing VFX: {str(e)}")
                vfx_active = False
        
        pygame.display.flip()
        clock.tick(60)
        
    except Exception as e:
        log_error(f"Critical error in main loop: {str(e)}")
        # Attempt to recover
        try:
            pet_state.change("idle")
            pygame.display.flip()
        except:
            log_error("Unable to recover - exiting")
            running = False

pygame.quit()
sys.exit()