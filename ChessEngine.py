"""
This module defines the ChessGame and Move classes, which handle:
- Storing all details about the current state of the chess game.
- Identifying valid moves at the current state.
- Maintaining a history of moves.
- Managing special moves such as castling, en passant, and pawn promotion.
"""

class ChessGame:
    def __init__(self):
        """
        Initialize the game state. Sets up the board, move functions, and game state variables.
        """
        # 8x8 2D list representing the chessboard. Each element is a 2-character string:
        # - First character: 'w' for white, 'b' for black.
        # - Second character: Piece type ('R', 'N', 'B', 'Q', 'K', 'P').
        self.chessboard = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        # Dictionary mapping piece types to their respective move functions.
        self.move_handlers = {
            "P": self.get_pawn_moves,
            "R": self.get_rook_moves,
            "N": self.get_knight_moves,
            "B": self.get_bishop_moves,
            "Q": self.get_queen_moves,
            "K": self.get_king_moves
        }
        self.is_white_turn = True  # True if it's white's turn, False if black's.
        self.move_history = []  # List to store all moves made in the game.
        self.white_king_pos = (7, 4)  # Initial position of the white king.
        self.black_king_pos = (0, 4)  # Initial position of the black king.
        self.is_checkmate = False  # True if the current player is in checkmate.
        self.is_stalemate = False  # True if the game is in a stalemate.
        self.in_check = False  # True if the current player is in check.
        self.pinned_pieces = []  # List of pinned pieces and their directions.
        self.attackers = []  # List of squares where enemy pieces are attacking the king.
        self.enpassant_possible = ()  # Coordinates for en passant capture.
        self.enpassant_log = [self.enpassant_possible]  # Log of en passant possibilities.
        # Castle rights for both sides (kingside and queenside).
        self.current_castle_rights = CastlePermissions(True, True, True, True)
        self.castle_rights_log = [CastlePermissions(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                                    self.current_castle_rights.wqs, self.current_castle_rights.bqs)]

    def execute_move(self, move):
        """
        Execute a move on the board.
        :param move: The move to execute.
        """
        self.chessboard[move.start_row][move.start_col] = "--"  # Clear the starting square.
        self.chessboard[move.end_row][move.end_col] = move.piece_moved  # Place the piece on the end square.
        self.move_history.append(move)  # Log the move.
        self.is_white_turn = not self.is_white_turn  # Switch turns.
        # Update king's position if moved.
        if move.piece_moved == "wK":
            self.white_king_pos = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_pos = (move.end_row, move.end_col)

        # Handle pawn promotion.
        if move.is_pawn_promotion:
            self.chessboard[move.end_row][move.end_col] = move.piece_moved[0] + "Q"  # Promote to queen.

        # Handle en passant.
        if move.is_enpassant_move:
            self.chessboard[move.start_row][move.end_col] = "--"  # Capture the pawn.

        # Update en passant possibility.
        if move.piece_moved[1] == "P" and abs(move.start_row - move.end_row) == 2:  # 2-square pawn advance.
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # Handle castling.
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # Kingside castle.
                self.chessboard[move.end_row][move.end_col - 1] = self.chessboard[move.end_row][move.end_col + 1]  # Move rook.
                self.chessboard[move.end_row][move.end_col + 1] = "--"  # Clear old rook position.
            else:  # Queenside castle.
                self.chessboard[move.end_row][move.end_col + 1] = self.chessboard[move.end_row][move.end_col - 2]  # Move rook.
                self.chessboard[move.end_row][move.end_col - 2] = "--"  # Clear old rook position.

        self.enpassant_log.append(self.enpassant_possible)

        # Update castling rights.
        self.update_castle_permissions(move)
        self.castle_rights_log.append(CastlePermissions(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                                        self.current_castle_rights.wqs, self.current_castle_rights.bqs))

    def undo_move(self):
        """
        Undo the last move made.
        """
        if len(self.move_history) != 0:  # Ensure there is a move to undo.
            move = self.move_history.pop()
            self.chessboard[move.start_row][move.start_col] = move.piece_moved  # Restore the moved piece.
            self.chessboard[move.end_row][move.end_col] = move.piece_captured  # Restore the captured piece.
            self.is_white_turn = not self.is_white_turn  # Switch turns back.
            # Restore king's position if moved.
            if move.piece_moved == "wK":
                self.white_king_pos = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_pos = (move.start_row, move.start_col)

            # Undo en passant.
            if move.is_enpassant_move:
                self.chessboard[move.end_row][move.end_col] = "--"  # Leave the landing square blank.
                self.chessboard[move.start_row][move.end_col] = move.piece_captured  # Restore the captured pawn.

            self.enpassant_log.pop()
            self.enpassant_possible = self.enpassant_log[-1]

            # Undo castling rights.
            self.castle_rights_log.pop()
            self.current_castle_rights = self.castle_rights_log[-1]

            # Undo castling move.
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # Kingside.
                    self.chessboard[move.end_row][move.end_col + 1] = self.chessboard[move.end_row][move.end_col - 1]
                    self.chessboard[move.end_row][move.end_col - 1] = "--"
                else:  # Queenside.
                    self.chessboard[move.end_row][move.end_col - 2] = self.chessboard[move.end_row][move.end_col + 1]
                    self.chessboard[move.end_row][move.end_col + 1] = "--"

            self.is_checkmate = False
            self.is_stalemate = False

    def update_castle_permissions(self, move):
        """
        Update castling rights based on the move made.
        :param move: The move that was made.
        """
        if move.piece_captured == "wR":
            if move.end_col == 0:  # Left rook.
                self.current_castle_rights.wqs = False
            elif move.end_col == 7:  # Right rook.
                self.current_castle_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # Left rook.
                self.current_castle_rights.bqs = False
            elif move.end_col == 7:  # Right rook.
                self.current_castle_rights.bks = False

        if move.piece_moved == 'wK':
            self.current_castle_rights.wqs = False
            self.current_castle_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castle_rights.bqs = False
            self.current_castle_rights.bks = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # Left rook.
                    self.current_castle_rights.wqs = False
                elif move.start_col == 7:  # Right rook.
                    self.current_castle_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # Left rook.
                    self.current_castle_rights.bqs = False
                elif move.start_col == 7:  # Right rook.
                    self.current_castle_rights.bks = False

    def get_valid_moves(self):
        """
        Get all valid moves considering checks, pins, and special moves.
        :return: A list of valid moves.
        """
        temp_castle_rights = CastlePermissions(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                               self.current_castle_rights.wqs, self.current_castle_rights.bqs)
        moves = []
        self.in_check, self.pinned_pieces, self.attackers = self.check_for_pins_and_checks()

        if self.is_white_turn:
            king_row, king_col = self.white_king_pos
        else:
            king_row, king_col = self.black_king_pos

        if self.in_check:
            if len(self.attackers) == 1:  # Only one check, block or move the king.
                moves = self.get_all_possible_moves()
                check = self.attackers[0]
                check_row, check_col, direction_row, direction_col = check
                piece_checking = self.chessboard[check_row][check_col]
                valid_squares = []

                if piece_checking[1] == "N":  # Knight checks must be captured or the king must move.
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + direction_row * i, king_col + direction_col * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break

                # Remove moves that don't block the check or move the king.
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved[1] != "K":
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares:
                            moves.remove(moves[i])
            else:  # Double check, king must move.
                self.get_king_moves(king_row, king_col, moves)
        else:  # Not in check, all moves are valid.
            moves = self.get_all_possible_moves()
            if self.is_white_turn:
                self.get_castle_moves(self.white_king_pos[0], self.white_king_pos[1], moves)
            else:
                self.get_castle_moves(self.black_king_pos[0], self.black_king_pos[1], moves)

        if len(moves) == 0:
            if self.in_check():
                self.is_checkmate = True
            else:
                self.is_stalemate = True
        else:
            self.is_checkmate = False
            self.is_stalemate = False

        self.current_castle_rights = temp_castle_rights
        return moves

    def in_check(self):
        """
        Determine if the current player is in check.
        :return: True if in check, False otherwise.
        """
        if self.is_white_turn:
            return self.is_square_attacked(self.white_king_pos[0], self.white_king_pos[1])
        else:
            return self.is_square_attacked(self.black_king_pos[0], self.black_king_pos[1])

    def is_square_attacked(self, row, col):
        """
        Determine if the square at (row, col) is under attack.
        :param row: The row of the square.
        :param col: The column of the square.
        :return: True if under attack, False otherwise.
        """
        self.is_white_turn = not self.is_white_turn  # Switch to opponent's perspective.
        opponent_moves = self.get_all_possible_moves()
        self.is_white_turn = not self.is_white_turn  # Switch back.
        for move in opponent_moves:
            if move.end_row == row and move.end_col == col:
                return True
        return False

    def get_all_possible_moves(self):
        """
        Get all possible moves without considering checks.
        :return: A list of all possible moves.
        """
        moves = []
        for row in range(len(self.chessboard)):
            for col in range(len(self.chessboard[row])):
                turn = self.chessboard[row][col][0]
                if (turn == "w" and self.is_white_turn) or (turn == "b" and not self.is_white_turn):
                    piece = self.chessboard[row][col][1]
                    self.move_handlers[piece](row, col, moves)  # Call the appropriate move function.
        return moves

    def check_for_pins_and_checks(self):
        """
        Check for pins and checks on the current player's king.
        :return: A tuple (in_check, pins, checks).
        """
        pins = []  # Squares pinned and the direction they are pinned from.
        checks = []  # Squares where enemy pieces are attacking the king.
        in_check = False
        if self.is_white_turn:
            enemy_color = "b"
            ally_color = "w"
            start_row, start_col = self.white_king_pos
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row, start_col = self.black_king_pos

        # Check outward from the king for pins and checks.
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # Reset possible pin.
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.chessboard[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # First allied piece could be pinned.
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  # Second allied piece, no pin or check in this direction.
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        # Check if the enemy piece can attack the king.
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "P" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():  # No piece blocking, so it's a check.
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  # Piece blocking, so it's a pin.
                                pins.append(possible_pin)
                                break
                        else:  # Enemy piece not applying a check.
                            break
                else:  # Off the board.
                    break

        # Check for knight checks.
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.chessboard[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # Enemy knight attacking the king.
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    def get_pawn_moves(self, row, col, moves):
        """
        Get all pawn moves for the pawn located at (row, col) and add them to the moves list.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == row and self.pinned_pieces[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pinned_pieces[i][2], self.pinned_pieces[i][3])
                self.pinned_pieces.remove(self.pinned_pieces[i])
                break

        if self.is_white_turn:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_pos
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_pos

        # 1-square pawn advance.
        if self.chessboard[row + move_amount][col] == "--":
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.chessboard))
                # 2-square pawn advance.
                if row == start_row and self.chessboard[row + 2 * move_amount][col] == "--":
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.chessboard))
        # Captures to the left.
        if col - 1 >= 0:
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.chessboard[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.chessboard))
                if (row + move_amount, col - 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # King is left of the pawn.
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # King is right of the pawn.
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.chessboard[row][i] != "--":  # Some piece is blocking.
                                blocking_piece = True
                        for i in outside_range:
                            square = self.chessboard[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.chessboard, is_enpassant_move=True))
        # Captures to the right.
        if col + 1 <= 7:
            if not piece_pinned or pin_direction == (move_amount, 1):
                if self.chessboard[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.chessboard))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # King is left of the pawn.
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  # King is right of the pawn.
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.chessboard[row][i] != "--":  # Some piece is blocking.
                                blocking_piece = True
                        for i in outside_range:
                            square = self.chessboard[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.chessboard, is_enpassant_move=True))

    def get_rook_moves(self, row, col, moves):
        """
        Get all rook moves for the rook located at (row, col) and add them to the moves list.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == row and self.pinned_pieces[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pinned_pieces[i][2], self.pinned_pieces[i][3])
                if self.chessboard[row][col][1] != "Q":  # Can't remove queen from pin on rook moves.
                    self.pinned_pieces.remove(self.pinned_pieces[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # Up, left, down, right.
        enemy_color = "b" if self.is_white_turn else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    if not piece_pinned or pin_direction == direction or pin_direction == (-direction[0], -direction[1]):
                        end_piece = self.chessboard[end_row][end_col]
                        if end_piece == "--":  # Empty space is valid.
                            moves.append(Move((row, col), (end_row, end_col), self.chessboard))
                        elif end_piece[0] == enemy_color:  # Capture enemy piece.
                            moves.append(Move((row, col), (end_row, end_col), self.chessboard))
                            break
                        else:  # Friendly piece.
                            break
                else:  # Off the board.
                    break

    def get_knight_moves(self, row, col, moves):
        """
        Get all knight moves for the knight located at (row, col) and add them to the moves list.
        """
        piece_pinned = False
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == row and self.pinned_pieces[i][1] == col:
                piece_pinned = True
                self.pinned_pieces.remove(self.pinned_pieces[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        ally_color = "w" if self.is_white_turn else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.chessboard[end_row][end_col]
                    if end_piece[0] != ally_color:  # Not an ally piece (empty or enemy).
                        moves.append(Move((row, col), (end_row, end_col), self.chessboard))

    def get_bishop_moves(self, row, col, moves):
        """
        Get all bishop moves for the bishop located at (row, col) and add them to the moves list.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == row and self.pinned_pieces[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pinned_pieces[i][2], self.pinned_pieces[i][3])
                self.pinned_pieces.remove(self.pinned_pieces[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # Diagonals.
        enemy_color = "b" if self.is_white_turn else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    if not piece_pinned or pin_direction == direction or pin_direction == (-direction[0], -direction[1]):
                        end_piece = self.chessboard[end_row][end_col]
                        if end_piece == "--":  # Empty space is valid.
                            moves.append(Move((row, col), (end_row, end_col), self.chessboard))
                        elif end_piece[0] == enemy_color:  # Capture enemy piece.
                            moves.append(Move((row, col), (end_row, end_col), self.chessboard))
                            break
                        else:  # Friendly piece.
                            break
                else:  # Off the board.
                    break

    def get_queen_moves(self, row, col, moves):
        """
        Get all queen moves for the queen located at (row, col) and add them to the moves list.
        """
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)

    def get_king_moves(self, row, col, moves):
        """
        Get all king moves for the king located at (row, col) and add them to the moves list.
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.is_white_turn else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.chessboard[end_row][end_col]
                if end_piece[0] != ally_color:  # Not an ally piece (empty or enemy).
                    # Place king on the end square and check for checks.
                    if ally_color == "w":
                        self.white_king_pos = (end_row, end_col)
                    else:
                        self.black_king_pos = (end_row, end_col)
                    in_check, pins, checks = self.check_for_pins_and_checks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.chessboard))
                    # Place king back on the original square.
                    if ally_color == "w":
                        self.white_king_pos = (row, col)
                    else:
                        self.black_king_pos = (row, col)

    def get_castle_moves(self, row, col, moves):
        """
        Get all valid castle moves for the king at (row, col) and add them to the moves list.
        """
        if self.is_square_attacked(row, col):
            return  # Can't castle while in check.
        if (self.is_white_turn and self.current_castle_rights.wks) or (
                not self.is_white_turn and self.current_castle_rights.bks):
            self.get_kingside_castle_moves(row, col, moves)
        if (self.is_white_turn and self.current_castle_rights.wqs) or (
                not self.is_white_turn and self.current_castle_rights.bqs):
            self.get_queenside_castle_moves(row, col, moves)

    def get_kingside_castle_moves(self, row, col, moves):
        """
        Get kingside castle moves for the king at (row, col) and add them to the moves list.
        """
        if self.chessboard[row][col + 1] == "--" and self.chessboard[row][col + 2] == "--":
            if not self.is_square_attacked(row, col + 1) and not self.is_square_attacked(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.chessboard, is_castle_move=True))

    def get_queenside_castle_moves(self, row, col, moves):
        """
        Get queenside castle moves for the king at (row, col) and add them to the moves list.
        """
        if self.chessboard[row][col - 1] == "--" and self.chessboard[row][col - 2] == "--" and self.chessboard[row][col - 3] == "--":
            if not self.is_square_attacked(row, col - 1) and not self.is_square_attacked(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.chessboard, is_castle_move=True))


class CastlePermissions:
    """
    Class to store castling rights for both sides.
    """
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks  # White kingside.
        self.bks = bks  # Black kingside.
        self.wqs = wqs  # White queenside.
        self.bqs = bqs  # Black queenside.


class Move:
    """
    Class to represent a move on the chessboard.
    """
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        # Pawn promotion.
        self.is_pawn_promotion = (self.piece_moved == "wP" and self.end_row == 0) or (
                self.piece_moved == "bP" and self.end_row == 7)
        # En passant.
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wP" if self.piece_moved == "bP" else "bP"
        # Castle move.
        self.is_castle_move = is_castle_move
        # Capture move.
        self.is_capture = self.piece_captured != "--"
        # Unique move ID.
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        """
        Override the equals method to compare moves by their moveID.
        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def get_chess_notation(self):
        """
        Get the chess notation for the move.
        """
        if self.is_pawn_promotion:
            return self.get_rank_file(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:
            return self.get_rank_file(self.start_row, self.start_col)[0] + "x" + self.get_rank_file(self.end_row,
                                                                                                    self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "P":
                return self.get_rank_file(self.start_row, self.start_col)[0] + "x" + self.get_rank_file(self.end_row,
                                                                                                        self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.get_rank_file(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "P":
                return self.get_rank_file(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, row, col):
        """
        Convert row and column to chess notation (e.g., (0, 0) -> "a8").
        """
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        """
        Override the string representation of the move.
        """
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.get_rank_file(self.end_row, self.end_col)

        if self.piece_moved[1] == "P":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square