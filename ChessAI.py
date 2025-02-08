"""
This module handles the AI's decision-making process for selecting moves in a chess game.
It uses a combination of piece values, positional scoring, and the minimax algorithm with alpha-beta pruning
to determine the optimal move.
"""

import random

# Dictionary defining the base score for each chess piece.
# The king (K) has a score of 0 because its value is implicit in the game's outcome.
piece_score = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "P": 1}

# Positional score tables for each piece type. These tables assign a score to each square on the board
# based on how advantageous it is for the piece to be on that square. Higher scores indicate better positions.

# Knight positional scores
knight_scores = [[0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0],
                 [0.1, 0.3, 0.5, 0.5, 0.5, 0.5, 0.3, 0.1],
                 [0.2, 0.5, 0.6, 0.65, 0.65, 0.6, 0.5, 0.2],
                 [0.2, 0.55, 0.65, 0.7, 0.7, 0.65, 0.55, 0.2],
                 [0.2, 0.5, 0.65, 0.7, 0.7, 0.65, 0.5, 0.2],
                 [0.2, 0.55, 0.6, 0.65, 0.65, 0.6, 0.55, 0.2],
                 [0.1, 0.3, 0.5, 0.55, 0.55, 0.5, 0.3, 0.1],
                 [0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0]]

# Bishop positional scores
bishop_scores = [[0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
                 [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
                 [0.2, 0.4, 0.5, 0.6, 0.6, 0.5, 0.4, 0.2],
                 [0.2, 0.5, 0.5, 0.6, 0.6, 0.5, 0.5, 0.2],
                 [0.2, 0.4, 0.6, 0.6, 0.6, 0.6, 0.4, 0.2],
                 [0.2, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.2],
                 [0.2, 0.5, 0.4, 0.4, 0.4, 0.4, 0.5, 0.2],
                 [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0]]

# Rook positional scores
rook_scores = [[0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
               [0.5, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.5],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.25, 0.25, 0.25, 0.5, 0.5, 0.25, 0.25, 0.25]]

# Queen positional scores
queen_scores = [[0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0],
                [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
                [0.2, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
                [0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
                [0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
                [0.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
                [0.2, 0.4, 0.5, 0.4, 0.4, 0.4, 0.4, 0.2],
                [0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0]]

# Pawn positional scores
pawn_scores = [[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
               [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
               [0.3, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0.3],
               [0.25, 0.25, 0.3, 0.45, 0.45, 0.3, 0.25, 0.25],
               [0.2, 0.2, 0.2, 0.4, 0.4, 0.2, 0.2, 0.2],
               [0.25, 0.15, 0.1, 0.2, 0.2, 0.1, 0.15, 0.25],
               [0.25, 0.3, 0.3, 0.0, 0.0, 0.3, 0.3, 0.25],
               [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]]

# Dictionary mapping each piece to its positional score table.
# The tables for black pieces are reversed to reflect the board's symmetry.
piece_position_scores = {"wN": knight_scores,
                         "bN": knight_scores[::-1],
                         "wB": bishop_scores,
                         "bB": bishop_scores[::-1],
                         "wQ": queen_scores,
                         "bQ": queen_scores[::-1],
                         "wR": rook_scores,
                         "bR": rook_scores[::-1],
                         "wP": pawn_scores,
                         "bP": pawn_scores[::-1]}

# Constants for scoring game outcomes
WIN_SCORE = 1000  # Score assigned for a winning position
DRAW_SCORE = 0    # Score assigned for a draw
SEARCH_DEPTH = 3  # Depth of the search tree for the minimax algorithm


def calculateOptimalMove(game_state, valid_moves, queue_result):
    """
    Determines the optimal move for the AI using the minimax algorithm with alpha-beta pruning.
    The function evaluates all possible moves up to a certain depth and selects the best one.
    
    :param game_state: The current state of the game.
    :param valid_moves: A list of valid moves available to the AI.
    :param queue_result: A queue to store the result of the best move.
    """
    global best_move
    best_move = None
    random.shuffle(valid_moves)  # Randomize moves to introduce variation and avoid predictability
    evaluateMoves(game_state, valid_moves, SEARCH_DEPTH, -WIN_SCORE, WIN_SCORE, 1 if game_state.is_white_turn else -1)
    queue_result.put(best_move)


def evaluateMoves(game_state, moves, depth, alpha, beta, turn_factor):
    """
    Recursive function to evaluate moves using the minimax algorithm with alpha-beta pruning.
    It returns the best score for the current player, considering the opponent's best response.
    
    :param game_state: The current state of the game.
    :param moves: A list of valid moves to evaluate.
    :param depth: The current depth of the search tree.
    :param alpha: The best score that the maximizing player can guarantee.
    :param beta: The best score that the minimizing player can guarantee.
    :param turn_factor: 1 for white's turn, -1 for black's turn.
    :return: The best score for the current player.
    """
    global best_move
    if depth == 0:  # Base case: evaluate the board at the leaf node
        return turn_factor * score_board(game_state)

    score_max = -WIN_SCORE  # Initialize the maximum score to the lowest possible value
    for current_move in moves:
        game_state.execute_move(current_move)  # Make the move on the board
        subsequent_moves = game_state.get_valid_moves()  # Get valid moves for the opponent
        # Recursively evaluate the opponent's moves
        score = -evaluateMoves(game_state, subsequent_moves, depth - 1, -beta, -alpha, -turn_factor)
        if score > score_max:
            score_max = score
            if depth == SEARCH_DEPTH:  # If at the root level, update the best move
                best_move = current_move
        game_state.undo_move()  # Undo the move to restore the board state

        # Update alpha and perform alpha-beta pruning
        if score_max > alpha:
            alpha = score_max
        if alpha >= beta:
            break  # Prune the branch if the current move is worse than the best found so far
    return score_max


def findRandomMove(valid_moves):
    """
    Selects and returns a random move from the list of valid moves.
    This function is used for testing or when the AI needs to make a random move.
    
    :param valid_moves: A list of valid moves.
    :return: A randomly selected move.
    """
    return random.choice(valid_moves)


def score_board(game_state):
    """
    Evaluates the current board state and returns a score.
    A positive score favors white, while a negative score favors black.
    
    :param game_state: The current state of the game.
    :return: The score of the board.
    """
    # Check for game-ending conditions
    if game_state.is_checkmate:
        if game_state.is_white_turn:
            return -WIN_SCORE  # Black wins
        else:
            return WIN_SCORE  # White wins
    elif game_state.is_stalemate:
        return DRAW_SCORE  # The game is a draw

    # Initialize the score
    score = 0

    # Iterate through the board to calculate the score based on piece values and positions
    for row in range(len(game_state.chessboard)):
        for col in range(len(game_state.chessboard[row])):
            piece = game_state.chessboard[row][col]
            if piece != "--":  # If there's a piece on the current square
                piece_position_score = 0
                if piece[1] != "K":  # Exclude the king from position scoring
                    piece_position_score = piece_position_scores[piece][row][col]
                if piece[0] == "w":  # White piece
                    score += piece_score[piece[1]] + piece_position_score
                elif piece[0] == "b":  # Black piece
                    score -= piece_score[piece[1]] + piece_position_score

    return score