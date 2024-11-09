
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

    def handle_move(self, game, move):
        """Places the move if valid and returns 'forfeit', True, or False"""
        if not isinstance(move, (list, tuple)) or len(move) < 2:
            print(f"Invalid move format by Player {'P1' if game.current_player == PLAYER1 else 'P2'}")
            return "forfeit"

        if len(move) != 2 and len(move) != 4:
            print(f"Invalid move format by Player {'P1' if game.current_player == PLAYER1 else 'P2'}")
            return "forfeit"

        try:
            print(move)
            # Convert move elements to integers if they aren't already
            move = [int(x) if isinstance(x, (int, str)) else x for x in move]

            if game.turn_count < 17:
                if game.is_valid_placement(move[0], move[1]):
                    game.place_checker(move[0], move[1])
                else:
                    print(f"Invalid placement by")
                    return "forfeit"
            else:
                if game.is_valid_move(move[0], move[1], move[2], move[3]):
                    game.move_checker(move[0], move[1], move[2], move[3])
                else:
                    print(f"Invalid move by {game.current_player}")
                    return "forfeit"
            return True
        except Exception as e:
            print(f"Error handling move: {str(e)}")
            return False

    def play_game(self, p1_agent, p2_agent) -> Dict:
        """Play a single game and record data"""
        game = Game()
        moves = []
        max_moves = 100  # Safety limit
        move_count = 0
        
        # Random moves tracking
        p1_random = 5
        p2_random = 5
        
        while move_count < max_moves:
            game.turn_count += 1
            start_time = time.time()
            current_agent = p1_agent if game.current_player == PLAYER1 else p2_agent
            current_random = p1_random if game.current_player == PLAYER1 else p2_random
            
            # First attempt

            print("starting")
            try:
                move = current_agent.get_best_move(game)

                move_time = time.time() - start_time
                
                move_record = {
                    'player': game.current_player,
                    'move': move,
                    'time': move_time,
                    'type': 'valid'
                }
                
                result = self.handle_move(game, move)
                if result == "forfeit":
                    moves.append(move_record)
                    return {
                        'p1_agent': p1_agent.__class__.__name__,
                        'p2_agent': p2_agent.__class__.__name__,
                        'winner': PLAYER2 if game.current_player == PLAYER1 else PLAYER1,
                        'moves': moves,
                        'total_moves': move_count,
                        'forfeit': True
                    }
                elif not result:
                    # Second attempt
                    start_time = time.time()
                    move = current_agent.get_best_move(game)
                    move_time = time.time() - start_time
                    
                    move_record = {
                        'player': game.current_player,
                        'move': move,
                        'time': move_time,
                        'type': 'valid'
                    }
                    
                    result = self.handle_move(game, move)
                    if result == "forfeit" or not result:
                        # Use random move if available
                        if current_random > 0:
                            random_agent = RandomAgent(player=game.current_player)
                            random_move = random_agent.get_best_move(game)
                            if self.handle_move(game, random_move):
                                move_record['type'] = 'random'
                                if game.current_player == PLAYER1:
                                    p1_random -= 1
                                else:
                                    p2_random -= 1
                            else:
                                # Forfeit if random move fails
                                return {
                                    'p1_agent': p1_agent.__class__.__name__,
                                    'p2_agent': p2_agent.__class__.__name__,
                                    'winner': PLAYER2 if game.current_player == PLAYER1 else PLAYER1,
                                    'moves': moves,
                                    'total_moves': move_count,
                                    'forfeit': True
                                }
                        else:
                            # No random moves left - forfeit
                            return {
                                'p1_agent': p1_agent.__class__.__name__,
                                'p2_agent': p2_agent.__class__.__name__,
                                'winner': PLAYER2 if game.current_player == PLAYER1 else PLAYER1,
                                'moves': moves,
                                'total_moves': move_count,
                                'forfeit': True
                            }

                moves.append(move_record)
                
            except Exception as e:
                print(f"Error during move: {str(e)}")
                move_record = {
                    'player': game.current_player,
                    'error': str(e),
                    'time': time.time() - start_time,
                    'type': 'error'
                }
                moves.append(move_record)
                
                # Use random move on error if available
                if current_random > 0:
                    random_agent = RandomAgent(player=game.current_player)
                    random_move = random_agent.get_best_move(game)
                    if self.handle_move(game, random_move):
                        if game.current_player == PLAYER1:
                            p1_random -= 1
                        else:
                            p2_random -= 1
                    else:
                        return {
                            'p1_agent': p1_agent.__class__.__name__,
                            'p2_agent': p2_agent.__class__.__name__,
                            'winner': PLAYER2 if game.current_player == PLAYER1 else PLAYER1,
                            'moves': moves,
                            'total_moves': move_count,
                            'forfeit': True
                        }
                else:
                    return {
                        'p1_agent': p1_agent.__class__.__name__,
                        'p2_agent': p2_agent.__class__.__name__,
                        'winner': PLAYER2 if game.current_player == PLAYER1 else PLAYER1,
                        'moves': moves,
                        'total_moves': move_count,
                        'forfeit': True
                    }
            
            winner = game.check_winner()
            if winner != EMPTY:
                game.display_board()
                return {
                    'p1_agent': p1_agent.__class__.__name__,
                    'p2_agent': p2_agent.__class__.__name__,
                    'winner': winner,
                    'moves': moves,
                    'total_moves': move_count
                }
                
            game.current_player *= -1
            move_count += 1
            
            # Debug output
            if move_count % 1 == 0:
                print(f"Move {move_count} completed")
                print(game.board)
                game.display_board()
        
        return {
            'p1_agent': p1_agent.__class__.__name__,
            'p2_agent': p2_agent.__class__.__name__,
            'winner': EMPTY,  # Draw
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
    def run_benchmark(self, num_games: int, agent1, agent2) -> None:
        """Run benchmark games between agents"""
        print(f"Running {num_games} benchmark games...")
        
        for game_num in range(num_games):
            print(f"\nGame {game_num + 1}/{num_games}")
            game_record = self.play_game(agent1, agent2)
            self.analyze_game(game_record)
            print(f"Game {game_num + 1} complete: {game_record['p1_agent']} vs {game_record['p2_agent']}")
            print(f"Winner: {game_record['winner']}")

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

def main():
    from random_agent import RandomAgent  # Your random agent
    from minimax_agent import MinimaxAgent  # Your advanced agent
    from smart_agent import SmartAgent
    from DQN_agent import DQNAgent
    # Run benchmark
    analyzer = GameAnalyzer()

    p1 = DQNAgent(PLAYER1)
    p2 = RandomAgent(PLAYER2)
    p1.load("dqn1_250.pth")
    analyzer.run_benchmark(10, p1, p2)  # Run 10 games
    
    # Export results
    with open('benchmark_results.json', 'w') as f:
        json.dump(analyzer.export_stats(), f, indent=2)
    
    print("\nBenchmark complete. Results saved to benchmark_results.json")

if __name__ == "__main__":
    main()