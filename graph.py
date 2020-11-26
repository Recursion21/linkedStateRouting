# z5166026 comp3331 assignment 19T2
# please use python3 

import datetime
import heapq
 
# NOTE: for LSAs
# header1 = [owner_node, seq_num]
# header2 = [visited_neighbours]
# footer  = [dead_node]


# NOTE: Graph ADT -> ALL elements in tuples/lists are str objects, except...
# self.identity = (node, port)
# self.neighbours = list of (node, cost from ident, port)
# graphDict keys are just nodes
# graphDict values are list of (node, cost, port)
# self.seqNums = list of [node, seq_num] -> seq_num = int type
# self.time = list of [node, datetime] -> datetime = datetime type
# self.markDead = list of nodes (dead) -> if revive, remove from this list

class Graph:
    
    def __init__(self, identity, neighbours, graphDict=None):
        if graphDict == None:
            graphDict = {}
        self._graphDict = graphDict # = array of linked lists...
        self._identity = identity # self -> (node_name, port) 
        # list of direct neighbours for detecting dead neighbours
        self._neighbours = neighbours # tuple (node_name, cost, port)
        self._seqNums = []
        self._time = []
        self._markDead = []
        self.add_node(self.identity[0])
        
        # add neighbours
        for node in neighbours:
            self.add_node(node[0])
        # add edges for each key in dict
        for src in graphDict:
            # if key = identity, just add neighbours
            if src == identity[0]:
                for dest in neighbours:
                    self.add_edge(src, dest)
            # otherwise...
            else:
                # add identity node, extract cost
                for dest in neighbours:
                    if src is dest[0]:
                        neighbourCost = dest[1]
                srcNode = (identity[0], neighbourCost, identity[1])
                self.add_edge(src, srcNode)

    def add_node(self, node):
        if node not in self._graphDict:
            self._graphDict[node] = []

    def add_neighbour(self, nodeTuple):
        if nodeTuple not in self.neighbours:
            self.neighbours.append(nodeTuple) 
    
    # edge is tuple -> (node_name, cost, port)
    def add_edge(self, node, edge):
        # append edge tutple to list
        self.graphDict[node].append(edge)

    def remove_neighbour(self, deadNode):
        neighbourName = [x[0] for x in self.neighbours]
        if deadNode in neighbourName:
            index = neighbourName.index(deadNode)
            del self.neighbours[index]

    def set_markDead(self, deadList):
        self._markDead = deadList
    
    def update_seq_nums(self, header1): 
        if header1 not in self.seqNums:
            # if node in seqNums, but seq num is diff 
            nodeList = [x[0] for x in self.seqNums]
            if header1[0] in nodeList:
                x = nodeList.index(header1[0]) #shifty
                self.seqNums[x][1] = header1[1]
            else:
                self.seqNums.append(header1)

    # if LSA already received once, 
    # increment time, return true
    def check_seq_nums(self, header1):
        if header1 in self.seqNums:
            self.increment_time(header1)
            return True
        else:
            return False
     
    # not really how it works, need to have like
    # if time detect not receive from neighbour, then increment heart beat
    # 3sec diff in time = neighbour is dead, call remove neighbour, modify LSA
    def increment_time(self, header1):
        # if neighbour, increment time
        if header1[0] in [x[0] for x in self.neighbours]:
            timeNodes = [x[0] for x in self.time]
            if header1[0] in timeNodes:
                index = timeNodes.index(header1[0])
                self.time[index][1] = datetime.datetime.now()
            else:
                self.time.append([header1[0], datetime.datetime.now()]) 

    # checks datetime(keep alive) of neighbours, if >3 sec, assume dead
    # cleans up dead neighbour in all graph data structure
    def check_time_update(self):
        changes = [] # list of nodes so caller knows which nodes died
        for node in self.time:
            # if 3 seconds not receive message
            if ((datetime.datetime.now() - node[1]).total_seconds()) > 3:
                self.update_graph(node[0]) # remove dead neighbour in nodes/edges
                self.remove_neighbour(node[0]) # remove dead neighbour
                self.time.remove([node[0], node[1]]) # remove dead in time list
                if node[0] not in self.markDead:
                    self.markDead.append(node[0])
                index = [x[0] for x in self.seqNums].index(node[0])
                self.seqNums[index][1] = -1 # set seq num of dead node to -1
                changes.append(node[0])

        return changes

    # deadNeighbour is only node name
    def update_graph(self, deadNode):
        # delete entire neighbour key
        self.graphDict.pop(deadNode)

        # delete entry of dead node from every other node
        for x in list(self.graphDict.keys()):
            values = [x[0] for x in self.graphDict[x]]
            if deadNode in values:
                index = values.index(deadNode)
                del self.graphDict[x][index]

        self.add_node(deadNode)

    # calculate shortest path from this node to other every node
    # need pred list
    def dijkstra(self):
        distanceDict = {key: float('infinity') for key in self.graphDict}
        distanceDict[self.identity[0]] = 0
        predDict = {key: 'xx' for key in self.graphDict}

        pq = [(0, self.identity[0])]
        while len(pq) > 0:
            currDist, currNode = heapq.heappop(pq)
            if currDist > distanceDict[currNode]: # replace with visited list
                continue
            values = [(x[0], x[1]) for x in self.graphDict[currNode]] 
            # if the node is in markDead, don't include it in calculations
            for value in values:
                if value[0] in self.markDead:
                    index = values.index(value)
                    del values[index]
            for neighbour, cost in values:
                dist = round((currDist + float(cost)), 1)
                if dist < distanceDict[neighbour]:
                    predDict[neighbour] = currNode
                    distanceDict[neighbour] = dist
                    heapq.heappush(pq, (dist, neighbour))
        
        print("I am Router {}".format(self.identity[0]))
        for node in list(self.graphDict.keys()):
            if node not in self.markDead:
                if node is not self.identity[0]:
                    pred = predDict[node]
                    if pred is 'xx':
                        continue
                    path = node + pred
                    while pred is not self.identity[0]:
                        pred = predDict[pred]
                        path += pred
                    print("Least cost path to router {}: {} and the cost is {}" \
                            .format(node, path[::-1], distanceDict[node]))



    @property
    def neighbours(self):
        return self._neighbours

    @property
    def identity(self):
        return self._identity

    @property
    def graphDict(self):
        return self._graphDict

    @property
    def seqNums(self):
        return self._seqNums

    @property
    def time(self):
        return self._time

    @property
    def markDead(self):
        return self._markDead
