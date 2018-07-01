import sys, os
import random
import numpy as np
from itertools import count, chain
import copy 

"""
1. Clone pycolab in the same directory of this file.
2. `cd pycolab`
3. `pip install -e .`
4. Open IPython in a folder that contains this file and the pycolab repo
5. `%run learner.py%
6. Interact with the history in `game_histories`


### TODO:
- Replace digits of boxes with the same symbol

"""

from pycolab.examples import warehouse_manager


def gen_history():
    game_histories = []

    n_episodes = 1
    max_game_steps = 100

    # Randomly generate history:
    for _ in range(n_episodes):
        episode = []
        game = warehouse_manager.make_game(0)
        obs, r, discount = game.its_showtime()

        for _ in range(max_game_steps):
            a = random.randint(0, 3)
            pos = game.things['P'].position
            episode.append([obs.board, pos, a])
            obs, r, discount = game.play(a)
            if game.game_over:
                pos = game.things['P'].position
                episode.append([obs.board, pos, None])
                break

        game_histories.append(episode)

    return game_histories


# Now we have some history, time to learn from it!

def gen_conditions(include_time=False):
    # WIP
    max_distance = 2
    min_time = -1
    objs = 11

    n_rel_positions = max_distance*2 + 1
    max_total_complexity = n_rel_positions**2 + include_time

    times = list(range(0, min_time, -1))
    cols = [0] + zip(range(max_distance + 1), range(0, -max_distance - 1, -1))
    rows = cols
    # rows = copy.deepcopy(cols)

    # TODO, loop through conditions in order of complexity:
    # while


def init_rule(preconditions, action, postcondition):
    def rule(s0, s, pos, a):
        if a != action:
            return None
        states = [s0, s]
        for t, row, col, obj in preconditions:
            if states[t][row, col] != obj:
                return None
        return postcondition
    return rule

def distribute(n, bins, n_max):
    assert bins > 0

    if bins == 1:
        return [[n]]

    def gen():
        for i in range(min(n+1, n_max)):
            for x in distribute(n - i, bins - 1, n_max):
                yield chain([i], x)
    return gen()

def init_rule_gen():
    """
    Generates the next 'least complex' set of possible rules.
    """
    preconditions = list(gen_conditions(True))
    postconditions = list(gen_conditions())

    for n_preconditions in count(1):
        max_complexity = n_preconditions*len(preconditions) + len(postconditions)

        for i in range(max_complexity):
            for j in range(min(i, len(postconditions))):
                postcondition = postconditions[j]
                remaining = max_complexity - j
                for precondition_config in distribute(remaining, n_preconditions, len(preconditions)):
                    precondition = [preconditions[i] for i in precondition_config]
                    for action in range(4):
                        yield init_rule(precondition, action, postcondition)


# Not necessary:
# # Mapping from (row, col, new_object) to preconditions that would end up in the target position
# rule_target_lookup = {}

def find_simplest_explanations(game_histories):
    rules_gen = init_rule_gen()
    failed = True
    while failed:
        failed = False
        rules = next(rules_gen)
        episode = game_histories[0]
        s0 = episode[0][0]
        for i in range(len(episode) - 1):
            s, pos, a = episode[i]
            sp = episode[i + 1][0]

            predicted_changes = set()
            for rule in rules:
                postcondition = rule(s0, s, pos, a)
                row, col, obj = postcondition
                if sp[row, col] != postcondition:
                    failed = True
                    break
                else:
                    predicted_changes.add((row, col))

            diff = s != sp
            changes = np.where(diff)
            changes = set(zip(*changes)) 
            # Check if we predicted all changes:
            if len(changes - predicted_changes) > 0:
                failed = True
                break


def main():
    history = gen_history()
    # find_simplest_explanations(history)