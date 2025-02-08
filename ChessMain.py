import pygame as p
import ChessEngine, ChessAI
import sys
from multiprocessing import Process, Queue

# Constants for the game window and board dimensions
BOARD_WIDTH = BOARD_HEIGHT = 512  # Size of the chessboard
MOVE_LOG_PANEL_WIDTH = 250  # Width of the move log panel
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT  # Height of the move log panel
DIMENSION = 8  # Number of squares per row/column
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION  # Size of each square
MAX_FPS = 15  # Maximum frames per second for the game
IMAGES = {}  # Dictionary to store piece images


def loadImages():
    """
    Load and scale images for all chess pieces.
    This function is called once at the start of the game.
    """
    pieces = ['wP', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bP', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        # Load each piece image and scale it to fit the square size
        IMAGES[piece] = p.transform.scale(p.image.load("imgs/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))


def main():
    """
    The main driver for the chess game.
    Handles user input, updates the game state, and renders the graphics.
    """
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    game_state = ChessEngine.ChessGame()  # Initialize the game state
    valid_moves = game_state.get_valid_moves()  # Get valid moves for the current state
    move_made = False  # Flag to track if a move has been made
    animate = False  # Flag to determine if a move should be animated
    loadImages()  # Load piece images
    running = True
    square_selected = ()  # Track the last square selected by the user
    player_clicks = []  # Track player clicks (two tuples: start and end positions)
    game_over = False  # Flag to track if the game is over
    ai_thinking = False  # Flag to track if the AI is calculating a move
    move_undone = False  # Flag to track if a move has been undone
    move_finder_process = None  # Process for AI move calculation
    move_log_font = p.font.SysFont("Arial", 14, False, False)  # Font for the move log
    player_one = True  # True if a human is playing white
    player_two = False  # True if a human is playing black
    board_state_counts = {}  # Dictionary to track board states for detecting repetition

    while running:
        human_turn = (game_state.is_white_turn  and player_one) or (not game_state.is_white_turn  and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            # Mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # Get mouse position
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:  # Deselect if the same square is clicked twice
                        square_selected = ()
                        player_clicks = []
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  # Add the clicked square to the list
                    if len(player_clicks) == 2 and human_turn:  # After the second click
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.chessboard)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.execute_move(valid_moves[i])  # Make the move
                                move_made = True
                                animate = True
                                square_selected = ()  # Reset clicks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]

            # Key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # Undo move when 'z' is pressed
                    game_state.undo_move()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == p.K_r:  # Reset the game when 'r' is pressed
                    game_state = ChessEngine.ChessGame()
                    valid_moves = game_state.get_valid_moves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # AI move finder
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # Queue to pass data between threads
                move_finder_process = Process(target=ChessAI.calculateOptimalMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)  # Fallback to a random move
                game_state.execute_move(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            # Update board state count for repetition detection
            board_state = str(game_state.chessboard) + str(game_state.is_white_turn ) + str(game_state.current_castle_rights)
            if board_state in board_state_counts:
                board_state_counts[board_state] += 1
            else:
                board_state_counts[board_state] = 1

            # Check for draw by repetition
            if board_state_counts[board_state] == 3:
                game_over = True
                drawEndGameText(screen, "Draw by repetition")

            if animate:
                animateMove(game_state.move_history[-1], screen, game_state.chessboard, clock)
            valid_moves = game_state.get_valid_moves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)
        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.is_checkmate:
            game_over = True
            if game_state.is_white_turn :
                drawEndGameText(screen, "Black wins by checkmate")
            else:
                drawEndGameText(screen, "White wins by checkmate")

        elif game_state.is_stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen, game_state, valid_moves, square_selected):
    """
    Draw the current game state, including the board, pieces, and highlights.
    """
    drawBoard(screen)  # Draw the chessboard squares
    highlightSquares(screen, game_state, valid_moves, square_selected)  # Highlight selected squares and valid moves
    drawPieces(screen, game_state.chessboard)  # Draw the pieces on the board


def drawBoard(screen):
    """
    Draw the squares of the chessboard.
    """
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Highlight the selected square and valid moves for the selected piece.
    """
    if len(game_state.move_history) > 0:
        last_move = game_state.move_history[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.chessboard[row][col][0] == ('w' if game_state.is_white_turn  else 'b'):
            # Highlight the selected square
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # Highlight valid moves
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))


def drawPieces(screen, board):
    """
    Draw the pieces on the board.
    """
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def drawMoveLog(screen, game_state, font):
    """
    Draw the move log on the side panel.
    """
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_history
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def drawEndGameText(screen, text):
    """
    Display the endgame text (e.g., checkmate or stalemate).
    """
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
    """
    Animate a move on the board.
    """
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10  # Frames to move one square
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # Erase the piece from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # Draw the captured piece
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # Draw the moving piece
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()