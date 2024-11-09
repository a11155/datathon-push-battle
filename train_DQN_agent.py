
from DQN_agent import DQNAgent
from PushBattle import Game, PLAYER1, PLAYER2, EMPTY, NUM_PIECES, BOARD_SIZE

def train_dqn(episodes=1000):
    agent = DQNAgent(PLAYER1)
    opponent = DQNAgent(PLAYER2)
    
    # Training metrics
    wins = 0
    losses = 0
    draws = 0
    invalid_moves = 0
    
    for episode in range(episodes):
        game = Game()
        total_reward = 0
        moves_made = 0
        episode_invalid_moves = 0
        
        print(f"\nStarting Episode {episode}")
        print(f"Current stats - Wins: {wins}, Losses: {losses}, Draws: {draws}")
        
        while moves_made < 100:  # Prevent infinite games
            current_agent = agent if game.current_player == PLAYER1 else opponent
            current_pieces = game.p1_pieces if game.current_player == PLAYER1 else game.p2_pieces
            is_placement = current_pieces < NUM_PIECES
            
            # Get state and display board
            state = current_agent.board_to_tensor(game)
            if moves_made % 10 == 0:
                print("\nCurrent board state:")
                game.display_board()
                print(f"P1 pieces: {game.p1_pieces}, P2 pieces: {game.p2_pieces}")
            
            # Get move
            move = current_agent.get_best_move(game)
            if move is None:
                print("No valid moves available")
                break
            
            # Validate move
            valid_move = False
            try:
                if is_placement:
                    if len(move) == 2 and game.is_valid_placement(move[0], move[1]):
                        game.place_checker(*move)
                        valid_move = True
                        print(f"Placement at {move}")
                else:
                    if len(move) == 4 and game.is_valid_move(move[0], move[1], move[2], move[3]):
                        game.move_checker(*move)
                        valid_move = True
                        print(f"Movement from {(move[0], move[1])} to {(move[2], move[3])}")
                        
                if not valid_move:
                    print(f"Invalid move attempted: {move}")
                    episode_invalid_moves += 1
                    break
                    
            except Exception as e:
                print(f"Error making move: {move}, Error: {e}")
                episode_invalid_moves += 1
                break
            
            # Get next state
            next_state = current_agent.board_to_tensor(game)
            
            # Calculate rewards
            base_reward = 0
            winner = game.check_winner()
            done = winner != EMPTY
            
            # Terminal rewards
            if winner == PLAYER1:
                base_reward = 1 if game.current_player == PLAYER1 else -1
            elif winner == PLAYER2:
                base_reward = -1 if game.current_player == PLAYER1 else 1
                
            # Intermediate rewards
            if current_agent == agent:
                # Reward for controlling center
                center_control = sum(1 for r in range(3,5) for c in range(3,5) 
                                  if game.board[r][c] == agent.player)
                position_reward = center_control * 0.1
                
                # Reward for protected pieces
                protected_pieces = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                                    if game.board[r][c] == agent.player and
                                    is_protected(game, r, c, agent.player))
                protection_reward = protected_pieces * 0.1
                
                # Combine rewards
                reward = base_reward + position_reward + protection_reward
                
                # Store experience and train
                agent.store_experience(state, move, reward, next_state, done)
                loss = agent.train_step()
                if loss is not None:
                    print(f"Move {moves_made}, Loss: {loss:.4f}")
                total_reward += reward
            
            moves_made += 1
            if done:
                if winner == PLAYER1:
                    wins += 1
                    print("Agent won!")
                elif winner == PLAYER2:
                    losses += 1
                    print("Opponent won!")
                else:
                    draws += 1
                    print("Draw!")
                break
            
            game.current_player *= -1
        
        # Update stats
        invalid_moves += episode_invalid_moves
        
        # Update target network
        if episode % 5 == 0:
            agent.update_target_network()
            print("Updated target network")
        
        # Adjust exploration
        if episode % 10 == 0:
            agent.epsilon = max(0.01, agent.epsilon * 0.995)  # Decay epsilon
            print(f"New epsilon: {agent.epsilon:.4f}")
            
        # Save model
        if episode % 50 == 0:
            agent.save(f'dqn_model_episode_{episode}.pth')
            print("Saved model")
        
        print(f"\nEpisode {episode} Summary:")
        print(f"Moves: {moves_made}")
        print(f"Total Reward: {total_reward:.2f}")
        print(f"Invalid Moves: {episode_invalid_moves}")
        print(f"Win Rate: {wins/(episode+1):.2%}")

def is_protected(game, r, c, player):
    """Check if a piece is protected from pushes"""
    if game.board[r][c] != player:
        return False
        
    for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
        # Check if there's an opponent piece that could push
        push_r = (r + dr) % BOARD_SIZE
        push_c = (c + dc) % BOARD_SIZE
        
        # Check if there's a friendly piece behind for protection
        behind_r = (r - dr) % BOARD_SIZE
        behind_c = (c - dc) % BOARD_SIZE
        
        if (game.board[push_r][push_c] != player and 
            game.board[push_r][push_c] != EMPTY and
            game.board[behind_r][behind_c] != player):
            return False
    return True

if __name__ == "__main__":
    train_dqn(300)
