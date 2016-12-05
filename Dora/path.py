
# Could use another constant
MAP_SIZE = 15


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
        if self.x + 1 <= MAP_SIZE:
            neighbors += [Node(self.x + 1, self.y)]
        if self.y + 1 <= MAP_SIZE:
            neighbors += [Node(self.x, self.y + 1)]

        return neighbors


def find_path(grid, start_pos, end_pos):
    """
    Performs a BFS-search of the grid to find a shortest route from start_pos to end_pos.
    MAP_SIZE must be set to the correct size.
    """
    start = Node(start_pos[0], start_pos[1])
    end = Node(end_pos[0], end_pos[1])

    visited = set()
    visited.add((start.x, start.y))
    node_queue = [start]

    current = start

    while node_queue:
        current = node_queue.pop()

        if current.equals(end):
            # We found the end node
            break

        for n in current.neighbors():
            if (n.x, n.y) not in visited and grid[n.y*MAP_SIZE + n.x] == 1:
                visited.add((n.x, n.y))
                n.previous = current
                node_queue += [n]

    if not current.equals(end):
        # No route to end could be found, maybe return [] instead?
        print("No route to end found in find_path")

    path = [[current.x, current.y]]

    while current != start:
        prev = current.previous
        path += [[prev.x, prev.y]]
        current = prev

    path.reverse()
    return path


if __name__ == "__main__":
    g = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
         2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
         2, 1, 2, 2, 2, 2, 1, 2, 1, 2, 2, 2, 2, 2, 2,
         2, 1, 2, 2, 2, 1, 1, 2, 1, 2, 2, 2, 2, 2, 2,
         2, 1, 1, 1, 1, 1, 1, 2, 1, 2, 2, 2, 2, 2, 2,
         2, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 2,
         2, 1, 1, 1, 2, 2, 2, 2, 1, 2, 1, 2, 2, 2, 2,
         2, 1, 1, 1, 2, 2, 2, 2, 1, 2, 1, 2, 2, 2, 2,
         2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2,
         2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2,
         2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2,
         2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2,
         2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2,
         2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2,
         2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]

    p = find_path(g, [1, 1], [8, 2])
    print(p)
    print(len(p))

