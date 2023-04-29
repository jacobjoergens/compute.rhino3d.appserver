import ingest 
import networkx as nx
import nondegenerateDecomposition
import degenerateDecomposition
import sys
import json
import asyncio
import websockets
import itertools
import copy
import matplotlib.pyplot as plt
import spaceDecomposition



corner_lists = None
k = 0
deg_partitions = {}
dir_patterns = None 
concave_corners = None
max_sets = []

def stagePartitioning(input):
    global corner_lists, k, max_sets
    curves = input['crvPoints']
    k = input['k']
    areas = input['areas']
    
    xcomp, ycomp, minx, maxy, vertices = spaceDecomposition.digestCurves(curves)
    spaceDecomposition.buildGrid(xcomp, ycomp, minx, maxy, vertices)
    corner_lists, max_extent = ingest.digestCurves(curves)
    concave_corners = ingest.findConcaveVertices(corner_lists)
    
    horizontal = ingest.findColinearVertices(corner_lists, concave_corners.copy(),0)
    vertical = ingest.findColinearVertices(corner_lists, concave_corners,1)
    intersections = ingest.findIntersections(horizontal,vertical)
    max_sets, G, top, bottom, h_counter, v_counter = degenerateDecomposition.getMaxIndependentSet(horizontal,vertical,intersections,corner_lists)
    bipartite_figures = degenerateDecomposition.generateGraphs(max_sets, G, top, bottom, horizontal, vertical, h_counter, v_counter)

    return bipartite_figures

def getConcaveCorners(cornerLists):
    concave_corners = []
    for corner_list in cornerLists:
        current_corner = corner_list.head
        if(current_corner.concave):
            concave_corners.append(current_corner)
        current_corner = current_corner.next
        while(current_corner!=corner_list.head):
            if(current_corner.concave):
                concave_corners.append(current_corner)
            current_corner = current_corner.next
    return concave_corners

def findOverlapping(overlap_dict, G, dir): 
    if dir == 'horizontal': 
        coor = 0 
    else: 
        coor = 1

    for cat in overlap_dict[dir].keys():
        colinear_edges = overlap_dict[dir][cat]
        # for i in range(len(colinear_edges)):
            # print(cat, i, colinear_edges[i][0].list_index, colinear_edges[i][1].list_index)
        if len(colinear_edges)>1: 
            for i in range(len(colinear_edges)-1): 
                outer = colinear_edges[i]
                ubound = max(outer[0].vertex[coor],outer[1].vertex[coor])
                lbound = min(outer[0].vertex[coor],outer[1].vertex[coor])
                for j in range(i+1, len(colinear_edges)):
                    inner = colinear_edges[j]
                    inner_ubound = max(inner[0].vertex[coor],inner[1].vertex[coor])
                    inner_lbound = min(inner[0].vertex[coor],inner[1].vertex[coor])
                    if(lbound <= inner_ubound and inner_lbound <= ubound):
                        # if(outer[1].list_index==inner[0].list_index):
                            # print(overlap_dict[dir])
                            # print(i,j)
                            # print(outer[0].vertex, outer[1].vertex)
                            # print(inner[0].vertex, inner[1].vertex)
                            # print(outer[0].list_index, outer[1].list_index, inner[0].list_index, inner[1].list_index)
                        G.add_edge(outer[1].list_index, inner[0].list_index)
    sys.stdout.flush()

def findNeighbors(interior_edges, G):
    overlap_dict = {
        'horizontal':{},
        'vertical':{}
        }
    for edge in interior_edges: 
        if(edge[0].vertex[0]==edge[1].vertex[0]):
            if edge[0].vertex[0] in overlap_dict['vertical']:
                overlap_dict['vertical'][edge[0].vertex[0]].append(edge)
            else: 
                overlap_dict['vertical'][edge[0].vertex[0]] = [edge]
        else: 
            if edge[0].vertex[1] in overlap_dict['horizontal']:
                overlap_dict['horizontal'][edge[0].vertex[1]].append(edge)
            else: 
                overlap_dict['horizontal'][edge[0].vertex[1]] = [edge]

    findOverlapping(overlap_dict, G, 'horizontal')
    findOverlapping(overlap_dict, G, 'vertical')

def getPartition(input): 
    global corner_lists, k, deg_partitions
    degSetIndex = input['degSetIndex']
    index = input['index']
    G = nx.Graph()

    if(degSetIndex not in deg_partitions): 
        interior_edges = []
        deg_corner_lists = []
        conversionTable = {}
        for corner_list in corner_lists:
            deg_corner_lists.append(corner_list.copyList(conversionTable))

        max_set = []
        for deg_chord in max_sets[degSetIndex]:
            max_set.append((conversionTable[deg_chord[0]],conversionTable[deg_chord[1]]))
        
        nonDegBasis = degenerateDecomposition.decompose(max_set, deg_corner_lists, interior_edges)
        
        concave_corners = getConcaveCorners(nonDegBasis)
        deg_partitions[degSetIndex] = { 
            'set': nonDegBasis,
            'concave_corners': concave_corners,
            'dir_patterns': list(itertools.product([0, 1], repeat=len(concave_corners))),
            'interior_edges': interior_edges
        }
        

    regions = []
    degSet = deg_partitions[degSetIndex]
    conversionTable = {}
    
    non_deg_corner_lists = []
    for i in range(len(degSet['set'])): 
        corner_list = degSet['set'][i]
        corner_list.updateState(i)
        non_deg_corner_lists.append(corner_list.copyList(conversionTable))

    interior_edges = []
    for deg_chord in degSet['interior_edges']:
        interior_edges.append([conversionTable[deg_chord[0]],conversionTable[deg_chord[1]]])

    concave_corners = []
    for corner in degSet['concave_corners']:
        concave_corners.append(conversionTable[corner])

    nondegenerateDecomposition.decompose(degSet['dir_patterns'][index], concave_corners, non_deg_corner_lists, regions, k, interior_edges)

    for i in range(len(interior_edges)):
        print(i,interior_edges[i][0].list_index,interior_edges[i][1].list_index)
    sys.stdout.flush()
    G.add_nodes_from(range(len(non_deg_corner_lists)))
    findNeighbors(interior_edges, G)
    print('interior_edges:',len(interior_edges))
    print(G.edges)
    plt.figure(figsize=(6,9))
    nx.draw(G, with_labels=True)
    plt.show()
    colors = nx.algorithms.greedy_color(G)
    
    data = {
        'regions': regions,
        'k': k,
        'numNonDegParts': degSet['dir_patterns'],
        'colors': colors
    }
    return data
    
# if __name__ == "__main__":
    # Start the WebSocket server

async def handle_client(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        action = data.get('action')
        params = data.get('params', [])

        if action == 'stage':
            bipartite_figures = stagePartitioning(params[0])
            message = {'type': 'stage', 
                       'message': {
                            # 'max_sets': len(max_sets), 
                            'bipartite_figures':bipartite_figures
                            }
                        }
            await websocket.send(json.dumps(message))
        elif action == 'get':
            data = getPartition(params[0])
            message = {'type': 'get', 
                       'message': {
                            'regions': data['regions'],
                            'k': data['k'],
                            'numNonDegParts':data['numNonDegParts'],
                            'colors':data['colors']
                        }
                       }
            await websocket.send(json.dumps(message))

async def start_server():
    print('Starting WebSocket server...')
    try:
        server = await websockets.serve(handle_client, 'localhost', 8765)
    except Exception as e:
        print(f'WebSocket server failed to start: {e}')
    else:
        print('WebSocket server started!')
        await server.wait_closed()

asyncio.run(start_server())

    # print("hello2")
    # input_json = sys.argv[1]
    # input = json.loads(input_json)

    # function = input['function']
    # if(function=="stagePartitioning"):
    #     stagePartitioning(input)

    # max_sets = degenerateDecomposition.getMaxIndependentSet(horizontal,vertical,intersections,corner_lists)
    # corner_lists = degenerateDecomposition.decompose(max_sets[deg_set_num],corner_lists)
    
    # regions = []
    # nondegenerateDecomposition.decompose(0, corner_lists, regions, k)
    # data = {
    #     'regions': regions,
    #     'k': len(independent_sets)
    # }
    # print(json.dumps(data))