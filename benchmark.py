import json
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from PushBattle import Game, PLAYER1, PLAYER2, EMPTY, BOARD_SIZE, NUM_PIECES

class GameAnalyzer:
    def __init__(self):
        self.stats = {
            'total_games': 0,
            'matchup_stats': defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0}),
            'move_stats': {
                'opening': defaultdict(int),   # moves 1-8
                'midgame': defaultdict(int),   # moves 9-16
                'endgame': defaultdict(int)    # moves 17+
            },
            'random_moves_used': defaultdict(int),
            'game_lengths': defaultdict(int),
            'average_move_time': defaultdict(float),
            'timeouts': defaultdict(int)
        }

    def analyze_game(self, game_record: Dict) -> None:
        """Analyze a single game record"""
        self.stats['total_games'] += 1
        
        # Update matchup stats
        winner = game_record['winner']
        matchup = f"{game_record['p1_agent']} vs {game_record['p2_agent']}"
        
        if winner == PLAYER1:
            self.stats['matchup_stats'][matchup]['wins'] += 1
        elif winner == PLAYER2:
            self.stats['matchup_stats'][matchup]['losses'] += 1
        else:
            self.stats['matchup_stats'][matchup]['draws'] += 1

        # Analyze moves
        for turn, move_data in enumerate(game_record['moves']):
            phase = 'opening' if turn < 8 else 'midgame' if turn < 16 else 'endgame'
            
            if move_data['type'] == 'random':
                self.stats['random_moves_used'][move_data['player']] += 1
            
            if move_data.get('time', 0) > 0.9:  # Close to timeout
                self.stats['timeouts'][phase] += 1
                
            self.stats['move_stats'][phase][move_data['type']] += 1
            
        # Record game length
        self.stats['game_lengths'][len(game_record['moves'])] += 1

    def run_benchmark(self, num_games: int = 1) -> None:
        """Run benchmark games between agents"""
        from smart_agent import SmartAgent  # Your agent
        from random_agent import RandomAgent
        
        print(f"Running {num_games} benchmark games...")
        
        for game_num in range(num_games):
            print(f"\nGame {game_num + 1}/{num_games}")
            # Run game with both players as P1 and P2
            game_record = self.play_game(SmartAgent(PLAYER1), RandomAgent(PLAYER2))
            self.analyze_game(game_record)
            
            print(f"Game {game_num + 1}a complete: {game_record['p1_agent']} vs {game_record['p2_agent']}")
            
            game_record = self.play_game(RandomAgent(PLAYER1), RandomAgent(PLAYER2))
            self.analyze_game(game_record)
            
            print(f"Game {game_num + 1}b complete: {game_record['p1_agent']} vs {game_record['p2_agent']}")

    def play_game(self, p1_agent, p2_agent) -> Dict:
        """Play a single game and record data"""
        game = Game()
        moves = []
        max_moves = 100  # Safety limit to prevent infinite games
        move_count = 0
        
        while move_count < max_moves:
            start_time = time.time()
            current_agent = p1_agent if game.current_player == PLAYER1 else p2_agent
            
            try:
                move = current_agent.get_best_move(game)
                move_time = time.time() - start_time
                
                # Record move data
                move_record = {
                    'player': game.current_player,
                    'move': move,
                    'time': move_time,
                    'type': 'valid'
                }
                
                # Validate and execute move
                is_valid = False
                if len(move) == 2:  # Placement move
                    if move_count < 16 and game.is_valid_placement(move[0], move[1]):
                        game.place_checker(move[0], move[1])
                        is_valid = True
                else:  # Movement move
                    if move_count >= 16 and len(move) == 4:
                        if game.is_valid_move(move[0], move[1], move[2], move[3]):
                            game.move_checker(move[0], move[1], move[2], move[3])
                            is_valid = True
                
                if not is_valid:
                    move_record['type'] = 'invalid'
                    # Make a random valid move instead
                    if move_count < 16:
                        valid_moves = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                                     if game.board[r][c] == EMPTY]
                    else:
                        valid_moves = []
                        for r0 in range(BOARD_SIZE):
                            for c0 in range(BOARD_SIZE):
                                if game.board[r0][c0] == game.current_player:
                                    for r1 in range(BOARD_SIZE):
                                        for c1 in range(BOARD_SIZE):
                                            if game.board[r1][c1] == EMPTY:
                                                if game.is_valid_move(r0, c0, r1, c1):
                                                    valid_moves.append((r0, c0, r1, c1))
                    
                    if valid_moves:
                        random_move = valid_moves[0]  # Take first valid move
                        if len(random_move) == 2:
                            game.place_checker(random_move[0], random_move[1])
                        else:
                            game.move_checker(random_move[0], random_move[1], 
                                            random_move[2], random_move[3])
                        move_record['type'] = 'random'
                
                moves.append(move_record)
                
            except Exception as e:
                print(f"Error during move: {str(e)}")
                moves.append({
                    'player': game.current_player,
                    'error': str(e),
                    'time': time.time() - start_time,
                    'type': 'error'
                })
                # Make a random valid move on error
                if move_count < 16:
                    valid_moves = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                                 if game.board[r][c] == EMPTY]
                    if valid_moves:
                        r, c = valid_moves[0]
                        game.place_checker(r, c)
                
            winner = game.check_winner()
            if winner != EMPTY:
                break
                
            game.current_player *= -1
            move_count += 1
            
            # Debug output
            if move_count % 5 == 0:
                print(f"Move {move_count} completed")
                game.display_board()
            
        return {
            'p1_agent': p1_agent.__class__.__name__,
            'p2_agent': p2_agent.__class__.__name__,
            'winner': winner,
            'moves': moves,
            'total_moves': move_count
        }

    def export_stats(self) -> Dict:
        """Export statistics in a format suitable for visualization"""
        return {
            'totalGames': self.stats['total_games'],
            'matchupStats': [
                {
                    'name': matchup,
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'draws': stats['draws']
                }
                for matchup, stats in self.stats['matchup_stats'].items()
            ],
            'moveStats': [
                {
                    'name': phase.capitalize(),
                    'validMoves': stats['valid'],
                    'timeouts': stats.get('timeout', 0),
                    'invalid': stats.get('invalid', 0)
                }
                for phase, stats in self.stats['move_stats'].items()
            ],
            'randomMovesUsed': [
                {
                    'name': agent,
                    'used': moves,
                    'remaining': 5 - moves  # 5 random moves allowed per game
                }
                for agent, moves in self.stats['random_moves_used'].items()
            ],
            'gameLength': [
                {
                    'length': f"{length}-{length+4}",
                    'games': count
                }
                for length, count in sorted(self.stats['game_lengths'].items())
            ]
        }

def main():
    # Run benchmark
    analyzer = GameAnalyzer()
    analyzer.run_benchmark(1)  # Run 1 game to start
    
    # Export results
    with open('benchmark_results.json', 'w') as f:
        json.dump(analyzer.export_stats(), f, indent=2)
    
    print("\nBenchmark complete. Results saved to benchmark_results.json")

if __name__ == "__main__":
    main()