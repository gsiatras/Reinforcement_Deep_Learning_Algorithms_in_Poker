import collections
from scipy.special import softmax
import os
import pickle

from rlcard.utils.utils import *

class MDPAgent():
    ''' Implement MDP policy iteration algorithm
    '''

    def __init__(self, env, model_path='./mdp_model'):
        ''' Initilize Agent

         Args:
         env (Env): Env class
        '''
        self.agent_id = 0
        self.use_raw = False
        self.env = env
        self.model_path = model_path

        # A policy is a dict state_str -> action probabilities
        self.policy = collections.defaultdict(list)

        # Regret is a dict state_str -> action regrets
        self.total_values = collections.defaultdict(list)

        self.iteration = 0

    def train(self):
        ''' Do one iteration of CFR
                '''
        self.iteration += 1
        self.env.reset()
        agents = self.env.get_agents()
        for id, agent in enumerate(agents):
            if isinstance(agent, MDPAgent):
                self.agent_id = id
                break
        self.traverse_tree()

    def traverse_tree(self):
        if self.env.is_over():
            chips = self.env.get_payoffs()
            return chips[self.agent_id]

        current_player = self.env.get_player_id()
        state_utility = 0
        if not current_player == self.agent_id:
            state = self.env.get_state(current_player)
            # other agent move
            action = self.env.agents[current_player].step(state)

            # Keep traversing the child state
            self.env.step(action)
            Vstate = self.traverse_tree()
            self.env.step_back()
            return Vstate;

        if current_player == self.agent_id:
            Vaction = {}
            Vstate = 0
            obs, legal_actions = self.get_state(current_player)
            action_probs = self.action_probs(obs, legal_actions, self.policy, self.total_values)
            for action in legal_actions:
                action_prob = action_probs[action]

                # Keep traversing the child state
                self.env.step(action)
                V = self.traverse_tree()
                self.env.step_back()

                Vstate += action_prob * V  # state value
                Vaction[action] = V  # value of each action
            ''' alter policy according to new Vactions'''
            self.update_policy(obs, Vaction, legal_actions)

        return Vstate

    def action_probs(self, obs, legal_actions, policy, action_values):
        ''' Obtain the action probabilities of the current state

        Args:
            obs (str): state_str
            legal_actions (list): List of leagel actions
            player_id (int): The current player
            policy (dict): The used policy
            action_values (dict): The action_values of policy

        Returns:
            (tuple) that contains:
                action_probs(numpy.array): The action probabilities
                legal_actions (list): Indices of legal actions
        '''
        if obs not in policy.keys() and obs not in self.total_values.keys():
            tactions = np.array([-np.inf for action in range(self.env.num_actions)])
            for action in range(self.env.num_actions):
                if action in legal_actions:
                    tactions[action] = 0
            self.total_values[obs] = tactions
            action_probs = softmax(tactions)
            self.total_values[obs] = action_values[obs]
            self.policy[obs] = action_probs
        else:
            action_probs = policy[obs]
        action_probs = remove_illegal(action_probs, legal_actions)
        return action_probs

    def update_policy(self, obs, Vaction, legal_actions):
        ''' Update the policy according to the new action values
                Args:
                    obs (str): state_str
                    Vaction (list): The new action_values of the current itaration
         '''

        t_vaction = self.total_values[obs]
        t_vaction *= self.iteration
        # for i in range(self.env.num_actions):
        #     if i in legal_actions:
        #         t_vaction[i] += Vaction[i]
        for i in Vaction:
            t_vaction[i] += Vaction[i]
        t_vaction /= (self.iteration + 1)

        # update action values
        self.total_values[obs] = t_vaction
        self.policy[obs] = softmax(t_vaction)


    def eval_step(self, state):
        ''' Given a state, predict action based on average policy

        Args:
            state (numpy.array): State representation

        Returns:
            action (int): Predicted action
            info (dict): A dictionary containing information
        '''
        probs = self.action_probs(state['obs'].tostring(), list(state['legal_actions'].keys()), self.policy, self.total_values)
        #action = np.random.choice(len(probs), p=probs)
        action = np.argmax(probs)

        info = {}
        info['probs'] = {state['raw_legal_actions'][i]: float(probs[list(state['legal_actions'].keys())[i]]) for i in
                         range(len(state['legal_actions']))}

        return action, info

    def get_state(self, player_id):
        ''' Get state_str of the player

        Args:
            player_id (int): The player id

        Returns:
            (tuple) that contains:
                state (str): The state str
                legal_actions (list): Indices of legal actions
        '''
        state = self.env.get_state(player_id)
        return state['obs'].tostring(), list(state['legal_actions'].keys())

    def save(self):
        '''  Save model
        '''

        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)

        policy_file = open(os.path.join(self.model_path, 'policy.pkl'),'wb')
        pickle.dump(self.policy, policy_file)
        policy_file.close()

        values_file = open(os.path.join(self.model_path, 'action_values.pkl'),'wb')
        pickle.dump(self.total_values, values_file)
        values_file.close()

        iteration_file = open(os.path.join(self.model_path, 'iteration.pkl'),'wb')
        pickle.dump(self.iteration, iteration_file)
        iteration_file.close()

    def load(self):
        ''' Load model
        '''
        if not os.path.exists(self.model_path):
            return

        policy_file = open(os.path.join(self.model_path, 'policy.pkl'),'rb')
        self.policy = pickle.load(policy_file)
        policy_file.close()

        values_file = open(os.path.join(self.model_path, 'action_values.pkl'),'rb')
        self.total_values = pickle.load(values_file)
        values_file.close()

        iteration_file = open(os.path.join(self.model_path, 'iteration.pkl'),'rb')
        self.iteration = pickle.load(iteration_file)
        iteration_file.close()
