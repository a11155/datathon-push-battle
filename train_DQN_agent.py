
from DQN_agent import DQNAgent
from PushBattle import Game, PLAYER1, PLAYER2, EMPTY, NUM_PIECES, BOARD_SIZE
from smart_agent import SmartAgent

def train_dqn(episodes=1000):
    agent = DQNAgent(PLAYER1)
    opponent = SmartAgent(PLAYER2)  # Use RandomAgent as opponent for reliable training
    
    # Training metrics
    wins = 0
    draws = 0
    losses = 0
    
    for episode in range(episodes):
        game = Game()
        total_reward = 0
        moves_made = 0
        
        while moves_made < 100:  # Prevent infinite games
            current_agent = agent if game.current_player == PLAYER1 else opponent
            
            # Get state before move
            state = agent.board_to_tensor(game) if current_agent == agent else None
            
            # Get and apply move
            move = current_agent.get_best_move(game)
            if move is None:
                break
            
            # Apply move
            try:
                if len(move) == 2:
                    if game.is_valid_placement(move[0], move[1]):
                        game.place_checker(*move)
                    else:
                        continue
                else:
                    if game.is_valid_move(move[0], move[1], move[2], move[3]):
                        game.move_checker(*move)
                    else:
                        continue
                        
            except Exception as e:
                continue
            
            moves_made += 1
            
            # Only process rewards and training for main agent
            if current_agent == agent:
                next_state = agent.board_to_tensor(game)
                winner = game.check_winner()
                done = winner != EMPTY
                
                # Simple reward structure
                reward = 0
                if done:
                    if winner == PLAYER1:
                        reward = 1
                    elif winner == PLAYER2:
                        reward = -1
                
                # Store experience and train
                agent.store_experience(state, move, reward, next_state, done)
                agent.train_step()
                total_reward += reward
                
                if done:
                    if winner == PLAYER1:
                        wins += 1
                    elif winner == PLAYER2:
                        losses += 1
                    else:
                        draws += 1
                    break
            
            game.current_player *= -1
        
        # Update target network periodically
        if episode % 10 == 0:
            agent.update_target_network()
        
        # Print progress
        if episode % 10 == 0:
            win_rate = wins / (episode + 1)
            print(f"Episode {episode}")
            print(f"Win Rate: {win_rate:.2%}")
            print(f"Wins: {wins}, Losses: {losses}, Draws: {draws}")
            print(f"Total Reward: {total_reward}")
            print("-" * 40)
            
            # Save if performance is good
            if win_rate > 0.6:
                agent.save(f'dqn_model_winrate_{win_rate:.2f}.pth')
    
    return agent

if __name__ == "__main__":
    train_dqn(1000)
