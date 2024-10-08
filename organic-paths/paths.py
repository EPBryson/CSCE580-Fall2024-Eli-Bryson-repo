from search import *
from PIL import Image
import random
import math

width = 50
height = 50

init_x = None
init_y = None
goal_x = None
goal_y = None

possible_initial_states = []
possible_goal_states = []

terrain_img = None
terrain_cost = {}
terrain_cost_factor = 500.0
terrain_impassible = [] # cache of impassible locations

def establish_terrain(img_filename):
    global terrain_img, terrain_cost, terrain_impassible, width, height, possible_initial_states, possible_goal_states
    possible_initial_states = []
    possible_goal_states = []
    terrain_cost = {}
    terrain_img = Image.open(img_filename)
    terrain_impassible = []
    (width, height) = terrain_img.size
    pixels = terrain_img.load()
    for x in range(0, width):
        for y in range(0, height):
            (r,g,b) = pixels[x,y]
            if r == g and g == b: # grayscale, terrain cost
                # the darker the color, the less it costs
                terrain_cost[(x,y)] = r
            elif r == 255 and g == 0 and b == 0: # red, impassible
                terrain_cost[(x,y)] = -1
                terrain_impassible.append((x,y))
            elif r == 0 and g == 255 and b == 0: # green, goal point
                possible_goal_states.append((x,y))
                terrain_cost[(x,y)] = 0
            elif r == 0 and g == 0 and b == 255: # blue, starting point
                possible_initial_states.append((x,y))
                terrain_cost[(x,y)] = -1

# Returns distance from coord1 to coord2
def dist(coord1, coord2):
    x1, y1 = coord1
    x2, y2 = coord2
    return ((x2-x1)**2 + (y2-y1)**2)**0.5

# Initializes the starting state
def make_initial_state():
    global possible_initial_states, init_x, init_y
    (init_x, init_y) = random.choice(possible_initial_states)

# Initializes the goal state
def make_goal_state():
    global possible_goal_states, goal_x, goal_y, init_x, init_y
    (goal_x, goal_y) = random.choice(possible_goal_states)
    while dist((init_x, init_y), (goal_x, goal_y)) < 10:
        (goal_x, goal_y) = random.choice(possible_goal_states)

def is_goal_state(coords):
    x,y = coords
    return x == goal_x and y == goal_y

# Checks how far the distance to the nearest obstacle is and returns an integer
def dist_to_nearest_obstacle(coords):
    x,y = coords
    global terrain_impassible
    min_dist = max(width, height)
    for (x2, y2) in terrain_impassible:
        if x != x2 or y != y2:
            d = dist((x, y), (x2, y2))
            if d < min_dist:
                min_dist = d
    return min_dist

# action cost from point 1 to point 2 is terrain cost on point 2
# returns a double that costs more if the ground is not travelled
def action_cost_true(coords1, action, coords2):
    x1,y1=coords1
    x2,y2=coords2
    global terrain_cost, terrain_cost_factor
    return 1.0 + terrain_cost[(x2, y2)]/terrain_cost_factor

#### A01: Modify some of the defintions below the TODOs.
####      Consider using some functions provided above.

# TODO
def heuristic_best_first(coords, time, parents):
    return dist(coords, (goal_x, goal_y))

# TODO
def action_cost_best_first(coords1, action, coords2):
    return 0 #return action_cost_true(coords1, action, coords2)

# TODO
beam_size_best_first = None

# TODO
def heuristic_astar(coords, time, parents):
    g_cost = path_cost(parents, coords) if parents else 0
    h_cost = dist(coords, (goal_x, goal_y))
    return g_cost + h_cost

# TODO
def action_cost_astar(coords1, action, coords2):
    return action_cost_true(coords1, action, coords2)

# TODO
beam_size_astar = None

# TODO
def heuristic_beam(coords, time, parents):
    g_cost = path_cost(parents, coords) if parents else 0
    h_cost = dist(coords, (goal_x, goal_y))
    return g_cost + h_cost

# TODO
def action_cost_beam(coords1, action, coords2):
    return action_cost_true(coords1, action, coords2)

# TODO
beam_size_beam = 10

# TODO
def heuristic_human(coords, time, parents):
    g_cost = path_cost(parents, coords) if parents else 0
    h_cost = dist(coords, (goal_x, goal_y))
    return g_cost + h_cost
    #return dist(coords, (goal_x, goal_y))

# TODO
def action_cost_human(coords1, action, coords2):
    true_cost = action_cost_true(coords1, action, coords2)
    nearest_obstacle_dist = dist_to_nearest_obstacle(coords2)
    if nearest_obstacle_dist < 4:
         safety_penalty = 1/nearest_obstacle_dist * 200/3
         return true_cost + safety_penalty
    else:
         return true_cost
# TODO
beam_size_human = 10

def possible_transitions(coords):
    x, y = coords
    global terrain_cost, width, height
    transitions = []
    if x > 0 and terrain_cost[(x-1,y)] >= 0:
        transitions.append(('west', (x-1, y)))
    if x < (width-1) and terrain_cost[(x+1,y)] >= 0:
        transitions.append(('east', (x+1, y)))
    if y > 0 and terrain_cost[(x,y-1)] >= 0:
        transitions.append(('north', (x, y-1)))
    if y < (height-1) and terrain_cost[(x,y+1)] >= 0:
        transitions.append(('south', (x, y+1)))
    if x < (width-1) and y < (height-1) and terrain_cost[(x+1,y+1)] >= 0:
        transitions.append(('southeast', (x+1, y+1)))
    if x > 0 and y < (height-1) and terrain_cost[(x-1,y+1)] >= 0:
        transitions.append(('soutwest', (x-1, y+1)))
    if x > 0 and y > 0 and terrain_cost[(x-1,y-1)] >= 0:
        transitions.append(('northwest', (x-1, y-1)))
    if x < (width-1) and y > 0 and terrain_cost[(x+1,y-1)] >= 0:
        transitions.append(('northeast', (x+1, y-1)))
    return transitions

def path_cost(parents, current_coords):
    cost = 0.0
    current = current_coords
    while current in parents:
        parent_state, parent_acton, parent_time = parents[current]
        cost += action_cost_true(parent_state, parent_action, current)
        current = parent_state
    return cost
    #for i in range(len(path)-1):
    #    cost += action_cost_true(path[i][0], path[i][1], path[i+1][0])
    #return cost

def update_terrain_costs(path):
    global terrain_cost
    for (x, y) in path:
        if terrain_cost[(x,y)] > 0:
            terrain_cost[(x,y)] = max(1, min(256, terrain_cost[(x,y)] - 1))

def make_graphviz_node(coords, direction, visited = False):
    pass

def draw_terrain(out_filename):
    global terrain_img, terrain_cost
    pixels = terrain_img.load()
    for x in range(0, width):
        for y in range(0, height):
            c = int(terrain_cost[(x, y)])
            if c > 0:
                pixels[x, y] = (c, c, c)
    img = terrain_img.resize((width * 5, height * 5))
    img.save(out_filename)
    img.show()

road_configs = ["road-config-tree-sidewalks", "road-config-garden", "road-config-aldrich-park", "road-config-tree"]
strategies = ["best-first", "astar", "beam", "human"]
iterations = 500

# generate random seeds, so we can be sure terrain and initial/goal positions
# are reused when strategies are switched
terrain_seeds = []
for i in range(0, len(strategies)):
    terrain_seeds.append(random.random())
state_seeds = []
for i in range(0, iterations):
    state_seeds.append(random.random())

path_lengths_csv = open("path_lengths.csv", "w")
path_lengths_csv.write("road_config,strategy,iteration,path_length\n")

for road_config in road_configs:

    for i in range(0, len(strategies)):
        strategy = strategies[i]

        random.seed(terrain_seeds[i])
        establish_terrain("%s.bmp" % road_config)

        for j in range(0, iterations):
            random.seed(state_seeds[j])
            make_initial_state()
            make_goal_state() # must come second

            if strategy == "best-first":
                print("best-first")
                (path, _, _) = search((init_x, init_y), None, 
                                      heuristic_best_first, action_cost_best_first, 
                                      beam_size_best_first, is_goal_state, 
                                      possible_transitions, make_graphviz_node)

            elif strategy == "astar":
                print("astar")
                (path, _, _) = search((init_x, init_y), None,
                                      heuristic_astar, action_cost_astar, beam_size_astar,
                                      is_goal_state, possible_transitions, make_graphviz_node)

            elif strategy == "beam":
                print("beam")
                (path, _, _) = search((init_x, init_y), None,
                                      heuristic_beam, action_cost_beam, beam_size_beam,
                                      is_goal_state, possible_transitions, make_graphviz_node)

            if strategy == "human":
                print("human")
                (path, _, _) = search((init_x, init_y), None,
                                      heuristic_human, action_cost_human, beam_size_human,
                                      is_goal_state, possible_transitions, make_graphviz_node)

            if path is None:
                print (goal_x + " " + goal_y + " " + init_x + " " + init_y)

            print (f"{road_config}{strategy}{(j+1)} path length {len(path)}")
            path_lengths_csv.write("%s,%s,%d,%d\n" % (road_config, strategy, (j+1), len(path)))

            update_terrain_costs(path)

        draw_terrain("%s-%s.png" % (road_config, strategy))

path_lengths_csv.close()
            
        
