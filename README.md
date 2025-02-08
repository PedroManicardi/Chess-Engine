# Chess Engine 
This is a simple chess engine built in Python. It includes a graphical user interface for playing chess against an AI. The engine follows standard chess rules and allows move validation, piece movement, and game logic implementation.

## How to Run
To start the chess engine, simply run the following command in your terminal or command prompt:

```sh
python ChessMain.py
```

## AI Algorithm
The AI in this chess engine uses the **Minimax algorithm with Alpha-Beta Pruning** to determine the best possible move by simulating potential future moves and counter-moves. Below is an overview of the key functions:

- **`calculateOptimalMove(game_state, valid_moves, queue_result)`**:  
  Initiates the AI's decision-making process by randomizing valid moves to introduce variation and calling `evaluateMoves` to determine the optimal move.
- **`evaluateMoves(game_state, moves, depth, alpha, beta, turn_factor)`**:  
  Implements the Minimax algorithm with Alpha-Beta Pruning to recursively evaluate moves. It assigns scores to board positions and selects the move that maximizes the AI’s advantage while minimizing the opponent’s best possible response.
- **`findRandomMove(valid_moves)`**:  
  Selects a random move, mainly used for testing or as a fallback.
- **`score_board(game_state)`**:  
  Evaluates the board state based on piece values, positioning, and game-ending conditions.

### Alpha-Beta Pruning
Alpha-beta pruning is an optimization for the Minimax algorithm that significantly reduces the number of board positions the AI needs to evaluate. It does this by maintaining two values:  

- **Alpha (α)**: The best score the maximizing player (AI) can guarantee.  
- **Beta (β)**: The best score the minimizing player (opponent) can guarantee.  

During the recursive search, if the algorithm finds a move that is worse than a previously examined option, it **"prunes"** that branch—meaning it stops evaluating that path because it will not be chosen.

This technique allows the AI to **ignore unnecessary calculations** and **speed up decision-making**, making it more efficient when analyzing deep positions.

