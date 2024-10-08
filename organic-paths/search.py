from sys import stdout
from operator import itemgetter
from subprocess import Popen, PIPE
from collections import deque
import random
import re
from heapq import heappop, heappush

def reconstruct_path(parents, current_state, action, time):
    path = [(current_state, action, time)]
    while path[-1] in parents:
        path.append(parents[path[-1]])
    path.reverse()
    return list(map(lambda state_action_time: state_action_time[0], path))

# Generic search algorithm
# TODO: rewrite IDDFS so it continues where it left off (yield? or return state?)
# TODO: use make_graphviz_node
# TODO: make sure (using graphviz) that iddfs works
def search(start_state, depth_limit, heuristic, action_cost, openset_limit, is_goal_state,
           possible_transitions, make_graphviz_node):

    # states already checked
    closedset = []

    # a map of (state, action, time) => parent
    parents = {}

    # map of actual+estimated costs of going from every known state to goal state;
    # initialize with start state (F-score is simply the heuristic, no path cost)
    f_scores = {start_state: heuristic(start_state, 0, parents)}

    # map of actual costs of going from start state to every known state
    # initialize with start state (path cost = 0)
    g_scores = {start_state: 0}

    # states that we know exist but have not checked;
    # need both openset and openheap because heaps won't let us check if a state is a member
    openset = [start_state]
    openheap = [(f_scores[start_state], (start_state, None, 0))]

    # keep track of the largest openset we ever had to maintain
    max_openset_size = 1

    # while we still have a state to visit, and haven't found the goal
    while len(openset) > 0:

        # keep track of max_openset_size (just for benchmarking purposes)
        if max_openset_size < len(openset):
            max_openset_size = len(openset)

        # pick best state, make it the current state
        (val, (current_state, current_action, time)) = heappop(openheap)
        # if next-best state is just as good, we'll need to randomly choose
        equally_good = [(val, (current_state, current_action, time))]
        while len(openheap) > 0 and openheap[0][0] == val:
            (val2, (current_state2, current_action2, time2)) = heappop(openheap)
            equally_good.append((val2, (current_state2, current_action2, time2)))
        random.shuffle(equally_good)
        (val, (current_state, current_action, time)) = equally_good[0]
        # push all equally-good states not used
        for i in range(1, len(equally_good)):
            heappush(openheap, equally_good[i])

        openset.remove(current_state)

        # if we found the goal, we're done
        if is_goal_state(current_state):
            path = reconstruct_path(parents, current_state, current_action, time)
            return (path, len(closedset), max_openset_size)

        # append current state to closed set so we don't visit it again
        closedset.append(current_state)

        # for each possible next state from current state
        transitions = possible_transitions(current_state)
        for (action, next_state) in transitions:

            # determine path cost to this next state
            tentative_g_score = g_scores[current_state] + action_cost(current_state, action, next_state)

            # skip next states that we've already visited and this path isn't cheaper
            if next_state in closedset and \
               (next_state not in g_scores or g_scores[next_state] <= tentative_g_score):
                continue

            # skip if we have a depth limit and this node is too deep
            if depth_limit is not None and time > depth_limit:
                closedset.append(next_state)
                continue

            # if this next state is new, or we found a cheaper way to get there, put it in the openset
            if next_state not in openset or tentative_g_score < g_scores[next_state]:

                # save the parentage and calculated scores for next state
                parents[(next_state, action, time+1)] = (current_state, current_action, time)
                g_scores[next_state] = tentative_g_score
                f_scores[next_state] = g_scores[next_state] + heuristic(next_state, time+1, parents)
                heappush(openheap, (f_scores[next_state], (next_state, action, time+1)))
                openset.append(next_state)

        # keep only best states if we have a limit (beam search / hillclimbing)
        if openset_limit is not None:
            new_openset = []
            new_openheap = []
            while len(new_openheap) < openset_limit and len(openheap) > 0:
                (val, (state, action, time)) = heappop(openheap)
                heappush(new_openheap, (val, (state, action, time)))
                new_openset.append(state)
            openset = new_openset
            openheap = new_openheap
            if len(openheap) == 1:
                #closedset = closedset[-openset_limit:] # keep only last N history
                closedset = closedset[-1:] # only one possible state to visit, may run out; so clear the history, allow covering old ground

        time += 1

    # if we made it here, we ran out of states to visit and never found the goal
    return (None, len(closedset), max_openset_size)

def create_graph(graphviz):
    for i in range(len(graphviz)):
        g = "digraph G {\n"
        for j in range(i+1):
            if j == (len(graphviz)-1):
                g += re.sub(r'color="black"', 'color="blue"', graphviz[j])
            else:
                g += graphviz[j]
        if i != (len(graphviz)-1):
            g += "node [color=\"white\"]; edge [color=\"white\"];\n"
        for j in range(i+1, len(graphviz)):
            g += re.sub(r'color=".*?"', 'color="white"', graphviz[j])
        g += "}\n"
        p = Popen(['dot', '-Tpng', '-o', "%03d.png" % i],
                  stdin=PIPE, stdout=PIPE, stderr=PIPE)
        p.stdin.write(g)
        p.communicate()

# compare different search techniques on the same search problem
def experiment(repetitions, types, random_initial_state, heuristic_map, action_cost_map,
               openset_limit_map, is_goal_state, possible_transitions, path_cost, make_graphviz_node):

    print("Type,PathCost,CheckedStates,MaxOpenSet")
    cost = {}
    checked = {}
    max_openset = {}
    for t in types:
        cost[t] = 0.0
        checked[t] = 0.0
        max_openset[t] = 0.0
    for i in range(repetitions):
        s = random_initial_state(i) # every rep has a random starting state (but same goal)
        for t in types:
            # need special handling for iddfs
            if t == "iddfs":
                depth_limit = 1
                p = None
                while p is None:
                    (p, ch, os) = search(s, depth_limit, heuristic_map["dfs"],
                                         action_cost_map["dfs"], openset_limit_map["dfs"],
                                         is_goal_state, possible_transitions, make_graphviz_node)
                    checked[t] += ch
                    max_openset[t] += os
                    depth_limit += 1
                cost[t] += path_cost(p)
            else:
                (p, ch, os) = search(s, None, heuristic_map[t],
                                     action_cost_map[t], openset_limit_map[t],
                                     is_goal_state, possible_transitions, make_graphviz_node)
                cost[t] += path_cost(p)
                checked[t] += ch
                max_openset[t] += os

    for t in types:
        print ("%s,%f,%f,%f" % (t, cost[t] / float(repetitions),
                                checked[t] / float(repetitions),
                                max_openset[t] / float(repetitions)))
    stdout.flush()

def show_graph(graphviz):
    p = Popen(['dot', '-Txlib'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.stdin.write("digraph G {\n")
    for g in graphviz:
        p.stdin.write(g)
    p.stdin.write("}\n")
    p.communicate()

