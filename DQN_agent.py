
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
from PushBattle import Game, PLAYER1, PLAYER2, EMPTY, BOARD_SIZE, NUM_PIECES

class DQN(nn.Module):
    def __init__(self):
        super(DQN, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU()
        )
        
        # Single output head for all moves (4096 outputs)
        self.fc = nn.Linear(64 * 64, 4096)
        
    def forward(self, x):
        x = self.conv(x)
        x = x.view(-1, 64 * 64)
        return self.fc(x)

class DQNAgent:
    def __init__(self, player=PLAYER1):
        self.player = player
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.policy_net = DQN().to(self.device)
        self.target_net = DQN().to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
        self.memory = deque(maxlen=10000)
        self.batch_size = 32
        self.gamma = 0.99
        self.epsilon = 0.1

    def board_to_tensor(self, game):
        state = np.zeros((3, BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
        
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if game.board[i][j] == self.player:
                    state[0][i][j] = 1
                elif game.board[i][j] == -self.player:
                    state[1][i][j] = 1
                elif game.board[i][j] == EMPTY:
                    state[2][i][j] = 1
                    
        return torch.FloatTensor(state).unsqueeze(0).to(self.device)

    def get_possible_moves(self, game):
        moves = []
        current_pieces = game.p1_pieces if game.current_player == PLAYER1 else game.p2_pieces
        
        if current_pieces < NUM_PIECES:
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if game.board[r][c] == EMPTY:
                        moves.append((r, c))
        else:
            for r0 in range(BOARD_SIZE):
                for c0 in range(BOARD_SIZE):
                    if game.board[r0][c0] == game.current_player:
                        for r1 in range(BOARD_SIZE):
                            for c1 in range(BOARD_SIZE):
                                if game.board[r1][c1] == EMPTY:
                                    moves.append((r0, c0, r1, c1))
        return moves

    def move_to_index(self, move):
        if len(move) == 2:
            r, c = move
            return r * BOARD_SIZE + c
        else:
            r0, c0, r1, c1 = move
            return r0 * (BOARD_SIZE**3) + c0 * (BOARD_SIZE**2) + r1 * BOARD_SIZE + c1

    def index_to_move(self, index, is_placement):
        if is_placement:
            r = index // BOARD_SIZE
            c = index % BOARD_SIZE
            return (r, c)
        else:
            r0 = index // (BOARD_SIZE**3)
            c0 = (index // (BOARD_SIZE**2)) % BOARD_SIZE
            r1 = (index // BOARD_SIZE) % BOARD_SIZE
            c1 = index % BOARD_SIZE
            return (r0, c0, r1, c1)

    def get_best_move(self, game):
        valid_moves = self.get_possible_moves(game)
        if not valid_moves:
            return None
            
        if random.random() < self.epsilon:
            return random.choice(valid_moves)
        
        state = self.board_to_tensor(game)
        with torch.no_grad():
            q_values = self.policy_net(state).squeeze()
            
        # Create a mask for valid moves
        valid_q_values = []
        for move in valid_moves:
            idx = self.move_to_index(move)
            valid_q_values.append((move, q_values[idx].item()))
            
        # Select move with highest Q-value
        best_move = max(valid_q_values, key=lambda x: x[1])[0]
        return best_move

    def store_experience(self, state, move, reward, next_state, done):
        move_idx = self.move_to_index(move)
        self.memory.append((state, move_idx, reward, next_state, done))

    def train_step(self):
        if len(self.memory) < self.batch_size:
            return
            
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        state_batch = torch.cat(states)
        action_batch = torch.tensor(actions, dtype=torch.long).to(self.device)
        reward_batch = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        next_state_batch = torch.cat(next_states)
        done_batch = torch.tensor(dones, dtype=torch.bool).to(self.device)
        
        # Get current Q values
        current_q = self.policy_net(state_batch).gather(1, action_batch.unsqueeze(1))
        
        # Get next Q values
        with torch.no_grad():
            next_q_values = self.target_net(next_state_batch)
            next_q = torch.zeros(self.batch_size, device=self.device)
            next_q[~done_batch] = next_q_values[~done_batch].max(1)[0]
            target_q = reward_batch + self.gamma * next_q
            
        # Compute loss and update
        loss = nn.MSELoss()(current_q.squeeze(), target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save(self, filename='dqn_model.pth'):
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, filename)

    def load(self, filename='dqn_model.pth'):
        checkpoint = torch.load(filename)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
