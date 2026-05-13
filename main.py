import os
import pygame
import sys
import random

from tictactoe import run_tic_tac_toe
from slide_puzzle import run_slide_puzzle

pygame.init()

WIDTH, HEIGHT = 1100, 720
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("FUN")
clock = pygame.time.Clock()

# Colors
BG_TOP = (26, 21, 58)
BG_BOTTOM = (92, 20, 57)
ACCENT = (255, 75, 92)
ACCENT_HOVER = (255, 95, 112)
TEXT = (255, 240, 245)
MUTED = (210, 130, 145)
SHADOW = (20, 10, 30)

FONT_TITLE = pygame.font.SysFont("arial", 90, bold=True)
FONT_SUBTITLE = pygame.font.SysFont("arial", 24)
FONT_BUTTON = pygame.font.SysFont("arial", 24)

tile_options = ["3x3", "4x4", "5x5"]
mode_options = ["Speed", "Step"]
type_options = ["Number", "Image"]


def draw_text(text, font, color, x, y, center=True):
    render = font.render(text, True, color)
    rect = render.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(render, rect)


def draw_background():
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
        g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
        b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    random.seed(10)
    for _ in range(45):
        x = random.randint(40, WIDTH - 40)
        y = random.randint(40, HEIGHT - 40)
        pygame.draw.circle(screen, (120, 80, 120), (x, y), 1)


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)

        color = ACCENT_HOVER if is_hover else ACCENT

        shadow_rect = self.rect.move(0, 6)
        pygame.draw.rect(screen, SHADOW, shadow_rect, border_radius=35)
        pygame.draw.rect(screen, color, self.rect, border_radius=35)

        draw_text(
            self.text,
            FONT_BUTTON,
            TEXT,
            self.rect.centerx,
            self.rect.centery
        )

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

class OptionButton:
    def __init__(self, x, y, w, h, text, group_name):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.group_name = group_name

    def draw(self, selected_value):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        is_selected = self.text == selected_value

        if is_selected:
            color = ACCENT
            border = TEXT
        elif is_hover:
            color = (55, 38, 88)
            border = ACCENT
        else:
            color = (42, 30, 68)
            border = (95, 65, 105)

        pygame.draw.rect(screen, SHADOW, self.rect.move(0, 5), border_radius=22)
        pygame.draw.rect(screen, color, self.rect, border_radius=22)
        pygame.draw.rect(screen, border, self.rect, width=2, border_radius=22)

        draw_text(self.text, FONT_BUTTON, TEXT, self.rect.centerx, self.rect.centery)

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

def main_menu():
    play_button = Button(WIDTH // 2 - 160, 350, 320, 65, "Play")
    quit_button = Button(WIDTH // 2 - 160, 440, 320, 65, "Quit")

    while True:
        clock.tick(FPS)
        draw_background()

        draw_text("PUZZLE RUSH", FONT_TITLE, ACCENT, WIDTH // 2, 155)
        draw_text("A FUN MINIGAME", FONT_SUBTITLE, MUTED, WIDTH // 2, 225)

        play_button.draw()
        quit_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if play_button.is_clicked(event):
                game_select()

            if quit_button.is_clicked(event):
                pygame.quit()
                sys.exit()

def load_image(path, size):
    try:
        image = pygame.image.load(path).convert_alpha()

        target_w, target_h = size
        img_w, img_h = image.get_size()

        scale = max(target_w / img_w, target_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        image = pygame.transform.smoothscale(image, (new_w, new_h))

        crop_x = (new_w - target_w) // 2
        crop_y = (new_h - target_h) // 2

        cropped = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        cropped.blit(image, (0, 0), pygame.Rect(crop_x, crop_y, target_w, target_h))

        return cropped
    except:
        return None

def draw_game_card(rect, title, image=None):
    mouse_pos = pygame.mouse.get_pos()
    is_hover = rect.collidepoint(mouse_pos)

    card_color = (42, 30, 68) if not is_hover else (55, 38, 88)
    border_color = ACCENT if is_hover else (95, 65, 105)

    shadow_rect = rect.move(0, 8)
    pygame.draw.rect(screen, SHADOW, shadow_rect, border_radius=28)
    pygame.draw.rect(screen, card_color, rect, border_radius=28)
    pygame.draw.rect(screen, border_color, rect, width=3, border_radius=28)

    image_rect = pygame.Rect(rect.x + 15, rect.y + 20, rect.width - 30, 150)

    if image:
        screen.blit(image, image_rect)
    else:
        pygame.draw.rect(screen, (70, 45, 85), image_rect, border_radius=20)
        draw_text("No Image", FONT_SUBTITLE, MUTED, image_rect.centerx, image_rect.centery)

    draw_text(title, FONT_BUTTON, TEXT, rect.centerx, rect.y + 215)

    draw_text("Click to play", FONT_SUBTITLE, MUTED, rect.centerx, rect.y + 255)

def game_select():
    base_dir = os.path.dirname(__file__)

    tic_thumb = load_image(os.path.join(base_dir, "assets", "tictactoe.png"), (230, 150))
    puzzle_thumb = load_image(os.path.join(base_dir, "assets", "slidepuzzle.png"), (230, 150))

    tic_card = pygame.Rect(250, 285, 260, 300)
    puzzle_card = pygame.Rect(590, 285, 260, 300)

    back_button = Button(WIDTH // 2 - 120, 625, 240, 55, "Back")

    while True:
        clock.tick(FPS)
        draw_background()

        draw_text("SELECT GAME", FONT_TITLE, ACCENT, WIDTH // 2, 120)
        draw_text("Choose your minigame", FONT_SUBTITLE, MUTED, WIDTH // 2, 195)

        draw_game_card(tic_card, "Tic Tac Toe", tic_thumb)
        draw_game_card(puzzle_card, "Slide Puzzle", puzzle_thumb)

        back_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if tic_card.collidepoint(event.pos):
                    tic_tac_toe_settings()

                if puzzle_card.collidepoint(event.pos):
                    slide_puzzle_settings()

            if back_button.is_clicked(event):
                return

def slide_puzzle_settings():
    selected_tile = "3x3"
    selected_mode = "Speed"
    selected_type = "Number"

    tile_buttons = [
        OptionButton(320, 250, 130, 55, "3x3", "tile"),
        OptionButton(485, 250, 130, 55, "4x4", "tile"),
        OptionButton(650, 250, 130, 55, "5x5", "tile"),
    ]

    mode_buttons = [
        OptionButton(375, 370, 160, 55, "Speed", "mode"),
        OptionButton(565, 370, 160, 55, "Step", "mode"),
    ]

    type_buttons = [
        OptionButton(375, 490, 160, 55, "Number", "type"),
        OptionButton(565, 490, 160, 55, "Image", "type"),
    ]

    start_button = Button(WIDTH // 2 - 150, 595, 300, 60, "Start")
    back_button = Button(40, 40, 140, 55, "Back")

    while True:
        clock.tick(FPS)
        draw_background()

        draw_text("SLIDE PUZZLE", FONT_TITLE, ACCENT, WIDTH // 2, 100)
        draw_text("Game Settings", FONT_SUBTITLE, MUTED, WIDTH // 2, 170)

        draw_text("Tile Size", FONT_BUTTON, TEXT, WIDTH // 2, 220)
        for button in tile_buttons:
            button.draw(selected_tile)

        draw_text("Mode", FONT_BUTTON, TEXT, WIDTH // 2, 340)
        for button in mode_buttons:
            button.draw(selected_mode)

        draw_text("Type", FONT_BUTTON, TEXT, WIDTH // 2, 460)
        for button in type_buttons:
            button.draw(selected_type)

        start_button.draw()
        back_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if back_button.is_clicked(event):
                return

            if start_button.is_clicked(event):
                run_slide_puzzle(selected_tile, selected_mode, selected_type)

            for button in tile_buttons:
                if button.is_clicked(event):
                    selected_tile = button.text

            for button in mode_buttons:
                if button.is_clicked(event):
                    selected_mode = button.text

            for button in type_buttons:
                if button.is_clicked(event):
                    selected_type = button.text

def tic_tac_toe_settings():
    selected_difficulty = "Easy"
    selected_turn = "First (O)"

    difficulty_buttons = [
        OptionButton(320, 290, 130, 55, "Easy", "difficulty"),
        OptionButton(485, 290, 130, 55, "Medium", "difficulty"),
        OptionButton(650, 290, 130, 55, "Hard", "difficulty"),
    ]

    turn_buttons = [
        OptionButton(375, 410, 160, 55, "First", "turn"),
        OptionButton(565, 410, 160, 55, "Second", "turn"),
    ]

    start_button = Button(WIDTH // 2 - 150, 540, 300, 60, "Start")
    back_button = Button(40, 40, 140, 55, "Back")

    while True:
        clock.tick(FPS)
        draw_background()

        draw_text("TIC TAC TOE", FONT_TITLE, ACCENT, WIDTH // 2, 110)
        draw_text("Game Settings", FONT_SUBTITLE, MUTED, WIDTH // 2, 180)

        draw_text("AI Difficulty", FONT_BUTTON, TEXT, WIDTH // 2, 255)
        for button in difficulty_buttons:
            button.draw(selected_difficulty)

        draw_text("Your Turn", FONT_BUTTON, TEXT, WIDTH // 2, 375)
        for button in turn_buttons:
            button.draw(selected_turn)

        start_button.draw()
        back_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if back_button.is_clicked(event):
                return

            if start_button.is_clicked(event):
                run_tic_tac_toe(selected_difficulty, selected_turn)

            for button in difficulty_buttons:
                if button.is_clicked(event):
                    selected_difficulty = button.text

            for button in turn_buttons:
                if button.is_clicked(event):
                    selected_turn = button.text

main_menu()