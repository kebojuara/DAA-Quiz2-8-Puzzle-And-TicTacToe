import pygame
import random
import math
import sys

WIDTH, HEIGHT = 1100, 720
FPS = 60

BG_TOP = (26, 21, 58)
BG_BOTTOM = (92, 20, 57)
ACCENT = (255, 75, 92)
TEXT = (255, 240, 245)
MUTED = (210, 130, 145)
SHADOW = (20, 10, 30)

BOARD_SIZE = 320
CELL_SIZE = BOARD_SIZE // 3
BOARD_X = (WIDTH - BOARD_SIZE) // 2
BOARD_Y = 235

FONT_TITLE = None
FONT_TEXT = None
FONT_SMALL = None
FONT_BIG = None


def init_fonts():
    global FONT_TITLE, FONT_TEXT, FONT_SMALL, FONT_BIG
    FONT_TITLE = pygame.font.SysFont("arial", 58, bold=True)
    FONT_TEXT = pygame.font.SysFont("arial", 24, bold=True)
    FONT_SMALL = pygame.font.SysFont("arial", 21)
    FONT_BIG = pygame.font.SysFont("arial", 48, bold=True)


def draw_text(screen, text, font, color, x, y, center=True):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(img, rect)


def draw_background(screen):
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
        g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
        b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    pygame.draw.circle(screen, (35, 28, 85), (WIDTH // 2, 120), 390)
    pygame.draw.circle(screen, (105, 18, 65), (WIDTH // 2, 720), 520)

    random.seed(10)
    for _ in range(40):
        x = random.randint(40, WIDTH - 40)
        y = random.randint(40, HEIGHT - 40)
        pygame.draw.circle(screen, (120, 80, 120), (x, y), 1)


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, screen):
        mouse = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse)
        color = (255, 95, 112) if hover else ACCENT

        pygame.draw.rect(screen, SHADOW, self.rect.move(0, 6), border_radius=28)
        pygame.draw.rect(screen, color, self.rect, border_radius=28)
        draw_text(screen, self.text, FONT_TEXT, TEXT, self.rect.centerx, self.rect.centery)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


def draw_o(screen, rect, warning=False):
    color = (130, 40, 45) if warning else (235, 35, 25)
    width = 10 if warning else 12

    pygame.draw.ellipse(screen, color, rect.inflate(-35, -35), width)


def draw_x(screen, rect, warning=False):
    color = (35, 120, 35) if warning else (70, 240, 40)
    width = 10 if warning else 13

    pad_x = 24
    pad_y = 32

    pygame.draw.line(
        screen,
        color,
        (rect.left + pad_x, rect.top + pad_y),
        (rect.right - pad_x, rect.bottom - pad_y),
        width
    )

    pygame.draw.line(
        screen,
        color,
        (rect.right - pad_x, rect.top + pad_y),
        (rect.left + pad_x, rect.bottom - pad_y),
        width
    )


def draw_wood_lines(screen, rect):
    for i in range(4):
        y = rect.y + 25 + i * 25
        pygame.draw.arc(
            screen,
            (205, 125, 65),
            (rect.x + 15, y, rect.w - 30, 28),
            0,
            math.pi,
            2
        )


def draw_board(screen, board, player_moves):
    oldest_o = player_moves["O"][0] if len(player_moves["O"]) >= 3 else None
    oldest_x = player_moves["X"][0] if len(player_moves["X"]) >= 3 else None

    frame = pygame.Rect(BOARD_X - 22, BOARD_Y - 22, BOARD_SIZE + 44, BOARD_SIZE + 44)

    pygame.draw.rect(screen, SHADOW, frame.move(0, 10), border_radius=25)
    pygame.draw.rect(screen, (110, 52, 45), frame, border_radius=25)
    pygame.draw.rect(screen, (75, 35, 35), frame, width=6, border_radius=25)

    for row in range(3):
        for col in range(3):
            x = BOARD_X + col * CELL_SIZE
            y = BOARD_Y + row * CELL_SIZE

            rect = pygame.Rect(x + 3, y + 3, CELL_SIZE - 6, CELL_SIZE - 6)

            pygame.draw.rect(screen, (240, 240, 240), rect, border_radius=5)
            pygame.draw.rect(screen, (45, 25, 25), rect, width=4, border_radius=5)

            value = board[row][col]
            warning = (row, col) == oldest_o or (row, col) == oldest_x

            if value == "O":
                draw_o(screen, rect, warning)
            elif value == "X":
                draw_x(screen, rect, warning)


def get_cell_from_mouse(pos):
    mx, my = pos

    if not (BOARD_X <= mx <= BOARD_X + BOARD_SIZE):
        return None
    if not (BOARD_Y <= my <= BOARD_Y + BOARD_SIZE):
        return None

    col = (mx - BOARD_X) // CELL_SIZE
    row = (my - BOARD_Y) // CELL_SIZE

    return int(row), int(col)


def get_empty_cells(board):
    empty = []

    for row in range(3):
        for col in range(3):
            if board[row][col] == "":
                empty.append((row, col))

    return empty


def make_move(board, player_moves, row, col, symbol):
    if board[row][col] != "":
        return False

    board[row][col] = symbol
    player_moves[symbol].append((row, col))

    if len(player_moves[symbol]) > 3:
        old_row, old_col = player_moves[symbol].pop(0)
        board[old_row][old_col] = ""

    return True


def copy_moves(player_moves):
    return {
        "O": player_moves["O"][:],
        "X": player_moves["X"][:]
    }


def simulate_move(board, player_moves, row, col, symbol):
    new_board = [r[:] for r in board]
    new_moves = copy_moves(player_moves)

    new_board[row][col] = symbol
    new_moves[symbol].append((row, col))

    if len(new_moves[symbol]) > 3:
        old_row, old_col = new_moves[symbol].pop(0)
        new_board[old_row][old_col] = ""

    return new_board, new_moves


def check_winner(board):
    lines = []

    for row in range(3):
        lines.append([board[row][0], board[row][1], board[row][2]])

    for col in range(3):
        lines.append([board[0][col], board[1][col], board[2][col]])

    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])

    for line in lines:
        if line[0] != "" and line[0] == line[1] == line[2]:
            return line[0]

    return None


def minimax(board, player_moves, is_ai_turn, ai_symbol, player_symbol, depth):
    winner = check_winner(board)

    if winner == ai_symbol:
        return 10 - depth

    if winner == player_symbol:
        return depth - 10

    if depth >= 7:
        return 0

    empty = get_empty_cells(board)

    if not empty:
        return 0

    if is_ai_turn:
        best_score = -999

        for row, col in empty:
            new_board, new_moves = simulate_move(board, player_moves, row, col, ai_symbol)
            score = minimax(new_board, new_moves, False, ai_symbol, player_symbol, depth + 1)
            best_score = max(best_score, score)

        return best_score

    else:
        best_score = 999

        for row, col in empty:
            new_board, new_moves = simulate_move(board, player_moves, row, col, player_symbol)
            score = minimax(new_board, new_moves, True, ai_symbol, player_symbol, depth + 1)
            best_score = min(best_score, score)

        return best_score


def best_ai_move(board, player_moves, ai_symbol, player_symbol):
    best_score = -999
    best_move = None

    for row, col in get_empty_cells(board):
        new_board, new_moves = simulate_move(board, player_moves, row, col, ai_symbol)
        score = minimax(new_board, new_moves, False, ai_symbol, player_symbol, 0)

        if score > best_score:
            best_score = score
            best_move = (row, col)

    return best_move


def get_ai_move(board, player_moves, difficulty, ai_symbol, player_symbol):
    empty = get_empty_cells(board)

    if not empty:
        return None

    if difficulty == "Easy":
        return random.choice(empty)

    best = best_ai_move(board, player_moves, ai_symbol, player_symbol)

    if difficulty == "Medium":
        if random.random() < 0.5:
            return random.choice(empty)
        return best

    if difficulty == "Hard":
        return best

    return random.choice(empty)


def run_tic_tac_toe(difficulty="Easy", player_turn="First"):
    screen = pygame.display.get_surface()

    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    init_fonts()
    clock = pygame.time.Clock()

    back_button = Button(35, 45, 150, 60, "Back")
    restart_button = Button(WIDTH - 190, 45, 150, 60, "Restart")

    board = [
        ["", "", ""],
        ["", "", ""],
        ["", "", ""]
    ]

    player_moves = {
        "O": [],
        "X": []
    }

    if player_turn == "First":
        player_symbol = "O"
        ai_symbol = "X"
        current_turn = "player"
    else:
        player_symbol = "X"
        ai_symbol = "O"
        current_turn = "ai"

    winner = None
    game_over = False

    while True:
        clock.tick(FPS)

        draw_background(screen)

        draw_text(screen, "TIC TAC TOE", FONT_TITLE, ACCENT, WIDTH // 2, 65)
        draw_text(
            screen,
            f"{difficulty}  |  Kamu: {player_symbol}  |  AI: {ai_symbol}",
            FONT_TEXT,
            MUTED,
            WIDTH // 2,
            118
        )

        draw_text(screen, "PLAYER", FONT_TEXT, TEXT, 300, 165)
        draw_text(screen, "Manual Board", FONT_SMALL, MUTED, 300, 195)

        draw_text(screen, "RIVAL", FONT_TEXT, TEXT, 800, 165)
        draw_text(screen, "Minimax AI", FONT_SMALL, MUTED, 800, 195)

        draw_board(screen, board, player_moves)

        back_button.draw(screen)
        restart_button.draw(screen)

        if game_over:
            if winner == player_symbol:
                message = "KAMU MENANG!"
            elif winner == ai_symbol:
                message = "AI MENANG!"
            else:
                message = "DRAW!"

            draw_text(screen, message, FONT_BIG, TEXT, WIDTH // 2, 650)

        else:
            if current_turn == "player":
                draw_text(screen, "Giliran Kamu", FONT_TEXT, TEXT, WIDTH // 2, 650)
            else:
                draw_text(screen, "Giliran AI...", FONT_TEXT, TEXT, WIDTH // 2, 650)

            draw_text(
                screen,
                "Simbol yang redup akan hilang saat simbol yang sama dipakai lagi",
                FONT_SMALL,
                MUTED,
                WIDTH // 2,
                680
            )

        pygame.display.flip()

        if current_turn == "ai" and not game_over:
            pygame.time.delay(450)

            move = get_ai_move(board, player_moves, difficulty, ai_symbol, player_symbol)

            if move:
                make_move(board, player_moves, move[0], move[1], ai_symbol)

            winner = check_winner(board)

            if winner:
                game_over = True
            else:
                current_turn = "player"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if back_button.clicked(event):
                return

            if restart_button.clicked(event):
                board = [
                    ["", "", ""],
                    ["", "", ""],
                    ["", "", ""]
                ]

                player_moves = {
                    "O": [],
                    "X": []
                }

                winner = None
                game_over = False

                if player_turn == "First":
                    current_turn = "player"
                else:
                    current_turn = "ai"

            if current_turn == "player" and not game_over:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    cell = get_cell_from_mouse(event.pos)

                    if cell:
                        row, col = cell

                        if make_move(board, player_moves, row, col, player_symbol):
                            winner = check_winner(board)

                            if winner:
                                game_over = True
                            else:
                                current_turn = "ai"

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tic Tac Toe Test")
    run_tic_tac_toe("Medium", "First")