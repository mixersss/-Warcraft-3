"""Incremental, checked A*: a route may take several decisions, never block networking."""
import heapq

class RoutePending(Exception):
    pass

class Search:
    def __init__(self,start,goal,heuristic_weight=1):
        self.goal=goal
        self.weight=heuristic_weight;self.closed=set()
        self.queue=[(0,0,start)]
        self.previous={start:None}
        self.costs={start:0}
        self.done=False;self.result=()
    def advance(self,nav,limit,spend):
        while self.queue and len(self.costs)<=limit:
            spend()
            _,negative,cell=heapq.heappop(self.queue)
            if -negative!=self.costs.get(cell) or cell in self.closed:continue
            self.closed.add(cell)
            if cell==self.goal:
                result=[]
                while cell is not None:result.append(nav.position(cell));cell=self.previous[cell]
                self.done=True;self.result=tuple(reversed(result));return self.result
            x,y=cell
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                target=x+dx,y+dy
                if target in self.closed or not nav.free(target):continue
                if dx and dy and not (nav.free((x+dx,y)) and nav.free((x,y+dy))):continue
                cost=self.costs[cell]+(14 if dx and dy else 10)
                if cost>=self.costs.get(target,float('inf')):continue
                self.previous[target]=cell;self.costs[target]=cost
                hx,hy=abs(target[0]-self.goal[0]),abs(target[1]-self.goal[1])
                h=14*min(hx,hy)+10*abs(hx-hy)
                heapq.heappush(self.queue,(cost+h*self.weight,-cost,target))
        self.done=True;self.result=();return ()
