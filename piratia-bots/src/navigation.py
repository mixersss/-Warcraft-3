"""Bounded A* over a derived walkability crop from the owner's garner.blk."""
import base64
import heapq
from functools import lru_cache
import json
import math
import zlib
from pathlib import Path


class Navigation:
    def __init__(self, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.map = data.get('map','garner')
        self.origin = tuple(data['origin'])
        self.width, self.height = data['width'], data['height']
        if not 1 <= self.width <= 1000 or not 1 <= self.height <= 1000:
            raise ValueError('Invalid navigation crop size')
        self.cells = zlib.decompress(base64.b64decode(data['walkable_zlib']))
        if len(self.cells) != self.width * self.height:
            raise ValueError('Incomplete navigation crop')
        self.waypoints = [tuple(p) for p in data['waypoints']]

    def cell(self, position):
        return position[0] // 100 - self.origin[0], position[1] // 100 - self.origin[1]

    def position(self, cell):
        return (cell[0] + self.origin[0]) * 100 + 50, (cell[1] + self.origin[1]) * 100 + 50

    def free(self, cell):
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height and self.cells[y*self.width+x] == 1

    def nearest(self, position, radius=6):
        x,y = self.cell(position)
        cells = ((x+dx,y+dy) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1))
        for cell in sorted(cells,key=lambda c:(c[0]-x)**2+(c[1]-y)**2):
            if self.free(cell):
                return self.position(cell)
        return None

    def path(self, start, end, limit=25000):
        cached = self._path(self.cell(start), self.cell(end), limit)
        result = list(cached)
        if result:
            result[0] = tuple(start)
        return result

    @lru_cache(maxsize=256)
    def _path(self, start_cell, goal, limit):
        if not self.free(start_cell) or not self.free(goal):
            return []
        queue = [(0, start_cell)]
        previous, costs = {start_cell: None}, {start_cell: 0}
        while queue and len(costs) <= limit:
            _, cell = heapq.heappop(queue)
            if cell == goal:
                result = []
                while cell is not None:
                    result.append(self.position(cell))
                    cell = previous[cell]
                result.reverse()
                return tuple(result)
            x, y = cell
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                target = x+dx, y+dy
                if not self.free(target):
                    continue
                if dx and dy and not (self.free((x+dx,y)) and self.free((x,y+dy))):
                    continue  # no diagonal cuts through walls
                cost = costs[cell] + (14 if dx and dy else 10)
                if cost >= costs.get(target, math.inf):
                    continue
                previous[target], costs[target] = cell, cost
                heuristic = 10 * max(abs(target[0]-goal[0]), abs(target[1]-goal[1]))
                heapq.heappush(queue, (cost+heuristic, target))
        return []
