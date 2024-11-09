import random
from PushBattle import Game, PLAYER1, PLAYER2, EMPTY, BOARD_SIZE, NUM_PIECES, _torus
import numpy as np
from typing import List, Tuple, Dict
import time

class SmartAgent:
    def __init__(self, player=PLAYER2):
        self.player = player
        self.opponent = PLAYER2 if player == PLAYER1 else PLAYER1
        
        # Simplified weights focusing on immediate threats and pushing opportunities
        self.weights = {
            'winning_threat': 1000.0,  # Immediate winning opportunities
            'blocking_threat': 800.0,  # Blocking opponent's wins
            'push_threat': 500.0,      # Pushing that creates winning opportunities
            'alignment': 100.0,        # Aligned pieces
            'protection': 50.0,        # Protected pieces
        }

    def get_possible_moves(self, game) -> List[tuple]:
        """Returns list of all possible moves in current state."""
        moves = []
        current_pieces = game.p1_pieces if game.current_player == PLAYER1 else game.p2_pieces
        
        if current_pieces < NUM_PIECES:
            # placement moves
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if game.board[r][c] == EMPTY:
                        moves.append((r, c))
        else:
            # movement moves
            for r0 in range(BOARD_SIZE):
                for c0 in range(BOARD_SIZE):
                    if game.board[r0][c0] == game.current_player:
                        for r1 in range(BOARD_SIZE):
                            for c1 in range(BOARD_SIZE):
                                if game.board[r1][c1] == EMPTY:
                                    moves.append((r0, c0, r1, c1))
        return moves

    def simulate_push_effects(self, board: List[List[int]], r: int, c: int) -> List[List[int]]:
        """Simulate pushing effects of placing/moving a piece to position (r,c)"""
        new_board = [row.copy() for row in board]
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            push_r, push_c = _torus(r + dr, c + dc)
            if new_board[push_r][push_c] != EMPTY:
                # There's a piece to push
                dest_r, dest_c = _torus(push_r + dr, push_c + dc)
                if new_board[dest_r][dest_c] == EMPTY:
                    # Can push to empty space
                    new_board[dest_r][dest_c] = new_board[push_r][push_c]
                    new_board[push_r][push_c] = EMPTY
                
        return new_board

    def check_winning_line(self, board: List[List[int]], player: int) -> bool:
        """Check if player has won"""
        # Horizontal
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE-2):
                if all(board[r][c+i] == player for i in range(3)):
                    return True

        # Vertical
        for r in range(BOARD_SIZE-2):
            for c in range(BOARD_SIZE):
                if all(board[r+i][c] == player for i in range(3)):
                    return True

        # Diagonal (top-left to bottom-right)
        for r in range(BOARD_SIZE-2):
            for c in range(BOARD_SIZE-2):
                if all(board[r+i][c+i] == player for i in range(3)):
                    return True

        # Diagonal (top-right to bottom-left)
        for r in range(BOARD_SIZE-2):
            for c in range(2, BOARD_SIZE):
                if all(board[r+i][c-i] == player for i in range(3)):
                    return True

        return False

    def count_two_in_row(self, board: List[List[int]], player: int) -> int:
        """Count number of two-in-a-row configurations with an empty third space"""
        count = 0
        # Horizontal
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE-2):
                window = [board[r][c+i] for i in range(3)]
                if window.count(player) == 2 and window.count(EMPTY) == 1:
                    count += 1

        # Vertical
        for r in range(BOARD_SIZE-2):
            for c in range(BOARD_SIZE):
                window = [board[r+i][c] for i in range(3)]
                if window.count(player) == 2 and window.count(EMPTY) == 1:
                    count += 1

        # Diagonals
        for r in range(BOARD_SIZE-2):
            for c in range(BOARD_SIZE-2):
                # Top-left to bottom-right
                window = [board[r+i][c+i] for i in range(3)]
                if window.count(player) == 2 and window.count(EMPTY) == 1:
                    count += 1
                
                # Top-right to bottom-left (if valid position)
                if c >= 2:
                    window = [board[r+i][c-i] for i in range(3)]
                    if window.count(player) == 2 and window.count(EMPTY) == 1:
                        count += 1

        return count

    def evaluate_move(self, game: Game, move: tuple) -> float:
        """Evaluate a single move considering pushing effects"""
        # Create board copy and simulate move
        board_copy = [row.copy() for row in game.board]
        
        if len(move) == 2:  # Placement move
            r, c = move
            board_copy[r][c] = game.current_player
        else:  # Movement move
            r0, c0, r1, c1 = move
            board_copy[r1][c1] = board_copy[r0][c0]
            board_copy[r0][c0] = EMPTY
            r, c = r1, c1

        # Simulate pushing effects
        final_board = self.simulate_push_effects(board_copy, r, c)
        
        score = 0.0
        
        # Check for immediate win
        if self.check_winning_line(final_board, self.player):
            return float('inf')
            
        # Check for opponent's immediate win
        if self.check_winning_line(final_board, self.opponent):
            return float('-inf')
            
        # Count two-in-a-row formations
        score += self.weights['alignment'] * self.count_two_in_row(final_board, self.player)
        score -= self.weights['alignment'] * self.count_two_in_row(final_board, self.opponent)
        
        # Check if move blocks opponent's two-in-row
        opponent_before = self.count_two_in_row(game.board, self.opponent)
        opponent_after = self.count_two_in_row(final_board, self.opponent)
        if opponent_after < opponent_before:
            score += self.weights['blocking_threat']
            
        # Evaluate pushing threats
        for push_r in range(BOARD_SIZE):
            for push_c in range(BOARD_SIZE):
                if final_board[push_r][push_c] == self.opponent:
                    # If opponent piece was pushed to a worse position
                    if self.is_vulnerable_position(final_board, push_r, push_c):
                        score += self.weights['push_threat']
                        
        return score

    def is_vulnerable_position(self, board: List[List[int]], r: int, c: int) -> bool:
        """Check if a position is vulnerable to being pushed off key positions"""
        # Check if piece can be pushed off the board or into a bad position
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            # Position that could push this piece
            push_r, push_c = _torus(r - dr, c - dc)
            # Position piece would be pushed to
            dest_r, dest_c = _torus(r + dr, c + dc)
            
            if board[push_r][push_c] == EMPTY and board[dest_r][dest_c] == EMPTY:
                return True
        return False

    def get_best_move(self, game) -> tuple:
        """Returns the best move based on position evaluation"""
        possible_moves = self.get_possible_moves(game)
        best_score = float('-inf')
        best_moves = []  # Keep track of all moves with the same best score
        
        start_time = time.time()
        
        # First, check for immediate winning moves
        for move in possible_moves:
            # Quick check for time limit
            if time.time() - start_time > 0.8:
                break
                
            score = self.evaluate_move(game, move)
            
            if score == float('inf'):  # Winning move found
                return move
                
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
                
        # If we have multiple moves with the same score, choose randomly among them
        if best_moves:
            return random.choice(best_moves)
        else:
            return random.choice(possible_moves)  # Fallback