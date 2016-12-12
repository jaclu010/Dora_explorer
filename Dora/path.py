from global_vars import *
import math


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.previous = None

    def equals(self, other):
        return self.x == other.x and self.y == other.y

    def neighbors(self):
        neighbors = []

        if self.x - 1 >= 0:
            neighbors += [Node(self.x - 1, self.y)]
        if self.y - 1 >= 0:
            neighbors += [Node(self.x, self.y - 1)]
        if self.x + 1 < MAP_SIZE:
            neighbors += [Node(self.x + 1, self.y)]
        if self.y + 1 < MAP_SIZE:
            neighbors += [Node(self.x, self.y + 1)]

        return neighbors


def find_path(grid, start_pos, end_pos=None, find_unidentified=False):
    """
    Performs a BFS-search of the grid to find a shortest route from start_pos to end_pos.
    MAP_SIZE must be set to the correct size.

    If find_unidentified is True and the end_pos empty the function will return a list of
    unidentified cells in the grid.
    """
    start = Node(start_pos[0], start_pos[1])
    end = None
    if end_pos:
        end = Node(end_pos[0], end_pos[1])
    elif not find_unidentified:
        return []

    visited = set()
    visited.add((start.x, start.y))
    node_queue = [start]
    unidentified_nodes = []

    current = start

    while node_queue:
        current = node_queue.pop()

        if end and current.equals(end):
            # We found the end node
            if find_unidentified and grid[end.y * MAP_SIZE + end.x] == 0:
                # We searched for and found an unidentified end node, return path to previous node
                current = current.previous
            break

        if end and end_pos in unidentified_nodes:
            # We found an end that is unidentified, go to next closest node
            current = current.previous
            break

        for n in current.neighbors():
            if (n.x, n.y) not in visited and \
                    (grid[n.y * MAP_SIZE + n.x] == 1 or (find_unidentified and grid[n.y * MAP_SIZE + n.x] == 0)):
                if find_unidentified and grid[n.y * MAP_SIZE + n.x] == 0:
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
    if find_path(grid, pos, find_unidentified=True):
        return False
    return True


def find_closest_unexplored(grid, pos):
    """
    Returns a path to the node next to the closest uneplored node.
    Returns empty list if no such path is found.
    """
    unexplored = find_path(grid, pos, find_unidentified=True)
    unexplored.sort(key=lambda x: math.sqrt((x[0] - pos[0])**2 + (x[1] - pos[1])**2))

    if unexplored:
        return find_path(grid, pos, unexplored[0], find_unidentified=True)
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
    """
    unexplored = find_path(grid, pos, find_unidentified=True)
    unexplored.sort(key=lambda x: math.sqrt((x[0] - pos[0]) ** 2 + (x[1] - pos[1]) ** 2))

    if unexplored:
        end = unexplored[0]
        path = find_path(grid, pos, unexplored[0], find_unidentified=True)

        while not (math.sqrt((path[-1][0] - end[0])**2 + (path[-1][1] - end[1])**2) > 2 and line_of_sight(grid, path[-1], end)):
            path.pop()

        return path
    return []


if __name__ == "__main__":
    gr = [2, 0, 0, 2, 2, 2, 2, 2, 2,
          2, 2, 2, 2, 2, 2, 0, 2, 2,
          2, 1, 1, 1, 1, 1, 2, 2, 2,
          2, 1, 1, 1, 1, 1, 2, 2, 2,
          2, 1, 1, 2, 1, 1, 2, 2, 2,
          2, 2, 2, 2, 0, 1, 2, 2, 2,
          2, 1, 2, 2, 0, 0, 2, 2, 2,
          2, 1, 1, 1, 2, 2, 2, 2, 2,
          2, 2, 2, 2, 2, 2, 2, 2, 2]

    p = find_line_of_sight(gr, [1, 3])
    print(p)
    print(follow_path(p, NORTH))

    """
    p = find_path(gr, [1, 4], [4, 5], find_unidentified=True)
    print(p)

    print(closed_room(gr, [3, 1]))

    cmd = follow_path(p, NORTH)
    print(cmd)

    print(find_closest_unexplored(gr, [3, 1]))
    """
