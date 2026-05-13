import os
import pygame
import sys
import random
import time
from collections import deque

# =========================================================
# slide_puzzle.py
#
# Cara pakai dari main.py:
#
# from slide_puzzle import run_slide_puzzle
#
# run_slide_puzzle("3x3", "Speed", "Number")
# run_slide_puzzle("4x4", "Step", "Image")
#
# Parameter:
# tile_size_text = "3x3" / "4x4" / "5x5"
# mode = "Speed" / "Step"
# puzzle_type = "Number" / "Image"
#
# Speed Mode = BFS
# Step Mode  = IDDFS / DFS dicicil per frame supaya tidak freeze
# =========================================================

pygame.init()

WIDTH, HEIGHT = 1100, 720
FPS = 60

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Slide Puzzle")
CLOCK = pygame.time.Clock()

BOARD_PIXEL_SIZE = 360
PLAYER_BOARD_X = 120
RIVAL_BOARD_X = 620
BOARD_Y = 205

RIVAL_SPEED_DELAY = 1.5

# Colors
BG_TOP = (26, 21, 58)
BG_BOTTOM = (92, 20, 57)
PANEL = (38, 30, 68)
ACCENT = (255, 75, 92)
ACCENT_2 = (167, 120, 255)
TEXT = (255, 240, 245)
MUTED = (210, 130, 145)
SHADOW = (20, 10, 30)

BOARD_FRAME = (105, 48, 46)
BOARD_FRAME_DARK = (65, 30, 32)
TILE_BG = (245, 245, 245)
TILE_TEXT = (28, 28, 32)
EMPTY = (163, 120, 78)
GRID_LINE = (45, 25, 28)
WHITE = (255, 255, 255)

FONT_TITLE = pygame.font.SysFont("arial", 46, bold=True)
FONT_SUBTITLE = pygame.font.SysFont("arial", 22)
FONT_BUTTON = pygame.font.SysFont("arial", 24, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 18)
FONT_SMALL_BOLD = pygame.font.SysFont("arial", 18, bold=True)
FONT_TILE_BIG = pygame.font.SysFont("arial", 62)
FONT_TILE_MED = pygame.font.SysFont("arial", 46)
FONT_TILE_SMALL = pygame.font.SysFont("arial", 34)


# =========================================================
# Basic UI
# =========================================================

def draw_text(text, font, color, x, y, center=True):
    render = font.render(str(text), True, color)
    rect = render.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    SCREEN.blit(render, rect)


def draw_background():
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
        g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
        b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
        pygame.draw.line(SCREEN, (r, g, b), (0, y), (WIDTH, y))

    pygame.draw.circle(SCREEN, (35, 24, 80), (WIDTH // 2, 110), 330)
    pygame.draw.circle(SCREEN, (90, 20, 62), (WIDTH // 2, HEIGHT + 130), 430)

    random.seed(8)
    for _ in range(45):
        x = random.randint(35, WIDTH - 35)
        y = random.randint(30, HEIGHT - 35)
        pygame.draw.circle(SCREEN, (110, 75, 120), (x, y), 1)


class Button:
    def __init__(self, x, y, w, h, text, color=ACCENT):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)

        color = tuple(min(255, c + 20) for c in self.color) if hover else self.color

        pygame.draw.rect(SCREEN, SHADOW, self.rect.move(0, 6), border_radius=28)
        pygame.draw.rect(SCREEN, color, self.rect, border_radius=28)

        draw_text(self.text, FONT_SMALL_BOLD, WHITE, self.rect.centerx, self.rect.centery)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


# =========================================================
# Puzzle Logic
# =========================================================

def parse_size(tile_size_text):
    if isinstance(tile_size_text, int):
        return tile_size_text

    if tile_size_text == "3x3":
        return 3
    if tile_size_text == "4x4":
        return 4
    if tile_size_text == "5x5":
        return 5

    return 3


def normalize_type(puzzle_type):
    if puzzle_type in ["Image", "Picture"]:
        return "Image"
    return "Number"


def goal_state(n):
    return tuple(list(range(1, n * n)) + [0])


def get_neighbors(state, n):
    neighbors = []
    blank = state.index(0)
    row, col = divmod(blank, n)

    possible = []

    if row > 0:
        possible.append(("UP", blank - n))
    if row < n - 1:
        possible.append(("DOWN", blank + n))
    if col > 0:
        possible.append(("LEFT", blank - 1))
    if col < n - 1:
        possible.append(("RIGHT", blank + 1))

    for move, target in possible:
        new_state = list(state)
        new_state[blank], new_state[target] = new_state[target], new_state[blank]
        neighbors.append((move, tuple(new_state)))

    return neighbors


def move_player(state, n, direction):
    blank = state.index(0)
    row, col = divmod(blank, n)
    target = None

    if direction == "UP" and row > 0:
        target = blank - n
    elif direction == "DOWN" and row < n - 1:
        target = blank + n
    elif direction == "LEFT" and col > 0:
        target = blank - 1
    elif direction == "RIGHT" and col < n - 1:
        target = blank + 1

    if target is None:
        return state, False

    new_state = list(state)
    new_state[blank], new_state[target] = new_state[target], new_state[blank]
    return tuple(new_state), True


def reconstruct_path(parent, start, goal):
    if goal not in parent:
        return []

    path = []
    current = goal

    while current != start:
        path.append(current)
        current = parent[current]

    path.append(start)
    path.reverse()
    return path


def bfs_path(start, n, max_nodes=90000):
    goal = goal_state(n)

    if start == goal:
        return [start], 0

    queue = deque([start])
    visited = {start}
    parent = {}
    nodes = 0

    while queue and nodes < max_nodes:
        current = queue.popleft()
        nodes += 1

        for move, next_state in get_neighbors(current, n):
            if next_state in visited:
                continue

            visited.add(next_state)
            parent[next_state] = current

            if next_state == goal:
                return reconstruct_path(parent, start, goal), nodes

            queue.append(next_state)

    return [], nodes


class LiveDFSRunner:
    def __init__(self, start, n, depth_limit=80):
        self.start = start
        self.n = n
        self.goal = goal_state(n)
        self.depth_limit = depth_limit

        self.stack = []
        self.current_path = [start]
        self.solution_path = []

        self.finished = False
        self.found = False
        self.nodes = 0
        self.attempt = 0

        self.reset_root()

    def reset_root(self):
        self.attempt += 1
        self.stack = [(self.start, [self.start], {self.start}, 0)]
        self.current_path = [self.start]

    def step_search(self, nodes_per_frame=200):
        if self.finished:
            return

        for _ in range(nodes_per_frame):
            if not self.stack:
                # DFS mentok, ulang dari root dengan urutan random baru
                self.reset_root()
                return

            current, path, path_set, depth = self.stack.pop()
            self.nodes += 1
            self.current_path = path

            if current == self.goal:
                self.finished = True
                self.found = True
                self.solution_path = path
                return

            if depth >= self.depth_limit:
                continue

            neighbors = get_neighbors(current, self.n)
            random.shuffle(neighbors)

            for move, next_state in neighbors:
                if next_state not in path_set:
                    self.stack.append((
                        next_state,
                        path + [next_state],
                        path_set | {next_state},
                        depth + 1
                    ))

    def get_live_path(self):
        if self.found:
            return self.solution_path

        return self.current_path


def generate_puzzle(n):
    state = goal_state(n)
    path_from_goal = [state]
    previous = None

    # Dibuat tidak terlalu dalam supaya BFS/IDDFS masih playable.
    if n == 3:
        scramble_steps = 14
    elif n == 4:
        scramble_steps = 18
    else:
        scramble_steps = 22

    for _ in range(scramble_steps):
        neighbors = get_neighbors(state, n)

        if previous is not None:
            filtered = [(m, s) for m, s in neighbors if s != previous]
            neighbors = filtered or neighbors

        move, next_state = random.choice(neighbors)
        previous = state
        state = next_state
        path_from_goal.append(state)

    guaranteed_solution = list(reversed(path_from_goal))
    return state, guaranteed_solution


# =========================================================
# Image Logic
# =========================================================

def get_random_slide_image_path():
    rng = random.SystemRandom()
    number = rng.randint(1, 10)
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "assets", f"slide_image_{number:02}.png")


def load_and_cut_image(image_path, n):
    try:
        image = pygame.image.load(image_path).convert_alpha()
        image = pygame.transform.smoothscale(image, (BOARD_PIXEL_SIZE, BOARD_PIXEL_SIZE))
    except Exception:
        return None

    tile_size = BOARD_PIXEL_SIZE // n
    pieces = {}

    for value in range(1, n * n):
        index = value - 1
        row, col = divmod(index, n)
        rect = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)

        piece = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        piece.blit(image, (0, 0), rect)
        pieces[value] = piece

    return pieces


# =========================================================
# Draw Puzzle
# =========================================================

def get_tile_font(n):
    if n == 3:
        return FONT_TILE_BIG
    if n == 4:
        return FONT_TILE_MED
    return FONT_TILE_SMALL


def draw_board(state, n, x, y, title, subtitle, moves, pieces=None):
    tile_size = BOARD_PIXEL_SIZE // n
    padding = 18

    outer_rect = pygame.Rect(
        x - padding,
        y - padding,
        BOARD_PIXEL_SIZE + padding * 2,
        BOARD_PIXEL_SIZE + padding * 2
    )

    draw_text(title, FONT_BUTTON, TEXT, x + BOARD_PIXEL_SIZE // 2, y - 63)
    draw_text(subtitle, FONT_SMALL, MUTED, x + BOARD_PIXEL_SIZE // 2, y - 38)

    pygame.draw.rect(SCREEN, SHADOW, outer_rect.move(0, 8), border_radius=22)
    pygame.draw.rect(SCREEN, BOARD_FRAME, outer_rect, border_radius=22)
    pygame.draw.rect(SCREEN, BOARD_FRAME_DARK, outer_rect, width=4, border_radius=22)

    board_inner = pygame.Rect(x, y, BOARD_PIXEL_SIZE, BOARD_PIXEL_SIZE)
    pygame.draw.rect(SCREEN, BOARD_FRAME_DARK, board_inner, border_radius=10)

    font = get_tile_font(n)

    for index, value in enumerate(state):
        row, col = divmod(index, n)

        tx = x + col * tile_size
        ty = y + row * tile_size
        rect = pygame.Rect(tx, ty, tile_size, tile_size)

        if value == 0:
            pygame.draw.rect(SCREEN, EMPTY, rect, border_radius=4)
            pygame.draw.rect(SCREEN, GRID_LINE, rect, width=2, border_radius=4)
            continue

        if pieces and value in pieces:
            SCREEN.blit(pieces[value], rect)
            pygame.draw.rect(SCREEN, GRID_LINE, rect, width=2, border_radius=4)
        else:
            pygame.draw.rect(SCREEN, TILE_BG, rect, border_radius=4)
            pygame.draw.rect(SCREEN, GRID_LINE, rect, width=2, border_radius=4)
            draw_text(value, font, TILE_TEXT, rect.centerx, rect.centery)

    draw_text(
        f"Moves: {moves}",
        FONT_SMALL_BOLD,
        ACCENT,
        x + BOARD_PIXEL_SIZE // 2,
        y + BOARD_PIXEL_SIZE + 42
    )


def draw_status_card(text_1, text_2):
    rect = pygame.Rect(320, 665, 460, 42)

    pygame.draw.rect(SCREEN, SHADOW, rect.move(0, 5), border_radius=18)
    pygame.draw.rect(SCREEN, PANEL, rect, border_radius=18)

    draw_text(text_1, FONT_SMALL_BOLD, TEXT, rect.centerx, rect.y + 12)
    draw_text(text_2, FONT_SMALL, MUTED, rect.centerx, rect.y + 30)


# =========================================================
# Result Screen
# =========================================================

def result_screen(title, winner_text, detail_text):
    menu_button = Button(WIDTH // 2 - 155, 500, 310, 60, "Back")
    retry_button = Button(WIDTH // 2 - 155, 580, 310, 60, "Retry")

    while True:
        CLOCK.tick(FPS)
        draw_background()

        draw_text(title, FONT_TITLE, ACCENT, WIDTH // 2, 145)
        draw_text(winner_text, FONT_BUTTON, TEXT, WIDTH // 2, 250)
        draw_text(detail_text, FONT_SUBTITLE, MUTED, WIDTH // 2, 300)

        menu_button.draw()
        retry_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if menu_button.clicked(event):
                return "BACK"

            if retry_button.clicked(event):
                return "RETRY"


# =========================================================
# Main Game
# =========================================================

def run_slide_puzzle(tile_size_text="3x3", mode="Speed", puzzle_type="Number", image_path=None):
    n = parse_size(tile_size_text)
    puzzle_type = normalize_type(puzzle_type)

    start_state, guaranteed_solution = generate_puzzle(n)

    player_state = start_state
    rival_state = start_state

    player_moves = 0
    rival_moves = 0
    rival_index = 0

    goal = goal_state(n)

    pieces = None

    if puzzle_type == "Image":
        if image_path is None:
            image_path = get_random_slide_image_path()

        pieces = load_and_cut_image(image_path, n)

    if mode == "Speed":
        rival_solution, nodes = bfs_path(start_state, n)

        if not rival_solution:
            rival_solution = guaranteed_solution

        rival_delay = RIVAL_SPEED_DELAY
        last_rival_move_time = time.time()
        dfs_runner = None

    else:
        dfs_runner = LiveDFSRunner(
            start_state,
            n,
            depth_limit=len(guaranteed_solution) + 40
        )

        rival_solution = []
        nodes = 0

    start_time = time.time()
    back_button = Button(35, 28, 120, 48, "Back")

    while True:
        CLOCK.tick(FPS)
        elapsed = time.time() - start_time

        if mode == "Step":
            dfs_runner.step_search(nodes_per_frame=200)
            rival_solution = dfs_runner.get_live_path()
            nodes = dfs_runner.nodes

        if mode == "Speed":
            if rival_index < len(rival_solution) - 1:
                if time.time() - last_rival_move_time >= rival_delay:
                    rival_index += 1
                    rival_state = rival_solution[rival_index]
                    rival_moves += 1
                    last_rival_move_time = time.time()

        draw_background()

        draw_text("SLIDE PUZZLE", FONT_TITLE, ACCENT, WIDTH // 2, 45)
        draw_text(f"{tile_size_text}  |  {mode} Mode  |  {puzzle_type}", FONT_SUBTITLE, MUTED, WIDTH // 2, 88)

        back_button.draw()

        draw_board(
            player_state,
            n,
            PLAYER_BOARD_X,
            BOARD_Y,
            "PLAYER",
            "Manual Board",
            player_moves,
            pieces
        )

        if mode == "Speed":
            rival_subtitle = "1.5s per move"
        else:
            rival_subtitle = "Thinking..."

        draw_board(
            rival_state,
            n,
            RIVAL_BOARD_X,
            BOARD_Y,
            "RIVAL",
            rival_subtitle,
            rival_moves,
            pieces
        )

        if mode == "Speed":
            draw_status_card(
                f"Timer: {elapsed:.2f}s",
                "Rival moves every 1.5 seconds"
            )
        else:
            draw_status_card(
                f"Timer: {elapsed:.2f}s",
                "Rival follows live DFS search"
            )

        pygame.display.flip()

        if player_state == goal or rival_state == goal:
            player_finished = player_state == goal
            rival_finished = rival_state == goal

            if player_finished and not rival_finished:
                result = result_screen(
                    "RESULT",
                    "Player Wins!",
                    f"Moves: {player_moves} | Time: {elapsed:.2f}s"
                )
            elif rival_finished and not player_finished:
                result = result_screen(
                    "RESULT",
                    "Rival Wins!",
                    f"Rival Moves: {rival_moves} | Time: {elapsed:.2f}s"
                )
            else:
                result = result_screen(
                    "RESULT",
                    "Draw!",
                    f"Player: {player_moves} | Rival: {rival_moves}"
                )

            if result == "BACK":
                return
            if result == "RETRY":
                return run_slide_puzzle(tile_size_text, mode, puzzle_type)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if back_button.clicked(event):
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

                direction = None

                if event.key in [pygame.K_UP, pygame.K_w]:
                    direction = "UP"
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    direction = "DOWN"
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    direction = "LEFT"
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    direction = "RIGHT"

                if direction:
                    new_state, moved = move_player(player_state, n, direction)

                    if moved:
                        player_state = new_state
                        player_moves += 1

                        if mode == "Step":
                            live_path = dfs_runner.get_live_path()

                            if len(live_path) > 1:
                                if rival_index >= len(live_path) - 1:
                                    rival_index = 0

                                rival_index += 1
                                rival_state = live_path[rival_index]
                                rival_moves += 1


if __name__ == "__main__":
    run_slide_puzzle("5x5", "Step", "Number")
