#####
#
# path.py
# Updated: 17/12 2016
# Authors: Jonathan Johansson, Martin Lundberg
#
#####
from global_vars import *
import math
import Queue


class PQueue(Queue.PriorityQueue):
    def __init__(self):
        Queue.PriorityQueue.__init__(self)
        self.counter = 0
        
    def put(self, item, priority):
        Queue.PriorityQueue.put(self, (priority, self.counter, item))
        self.counter += 1
        
    def get(self, *args, **kwargs):
        _, _, item = Queue.PriorityQueue.get(self, *args, **kwargs)
        return item


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.previous = None
        self.cost = float("inf")

    def equals(self, other):
        return self.x == other.x and self.y == other.y

    def neighbors(self):
        neighbors = []

        if self.y - 1 >= 0:
            neighbors += [Node(self.x, self.y - 1)]
        if self.x + 1 < MAP_SIZE:
            neighbors += [Node(self.x + 1, self.y)]
        if self.y + 1 < MAP_SIZE:
            neighbors += [Node(self.x, self.y + 1)]
        if self.x - 1 >= 0:
            neighbors += [Node(self.x - 1, self.y)]
            
        return neighbors

    def heuristic(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def tuple(self):
        return (self.x, self.y)

    
def generate_costs(grid):
    """
    Generate costs for tiles so that A-star search favors driving next to walls
    rather than through the room.
    """
    costs = []

    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            current = Node(x, y)
            wall_neighbors = 0
            
            if grid[y * MAP_SIZE + x] == 0:
                costs += [100]
                continue
            
            for n in current.neighbors():
                if grid[n.y * MAP_SIZE + n.x] == 2:
                    wall_neighbors += 1
                    break
                
            if wall_neighbors == 2:
                costs += [1]
            elif wall_neighbors == 1:
                costs += [3]
            else:
                costs += [8]
                
    return costs


def a_star(grid, start_pos, end_pos, costs=None):
    """
    Uses A-star to find the cheapest path from start_pos to end_pos in grid.
    Costs is an array of the same size as grid and defines the cost to travel on
    a specific tile. If costs=None, costs are generated so that tiles next to walls
    are cheaper to travel.
    """
    pqueue = PQueue()
    visited = set()
    
    start = Node(int(start_pos[0]), int(start_pos[1]))
    end = Node(int(end_pos[0]), int(end_pos[1]))
    
    if not costs:
        costs = generate_costs(grid)
        
    start.cost = 0.0
    pqueue.put(start, start.heuristic(end))
        
    v = None
        
    while not pqueue.empty():
        v = pqueue.get()
        visited.add(v.tuple())
            
        if v.equals(end):
            break
            
        for n in v.neighbors():
            if n.tuple() not in visited and \
               (grid[int(n.y * MAP_SIZE + n.x)] == 1 or (grid[int(n.y * MAP_SIZE + n.x)] == 0 and n.equals(end))):
                cost = v.cost + costs[int(n.y * MAP_SIZE + n.x)]
                if cost < n.cost:
                    n.cost = cost
                    n.previous = v
                    pqueue.put(n, cost + n.heuristic(end))

    path = []
    if not (grid[int(v.y * MAP_SIZE + v.x)] == 0 and v.equals(end)):
        path += [[v.x, v.y]]
    while not v.equals(start):
        path += [[v.previous.x, v.previous.y]]
        v = v.previous
        
    path.reverse()
    return path

def bfs(grid, start_pos, end_pos=None, find_unidentified=False):
    """
    Performs a BFS-search of the grid to find a shortest route from start_pos to end_pos.
    MAP_SIZE must be set to the correct size.

    If find_unidentified is True and the end_pos empty the function will return a list of
    unidentified cells in the grid.
    """
    start = Node(int(start_pos[0]), int(start_pos[1]))
    end = None
    if end_pos:
        end = Node(int(end_pos[0]), int(end_pos[1]))
    elif not find_unidentified:
        return []

    visited = set()
    visited.add((start.x, start.y))
    node_queue = [start]
    unidentified_nodes = []

    current = start

    while node_queue:
        current = node_queue.pop(0)
        
        if end and current.equals(end):
            # We found the end node
            if find_unidentified and grid[int(end.y) * MAP_SIZE + int(end.x)] == 0:
                # We searched for and found an unidentified end node, return path to previous node
                current = current.previous
            break

        if end and end_pos in unidentified_nodes and current.equals(end):
            # We found an end that is unidentified, go to next closest node
            current = current.previous
            break

        for n in current.neighbors():
            if (n.x, n.y) not in visited and \
                    (grid[int(n.y) * MAP_SIZE + int(n.x)] == 1 or (find_unidentified and grid[int(n.y) * MAP_SIZE + int(n.x)] == 0)):
                if find_unidentified and grid[int(n.y) * MAP_SIZE + int(n.x)] == 0:
                    unidentified_nodes += [[n.x, n.y]]
                visited.add((n.x, n.y))        
                n.previous = current
                node_queue += [n]

    if end and not find_unidentified and not current.equals(end):
        # No route to end could be found
        return []

    # Returns the unidentified nodes if we searched for them
    if not end and find_unidentified:
        return list(unidentified_nodes)

    # Find the path by walking backwards through the nodes
    path = [[current.x, current.y]]
    while current != start:
        prev = current.previous
        path += [[prev.x, prev.y]]
        current = prev

    path.reverse()
    return path


def follow_path(path, rotation):
    """
    Generates a set of movement instructions for the robot to execute from a path.
    """
    if not path:
        return []

    current_cell = path[0]
    num_tiles = 0
    move_in_y = False
    commands = []
    if rotation % 4 == NORTH or rotation % 4 == SOUTH:
        move_in_y = True
    for i in path[1:]:
        if current_cell[0] == i[0]:
            if not move_in_y and num_tiles != 0:
                commands += ["go_tiles_" + str(num_tiles)]
                num_tiles = 0
            num_tiles += 1
            move_in_y = True
            if current_cell[1] < i[1]:
                # set rotation to SOUTH
                deg = 0
                while rotation != SOUTH:
                    rotation = (rotation + 1) % 4
                    deg += 90
                if deg > 180:
                    deg = 360 - deg
                    commands += ["turn_left_" + str(deg)]
                elif deg != 0:
                    commands += ["turn_right_" + str(deg)]
            else:
                # set rotation to NORTH
                deg = 0
                while rotation != NORTH:
                    rotation = (rotation + 1) % 4
                    deg += 90
                if deg > 180:
                    deg = 360 - deg
                    commands += ["turn_left_" + str(deg)]
                elif deg != 0:
                    commands += ["turn_right_" + str(deg)]
        else:
            if move_in_y and num_tiles != 0:
                commands += ["go_tiles_" + str(num_tiles)]
                num_tiles = 0
            num_tiles += 1
            move_in_y = False
            if current_cell[0] < i[0]:
                # set rotation to EAST
                deg = 0
                while rotation != EAST:
                    rotation = (rotation + 1) % 4
                    deg += 90
                if deg > 180:
                    deg = 360 - deg
                    commands += ["turn_left_" + str(deg)]
                elif deg != 0:
                    commands += ["turn_right_" + str(deg)]
            else:
                # set rotation to WEST
                deg = 0
                while rotation != WEST:
                    rotation = (rotation + 1) % 4
                    deg += 90
                if deg > 180:
                    deg = 360 - deg
                    commands += ["turn_left_" + str(deg)]
                elif deg != 0:
                    commands += ["turn_right_" + str(deg)]
        current_cell = i
    if num_tiles != 0:
        commands += ["go_tiles_" + str(num_tiles)]
    return commands


def closed_room(grid, pos):
    """
    Returns True if grid is a closed room around pos, False otherwise.
    """
    if bfs(grid, pos, find_unidentified=True):
        return False
    return True


def find_closest_unexplored(grid, pos):
    """
    Returns a path to the node next to the closest uneplored node.
    Returns empty list if no such path is found.
    """
    unexplored = bfs(grid, pos, find_unidentified=True)
    #unexplored.sort(key=lambda x: math.sqrt((x[0] - pos[0])**2 + (x[1] - pos[1])**2))

    if unexplored:
        return a_star(grid, pos, unexplored[0])
    return []


def line_of_sight(grid, start_pos, end_pos):
    """
    Uses a modified Bresenhams algorithm to test for line of sight between two tiles in grid
    """
    dx = float(end_pos[0] - start_pos[0])
    dy = float(end_pos[1] - start_pos[1])
    error = -1.0
    if dx != 0.0:
        derror = abs(dy/dx)
    else:
        # Check vertical lines
        x = start_pos[0]
        for y in range(start_pos[1], end_pos[1]):
            if grid[y*MAP_SIZE + x] == 2:
                return False
        return True

    y = start_pos[1]
    for x in range(start_pos[0], end_pos[0]-1):
        print(x, y)
        if grid[y*MAP_SIZE + x] == 2:
            return False

        error += derror
        if error >= 0.0:
            y += 1
            error -= 1.0
    return True


def find_line_of_sight(grid, pos):
    """
    Returns a path to a node which is close to the closest unexplored node, is at least 2 squares away from the unexplored
    node and has line of sight to the unexplored node
    Returns empty list if no such path is found.
    Note: currently does not work well, avoid using.
    """
    unexplored = bfs(grid, pos, find_unidentified=True)
    unexplored.sort(key=lambda x: math.sqrt((x[0] - pos[0]) ** 2 + (x[1] - pos[1]) ** 2))

    if unexplored:
        end = unexplored[0]
        path = bfs(grid, pos, unexplored[0], find_unidentified=True)

        while not (math.sqrt((path[-1][0] - end[0])**2 + (path[-1][1] - end[1])**2) > 2 and line_of_sight(grid, path[-1], end)):
            path.pop()

        return path
    return []


if __name__ == "__main__":
    gr = [2, 2, 2, 2, 2, 2, 2, 2, 2,
          2, 2, 2, 2, 2, 2, 2, 2, 2,
          2, 1, 1, 2, 2, 2, 2, 2, 2,
          2, 1, 2, 2, 2, 2, 2, 2, 2,
          2, 1, 2, 2, 0, 2, 2, 2, 2,
          2, 1, 1, 1, 1, 2, 2, 2, 2,
          2, 1, 2, 2, 2, 2, 2, 2, 2,
          2, 1, 2, 2, 2, 2, 2, 2, 2,
          2, 2, 2, 2, 2, 2, 2, 2, 2]

    print(find_closest_unexplored(gr, [1,5]))
    

    
    #p = find_line_of_sight(gr, [1, 3])
    #print(p)
    #print(follow_path(p, NORTH))

    """
    p = find_path(gr, [1, 4], [4, 5], find_unidentified=True)
    print(p)

    print(closed_room(gr, [3, 1]))

    cmd = follow_path(p, NORTH)
    print(cmd)

    print(find_closest_unexplored(gr, [3, 1]))
    """
