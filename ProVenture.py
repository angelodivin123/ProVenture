"""
ProVenture - REVISED VERSION
Major Changes:
- Character Selection (Tank, Assassin, Knight)
- 3 Lives System with Buyback
- Boss Fight before victory
- Leaderboards (Top 10)
- Settings (Volume/Mute)
- 30 Questions (Easy/Average/Difficult)
- 15-second Quiz Timer
- Respawn Timer (5 seconds)
- Victory Video + Credits
- Continue Function Fixed
- Centered Window Display
- 16:9 ASPECT RATIO (1280x720)

Run: python ProVenture_REVISED.py
Requires: pygame, Pillow
"""

import pygame, sys, os, json, time, random, math
from pathlib import Path
from copy import deepcopy
from PIL import Image, ImageSequence

# ------------------- CONFIG -------------------
WIN_W, WIN_H = 1280, 720  #     
BG_COLOR = (18, 24, 38)
INPUT_BG = (255, 255, 255)
INPUT_ACTIVE = (235, 235, 255)
BUTTON_COLOR = (64, 160, 255)
BUTTON_HOVER = (80, 180, 255)
ERROR_COLOR = (255, 80, 80)
SUCCESS_COLOR = (80, 200, 80)
INFO_COLOR = (200, 200, 200)
HUD_MSG_COLOR = (255, 255, 200)
USERS_FILE = "users.json"

# Game constants
TILE = 40
ROWS, COLS = 15, 20
PLAYER_RADIUS = TILE // 3
MAZES_COUNT = 4

# Game mechanics
DESTRUCTIBLE_HP = 60
DESTRUCTIBLE_SPAWN_CHANCE = 0.0  # Set to 0 to remove destructible blocks
ENEMY_BASE_HP = 40
ENEMY_BASE_DMG = 8
ENEMY_SCALE_PER_SEC_HP = 0.6
ENEMY_SCALE_PER_SEC_DMG = 0.15
DOOR_COST = 25
PLAYER_BASE_SPEED = 160
ENEMY_BASE_SPEED = 50
ENEMY_MAX_SPEED_BONUS = 120
ENEMY_SPAWN_INTERVAL = 8.0
ENEMY_SPAWN_INTERVAL_MIN = 2.5
ENEMY_SPAWN_INTERVAL_SCALING_TIME = 8.0

# Lives and Respawn
MAX_LIVES = 3
RESPAWN_TIMER = 5.0
BUYBACK_COST = 200  # INCREASED: More expensive buyback

# Quiz settings
QUIZ_TIME_LIMIT = 15.0  # 15 seconds per quiz
QUIZ_EASY_ITEMS = {"wood": (1, 2), "rope": (0, 1), "metal": (0, 1), "sail": (0, 0), "points": (50, 75)}
QUIZ_AVERAGE_ITEMS = {"wood": (2, 3), "rope": (1, 2), "metal": (1, 1), "sail": (0, 1), "points": (75, 125)}
QUIZ_DIFFICULT_ITEMS = {"wood": (3, 4), "rope": (2, 3), "metal": (1, 2), "sail": (1, 2), "points": (150, 200)}

# Crafting
SHIP_CRAFT_REQUIREMENTS = {"wood": 8, "rope": 5, "metal": 4, "sail": 2}

# Boss stats
BOSS_HP = 300
BOSS_DMG = 50  # Damage to player when wrong answer
BOSS_SPEED = 30
BOSS_POINTS_REWARD = 1000

# Character stats
CHARACTERS = {
    "Tank": {
        "speed": 100,  # Low speed
        "health": 200,  # High health
        "damage": 30,  # Balanced damage
        "regen_rate": 20,  # Regenerates 3 HP every 5 seconds
        "special": "regeneration"
    },
    "Assassin": {
        "speed": 250,  # High speed
        "health": 80,  # Low health
        "damage": 30,  # Balanced damage
        "crit_chance": 0.25,  # 25% one-hit kill chance
        "special": "critical"
    },
    "Knight": {
        "speed": 150,  # Balanced speed
        "health": 100,  # Balanced health
        "damage": 50,  # Highest damage
        "quiz_help": True,  # Removes 2 wrong choices
        "special": "enlightenment"
    }
}

# Settings
SETTINGS = {
    "volume": 0.5,
    "muted": False
}

# Colors & fonts
pygame.init()
# Center window on screen
os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.display.set_caption("ProVenture")
screen = pygame.display.set_mode((WIN_W, WIN_H))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("consolas", 18)
BIG = pygame.font.SysFont("consolas", 28)
SMALL = pygame.font.SysFont("consolas", 14)
HUGE = pygame.font.SysFont("consolas", 48)

WHITE = (255, 255, 255)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#----------for characters def so that wont repeat------------
def load_gif_frames(path, size=(60, 60)):
    gif = Image.open(path)
    frames = []
    try:
        while True:
            fr = gif.copy().convert("RGBA")
            fr = fr.resize(size)
            pg_fr = pygame.image.frombytes(fr.tobytes(), fr.size, "RGBA").convert_alpha()
            frames.append(pg_fr)
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

# ------------------- LOAD RESOURCES -------------------

crosshair_img = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "crosshair.png")).convert_alpha()
crosshair_img = pygame.transform.scale(crosshair_img, (30, 30))
pygame.mouse.set_visible(False)

grim_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "resources", "sounds", "Jumpscare.mp3"))
grim_sound.set_volume(0.6)

door_block = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "DOOR.png")).convert_alpha()
door_block = pygame.transform.scale(door_block, (40, 40))

question_block = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "QABOX.png")).convert_alpha()
question_block = pygame.transform.scale(question_block, (40, 40))

block_path_img = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "block.png"))
block_path_img = pygame.transform.scale(block_path_img, (50, 50))

path_img = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "path.png")).convert()
path_img = pygame.transform.scale(path_img, (TILE, TILE))

button_img = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "button.png")).convert_alpha()

custom_font_login = pygame.font.Font(os.path.join(BASE_DIR, "resources", "font", "loginfont.ttf"), 28)

wall_img = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "wall.png")).convert_alpha()
wall_img = pygame.transform.scale(wall_img, (TILE, TILE))

maze_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "mazeback.png")).convert()
maze_bg = pygame.transform.scale(maze_bg, (WIN_W, WIN_H))

leaderboard_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "LDback.jpg")).convert()
leaderboard_bg = pygame.transform.scale(leaderboard_bg, (WIN_W, WIN_H))

Tutorial_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "TUTORIALB.jpg")).convert()
Tutorial_bg = pygame.transform.scale(Tutorial_bg, (WIN_W, WIN_H))

gameover_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "Game_Over_bg.jpg")).convert()
gameover_bg = pygame.transform.scale(gameover_bg, (WIN_W, WIN_H))

settings_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "SETTINGS_bg.jpg")).convert()
settings_bg = pygame.transform.scale(settings_bg, (WIN_W, WIN_H))

Door_selec_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "Bg_Door_select.jpg")).convert()
Door_selec_bg = pygame.transform.scale(Door_selec_bg, (WIN_W, WIN_H))

Boss_final_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "boss_bg.jpg")).convert()
Boss_final_bg = pygame.transform.scale(Boss_final_bg, (WIN_W, WIN_H))

q_a_bg = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "q_a.jpg")).convert()
q_a_bg = pygame.transform.scale(q_a_bg, (WIN_W, WIN_H))

Tank_image = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Tank_idle.gif"))
tank_frame_index = 0
tank_frame_timer = 0

Tank_image_run = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Tank_walk.gif"))
tank_walk_frame_index = 0
tank_walk_frame_timer = 0

Tank_image_attack = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Tank_attack.gif"))
tank_attack_frame_index = 0
tank_attack_frame_timer = 0

Knight_image = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Knight_idle.gif"))
knight_frame_index = 0
knight_frame_timer = 0

Knight_image_run = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Knight_walk.gif"))
knight_walk_frame_index = 0
knight_walk_frame_timer = 0

Knight_image_attack = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Knight_attack.gif"))
knight_attack_frame_index = 0
knight_attack_frame_timer = 0

Assasin_image = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Assasin_idle.gif"))
assassin_frame_index = 0
assassin_frame_timer = 0

Assasin_image_run = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Assasin_walk.gif"))
assassin_walk_frame_index = 0
assassin_walk_frame_timer = 0

Assasin_image_attack = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Assasin_attack.gif"))
assassin_attack_frame_index = 0
assassin_attack_frame_timer = 0

Tank_image_boss = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Tank_boss.gif"))
Assasin_image_boss = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Assasin_boss.gif"))
Knight_image_boss = load_gif_frames(os.path.join(BASE_DIR, "resources", "images", "Knight_boss.gif"))


    
# Load enemy GIF
gif = Image.open(os.path.join(BASE_DIR, "resources", "images", "Enemy.gif"))
frames = []
try:
    while True:
        frame = gif.copy().convert("RGBA")
        frame = frame.resize((60, 60))
        pygame_frame = pygame.image.frombytes(frame.tobytes(), frame.size, "RGBA").convert_alpha()
        frames.append(pygame_frame)
        gif.seek(gif.tell() + 1)
except EOFError:
    pass

print(f"Loaded {len(frames)} frames from Enemy.gif")

# Grim image (for boss)
grim_image = pygame.image.load(os.path.join(BASE_DIR, "resources", "images", "grim.png")).convert_alpha()
grim_image = pygame.transform.scale(grim_image, (300, 300))

# ------------------- JSON Utilities -------------------
def atomic_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def load_json_or_default(path, default):
    if not os.path.exists(path):
        atomic_write(path, default)
        return deepcopy(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print(f"Error loading {path}, recreating with default.")
        atomic_write(path, default)
        return deepcopy(default)

DEFAULT_USERS = {"users": {}}
users_data = load_json_or_default(USERS_FILE, DEFAULT_USERS)

def save_users():
    atomic_write(USERS_FILE, users_data)

def create_user(username, password):
    if username in users_data['users']:
        return False, "Username already exists."
    users_data['users'][username] = {
        "password": password,
        "created": time.time(),
        "character": None,
        "current_maze": 1,
        "maze_seeds": {},
        "x": None,
        "y": None,
        "health": 100,
        "lives": MAX_LIVES,
        "points": 100,
        "materials": {"wood": 0, "rope": 0, "metal": 0, "sail": 0},
        "completed_quizzes": [],
        "achievements": [],
        "kills": 0,
        "wins": 0,
        "total_items": 0,
        "high_score": 0,
        "enemies_state": [],
        "in_boss_fight": False
    }
    save_users()
    return True, "Account created."

def validate_user(username, password):
    u = users_data['users'].get(username)
    if not u:
        return False, "No such username."
    if u.get("password") != password:
        return False, "Incorrect password."
    return True, "Login successful."

def update_leaderboard(username):
    """Update player stats for leaderboard"""
    user = users_data['users'][username]
    total_items = sum(user['materials'].values())
    user['total_items'] = total_items
    user['high_score'] = max(user.get('high_score', 0), user['points'])
    save_users()

def get_leaderboard():
    """Get top 10 players by high_score, then total_items, then wins"""
    players = []
    for username, data in users_data['users'].items():
        players.append({
            'username': username,
            'high_score': data.get('high_score', 0),
            'total_items': data.get('total_items', 0),
            'wins': data.get('wins', 0)
        })
    players.sort(key=lambda x: (x['high_score'], x['total_items'], x['wins']), reverse=True)
    return players[:10]

# ------------------- Drawing helper -------------------
def draw_text(surf, text, pos, color=(255, 255, 255), font=FONT, center=False):
    text_surface = font.render(text, True, color)
    if center:
        text_rect = text_surface.get_rect(center=pos)
        surf.blit(text_surface, text_rect)
    else:
        surf.blit(text_surface, pos)

def apply_volume_settings():
    """Apply current volume settings to all sounds"""
    vol = 0 if SETTINGS['muted'] else SETTINGS['volume']
    pygame.mixer.music.set_volume(vol)
    grim_sound.set_volume(vol * 0.6)

# ------------------- Input / Button UI -------------------
class InputBox:
    def __init__(self, rect, placeholder="", is_password=False, font=None):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.is_password = is_password
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.text_color = (0, 0, 0)
        self.max_len = 32
        self.font = font or FONT
        self.text_surface = self.font.render("", True, self.text_color)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.cursor_timer = 0.0
            self.cursor_visible = True
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "enter"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_TAB:
                return "tab"
            else:
                if event.unicode.isprintable() and len(self.text) < self.max_len:
                    self.text += event.unicode
            self.text_surface = self.font.render(self.get_display_text(), True, self.text_color)
            self.cursor_timer = 0.0
            self.cursor_visible = True
        return None

    def get_display_text(self):
        return "*" * len(self.text) if self.is_password else self.text

    def update(self, dt):
        if self.active:
            self.cursor_timer += dt
            if self.cursor_timer > 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0.0

    def draw(self, surf):
        bg = INPUT_ACTIVE if self.active else INPUT_BG
        pygame.draw.rect(surf, bg, self.rect, border_radius=4)
        pygame.draw.rect(surf, (140, 140, 140), self.rect, 2, border_radius=4)

        display_text = self.get_display_text()
        if not display_text and not self.active:
            draw_text(surf, self.placeholder, (self.rect.x + 8, self.rect.y + 6), color=(110, 110, 110))
        else:
            surf.blit(self.text_surface, (self.rect.x + 8, self.rect.y + 6))
        
        if self.active and self.cursor_visible:
            text_w = self.font.size(display_text)[0]
            cx = self.rect.x + 8 + text_w + 2
            cy = self.rect.y + 6
            pygame.draw.rect(surf, (0, 0, 0), (cx, cy, 2, self.font.get_height()))

class Button:
    def __init__(self, rect, text, font=BIG, color=BUTTON_COLOR, hover_color=BUTTON_HOVER, text_color=(0, 0, 0)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surf):
        scaled_img = pygame.transform.scale(button_img, (self.rect.width, self.rect.height))
        surf.blit(scaled_img, self.rect)
        tw, th = self.font.size(self.text)
        tx = self.rect.x + (self.rect.w - tw) // 2
        ty = self.rect.y + (self.rect.h - th) // 2
        draw_text(surf, self.text, (tx, ty), font=self.font, color=self.text_color)
    
def draw_cursor(surface):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    surface.blit(crosshair_img, crosshair_img.get_rect(center=(mouse_x, mouse_y)))
# ------------------- Settings Screen -------------------
def settings_screen():
    back_btn = Button((50, 50, 150, 50), "BACK",color=ERROR_COLOR, text_color=WHITE, font=custom_font_login)
    mute_btn = Button((WIN_W//2 - 150, 250, 300, 60), "Mute: OFF", text_color=WHITE, font=custom_font_login)
    vol_up_btn = Button((WIN_W//2 + 50, 350, 135, 50), "VOL +", text_color=WHITE, font=custom_font_login)
    vol_down_btn = Button((WIN_W//2 - 180, 350, 125, 50), "VOL -", text_color=WHITE, font=custom_font_login)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if back_btn.handle_event(event):
                return
            
            if mute_btn.handle_event(event):
                SETTINGS['muted'] = not SETTINGS['muted']
                apply_volume_settings()
            
            if vol_up_btn.handle_event(event):
                SETTINGS['volume'] = min(1.0, SETTINGS['volume'] + 0.1)
                apply_volume_settings()
            
            if vol_down_btn.handle_event(event):
                SETTINGS['volume'] = max(0.0, SETTINGS['volume'] - 0.1)
                apply_volume_settings()
        
        
        screen.blit(settings_bg, (0, 0))  # draw image
        draw_text(screen, "SETTINGS", (WIN_W//2, 100), color=(255, 210, 0), font=custom_font_login, center=True)
        
        mute_btn.text = f"MUTE: {'ON' if SETTINGS['muted'] else 'OFF'}"
        mute_btn.draw(screen)
        
        draw_text(screen, f"Volume: {int(SETTINGS['volume'] * 100)}%", (WIN_W//2, 320), color=WHITE, font=BIG, center=True)
        vol_up_btn.draw(screen)
        vol_down_btn.draw(screen)
        back_btn.draw(screen)

        draw_cursor(screen)
        pygame.display.flip()
       

# ------------------- Auth Screen -------------------
def login_register_screen():
    user_box = InputBox((WIN_W//2 - 100, 280, 340, 40), "ENTER USERNAME", font=custom_font_login)
    pass_box = InputBox((WIN_W//2 - 100, 340, 340, 40), "ENTER PASSWORD", is_password=True, font=custom_font_login)
    login_btn = Button((WIN_W//2 - 280, 410, 200, 70), "LOGIN", text_color=WHITE, font=custom_font_login)
    reg_btn = Button((WIN_W//2 + 50, 410, 200, 70), "SIGN UP", text_color=WHITE, font=custom_font_login)
    settings_btn = Button((WIN_W - 260, 30, 250, 50), "SETTINGS", text_color=WHITE, font=custom_font_login)
    
    info_msg = ""
    info_color = INFO_COLOR
    
    pygame.mixer.music.load(os.path.join(BASE_DIR, "resources", "sounds", "loginsound.mp3"))
    apply_volume_settings()
    pygame.mixer.music.play(-1)
    
    gif_login_background = Image.open(os.path.join(BASE_DIR, "resources", "images", "background.gif"))
    bg_frames = []
    
    try:
        while True:
            frame = gif_login_background.copy().convert("RGBA")
            frame = frame.resize((WIN_W, WIN_H))
            pygame_frame = pygame.image.frombytes(frame.tobytes(), frame.size, "RGBA").convert_alpha()
            bg_frames.append(pygame_frame)
            gif_login_background.seek(gif_login_background.tell() + 1)
    except EOFError:
        pass
    
    bg_frame_index = 0
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if settings_btn.handle_event(event):
                settings_screen()
                continue
            
            res_user = user_box.handle_event(event)
            res_pass = pass_box.handle_event(event)
            
            if res_user == "tab":
                user_box.active = False
                pass_box.active = True
            elif res_pass == "tab":
                pass_box.active = False
                user_box.active = True
            elif res_user == "enter" or res_pass == "enter":
                username = user_box.text.strip()
                password = pass_box.text
                ok, txt = validate_user(username, password)
                if ok:
                    return username
                else:
                    info_msg = txt
                    info_color = ERROR_COLOR
            
            if login_btn.handle_event(event):
                username = user_box.text.strip()
                password = pass_box.text
                ok, txt = validate_user(username, password)
                if ok:
                    return username
                else:
                    info_msg = txt
                    info_color = ERROR_COLOR
            
            if reg_btn.handle_event(event):
                username = user_box.text.strip()
                password = pass_box.text
                if not username or not password:
                    info_msg = "Enter username and password to register."
                    info_color = ERROR_COLOR
                else:
                    ok, txt = create_user(username, password)
                    info_msg = txt
                    info_color = SUCCESS_COLOR if ok else ERROR_COLOR
        
        user_box.update(dt)
        pass_box.update(dt)
        
        screen.blit(bg_frames[bg_frame_index], (0, 0))
        if pygame.time.get_ticks() % 10 == 0:
            bg_frame_index = (bg_frame_index + 1) % len(bg_frames)
        
        user_box.draw(screen)
        pass_box.draw(screen)
        draw_text(screen, "Username:", (WIN_W//2 - 270, 283), color=WHITE, font=custom_font_login)
        draw_text(screen, "Password:", (WIN_W//2 - 270, 343), color=WHITE, font=custom_font_login)
        login_btn.draw(screen)
        reg_btn.draw(screen)
        settings_btn.draw(screen)
        
        if info_msg:
            draw_text(screen, info_msg, (WIN_W//2, 500), color=info_color, font=custom_font_login, center=True)

        draw_cursor(screen)
        pygame.display.flip()

# ------------------- Story Intro Screen -------------------
def story_intro_screen():
    pygame.mixer.music.load(os.path.join(BASE_DIR, "resources", "sounds", "STORY.MP3"))
    apply_volume_settings()
    pygame.mixer.music.play(-1)

    gif = Image.open(os.path.join(BASE_DIR, "resources", "images", "STORY SCENE.gif"))
    frames = []
    durations = []
    
    for frame in ImageSequence.Iterator(gif):
        frame_copy = frame.convert("RGBA").copy()
        frame_copy = frame_copy.resize((WIN_W, WIN_H))
        frames.append(pygame.image.frombytes(frame_copy.tobytes(), frame_copy.size, "RGBA").convert_alpha())
        durations.append(frame.info.get('duration', 100))
    
    start_time = pygame.time.get_ticks()
    frame_index = 0
    frame_timer = start_time
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        now = pygame.time.get_ticks()
        if now - frame_timer >= durations[frame_index]:
            frame_index = (frame_index + 1) % len(frames)
            frame_timer = now
        
        screen.blit(frames[frame_index], (0, 0))
        
        if now - start_time >= 18000:
            running = False
        
        draw_cursor(screen)
        pygame.display.flip()

# ------------------- Tutorial Screen -------------------
def tutorial_screen():
    # --- Load tutorial GIF (500x300) ---
    tutorial_gif_path = Image.open(os.path.join(BASE_DIR, "resources", "images", "Tutorial.gif"))
    tutorial_frames = []
    durations = []  # store frame durations for smoother playback
    
    for frame in ImageSequence.Iterator(tutorial_gif_path):
        frame_copy = frame.convert("RGBA").copy()
        frame_copy = frame_copy.resize((500, 300))  # resize to 500x300
        tutorial_frames.append(pygame.image.frombytes(frame_copy.tobytes(), frame_copy.size, "RGBA").convert_alpha())
        durations.append(frame.info.get('duration', 100))  # default 100ms if not set

    back_btn = Button((50, 50, 150, 40), "BACK", font=custom_font_login, color=ERROR_COLOR, text_color=WHITE)
    frame_index = 0
    last_frame_time = pygame.time.get_ticks()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if back_btn.handle_event(event):
                return
            
        # --- Frame update ---
        now = pygame.time.get_ticks()
        if now - last_frame_time >= durations[frame_index]:
            frame_index = (frame_index + 1) % len(tutorial_frames)
            last_frame_time = now
        
        #instead of solid color "screen.fill(BG_COLOR)"
        screen.blit(Tutorial_bg, (0, 0))  # draw image at top-left
        draw_text(screen, "TUTORIAL", (WIN_W//2, 80), color=(255, 255, 0), font=custom_font_login, center=True)
        
        # Left column
        draw_text(screen, "CONTROLS:", (WIN_W//4, 200), color=(255, 255, 0), font=custom_font_login, center=True)
        draw_text(screen, "WASD - Move", (WIN_W//4, 250), color=(255, 255, 255), font=FONT, center=True)
        draw_text(screen, "Mouse Left Click - Attack", (WIN_W//4, 280), color=(255, 255, 255), font=FONT, center=True)
        draw_text(screen, "E - Interact", (WIN_W//4, 310), color=(255, 255, 255), font=FONT, center=True)
        draw_text(screen, "ESC - Menu", (WIN_W//4, 340), color=(255, 255, 255), font=FONT, center=True)
        
        # Right column
        draw_text(screen, "OBJECTIVE", (3*WIN_W//4, 200), color=(255, 255, 0), font=custom_font_login, center=True)
        draw_text(screen, "Collect materials", (3*WIN_W//4, 250), color=(255, 255, 255), font=FONT, center=True)
        draw_text(screen, "Complete quizzes", (3*WIN_W//4, 280), color=(255, 255, 255), font=FONT, center=True)
        draw_text(screen, "Defeat the boss", (3*WIN_W//4, 310), color=(255, 255, 255), font=FONT, center=True)
        draw_text(screen, "Build your ship!", (3*WIN_W//4, 340), color=(255, 255, 255), font=FONT, center=True)
        
        # Center
        gif_x = WIN_W // 2 - 250  # center horizontally
        gif_y = 400               # vertical position
        screen.blit(tutorial_frames[frame_index], (gif_x, gif_y))
        
        
        back_btn.draw(screen)
        draw_cursor(screen)
        pygame.display.flip()

# ------------------- Leaderboard Screen -------------------
def leaderboard_screen(current_username=None):
    back_btn = Button((50, 50, 150, 40), "BACK", font=custom_font_login, color=ERROR_COLOR, text_color=WHITE)
    leaderboard = get_leaderboard()
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if back_btn.handle_event(event):
                return
        
        screen.blit(leaderboard_bg, (0, 0))  # draw image
        draw_text(screen, "LEADERBOARD - TOP 10", (WIN_W//2, 50), color=(255, 210, 0), font=custom_font_login, center=True)
        
        # Headers
        draw_text(screen, "RANK", (120, 100), color=WHITE, font=custom_font_login)
        draw_text(screen, "PLAYER", (300, 100), color=WHITE, font=custom_font_login)
        draw_text(screen, "HIGH SCORE", (530, 100), color=WHITE, font=custom_font_login)
        draw_text(screen, "ITEMS", (830, 100), color=WHITE, font=custom_font_login)
        draw_text(screen, "WINS", (1030, 100), color=WHITE, font=custom_font_login)
        
        # Draw line
        pygame.draw.line(screen, WHITE, (100, 145), (WIN_W - 100, 145), 2)
        
        # Display top 10
        for i, player in enumerate(leaderboard):
            y_pos = 160 + i * 45
            rank_color = WHITE
            
            # Highlight current player
            if current_username and player['username'] == current_username:
                pygame.draw.rect(screen, (80, 80, 120), (90, y_pos - 5, WIN_W - 180, 40))
                rank_color = (255, 255, 0)
            
            # Medal colors for top 3
            if i == 0:
                rank_color = (255, 215, 0)  # Gold
            elif i == 1:
                rank_color = (192, 192, 192)  # Silver
            elif i == 2:
                rank_color = (205, 127, 50)  # Bronze
            
            draw_text(screen, f"#{i + 1}", (150, y_pos), color=rank_color, font=FONT)
            draw_text(screen, player['username'][:15], (350, y_pos), color=WHITE, font=FONT)
            draw_text(screen, str(player['high_score']), (650, y_pos), color=SUCCESS_COLOR, font=FONT)
            draw_text(screen, str(player['total_items']), (880, y_pos), color=INFO_COLOR, font=FONT)
            draw_text(screen, str(player['wins']), (1075, y_pos), color=WHITE, font=FONT)

        back_btn.draw(screen)
        draw_cursor(screen)
        pygame.display.flip()

# ------------------- Main Menu -------------------
def main_menu_screen(username):
    logout_btn = Button((WIN_W - 200, 30, 200, 50), "LOG OUT", text_color=WHITE,font=custom_font_login)
    start_btn = Button((WIN_W//2 - 175, 220, 360, 54), "START GAME", text_color=WHITE, font=custom_font_login)
    tutorial_btn = Button((WIN_W//2 - 175, 290, 360, 54), "TUTORIAL", text_color=WHITE, font=custom_font_login)
    leaderboard_btn = Button((WIN_W//2 - 175, 360, 360, 54), "LEADERBOARD", text_color=WHITE, font=custom_font_login)
    settings_btn = Button((30, 30, 240, 50), "SETTINGS",text_color=WHITE, font=custom_font_login)
    
    user_state = users_data['users'].get(username)
    can_continue = user_state and user_state.get('character') is not None
    continue_btn = Button((WIN_W//2 - 130, 430, 260, 54), "CONTINUE", text_color=WHITE, font=custom_font_login) if can_continue else None
    
    exit_btn = Button((WIN_W//2 - 130, 500 if can_continue else 430, 260, 54), "EXIT", text_color=WHITE, font=custom_font_login)
    info = f"LOGGED IN AS {username}"
    
    pygame.mixer.music.load(os.path.join(BASE_DIR, "resources", "sounds", "intro.mp3"))
    apply_volume_settings()
    pygame.mixer.music.play(-1)
    
    gif_main_menu_background = Image.open(os.path.join(BASE_DIR, "resources", "images", "MAINMENUBACK.gif"))
    bg_frames = []
    
    try:
        while True:
            frame = gif_main_menu_background.copy().convert("RGBA")
            frame = frame.resize((WIN_W, WIN_H))
            pygame_frame = pygame.image.frombytes(frame.tobytes(), frame.size, "RGBA").convert_alpha()
            bg_frames.append(pygame_frame)
            gif_main_menu_background.seek(gif_main_menu_background.tell() + 1)
    except EOFError:
        pass
    
    bg_frame_index = 0
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if logout_btn.handle_event(event):
                pygame.mixer.music.stop()
                return "logout"
            
            if settings_btn.handle_event(event):
                settings_screen()
                continue
            
            if exit_btn.handle_event(event):
                pygame.quit()
                sys.exit()
            
            if tutorial_btn.handle_event(event):
                tutorial_screen()
                continue
            
            if leaderboard_btn.handle_event(event):
                leaderboard_screen(username)
                continue
            
            if start_btn.handle_event(event):
                pygame.mixer.music.stop()
                story_intro_screen()
                choice = character_select_screen(username, is_new_game=True)
                if choice:
                    return "start_game"
            
            if continue_btn and continue_btn.handle_event(event):
                pygame.mixer.music.stop()
                return "start_game"
        
        screen.blit(bg_frames[bg_frame_index], (0, 0))
        if pygame.time.get_ticks() % 10 == 0:
            bg_frame_index = (bg_frame_index + 1) % len(bg_frames)
        
        draw_text(screen, "PROVENTURE - MAIN MENU", (WIN_W//2, 100), color=(255, 210, 0), font=custom_font_login, center=True)
        draw_text(screen, info, (WIN_W//2, 140), color=WHITE, font=FONT, center=True)
        
        start_btn.draw(screen)
        tutorial_btn.draw(screen)
        leaderboard_btn.draw(screen)
        if continue_btn:
            continue_btn.draw(screen)
        logout_btn.draw(screen)
        settings_btn.draw(screen)
        exit_btn.draw(screen)
        draw_cursor(screen)

        draw_cursor(screen)
        pygame.display.flip()

# ------------------- Character Select Screen -------------------
def character_select_screen(username, is_new_game=False):
    user_data = users_data['users'][username]
    if user_data.get('character') is not None and not is_new_game:
        return True
    
    
    
    tank_btn = Button((WIN_W//2 - 500, 250, 200, 60), "TANK", color=(100, 100, 100), hover_color=(140, 140, 140), text_color=WHITE, font=custom_font_login)
    assassin_btn = Button((WIN_W//2 - 120, 250, 250, 60), "ASSASSIN", color=(100, 100, 100), hover_color=(140, 140, 140), text_color=WHITE, font=custom_font_login)
    knight_btn = Button((WIN_W//2 + 350, 250, 200, 60), "KNIGHT", color=(100, 100, 100), hover_color=(140, 140, 140), text_color=WHITE, font=custom_font_login)
    back_btn = Button((WIN_W - 200, 40, 150, 40), "BACK", font=custom_font_login, color=ERROR_COLOR, hover_color=(255, 100, 100), text_color=WHITE)
    
    info_msg = "Choose your character:"
    running = True
    selected_character = None

    character_select_screen = Image.open(os.path.join(BASE_DIR, "resources", "images", "Character_select.gif"))
    bg_frames = []

    try:
        while True:
            frame = character_select_screen.copy().convert("RGBA")
            frame = frame.resize((WIN_W, WIN_H))
            pygame_frame = pygame.image.frombytes(frame.tobytes(), frame.size, "RGBA").convert_alpha()
            bg_frames.append(pygame_frame)
            character_select_screen.seek(character_select_screen.tell() + 1)
    except EOFError:
        pass
    
    bg_frame_index = 0
    
    while running:
        pygame.mixer.music.stop()
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if tank_btn.handle_event(event):
                selected_character = "Tank"
            if assassin_btn.handle_event(event):
                selected_character = "Assassin"
            if knight_btn.handle_event(event):
                selected_character = "Knight"
            if back_btn.handle_event(event):
                return None
            
            if selected_character:
                if is_new_game:
                    users_data['users'][username].update({
                        "current_maze": 1,
                        "maze_seeds": {},
                        "x": None,
                        "y": None,
                        "health": CHARACTERS[selected_character]['health'],
                        "lives": MAX_LIVES,
                        "points": 100,
                        "materials": {"wood": 0, "rope": 0, "metal": 0, "sail": 0},
                        "completed_quizzes": [],
                        "achievements": [],
                        "kills": 0,
                        "enemies_state": [],
                        "in_boss_fight": False
                    })
                users_data['users'][username]['character'] = selected_character
                save_users()
                return selected_character
        
        screen.blit(bg_frames[bg_frame_index], (0, 0))
        if pygame.time.get_ticks() % 3 == 0: #gif speed high num slow low num fast
            bg_frame_index = (bg_frame_index + 1) % len(bg_frames)

        draw_text(screen, "CHARACTER SELECTION", (WIN_W//2, 80), color=(255, 210, 0), font=custom_font_login, center=True)
        draw_text(screen, info_msg, (WIN_W//2, 120), color=INFO_COLOR, center=True)
        
        # Tank stats
        tank_btn.draw(screen)
        draw_text(screen, f"Speed: {CHARACTERS['Tank']['speed']}", (tank_btn.rect.x + 10, tank_btn.rect.y + 70), color=WHITE, font=SMALL)
        draw_text(screen, f"Health: {CHARACTERS['Tank']['health']}", (tank_btn.rect.x + 10, tank_btn.rect.y + 90), color=SUCCESS_COLOR, font=SMALL)
        draw_text(screen, f"Damage: {CHARACTERS['Tank']['damage']}", (tank_btn.rect.x + 10, tank_btn.rect.y + 110), color=ERROR_COLOR, font=SMALL)
        draw_text(screen, f"Regen: {CHARACTERS['Tank']['regen_rate']} HP/5s", (tank_btn.rect.x + 10, tank_btn.rect.y + 130), color=INFO_COLOR, font=SMALL)
        
        # Assassin stats
        assassin_btn.draw(screen)
        draw_text(screen, f"Speed: {CHARACTERS['Assassin']['speed']}", (assassin_btn.rect.x + 10, assassin_btn.rect.y + 70), color=WHITE, font=SMALL)
        draw_text(screen, f"Health: {CHARACTERS['Assassin']['health']}", (assassin_btn.rect.x + 10, assassin_btn.rect.y + 90), color=SUCCESS_COLOR, font=SMALL)
        draw_text(screen, f"Damage: {CHARACTERS['Assassin']['damage']}", (assassin_btn.rect.x + 10, assassin_btn.rect.y + 110), color=ERROR_COLOR, font=SMALL)
        draw_text(screen, "25% One-Hit Kill", (assassin_btn.rect.x + 10, assassin_btn.rect.y + 130), color=(255, 200, 0), font=SMALL)
        
        # Knight stats
        knight_btn.draw(screen)
        draw_text(screen, f"Speed: {CHARACTERS['Knight']['speed']}", (knight_btn.rect.x + 10, knight_btn.rect.y + 70), color=WHITE, font=SMALL)
        draw_text(screen, f"Health: {CHARACTERS['Knight']['health']}", (knight_btn.rect.x + 10, knight_btn.rect.y + 90), color=SUCCESS_COLOR, font=SMALL)
        draw_text(screen, f"Damage: {CHARACTERS['Knight']['damage']}", (knight_btn.rect.x + 10, knight_btn.rect.y + 110), color=ERROR_COLOR, font=SMALL)
        draw_text(screen, "Quiz: Remove 2 choices", (knight_btn.rect.x + 10, knight_btn.rect.y + 130), color=(180, 200, 220), font=SMALL)
        
        back_btn.draw(screen)
        draw_cursor(screen)
        pygame.display.flip()

# ------------------- EXPANDED QUESTION POOL (30 questions) -------------------
QUESTIONS = [
    # EASY (15 questions)
    {"id": "e1", "q": "What is 5 + 5?", "choices": ["10", "15", "20", "5"], "answer": 0, "hint": "Basic addition", "difficulty": "easy"},
    {"id": "e2", "q": "What color is the sky on a clear day?", "choices": ["Blue", "Green", "Red", "Yellow"], "answer": 0, "hint": "Look up", "difficulty": "easy"},
    {"id": "e3", "q": "How many days in a week?", "choices": ["7", "5", "6", "8"], "answer": 0, "hint": "Count them", "difficulty": "easy"},
    {"id": "e4", "q": "What is 10 - 3?", "choices": ["7", "6", "8", "5"], "answer": 0, "hint": "Simple subtraction", "difficulty": "easy"},
    {"id": "e5", "q": "What animal says 'meow'?", "choices": ["Cat", "Dog", "Cow", "Bird"], "answer": 0, "hint": "Feline friend", "difficulty": "easy"},
    {"id": "e6", "q": "What is 2 x 4?", "choices": ["8", "6", "10", "12"], "answer": 0, "hint": "Basic multiplication", "difficulty": "easy"},
    {"id": "e7", "q": "How many legs does a spider have?", "choices": ["8", "6", "4", "10"], "answer": 0, "hint": "Arachnid", "difficulty": "easy"},
    {"id": "e8", "q": "What is the capital of France?", "choices": ["Paris", "London", "Berlin", "Madrid"], "answer": 0, "hint": "City of lights", "difficulty": "easy"},
    {"id": "e9", "q": "What is 100 / 10?", "choices": ["10", "5", "20", "1"], "answer": 0, "hint": "Simple division", "difficulty": "easy"},
    {"id": "e10", "q": "How many months in a year?", "choices": ["12", "10", "11", "13"], "answer": 0, "hint": "Calendar year", "difficulty": "easy"},
    {"id": "e11", "q": "What is frozen water called?", "choices": ["Ice", "Steam", "Rain", "Snow"], "answer": 0, "hint": "Cold solid", "difficulty": "easy"},
    {"id": "e12", "q": "What planet do we live on?", "choices": ["Earth", "Mars", "Venus", "Jupiter"], "answer": 0, "hint": "Our home", "difficulty": "easy"},
    {"id": "e13", "q": "How many sides does a triangle have?", "choices": ["3", "4", "5", "6"], "answer": 0, "hint": "Tri means three", "difficulty": "easy"},
    {"id": "e14", "q": "What is the opposite of hot?", "choices": ["Cold", "Warm", "Cool", "Freezing"], "answer": 0, "hint": "Temperature opposite", "difficulty": "easy"},
    {"id": "e15", "q": "What do bees make?", "choices": ["Honey", "Milk", "Butter", "Cheese"], "answer": 0, "hint": "Sweet and sticky", "difficulty": "easy"},
    
    # AVERAGE (10 questions)
    {"id": "a1", "q": "What is 15 x 8?", "choices": ["120", "110", "130", "100"], "answer": 0, "hint": "Multiply carefully", "difficulty": "average"},
    {"id": "a2", "q": "Who wrote 'Romeo and Juliet'?", "choices": ["Shakespeare", "Dickens", "Hemingway", "Tolkien"], "answer": 0, "hint": "English playwright", "difficulty": "average"},
    {"id": "a3", "q": "What is the square root of 144?", "choices": ["12", "14", "10", "16"], "answer": 0, "hint": "12 squared", "difficulty": "average"},
    {"id": "a4", "q": "What element has the symbol 'O'?", "choices": ["Oxygen", "Gold", "Silver", "Iron"], "answer": 0, "hint": "We breathe it", "difficulty": "average"},
    {"id": "a5", "q": "In what year did World War 2 end?", "choices": ["1945", "1944", "1946", "1943"], "answer": 0, "hint": "Mid 1940s", "difficulty": "average"},
    {"id": "a6", "q": "What is the speed of light (approx)?", "choices": ["300,000 km/s", "150,000 km/s", "500,000 km/s", "100,000 km/s"], "answer": 0, "hint": "Very fast", "difficulty": "average"},
    {"id": "a7", "q": "What is the largest ocean?", "choices": ["Pacific", "Atlantic", "Indian", "Arctic"], "answer": 0, "hint": "Biggest body of water", "difficulty": "average"},
    {"id": "a8", "q": "What gas do plants absorb?", "choices": ["CO2", "O2", "N2", "H2"], "answer": 0, "hint": "Photosynthesis", "difficulty": "average"},
    {"id": "a9", "q": "Who painted the Mona Lisa?", "choices": ["Da Vinci", "Picasso", "Van Gogh", "Monet"], "answer": 0, "hint": "Renaissance artist", "difficulty": "average"},
    {"id": "a10", "q": "What is the derivative of x^2?", "choices": ["2x", "x", "x^2", "2"], "answer": 0, "hint": "Calculus power rule", "difficulty": "average"},
    
    # DIFFICULT (5 questions)
    {"id": "d1", "q": "What is the Planck constant (approx)?", "choices": ["6.63e-34 J·s", "3.14e-34 J·s", "9.81e-34 J·s", "1.60e-34 J·s"], "answer": 0, "hint": "Quantum physics", "difficulty": "difficult"},
    {"id": "d2", "q": "Who proved Fermat's Last Theorem?", "choices": ["Andrew Wiles", "Euler", "Gauss", "Riemann"], "answer": 0, "hint": "1990s mathematician", "difficulty": "difficult"},
    {"id": "d3", "q": "What is the Schrödinger equation for?", "choices": ["Quantum mechanics", "Relativity", "Thermodynamics", "Electromagnetism"], "answer": 0, "hint": "Wave function", "difficulty": "difficult"},
    {"id": "d4", "q": "What is the Goldbach conjecture about?", "choices": ["Even numbers", "Odd numbers", "Prime gaps", "Perfect numbers"], "answer": 0, "hint": "Unsolved math problem", "difficulty": "difficult"},
    {"id": "d5", "q": "What is Gödel's incompleteness theorem?", "choices": ["Math limits", "Physics theory", "Logic paradox", "Set theory"], "answer": 0, "hint": "Provability limits", "difficulty": "difficult"}
]

# ------------------- Part 2: Game Classes -------------------
def generate_maze(seed=None):
    if seed:
        rng = random.Random(seed)
    else:
        rng = random.Random()
    
    rows, cols = ROWS, COLS
    maze = [[1 for _ in range(cols)] for _ in range(rows)]
    
    def is_valid(r, c):
        return 0 <= r < rows and 0 <= c < cols
    
    def carve(cx, cy):
        maze[cx][cy] = 0
        dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        rng.shuffle(dirs)
        
        for dr, dc in dirs:
            nx, ny = cx + dr * 2, cy + dc * 2
            wall_x, wall_y = cx + dr, cy + dc
            
            if is_valid(nx, ny) and maze[nx][ny] == 1:
                maze[wall_x][wall_y] = 0
                maze[nx][ny] = 0
                carve(nx, ny)
    
    start_r, start_c = rng.randrange(1, rows - 1, 2), rng.randrange(1, cols - 1, 2)
    carve(start_r, start_c)
    
    path_tiles = [(r, c) for r in range(1, rows - 1) for c in range(1, cols - 1) if maze[r][c] == 0]
    rng.shuffle(path_tiles)
    
    # Place 3 quizzes per maze
    for i in range(3):
        if i < len(path_tiles):
            r, c = path_tiles.pop()
            maze[r][c] = 2
    
    # Place 2 doors
    for i in range(2):
        if i < len(path_tiles):
            r, c = path_tiles.pop()
            maze[r][c] = 3
    
    # REMOVED: Destructible blocks generation
    
    return maze

def tile_to_screen(col, row):
    x = col * TILE + (WIN_W - COLS * TILE) // 2  # Center the maze horizontally
    y = row * TILE + 100
    return x, y

def screen_to_tile(x, y):
    maze_start_x = (WIN_W - COLS * TILE) // 2
    col = (x - maze_start_x) // TILE
    row = (y - 100) // TILE
    return int(col), int(row)

class Block:
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.health = DESTRUCTIBLE_HP

class Enemy:
    def __init__(self, x, y, level=1, is_boss=False):
        self.x = x
        self.y = y
        self.is_boss = is_boss
        
        if is_boss:
            self.hp = BOSS_HP
            self.max_hp = BOSS_HP
            self.dmg = BOSS_DMG
            self.speed = BOSS_SPEED
            self.last_attack_time = 0
        else:
            self.base_hp = ENEMY_BASE_HP
            self.base_dmg = ENEMY_BASE_DMG
            self.level = level
            self.hp = self.base_hp + (self.level - 1) * ENEMY_SCALE_PER_SEC_HP * 10
            self.max_hp = self.hp
            self.dmg = self.base_dmg + (self.level - 1) * ENEMY_SCALE_PER_SEC_DMG * 10
            self.speed = ENEMY_BASE_SPEED + min(ENEMY_MAX_SPEED_BONUS, (level - 1) * 10)
            self.last_attack_time = 0

class Player:
    def __init__(self, character='Tank'):
        self.x = 0
        self.y = 0
        self.character = character
        char_data = CHARACTERS[character]
        self.health = char_data['health']
        self.max_health = char_data['health']
        self.speed = char_data['speed']
        self.damage = char_data['damage']
        self.points = 200
        self.lives = MAX_LIVES
        self.materials = {"wood": 0, "rope": 0, "metal": 0, "sail": 0}
        self.last_regen_time = 0
        self.kills = 0
        self.respawn_timer = 0
        self.is_respawning = False
        self.death_position = (0, 0)
        self.last_attack_time = 0  # NEW: Track last attack time for cooldown
        self.is_moving = False
        self.is_attacking = False

class GameMaze:
    def __init__(self, seed=None):
        self.grid = generate_maze(seed)
        self.quiz_tiles = set()
        self.door_tiles = set()
        # REMOVED: destructibles initialization
        rows, cols = ROWS, COLS
        for r in range(rows):
            for c in range(cols):
                v = self.grid[r][c]
                if v == 2:
                    self.quiz_tiles.add((c, r))
                elif v == 3:
                    self.door_tiles.add((c, r))
                # REMOVED: destructible blocks initialization
    
    def get_empty_path_tiles(self):
        empties = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] == 0 and \
                   (c, r) not in self.quiz_tiles and \
                   (c, r) not in self.door_tiles:
                    empties.append((c, r))
        return empties
    
    def is_blocked(self, c, r):
        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            return True
        if self.grid[r][c] == 1:
            return True
        # REMOVED: destructible blocks check
        return False

class HUD:
    def __init__(self):
        self.messages = []
    
    def add(self, text, x=10, y=None, duration=2.5, color=HUD_MSG_COLOR):
        if y is None:
            y = WIN_H - 80 - len(self.messages) * 20
        self.messages.append([text, time.time() + duration, x, y, color])
    
    def update(self):
        now = time.time()
        self.messages = [m for m in self.messages if m[1] > now]
    
    def draw(self, surf):
        for txt, exp, x, y, color in self.messages:
            draw_text(surf, txt, (x, y), color=color)

hud = HUD()

# ------------------- Victory Video Screen -------------------
def victory_video_screen():
    # Play victory music
    pygame.mixer.music.load(os.path.join(BASE_DIR, "resources", "sounds", "Credit.MP3"))
    apply_volume_settings()
    pygame.mixer.music.play(-1)

    # Load GIF frames
    Video_credit = Image.open(os.path.join(BASE_DIR, "resources", "images", "CREDITS.gif"))
    frames = []
    durations = []

    for frame in ImageSequence.Iterator(Video_credit):
        frame_copy = frame.convert("RGBA").resize((WIN_W, WIN_H))
        frames.append(pygame.image.frombytes(frame_copy.tobytes(), frame_copy.size, "RGBA").convert_alpha())
        durations.append(frame.info.get("duration", 100))  # Default 100ms per frame
    frame_index = 0

    total_duration = sum(durations)  # total time of GIF
    start_time = pygame.time.get_ticks()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        now = pygame.time.get_ticks()
        elapsed = now - start_time

        # Change frames based on time
        if elapsed >= durations[frame_index]:
            frame_index = (frame_index + 1) % len(frames)
            frame_timer = now

        # Draw current frame
        screen.blit(frames[frame_index], (0, 0))
        pygame.display.flip()

        # When total time passes, stop and go to credits
        if elapsed >= total_duration:
            running = False

        clock.tick(15)
    """
    start_time = pygame.time.get_ticks()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.fill((0, 20, 40))
        draw_text(screen, "VICTORY!", (WIN_W//2, 250), color=(255, 215, 0), font=HUGE, center=True)
        draw_text(screen, "[Victory Video Here]", (WIN_W//2, 350), color=WHITE, font=BIG, center=True)
        draw_text(screen, "You escaped the island!", (WIN_W//2, 420), color=SUCCESS_COLOR, font=BIG, center=True)
        
        now = pygame.time.get_ticks()
        if now - start_time >= 5000:
            running = False
        
        draw_cursor(screen)
        pygame.display.flip()
"""
# ------------------- Credits Screen -------------------
def credits_screen(username):
    pygame.mixer.music.stop()

    # --- PLAY NEW CREDITS MUSIC ---
    # Load your credits music file here
    credits_music = os.path.join(BASE_DIR, "resources", "sounds", "credits_music.mp3")
    pygame.mixer.music.load(credits_music)# play credits music
    apply_volume_settings()          
    pygame.mixer.music.play(-1)# -1 = loop forever
    """
    credits_text = [
        ("PROVENTURE", 2.0, HUGE, (255, 215, 0)),
        ("A story-driven maze adventure", 2.0, BIG, WHITE),
        ("", 1.0, FONT, WHITE),
        ("SURVIVE THE UNKNOWN", 2.0, BIG, (255, 100, 100)),
        ("", 1.5, FONT, WHITE),
        ("PRODUCTION:", 2.0, BIG, (100, 200, 255)),
        ("", 0.5, FONT, WHITE),
        ("Publisher", 1.5, FONT, WHITE),
        ("Southwestern University PHINMA", 2.0, FONT, INFO_COLOR),
        ("", 0.5, FONT, WHITE),
        ("Executive Producer", 1.5, FONT, WHITE),
        ("Dr. Desiree Cendana Perreras", 2.0, FONT, INFO_COLOR),
        ("", 0.5, FONT, WHITE),
        ("Producer", 1.5, FONT, WHITE),
        ("Engr. Jeremy Neal Caballero", 2.0, FONT, INFO_COLOR),
        ("", 0.5, FONT, WHITE),
        ("Associate Producer", 1.5, FONT, WHITE),
        ("Dr. Ira Pongasi", 2.0, FONT, INFO_COLOR),
        ("", 1.5, FONT, WHITE),
        ("CREATORS:", 2.0, BIG, (100, 255, 100)),
        ("", 0.5, FONT, WHITE),
        ("Project Manager / Lead Programmer", 1.5, FONT, WHITE),
        ("Divinangelo C. Abarquez", 2.0, FONT, SUCCESS_COLOR),
        ("", 0.5, FONT, WHITE),
        ("Assistant Programmer / Graphics Designer", 1.5, FONT, WHITE),
        ("John Michael L. Cabilao", 2.0, FONT, SUCCESS_COLOR),
        ("", 0.5, FONT, WHITE),
        ("Graphics Designer", 1.5, FONT, WHITE),
        ("John Villegas Cabansag", 2.0, FONT, SUCCESS_COLOR),
        ("", 2.0, FONT, WHITE),
        ("Thank you for playing!", 3.0, BIG, (255, 215, 0)),
    ]
    """ 
    continue_btn = Button((WIN_W//2 - 10, 500, 630, 200), "CONTINUE TO LEADERBOARD", font=custom_font_login, text_color=WHITE)
    show_button = True 
    current_credit = 0
    credit_timer = 0
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        credit_timer += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if show_button and continue_btn.handle_event(event):
                update_leaderboard(username)
                leaderboard_screen(username)
                return
        """"
        if current_credit < len(credits_text):
            text, duration, font, color = credits_text[current_credit]
            if text:
                text_surface = font.render(text, True, color)
                text_rect = text_surface.get_rect(center=(WIN_W // 2, WIN_H // 2))
                screen.blit(text_surface, text_rect)
            
            if credit_timer >= duration:
                credit_timer = 0
                current_credit += 1
        else:
            show_button = True
        """
        screen.fill((0, 0, 0))  # Pure black background
        
        if show_button:
            continue_btn.draw(screen)

        # Custom cursor
        draw_cursor(screen)

        pygame.display.flip()

# ------------------- Educational Boss Fight Screen -------------------
# ------------------- Educational Boss Fight Screen -------------------
def boss_fight_screen(player, username):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(os.path.join(BASE_DIR, "resources", "sounds", "boss_music.mp3"))
    pygame.mixer.music.play(-1)

    # Initialize boss
    boss_hp = BOSS_HP
    boss_max_hp = BOSS_HP
    player_start_health = player.health
    boss_idle_index = 0
    boss_idle_timer = 0
    
    # State variables
    current_question = None
    question_start_time = 0
    time_limit = 15.0
    stage = "intro"  # intro, question, result, win, lose
    result_timer = 0
    result_duration = 3.0
    intro_timer = 0
    intro_duration = 3.5
    
    # Question pool - shuffle all questions
    available_questions = QUESTIONS.copy()
    random.shuffle(available_questions)
    question_index = 0

    # Initialize answer_rects at the beginning of the function
    answer_rects = []
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if stage == "question" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if player clicked on an answer
                mouse_pos = pygame.mouse.get_pos()
                for i, rect in enumerate(answer_rects):
                    if rect.collidepoint(mouse_pos):
                        # Answer selected
                        if i == current_question["answer"]:
                            # Correct answer - damage boss
                            boss_hp -= 50  # Fixed damage per correct answer
                            stage = "result"
                            result_timer = 0
                            result_text = "CORRECT! Boss takes 50 damage!"
                            result_color = SUCCESS_COLOR
                        else:
                            # Wrong answer - damage player
                            player.health -= BOSS_DMG
                            stage = "result"
                            result_timer = 0
                            result_text = f"WRONG! You take {BOSS_DMG} damage!"
                            result_color = ERROR_COLOR
                        break
        
        # Update timers
        if stage == "intro":
            intro_timer += dt
            if intro_timer >= intro_duration:
                stage = "question"
                # Load first question
                if question_index < len(available_questions):
                    current_question = available_questions[question_index]
                    # FIX: Shuffle the answer choices while preserving the correct answer
                    current_question = shuffle_question_choices(current_question)
                    question_start_time = time.time()
                else:
                    # No more questions, player wins by default
                    stage = "win"
        
        elif stage == "question":
            # Check for timeout
            elapsed_time = time.time() - question_start_time
            if elapsed_time >= time_limit:
                # Timeout - damage player
                player.health -= BOSS_DMG
                stage = "result"
                result_timer = 0
                result_text = f"TIME'S UP! You take {BOSS_DMG} damage!"
                result_color = ERROR_COLOR
        
        elif stage == "result":
            result_timer += dt
            if result_timer >= result_duration:
                # Check win/lose conditions
                if boss_hp <= 0:
                    stage = "win"
                elif player.health <= 0:
                    stage = "lose"
                else:
                    # Next question
                    question_index += 1
                    if question_index < len(available_questions):
                        stage = "question"
                        current_question = available_questions[question_index]
                        # FIX: Shuffle the answer choices for the new question
                        current_question = shuffle_question_choices(current_question)
                        question_start_time = time.time()
                    else:
                        # No more questions, check who won
                        if boss_hp > 0 and player.health > 0:
                            # Player wins by surviving all questions
                            stage = "win"
        
        # Draw everything
        screen.blit(Boss_final_bg, (0, 0))  # draw image
        
        # Draw boss
        screen.blit(grim_image, (60, 200))
        
# --- Draw correct GIF (boss version) ---
        boss_idle_timer += dt
        if boss_idle_timer >= 0.10:  
            boss_idle_timer = 0

            if player.character == "Tank":
                boss_idle_index = (boss_idle_index + 1) % len(Tank_image_boss)
                frame = Tank_image_boss[boss_idle_index]

            elif player.character == "Assassin":
                boss_idle_index = (boss_idle_index + 1) % len(Assasin_image_boss)
                frame = Assasin_image_boss[boss_idle_index]

            elif player.character == "Knight":
                boss_idle_index = (boss_idle_index + 1) % len(Knight_image_boss)
                frame = Knight_image_boss[boss_idle_index]

            else:
                frame = player_image  # fallback
        else:
            if player.character == "Tank":
                frame = Tank_image_boss[boss_idle_index]
            elif player.character == "Assassin":
                frame = Assasin_image_boss[boss_idle_index]
            elif player.character == "Knight":
                frame = Knight_image_boss[boss_idle_index]
            else:
                frame = player_image  # fallback
        big_frame = pygame.transform.scale(frame, (400,400))
        screen.blit(big_frame, (WIN_W - 400, 150))
        
        # Draw boss health bar
        pygame.draw.rect(screen, (255, 0, 0), (WIN_W//2 - 200, 50, 400, 30))
        pygame.draw.rect(screen, (0, 255, 0), (WIN_W//2 - 200, 50, 400 * (boss_hp / boss_max_hp), 30))
        draw_text(screen, f"BOSS HP: {int(boss_hp)}/{boss_max_hp}", (WIN_W//2, 20), color=WHITE, font=custom_font_login, center=True)
        
        # Draw player health
        pygame.draw.rect(screen, (255, 0, 0), (50, 50, 200, 20))
        pygame.draw.rect(screen, (0, 255, 0), (50, 50, 200 * (player.health / player.max_health), 20))
        draw_text(screen, f"HP: {int(player.health)}/{player.max_health}", (50, 30), color=WHITE, font=FONT)
        
        # Draw lives
        draw_text(screen, f"Lives: {player.lives}", (50, 80), color=WHITE, font=FONT)
        
        # Draw current stage content
        if stage == "intro":
            draw_text(screen, "GET READY!", (WIN_W//2, WIN_H//2), color=(255, 215, 0), font=custom_font_login, center=True)
            draw_text(screen, "Educational Boss Battle Starting...", (WIN_W//2, WIN_H//2 + 60), color=WHITE, font=BIG, center=True)
        
        elif stage == "question" and current_question:
            # Draw timer
            elapsed_time = time.time() - question_start_time
            time_left = max(0, time_limit - elapsed_time)
            timer_width = (WIN_W - 100) * (time_left / time_limit)
            pygame.draw.rect(screen, (100, 100, 100), (50, 120, WIN_W - 100, 20))
            pygame.draw.rect(screen, (0, 200, 0) if time_left > 5 else (255, 0, 0), 
                            (50, 120, timer_width, 20))
            draw_text(screen, f"Time: {time_left:.1f}s", (WIN_W // 2, 120), color=WHITE, font=FONT, center=True)
            
            # Draw question
            draw_text(screen, current_question["q"], (WIN_W // 2, 180), color=WHITE, font=BIG, center=True)
            
            # Draw choices
            answer_rects = []  # Reset answer_rects for this question
            button_height = 50
            for i, choice in enumerate(current_question["choices"]):
                rect = pygame.Rect(WIN_W//2 - 200, 220 + i * 70, 400, button_height)
                answer_rects.append(rect)
                
                # Draw button
                color = BUTTON_COLOR
                if rect.collidepoint(pygame.mouse.get_pos()):
                    color = BUTTON_HOVER
                
                pygame.draw.rect(screen, color, rect, border_radius=5)
                pygame.draw.rect(screen, WHITE, rect, 2, border_radius=5)
                draw_text(screen, choice, (WIN_W//2, 220 + i * 70 + button_height//2), 
                         color=WHITE, font=FONT, center=True)
        
        elif stage == "result":
            # Show result
            draw_text(screen, result_text, (WIN_W//2, WIN_H//2), color=result_color, font=BIG, center=True)
            draw_text(screen, f"Next question in {result_duration - result_timer:.1f}s", 
                     (WIN_W//2, WIN_H//2 + 40), color=WHITE, font=FONT, center=True)
        
        elif stage == "win":
            draw_text(screen, "VICTORY!", (WIN_W//2, WIN_H//2 - 50), color=(255, 215, 0), font=custom_font_login, center=True)
            draw_text(screen, "You defeated the boss with knowledge!", (WIN_W//2, WIN_H//2 + 20), color=SUCCESS_COLOR, font=BIG, center=True)
            draw_text(screen, "Click to continue...", (WIN_W//2, WIN_H//2 + 70), color=WHITE, font=FONT, center=True)
            
            # Check for click to exit
            if pygame.mouse.get_pressed()[0]: 
                player.points += BOSS_POINTS_REWARD
                users_data['users'][username]['wins'] = users_data['users'][username].get('wins', 0) + 1
                save_users()
                return True
        
        elif stage == "lose":
            draw_text(screen, "DEFEAT!", (WIN_W//2, WIN_H//2 - 50), color=ERROR_COLOR, font=custom_font_login, center=True)
            draw_text(screen, "The boss overwhelmed you with questions!", (WIN_W//2, WIN_H//2 + 20), color=WHITE, font=BIG, center=True)
            draw_text(screen, "Click to continue...", (WIN_W//2, WIN_H//2 + 70), color=WHITE, font=FONT, center=True)
            
            # Check for click to exit
            if pygame.mouse.get_pressed()[0]:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(os.path.join(BASE_DIR, "resources", "sounds", "INGAME_SOUND.mp3"))
                pygame.mixer.music.play(-1)
                player.lives -= 1
                if player.lives <= 0:
                    return False
                # Reset health for respawn
                player.health = player.max_health
                return False
            
        draw_cursor(screen)
        pygame.display.flip()
    
    return False

def shuffle_question_choices(question):
    """Shuffle choices and keep correct answer index accurate"""
    # Copy choices and correct answer before shuffling
    choices = question["choices"][:]  # new list, not shared
    correct_answer_text = choices[question["answer"]]

    # Shuffle safely
    random.shuffle(choices)

    # Find the new index of the correct answer
    new_correct_index = choices.index(correct_answer_text)

    # Return a clean new question dictionary
    return {
        "q": question["q"],
        "choices": choices,
        "answer": new_correct_index,
        "difficulty": question.get("difficulty", "easy"),
        "id": question.get("id", 0)
    }
"""
# NEW FUNCTION: Shuffle question choices while preserving correct answer
def shuffle_question_choices(question):
    #Shuffle answer choices while keeping track of the correct answer
    # Create a copy to avoid modifying the original
    shuffled_question = question.copy()
    
    # Get the current correct answer and choices
    correct_index = shuffled_question["answer"]
    choices = shuffled_question["choices"]
    correct_answer = choices[correct_index]
    
    # Shuffle the choices
    random.shuffle(choices)
    
    # Find the new index of the correct answer
    new_correct_index = choices.index(correct_answer)
    shuffled_question["answer"] = new_correct_index
    
    return shuffled_question
"""
# ------------------- Door Selection Screen -------------------
def door_selection_screen(current_maze):
    options = []
    
    # FIXED: Correct maze connections based on the specified structure
    if current_maze == 1:
        options = [("SHIPYARD", "shipyard"), ("MAZE 2", 2)]
    elif current_maze == 2:
        options = [("MAZE 1", 1), ("MAZE 3", 3)]
    elif current_maze == 3:
        options = [("MAZE 2", 2), ("MAZE 4", 4)]
    elif current_maze == 4:
        options = [("MAZE 3", 3)]  # Maze 4 only connects back to Maze 3
    
    buttons = []
    for i, (name, target) in enumerate(options):
        rect = pygame.Rect(WIN_W//2 - 150, 200 + i * 70, 300, 60)
        buttons.append((Button(rect, name, font=custom_font_login, text_color=WHITE), target))
    
    back_btn = Button((WIN_W//2 - 150, 200 + len(options) * 70, 300, 60), "BACK", font=custom_font_login, color=ERROR_COLOR, text_color=WHITE)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if back_btn.handle_event(event):
                return None
            
            for btn, target in buttons:
                if btn.handle_event(event):
                    return target
        
        screen.blit(Door_selec_bg, (0, 0))  # draw image
        draw_text(screen, "SELECT DESTINATION", (WIN_W//2, 100), color=(255, 210, 0), font=custom_font_login, center=True)
        draw_text(screen, f"CURRENT MAZE: {current_maze}", (WIN_W//2, 150), color=WHITE, font=custom_font_login, center=True)
        
        for btn, target in buttons:
            btn.draw(screen)
        
        back_btn.draw(screen)
        draw_cursor(screen)
        pygame.display.flip()
    
    return None

# ------------------- Quiz Screen -------------------
# ------------------- Quiz Screen -------------------
def quiz_screen(question_data, player):
    start_time = time.time()
    time_left = QUIZ_TIME_LIMIT
    
    # FIX: Shuffle the question choices while preserving correct answer
    question_data = shuffle_question_choices(question_data)
    
    # Knight ability: remove 2 wrong choices (after shuffling)
    if player.character == "Knight" and len(question_data["choices"]) > 2:
        correct_index = question_data["answer"]
        wrong_indices = [i for i in range(len(question_data["choices"])) if i != correct_index]
        if len(wrong_indices) >= 2:
            # Keep only the correct answer and one wrong answer
            indices_to_remove = random.sample(wrong_indices, 2)
            # Remove the wrong choices (in reverse order to avoid index issues)
            indices_to_remove.sort(reverse=True)
            for idx in indices_to_remove:
                question_data["choices"].pop(idx)
                # Adjust the correct answer index if necessary
                if idx < correct_index:
                    correct_index -= 1
            question_data["answer"] = correct_index
    
    choice_buttons = []
    button_height = 50
    for i, choice in enumerate(question_data["choices"]):
        rect = pygame.Rect(WIN_W//2 - 200, 200 + i * 70, 400, button_height)
        choice_buttons.append(Button(rect, choice, font=custom_font_login, text_color=WHITE))
    
    back_btn = Button((50, 50, 150, 40), "BACK", font=custom_font_login, color=ERROR_COLOR, text_color=WHITE)
    
    selected_answer = None
    result_msg = ""
    result_color = INFO_COLOR
    
    running = True
    while running and time_left > 0:
        dt = clock.tick(60) / 1000.0
        time_left = QUIZ_TIME_LIMIT - (time.time() - start_time)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if back_btn.handle_event(event):
                return False, None
            
            for i, btn in enumerate(choice_buttons):
                if btn.handle_event(event) and selected_answer is None:
                    selected_answer = i
                    if i == question_data["answer"]:
                        result_msg = "Correct!"
                        result_color = SUCCESS_COLOR
                    else:
                        result_msg = f"Wrong! Correct: {question_data['choices'][question_data['answer']]}"
                        result_color = ERROR_COLOR
                    break
        
        if selected_answer is not None:
            time_left = 0
        
        screen.blit(q_a_bg, (0, 0))  # draw image as background
        
        # Draw timer
        timer_width = (WIN_W - 100) * (time_left / QUIZ_TIME_LIMIT)
        pygame.draw.rect(screen, (100, 100, 100), (50, 120, WIN_W - 100, 20))
        pygame.draw.rect(screen, (0, 200, 0) if time_left > 5 else (255, 0, 0), 
                        (50, 120, timer_width, 20))
        draw_text(screen, f"Time: {time_left:.1f}s", (WIN_W // 2, 129), color=WHITE, font=FONT, center=True)
        
        # Draw question
        draw_text(screen, question_data["q"], (WIN_W // 2, 180),color=WHITE, font=BIG, center=True)
        
        # Draw choices
        for btn in choice_buttons:
            btn.draw(screen)
        
        # Draw result
        if result_msg:
            draw_text(screen, result_msg, (WIN_W // 2, WIN_H - 100), color=result_color, font=BIG, center=True)
        
        back_btn.draw(screen)
        draw_cursor(screen)
        pygame.display.flip()
    
    # Determine rewards
    if selected_answer == question_data["answer"]:
        if question_data["difficulty"] == "easy":
            rewards = QUIZ_EASY_ITEMS
        elif question_data["difficulty"] == "average":
            rewards = QUIZ_AVERAGE_ITEMS
        else:
            rewards = QUIZ_DIFFICULT_ITEMS
        
        # Apply rewards
        materials_gained = {}
        for mat in ["wood", "rope", "metal", "sail"]:
            min_val, max_val = rewards[mat]
            gained = random.randint(min_val, max_val)
            if gained > 0:
                player.materials[mat] += gained
                materials_gained[mat] = gained
        
        points_gained = random.randint(rewards["points"][0], rewards["points"][1])
        player.points += points_gained
        
        reward_text = f"+{points_gained} points"
        for mat, amt in materials_gained.items():
            reward_text += f", +{amt} {mat}"
        
        hud.add(reward_text, color=SUCCESS_COLOR)
        return True, question_data["id"]
    
    return False, None

# ------------------- Game Over Screen -------------------
def game_over_screen(player, username):
    buyback_btn = Button((WIN_W//2 - 190, 450, 390, 60), f"BUYBACK ({BUYBACK_COST} PTS)", font=custom_font_login, text_color=WHITE)
    retry_btn = Button((WIN_W//2 - 300, 400, 160, 50), "RETRY", font=custom_font_login, text_color=WHITE)
    menu_btn = Button((WIN_W//2 + 150, 400, 250, 50), "MAIN MENU", font=custom_font_login, text_color=WHITE)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if buyback_btn.handle_event(event) and player.points >= BUYBACK_COST:
                player.points -= BUYBACK_COST
                player.lives = 1
                player.health = player.max_health
                hud.add(f"Bought back for {BUYBACK_COST} points!", color=SUCCESS_COLOR)
                return "continue"
            
            if retry_btn.handle_event(event):
                character = player.character
                player.__init__(character)
                player.points = 100
                return "retry"
            
            if menu_btn.handle_event(event):
                return "menu"
        
        screen.blit(gameover_bg, (0, 0))  # draw image as background
        draw_text(screen, "GAME OVER", (WIN_W // 2, 200), color=ERROR_COLOR, font=custom_font_login, center=True)
        draw_text(screen, "You have exhausted all your lives!", (WIN_W // 2, 280), color=WHITE, font=BIG, center=True)
        draw_text(screen, f"FINAL SCORE: {player.points}", (WIN_W // 2, 320), color=INFO_COLOR, font=custom_font_login, center=True)
        
        if player.points >= BUYBACK_COST:
            buyback_btn.draw(screen)
            draw_text(screen, "Buy back with your points", (WIN_W // 2, 370), color=WHITE, font=FONT, center=True)
        else:
            draw_text(screen, f"Need {BUYBACK_COST} points for buyback", (WIN_W // 2, 370), color=ERROR_COLOR, font=FONT, center=True)
        
        retry_btn.draw(screen)
        menu_btn.draw(screen)
        draw_cursor(screen)
        pygame.display.flip()
    
    return "menu"

# ------------------- Main Game Loop -------------------
# ------------------- Main Game Loop -------------------
def game_screen(username):
    pygame.mixer.music.load(os.path.join(BASE_DIR, "resources", "sounds", "INGAME_SOUND.mp3"))
    apply_volume_settings()
    pygame.mixer.music.play(-1)

    user_data = users_data['users'][username]
    character = user_data['character']
    
    # Initialize player from saved data - ALWAYS load all player data
    player = Player(character)
    
    # Load ALL player data from saved state, regardless of position
    if user_data.get('health') is not None:
        player.health = user_data['health']
    if user_data.get('lives') is not None:
        player.lives = user_data['lives']
    if user_data.get('points') is not None:
        player.points = user_data['points']
    if user_data.get('materials') is not None:
        player.materials = user_data['materials'].copy()
    if user_data.get('kills') is not None:
        player.kills = user_data['kills']
    
    current_maze = user_data.get('current_maze', 1)
    maze_seeds = user_data.get('maze_seeds', {})
    completed_quizzes = user_data.get('completed_quizzes', [])
    in_boss_fight = user_data.get('in_boss_fight', False)
    
    # Generate or load maze
    if current_maze not in maze_seeds:
        maze_seeds[current_maze] = random.randint(1, 1000000)
    
    maze = GameMaze(maze_seeds[current_maze])
    
    # Create quiz position mapping
    quiz_positions = {}
    for r in range(ROWS):
        for c in range(COLS):
            if maze.grid[r][c] == 2:
                quiz_positions[(c, r)] = f"maze{current_maze}_quiz_{c}_{r}"
    
    # Place player at start if not continuing from saved position
    if user_data.get('x') is not None and user_data.get('y') is not None:
        player.x = user_data['x']
        player.y = user_data['y']
    else:
        empty_tiles = maze.get_empty_path_tiles()
        if empty_tiles:
            start_col, start_row = empty_tiles[0]
            player.x, player.y = tile_to_screen(start_col, start_row)
            player.x += TILE // 2
            player.y += TILE // 2
    
    # Initialize enemies from saved state or create new
    enemies = []
    if user_data.get('enemies_state'):
        for enemy_data in user_data['enemies_state']:
            enemy = Enemy(enemy_data['x'], enemy_data['y'], enemy_data.get('level', 1))
            enemy.hp = enemy_data['hp']
            enemy.last_attack_time = time.time()
            enemies.append(enemy)
    else:
        empty_tiles = maze.get_empty_path_tiles()
        for _ in range(3):
            if empty_tiles:
                col, row = random.choice(empty_tiles)
                empty_tiles.remove((col, row))
                x, y = tile_to_screen(col, row)
                x += TILE // 2
                y += TILE // 2
                enemy = Enemy(x, y)
                enemy.last_attack_time = time.time()
                enemies.append(enemy)
    
    last_enemy_spawn = time.time()
    enemy_spawn_interval = ENEMY_SPAWN_INTERVAL
    game_time = 0
    
    last_regen_time = time.time()
    
    # Game state
    paused = False
    current_quiz = None
    quiz_completed = completed_quizzes.copy()
    current_quiz_position = None
    
    # If continuing in boss fight, go directly to boss
    if in_boss_fight:
        victory = boss_fight_screen(player, username)
        if victory:
            victory_video_screen()
            credits_screen(username)
            users_data['users'][username].update({
                "current_maze": 1,
                "maze_seeds": {},
                "x": None,
                "y": None,
                "health": player.max_health,
                "lives": MAX_LIVES,
                "points": player.points,
                "materials": {"wood": 0, "rope": 0, "metal": 0, "sail": 0},
                "completed_quizzes": [],
                "enemies_state": [],
                "in_boss_fight": False
            })
            save_users()
            return
        else:
            in_boss_fight = False
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        game_time += dt
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                users_data['users'][username].update({
                    "x": player.x,
                    "y": player.y,
                    "health": player.health,
                    "lives": player.lives,
                    "points": player.points,
                    "materials": player.materials,
                    "kills": player.kills,
                    "current_maze": current_maze,
                    "maze_seeds": maze_seeds,
                    "completed_quizzes": quiz_completed,
                    "enemies_state": [{"x": e.x, "y": e.y, "hp": e.hp, "level": getattr(e, 'level', 1)} for e in enemies],
                    "in_boss_fight": in_boss_fight
                })
                save_users()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                elif event.key == pygame.K_e and not paused and not player.is_respawning:
                    player_col, player_row = screen_to_tile(player.x, player.y)
                    
                    # Check for quiz interaction
                    if (player_col, player_row) in quiz_positions:
                        quiz_id = quiz_positions[(player_col, player_row)]
                        
                        # Check if quiz already completed
                        if quiz_id in quiz_completed:
                            hud.add("Quiz already completed!", color=ERROR_COLOR)
                        else:
                            # Get available questions (not completed)
                            available_questions = [q for q in QUESTIONS if q["id"] not in quiz_completed]
                            if available_questions:
                                current_quiz = random.choice(available_questions)
                                current_quiz_position = (player_col, player_row)
                            else:
                                hud.add("No more quizzes available!", color=INFO_COLOR)
                    
                    # Check for door interaction
                    if (player_col, player_row) in maze.door_tiles:
                        door_choice = door_selection_screen(current_maze)
                        if door_choice:
                            if door_choice == "shipyard":
                                can_build = all(player.materials[mat] >= SHIP_CRAFT_REQUIREMENTS[mat] for mat in SHIP_CRAFT_REQUIREMENTS)
                                if can_build:
                                    hud.add("Entering shipyard... Prepare for BOSS FIGHT!", color=(255, 215, 0))
                                    in_boss_fight = True
                                    victory = boss_fight_screen(player, username)
                                    if victory:
                                        victory_video_screen()
                                        credits_screen(username)
                                        users_data['users'][username].update({
                                            "current_maze": 1,
                                            "maze_seeds": {},
                                            "x": None,
                                            "y": None,
                                            "health": player.max_health,
                                            "lives": MAX_LIVES,
                                            "points": player.points,
                                            "materials": {"wood": 0, "rope": 0, "metal": 0, "sail": 0},
                                            "completed_quizzes": [],
                                            "enemies_state": [],
                                            "in_boss_fight": False
                                        })
                                        save_users()
                                        return
                                    else:
                                        in_boss_fight = False
                                else:
                                    missing = {mat: SHIP_CRAFT_REQUIREMENTS[mat] - player.materials[mat] 
                                             for mat in SHIP_CRAFT_REQUIREMENTS 
                                             if player.materials[mat] < SHIP_CRAFT_REQUIREMENTS[mat]}
                                    missing_str = ", ".join(f"{amt} {mat}" for mat, amt in missing.items())
                                    hud.add(f"Need more materials: {missing_str}", color=ERROR_COLOR)
                            else:
                                # Transition to another maze - DEDUCT 300 POINTS
                                new_maze = door_choice
                                
                                # Check if player has enough points
                                if player.points < 300:
                                    hud.add("Not enough points! Need 300 points for maze transition.", color=ERROR_COLOR)
                                else:
                                    # Deduct points for maze transition
                                    player.points -= 300
                                    hud.add(f"Deducted 300 points for maze transition. Remaining: {player.points}", color=INFO_COLOR)
                                    
                                    hud.add(f"Moving to Maze {new_maze}...", color=SUCCESS_COLOR)
                                    
                                    # Save current state with ALL progress maintained
                                    users_data['users'][username].update({
                                        "x": None,  # Reset position for new maze
                                        "y": None,
                                        "health": player.health,  # Keep current health
                                        "lives": player.lives,    # Keep current lives
                                        "points": player.points,  # Keep current points (after deduction)
                                        "materials": player.materials,  # Keep all collected materials
                                        "kills": player.kills,    # Keep kill count
                                        "current_maze": new_maze,  # Update to new maze
                                        "maze_seeds": maze_seeds,
                                        "completed_quizzes": quiz_completed,  # Keep completed quizzes
                                        "enemies_state": [],  # Reset enemies for new maze
                                        "in_boss_fight": False
                                    })
                                    save_users()
                                    
                                    # Restart game screen with new maze
                                    return game_screen(username)
            
            # Mouse-based combat system
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not paused and not player.is_respawning:
                current_time = time.time()
                # Check if player can attack (1-second cooldown)
                if current_time - player.last_attack_time >= 1.0:
                    player.last_attack_time = current_time
                    player.is_attacking = True

                    # Attack all enemies in range
                    for enemy in enemies[:]:
                        attack_dist = math.sqrt((player.x - enemy.x)**2 + (player.y - enemy.y)**2)
                        if attack_dist < 60:  # Attack range
                            damage = player.damage
                            
                            # Assassin critical hit chance
                            if player.character == "Assassin" and random.random() < CHARACTERS['Assassin']['crit_chance']:
                                damage = enemy.hp
                                hud.add("CRITICAL HIT!", color=(255, 215, 0))
                            
                            enemy.hp -= damage
                            
                            if enemy.hp <= 0:
                                enemies.remove(enemy)
                                player.kills += 1
                                player.points += 50 + (getattr(enemy, 'level', 1) * 5)
                                player.health = min(player.max_health, player.health + 10)
                                hud.add(f"Enemy defeated! +{50 + (getattr(enemy, 'level', 1) * 5)} points", color=SUCCESS_COLOR)
        
        if paused or current_quiz or player.is_respawning:
            if current_quiz:
                success, quiz_id = quiz_screen(current_quiz, player)
                
                # Mark the quiz as completed regardless of success
                if current_quiz_position:
                    position_id = quiz_positions[current_quiz_position]
                    if position_id not in quiz_completed:
                        quiz_completed.append(position_id)
                
                # Also mark the question ID as completed
                if current_quiz["id"] not in quiz_completed:
                    quiz_completed.append(current_quiz["id"])
                
                current_quiz = None
                current_quiz_position = None
            
            if player.is_respawning:
                player.respawn_timer -= dt
                if player.respawn_timer <= 0:
                    player.is_respawning = False
                    player.health = player.max_health
                    player.x, player.y = player.death_position
                    hud.add("Respawned!", color=SUCCESS_COLOR)
            
            screen.blit(maze_bg, (0, 0))
            draw_maze(maze, quiz_positions, quiz_completed)
            draw_enemies(enemies)
            draw_player(player)
            draw_hud(player, current_maze)
            
            if paused:
                s = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
                s.fill((0, 0, 0, 128))
                screen.blit(s, (0, 0))
                draw_text(screen, "PAUSED", (WIN_W // 2, WIN_H // 2), color=WHITE, font=HUGE, center=True)
                draw_text(screen, "Press ESC to continue", (WIN_W // 2, WIN_H // 2 + 60), color=WHITE, font=BIG, center=True)
                
            draw_cursor(screen)
            pygame.display.flip()
            continue
        
        # Handle player movement
        keys = pygame.key.get_pressed()
        move_x, move_y = 0, 0
        
        if keys[pygame.K_w]:
            move_y = -1
        if keys[pygame.K_s]:
            move_y = 1
        if keys[pygame.K_a]:
            move_x = -1
        if keys[pygame.K_d]:
            move_x = 1

        # -----RUN ANIMATION ---
        player.is_moving = (move_x != 0 or move_y != 0)
        
        if move_x != 0 and move_y != 0:
            move_x *= 0.7071
            move_y *= 0.7071
        
        new_x = player.x + move_x * player.speed * dt
        new_y = player.y + move_y * player.speed * dt
        
        new_col, new_row = screen_to_tile(new_x, new_y)
        if not maze.is_blocked(new_col, new_row):
            player.x = new_x
            player.y = new_y
        
        # Character abilities
        now = time.time()
        if player.character == "Tank" and now - last_regen_time >= 5.0:
            last_regen_time = now
            player.health = min(player.max_health, player.health + CHARACTERS['Tank']['regen_rate'])
        
        # Enemy spawning with scaling difficulty
        if time.time() - last_enemy_spawn > enemy_spawn_interval and len(enemies) < 8:
            empty_tiles = maze.get_empty_path_tiles()
            if empty_tiles:
                col, row = random.choice(empty_tiles)
                x, y = tile_to_screen(col, row)
                x += TILE // 2
                y += TILE // 2
                
                enemy_level = max(1, int(game_time / ENEMY_SPAWN_INTERVAL_SCALING_TIME) + 1)
                enemy = Enemy(x, y, enemy_level)
                enemy.last_attack_time = time.time()
                enemies.append(enemy)
                last_enemy_spawn = time.time()
                
                enemy_spawn_interval = max(ENEMY_SPAWN_INTERVAL_MIN, 
                                         ENEMY_SPAWN_INTERVAL - (game_time / 60))
        
        # Update enemies
        for enemy in enemies[:]:
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            dist = max(1, math.sqrt(dx*dx + dy*dy))
            
            enemy.x += (dx / dist) * enemy.speed * dt
            enemy.y += (dy / dist) * enemy.speed * dt
            
            enemy_rect = pygame.Rect(enemy.x - 20, enemy.y - 20, 40, 40)
            player_rect = pygame.Rect(player.x - PLAYER_RADIUS, player.y - PLAYER_RADIUS, 
                                    PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
            
            current_time = time.time()
            # Enemy attack with 1-second cooldown
            if enemy_rect.colliderect(player_rect) and current_time - enemy.last_attack_time >= 1.0:
                enemy.last_attack_time = current_time
                player.health -= enemy.dmg
                hud.add(f"Enemy hit you for {enemy.dmg} damage!", color=ERROR_COLOR)
        
        # Check if player died
        if player.health <= 0:
            player.lives -= 1
            player.death_position = (player.x, player.y)
            
            if player.lives <= 0:
                pygame.mixer.music.stop() #player dead end music
                result = game_over_screen(player, username)
                if result == "continue":
                    pass
                elif result == "retry":
                    users_data['users'][username].update({
                        "current_maze": 1,
                        "maze_seeds": {},
                        "x": None,
                        "y": None,
                        "health": player.max_health,
                        "lives": player.lives,
                        "points": player.points,
                        "materials": player.materials,
                        "completed_quizzes": [],
                        "enemies_state": [],
                        "in_boss_fight": False
                    })
                    save_users()
                    return game_screen(username)
                else:
                    return
            
            player.is_respawning = True
            player.respawn_timer = RESPAWN_TIMER
            hud.add(f"Respawning in {RESPAWN_TIMER} seconds...", color=ERROR_COLOR)
        
        # Draw everything
        screen.blit(maze_bg, (0, 0))
        draw_maze(maze, quiz_positions, quiz_completed)
        draw_enemies(enemies)
        draw_player(player)
        draw_hud(player, current_maze)
        hud.update()
        hud.draw(screen)
        
        draw_cursor(screen)
        pygame.display.flip()
    
    # Save game state when exiting
    users_data['users'][username].update({
        "x": player.x,
        "y": player.y,
        "health": player.health,
        "lives": player.lives,
        "points": player.points,
        "materials": player.materials,
        "kills": player.kills,
        "current_maze": current_maze,
        "maze_seeds": maze_seeds,
        "completed_quizzes": quiz_completed,
        "enemies_state": [{"x": e.x, "y": e.y, "hp": e.hp, "level": getattr(e, 'level', 1)} for e in enemies],
        "in_boss_fight": in_boss_fight
    })
    save_users()

def draw_maze(maze, quiz_positions, quiz_completed):
    for r in range(ROWS):
        for c in range(COLS):
            x, y = tile_to_screen(c, r)
            if maze.grid[r][c] == 1:
                screen.blit(wall_img, (x, y))
            elif maze.grid[r][c] == 0:
                screen.blit(path_img, (x, y))
            elif maze.grid[r][c] == 2:
                screen.blit(path_img, (x, y))
                
                # Check if this quiz is completed
                quiz_id = quiz_positions.get((c, r))
                if quiz_id and quiz_id in quiz_completed:
                    # Draw completed quiz (grayed out)
                    completed_block = question_block.copy()
                    completed_block.fill((100, 100, 100, 180), special_flags=pygame.BLEND_RGBA_MULT)
                    screen.blit(completed_block, (x, y))
                    draw_text(screen, "Completed", (x + 5, y - 15), color=(150, 150, 150), font=SMALL)
                else:
                    # Draw active quiz
                    screen.blit(question_block, (x, y))
                    draw_text(screen, "Quiz", (x + 5, y - 15), color=WHITE, font=SMALL)
            
            elif maze.grid[r][c] == 3:
                screen.blit(path_img, (x, y))
                screen.blit(door_block, (x, y))
                draw_text(screen, "Door", (x, y - 15), color=WHITE, font=SMALL)
def draw_enemies(enemies):
    for enemy in enemies:
        frame_index = int(pygame.time.get_ticks() / 100) % len(frames)
        screen.blit(frames[frame_index], (enemy.x - 30, enemy.y - 30))
        
        bar_width = 40
        bar_height = 6
        health_ratio = enemy.hp / enemy.max_hp
        pygame.draw.rect(screen, (255, 0, 0), 
                        (enemy.x - bar_width//2, enemy.y - 40, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                        (enemy.x - bar_width//2, enemy.y - 40, bar_width * health_ratio, bar_height))

def draw_player(player):
    if not player.is_respawning:

        # ------------------------- TANK---------------------------
        if player.character == "Tank":

            # ---- TANK ATTACK ----
            if getattr(player, "is_attacking", False):
                global tank_attack_frame_index, tank_attack_frame_timer
                tank_attack_frame_timer += 0.016

                if tank_attack_frame_timer >= 0.30:
                    # advance linearly so attack plays once
                    tank_attack_frame_index += 1
                    tank_attack_frame_timer = 0

                    # if reached last frame, stop attacking and reset
                    if tank_attack_frame_index >= len(Tank_image_attack):
                        player.is_attacking = False
                        tank_attack_frame_index = 0

                # draw current attack frame
                if Tank_image_attack:
                    screen.blit(Tank_image_attack[tank_attack_frame_index], (player.x - 25, player.y - 25))
                return

            # ---- TANK WALK ----
            if player.is_moving:
                global tank_walk_frame_index, tank_walk_frame_timer
                tank_walk_frame_timer += 0.016
                if tank_walk_frame_timer >= 0.09:
                    tank_walk_frame_index = (tank_walk_frame_index + 1) % len(Tank_image_run)
                    tank_walk_frame_timer = 0
                screen.blit(Tank_image_run[tank_walk_frame_index], (player.x - 25, player.y - 25))

            # ---- TANK IDLE ----
            else:
                global tank_frame_index, tank_frame_timer
                tank_frame_timer += 0.016
                if tank_frame_timer >= 0.1:
                    tank_frame_index = (tank_frame_index + 1) % len(Tank_image)
                    tank_frame_timer = 0
                screen.blit(Tank_image[tank_frame_index], (player.x - 25, player.y - 25))

        # ----------------------- ASSASSIN ---------------------------
        elif player.character == "Assassin":

            # ---- ASSASSIN ATTACK ----
            if getattr(player, "is_attacking", False):
                global assassin_attack_frame_index, assassin_attack_frame_timer
                assassin_attack_frame_timer += 0.016

                if assassin_attack_frame_timer >= 0.05:
                    assassin_attack_frame_index += 1
                    assassin_attack_frame_timer = 0

                    if assassin_attack_frame_index >= len(Assasin_image_attack):
                        player.is_attacking = False
                        assassin_attack_frame_index = 0

                if Assasin_image_attack:
                    screen.blit(Assasin_image_attack[assassin_attack_frame_index], (player.x - 25, player.y - 25))
                return

            # ---- ASSASSIN WALK ----
            if player.is_moving:
                global assassin_walk_frame_index, assassin_walk_frame_timer
                assassin_walk_frame_timer += 0.016
                if assassin_walk_frame_timer >= 0.07:
                    assassin_walk_frame_index = (assassin_walk_frame_index + 1) % len(Assasin_image_run)
                    assassin_walk_frame_timer = 0
                screen.blit(Assasin_image_run[assassin_walk_frame_index], (player.x - 25, player.y - 25))

            # ---- ASSASSIN IDLE ----
            else:
                global assassin_frame_index, assassin_frame_timer
                assassin_frame_timer += 0.016
                if assassin_frame_timer >= 0.08:
                    assassin_frame_index = (assassin_frame_index + 1) % len(Assasin_image)
                    assassin_frame_timer = 0
                screen.blit(Assasin_image[assassin_frame_index], (player.x - 25, player.y - 25))

        #---------------KNIGHT----------------
        elif player.character == "Knight":

            # ---- KNIGHT ATTACK ----
            if getattr(player, "is_attacking", False):
                global knight_attack_frame_index, knight_attack_frame_timer
                knight_attack_frame_timer += 0.016

                if knight_attack_frame_timer >= 0.06:
                    knight_attack_frame_index += 1
                    knight_attack_frame_timer = 0

                    if knight_attack_frame_index >= len(Knight_image_attack):
                        player.is_attacking = False
                        knight_attack_frame_index = 0

                if Knight_image_attack:
                    screen.blit(Knight_image_attack[knight_attack_frame_index], (player.x - 25, player.y - 25))
                return

            # ---- KNIGHT WALK ----
            if player.is_moving:
                global knight_walk_frame_index, knight_walk_frame_timer
                knight_walk_frame_timer += 0.016
                if knight_walk_frame_timer >= 0.10:
                    knight_walk_frame_index = (knight_walk_frame_index + 1) % len(Knight_image_run)
                    knight_walk_frame_timer = 0
                screen.blit(Knight_image_run[knight_walk_frame_index], (player.x - 25, player.y - 25))

            # ---- KNIGHT IDLE ----
            else:
                global knight_frame_index, knight_frame_timer
                knight_frame_timer += 0.016
                if knight_frame_timer >= 0.12:
                    knight_frame_index = (knight_frame_index + 1) % len(Knight_image)
                    knight_frame_timer = 0
                screen.blit(Knight_image[knight_frame_index], (player.x - 25, player.y - 25))

        # --------------------- DEFAULT (fallback) ---------------------
        else:
            return

    if player.is_respawning:
        draw_text(screen, f"Respawning: {player.respawn_timer:.1f}s",
              (player.x - 50, player.y - 60), color=ERROR_COLOR, font=FONT)

def draw_hud(player, maze_id):
    draw_text(screen, f"Points: {player.points}", (20, 20), color=WHITE)
    draw_text(screen, f"Maze: {maze_id}/{MAZES_COUNT}", (20, 45), color=WHITE)
    
    pygame.draw.rect(screen, (255, 0, 0), (20, 70, 200, 20))
    pygame.draw.rect(screen, (0, 255, 0), (20, 70, 200 * (player.health / player.max_health), 20))
    draw_text(screen, f"HP: {int(player.health)}/{player.max_health}", (20, 70), color=WHITE, font=SMALL)
    
    draw_text(screen, f"Lives: {player.lives}", (20, 100), color=WHITE)
    
    y_offset = 130
    for mat, amount in player.materials.items():
        needed = SHIP_CRAFT_REQUIREMENTS[mat]
        color = SUCCESS_COLOR if amount >= needed else WHITE
        draw_text(screen, f"{mat}: {amount}/{needed}", (20, y_offset), color=color)
        y_offset += 25
    
    # Updated controls text
    controls_text = "WASD: Move | Mouse Left Click: Attack | E: Interact | ESC: Pause"
    text_surface = SMALL.render(controls_text, True, INFO_COLOR)
    text_rect = text_surface.get_rect(center=(WIN_W // 2, WIN_H - 30))
    screen.blit(text_surface, text_rect)

# ------------------- Main Application Loop -------------------
def main():
    while True:
        username = login_register_screen()
        if not username:
            continue
        
        while True:
            result = main_menu_screen(username)
            if result == "logout":
                break
            elif result == "start_game":
                game_screen(username)

if __name__ == "__main__":
    main()
