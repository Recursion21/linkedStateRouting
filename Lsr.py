# please use python3 
# requires graph.py as header file
# usage: python3 Lsr.py configX.txt

from socket import *
import sys
import threading
import pickle
import signal
import datetime
from time import *
from graph import *

# header1 = LSA[0] = [owner_node, seq_num]
# header2 = LSA[1] = [visited_neighbours (and will visit on when sending)]
# footer1 = LSA[int(LSA[4]) * 3 + 5] = markDead list

# takes input file and initialises the graph topography 
# of this router and its neighbours
def init(rawData):
    data = rawData.split()
    neighbours = []
    for x in range(int(data[2])):
        neighbours.append((data[x*3 + 3], data[x*3 + 4], data[x*3 + 5]))
        
    graph = Graph((data[0], data[1]), neighbours)
    
    return graph

# attach header to LSA own LSA
# header 1 = [owner_node, seq_num]
# header 2 = [visited_neighbours (and will visit on when sending)]
def attach_header(rawData):
    data = rawData.split()
    header1 = [graph.identity[0], 0]
    header2 = [graph.identity[0]]
    for x in graph.neighbours:
        header2.append(x[0])
    data.insert(0, header2)
    data.insert(0, header1)
    data.append([]) # markdead
    return data

def update_LSA_alive(neighbour):

    # add neighbour info back onto LSA
    headerLSA.insert(-1, neighbour[0])
    headerLSA.insert(-1, neighbour[1])
    headerLSA.insert(-1, neighbour[2])

    # update headers
    num = int(headerLSA[4]) + 1
    headerLSA[4] = str(num)
    headerLSA[0][1] += 1
    headerLSA[1].append(neighbour[0])
    headerLSA[int(headerLSA[4])*3 + 5] = graph.markDead

# updates if neighbours die
# think testing can only make len(changeList = 1), but 
# just incase, use can handle simultaneous faliure (probably)
def update_LSA_dead(headerLSA, changeList):
    nCurr = int(headerLSA[4]) # no. old neighbours

    # delete that node from header
    for node in changeList:
        for x in range(nCurr - 1):
            if node == headerLSA[x*3 + 5]:
                for i in range(3):
                    del headerLSA[x*3 + 5]
                nCurr -= 1
    
    headerLSA[4] = str(nCurr) # change no.neighbours
    headerLSA[0][1] += 1 # increment seqNum
    headerLSA[int(headerLSA[4])*3 + 5] = graph.markDead # update markDead list
    
    headerLSA[1] = []

    # reset visited array
    headerLSA[1].append(graph.identity[0])
    for x in graph.neighbours:
        headerLSA[1].append(x[0])

    return headerLSA

# sends LSA to neighbours
def send_self_LSA(headerLSA):
    pickleData = pickle.dumps(headerLSA)
    for node in graph.neighbours:
        clientSocket.sendto(pickleData, (LH, int(node[2])))

# parses decoded LSA
# updates graph topography according with LSA data
def parse(LSA):

    check_repeat(LSA) # check/updates time
    
    # graph.set_markDead(LSA[int(LSA[4])*3 + 5])
    # update markDead
    for deadNode in LSA[int(LSA[4])*3 + 5]:
       if deadNode not in graph.markDead:
          graph.markDead.append(deadNode) 

    # add any new keys to dict (from visited array)
    # LSA[1] = header1 = visited array
    for node in LSA[1]:
        if node not in graph.graphDict.keys():
            graph.add_node(node)

    # if node revives, remove from markDead
    if LSA[0][0] in graph.markDead:
        graph.markDead.remove(LSA[0][0])

    # add edges, first by key = src (owner of LSA), values = dest tuple
    # then add by key = dest, values = src tuple
    # LSA[4] = no. neighbours
    for x in range(int(LSA[4])):
        src = LSA[2]
        srcPort = LSA[3]
        dest = LSA[x*3+5]
        cost = LSA[x*3+6]
        destPort = LSA[x*3+7]

        # if its a neighbour, do extra info updating 
        nList = [x[0] for x in graph.neighbours]
        if dest == graph.identity[0] and src not in nList:
            neighbourTuple = (src, cost, srcPort)
            graph.add_neighbour(neighbourTuple)
            update_LSA_alive(neighbourTuple)

        if src not in graph.markDead:
            nodeValues = (dest, cost, destPort)
            if src not in list(graph.graphDict.keys()):
                graph.add_node(src)
            if nodeValues not in graph.graphDict[src]:
                graph.add_edge(src, nodeValues)

        if dest not in graph.markDead:
            srcNodeValues = (src, cost, srcPort)
            if src not in list(graph.graphDict.keys()):
                graph.add_node(dest)
            if srcNodeValues not in graph.graphDict[dest]:
                graph.add_edge(dest, srcNodeValues)

    # update seq_num info
    graph.update_seq_nums(LSA[0])
     
# update visited array in header, LSA[1]
def update_visited_header(LSA):

    # append neighbours to visited array, since this LSA will
    # get send to that neighbour
    # this helps eliminate some useless LSA broadcasts
    for node in graph.neighbours:
        if node[0] not in LSA[1]: 
            LSA[1].append(node[0])

# if sequence number is the same, don't send
# sends encoded LSA to non-received neighbours 
def relay(LSA):
    
    unvisited = [] 
    for node in graph.neighbours:
        if node[0] not in LSA[1]:
            unvisited.append((node[0], node[2]))
    update_visited_header(LSA)
    for node in unvisited:
        pickleLSA = pickle.dumps(LSA)
        clientSocket.sendto(pickleLSA, (LH, int(node[1])))

# return true if LSA header1 is same (already received)
# if true, don't broadcast it again
# also monitors time of LSA
# LSA[0] = header1
def check_repeat(LSA):
    if graph.check_seq_nums(LSA[0]):
        return True
    else:
        return False

# thread for receiving LSAs from other routers
# decodes and encodes data via pickle
# calls parse, update_visited_header, relay
def read_LSA():
    while True:
        rawLSA, clientAddress = serverSocket.recvfrom(2048)
        # LSA = message.decode() # use pickle on list object instead
        LSA = pickle.loads(rawLSA)
        parse(LSA)     
        relay(LSA)

def run_dijkstra():
    while True:
        sleep(30)
        graph.dijkstra()

def keyboardInterruptHandler(signal, frame):
     exit(0)

if len(sys.argv) != 2:
    sys.exit("Usage: python3 lsa.py config[x].txt")

# opens config.txt
with open(sys.argv[1]) as fd:
    rawData = fd.read()
graph = init(rawData)
print(graph.neighbours)
headerLSA = attach_header(rawData)
serverPort = int(graph.identity[1])
print(serverPort)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('localhost', serverPort)) 
clientSocket = socket(AF_INET, SOCK_DGRAM)
LH = 'localhost'
fd.close()

threadRead = threading.Thread(None, read_LSA, None)
threadRead.daemon = True
threadRead.start()

threadDijkstra = threading.Thread(None, run_dijkstra, None)
threadDijkstra.daemon = True
threadDijkstra.start()

while True:
    signal.signal(signal.SIGINT, keyboardInterruptHandler) 
    send_self_LSA(headerLSA)
    # graph.run_dijkstra()

    changeList = graph.check_time_update() 
    if changeList:
        # new headerLSA = update
        headerLSA = update_LSA_dead(headerLSA, changeList)
        # print("==== after return in main ====")
        # print(headerLSA)
    sleep(1)



