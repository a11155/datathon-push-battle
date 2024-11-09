import random
from PushBattle import Game, PLAYER1, PLAYER2, EMPTY, BOARD_SIZE, NUM_PIECES, _torus

'''
This is a sample implementation of an agent that just plays a random valid move every turn.
I would not recommend using this lol, but you are welcome to use functions and the structure of this.
'''

class RandomAgent:
    def __init__(self, player=PLAYER1):
        self.player = player
    
    # given the game state, gets all of the possible moves
    def get_possible_moves(self, game):
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
        
    def get_best_move(self, game):
        """Returns a random valid move."""
        possible_moves = self.get_possible_moves(game)
        return random.choice(possible_moves)



import random
from PushBattle import Game, PLAYER1, PLAYER2, EMPTY, BOARD_SIZE, NUM_PIECES, _torus
import numpy as np
from typing import List, Tuple, Dict
import time

class SmartAgent:
    def __init__(self, player=PLAYER1):
        self.player = player
        self.opponent = PLAYER2 if player == PLAYER1 else PLAYER1
        
        # Weights for different evaluation components
        self.weights = {
            'alignment': 10.0,      # Value of aligned pieces
            'center_control': 5.0,  # Value of controlling center squares
            'protection': 3.0,      # Value of protected pieces
            'mobility': 2.0,        # Value of having more moves available
            'pushing_power': 4.0    # Value of being able to push opponent pieces
        }
        
        # Define center squares for center control evaluation
        self.center_squares = [
            (r, c) for r in range(2, 6) for c in range(2, 6)
        ]
        
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

    def evaluate_alignment(self, game, player: int) -> float:
        """Evaluate piece alignment (2 or 3 in a row)"""
        score = 0
        board = game.board
        
        # Check horizontal alignments
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE-2):
                window = [board[r][c+i] for i in range(3)]
                if window.count(player) == 3:
                    score += 100  # Winning position
                elif window.count(player) == 2 and window.count(EMPTY) == 1:
                    score += 5
                    
        # Check vertical alignments
        for r in range(BOARD_SIZE-2):
            for c in range(BOARD_SIZE):
                window = [board[r+i][c] for i in range(3)]
                if window.count(player) == 3:
                    score += 100
                elif window.count(player) == 2 and window.count(EMPTY) == 1:
                    score += 5
                    
        # Check diagonal alignments (top-left to bottom-right)
        for r in range(BOARD_SIZE-2):
            for c in range(BOARD_SIZE-2):
                window = [board[r+i][c+i] for i in range(3)]
                if window.count(player) == 3:
                    score += 100
                elif window.count(player) == 2 and window.count(EMPTY) == 1:
                    score += 5
                    
        # Check diagonal alignments (top-right to bottom-left)
        for r in range(BOARD_SIZE-2):
            for c in range(2, BOARD_SIZE):
                window = [board[r+i][c-i] for i in range(3)]
                if window.count(player) == 3:
                    score += 100
                elif window.count(player) == 2 and window.count(EMPTY) == 1:
                    score += 5
                    
        return score

    def evaluate_center_control(self, game, player: int) -> float:
        """Evaluate control of center squares"""
        score = 0
        board = game.board
        
        for r, c in self.center_squares:
            if board[r][c] == player:
                score += 1
                # Extra points for protected center pieces
                if self.is_protected(game, r, c):
                    score += 0.5
                    
        return score

    def is_protected(self, game, r: int, c: int) -> bool:
        """Check if a piece is protected (has friendly pieces behind it)"""
        board = game.board
        player = board[r][c]
        if player == EMPTY:
            return False
            
        # Check all four directions
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            # Position of potential pushing piece
            push_r, push_c = _torus(r + dr, c + dc)
            # Position behind the current piece
            behind_r, behind_c = _torus(r - dr, c - dc)
            
            # If there's an opponent piece that could push
            if board[push_r][push_c] != player and board[push_r][push_c] != EMPTY:
                # And there's no friendly piece behind for protection
                if board[behind_r][behind_c] != player:
                    return False
                    
        return True

    def evaluate_mobility(self, game) -> float:
        """Evaluate number of available moves"""
        original_player = game.current_player
        
        # Count moves for current player
        my_moves = len(self.get_possible_moves(game))
        
        # Temporarily switch player to count opponent moves
        game.current_player = PLAYER2 if game.current_player == PLAYER1 else PLAYER1
        opp_moves = len(self.get_possible_moves(game))
        
        # Restore original player
        game.current_player = original_player
        
        return my_moves - opp_moves

    def evaluate_pushing_power(self, game, player: int) -> float:
        """Evaluate potential to push opponent pieces advantageously"""
        score = 0
        board = game.board
        
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == player:
                    for dr, dc in directions:
                        # Position of piece that could be pushed
                        push_r, push_c = _torus(r + dr, c + dc)
                        # Position where piece would end up
                        dest_r, dest_c = _torus(push_r + dr, push_c + dc)
                        
                        if board[push_r][push_c] == self.opponent:
                            # Bonus for pushing opponent piece
                            score += 1
                            # Extra bonus if push would break opponent alignment
                            if self.would_break_alignment(game, push_r, push_c, dest_r, dest_c):
                                score += 2
                                
        return score

    def would_break_alignment(self, game, from_r: int, from_c: int, to_r: int, to_c: int) -> bool:
        """Check if moving a piece would break an alignment"""
        # Create a copy of the board
        board_copy = [row.copy() for row in game.board]
        piece = board_copy[from_r][from_c]
        
        # Simulate the move
        board_copy[to_r][to_c] = piece
        board_copy[from_r][from_c] = EMPTY
        
        # Check if alignment score decreased
        orig_score = self.evaluate_alignment(game, self.opponent)
        
        # Create temporary game state with new board
        temp_game = Game()
        temp_game.board = board_copy
        
        new_score = self.evaluate_alignment(temp_game, self.opponent)
        
        return new_score < orig_score

    def evaluate_position(self, game) -> float:
        """Combine all evaluation components with weights"""
        if game.check_winner() == self.player:
            return float('inf')
        elif game.check_winner() == self.opponent:
            return float('-inf')
            
        score = 0
        
        # Alignment score
        score += self.weights['alignment'] * (
            self.evaluate_alignment(game, self.player) -
            self.evaluate_alignment(game, self.opponent)
        )
        
        # Center control score
        score += self.weights['center_control'] * (
            self.evaluate_center_control(game, self.player) -
            self.evaluate_center_control(game, self.opponent)
        )
        
        # Mobility score
        score += self.weights['mobility'] * self.evaluate_mobility(game)
        
        # Pushing power score
        score += self.weights['pushing_power'] * (
            self.evaluate_pushing_power(game, self.player) -
            self.evaluate_pushing_power(game, self.opponent)
        )
        
        return score

    def get_best_move(self, game) -> tuple:
        """Returns the best move based on position evaluation"""
        possible_moves = self.get_possible_moves(game)
        best_score = float('-inf')
        best_move = random.choice(possible_moves)  # Fallback
        
        start_time = time.time()
        
        for move in possible_moves:
            # Create a copy of the game to simulate move
            game_copy = Game()
            game_copy.board = [row.copy() for row in game.board]
            game_copy.current_player = game.current_player
            game_copy.p1_pieces = game.p1_pieces
            game_copy.p2_pieces = game.p2_pieces
            
            # Apply move
            if len(move) == 2:  # Placement move
                r, c = move
                game_copy.board[r][c] = game.current_player
                if game.current_player == PLAYER1:
                    game_copy.p1_pieces += 1
                else:
                    game_copy.p2_pieces += 1
            else:  # Movement move
                r0, c0, r1, c1 = move
                game_copy.board[r1][c1] = game_copy.board[r0][c0]
                game_copy.board[r0][c0] = EMPTY
            
            # Evaluate resulting position
            score = self.evaluate_position(game_copy)
            
            if score > best_score:
                best_score = score
                best_move = move
                
            # Check time limit (leave some margin for safety)
            if time.time() - start_time > 0.9:
                break
                
        return best_move