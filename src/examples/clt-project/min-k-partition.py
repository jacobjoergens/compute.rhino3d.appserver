import ingest 
import nondegenerateDecomposition
import degenerateDecomposition
import sys
import json
import asyncio
import websockets
import itertools
import copy

sys.stdout.flush()

corner_lists = None
k = 0
deg_partitions = {}
dir_patterns = None 
concave_corners = None
max_sets = []

def stagePartitioning(input):
    global corner_lists, k, max_sets
    curve = input['crvPoints']
    k = input['k']
    
    corner_lists, max_extent = ingest.digestCurves(curve)
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

def getPartition(input): 
    global corner_lists, k, deg_partitions
    degSetIndex = input['degSetIndex']
    index = input['index']

    if(degSetIndex not in deg_partitions): 
        deg_corner_lists = []
        conversionTable = {}
        for corner_list in corner_lists:
            deg_corner_lists.append(corner_list.copyList(conversionTable))

        max_set = []
        for deg_chord in max_sets[degSetIndex]:
            max_set.append((conversionTable[deg_chord[0]],conversionTable[deg_chord[1]]))

        nonDegBasis = degenerateDecomposition.decompose(max_set,deg_corner_lists)

        concave_corners = getConcaveCorners(nonDegBasis)
        deg_partitions[degSetIndex] = { 
            'set': nonDegBasis,
            'concave_corners': concave_corners,
            'dir_patterns': list(itertools.product([0, 1], repeat=len(concave_corners)))
        }
        

    regions = []
    degSet = deg_partitions[degSetIndex]
    conversionTable = {}
    non_deg_corner_lists = []
    for corner_list in degSet['set']: 
        non_deg_corner_lists.append(corner_list.copyList(conversionTable))
    


    concave_corners = []
    for corner in degSet['concave_corners']:
        concave_corners.append(conversionTable[corner])
    nondegenerateDecomposition.decompose(degSet['dir_patterns'][index], concave_corners, non_deg_corner_lists, regions, k)
    data = {
        'regions': regions,
        'k': k,
        'numNonDegParts': degSet['dir_patterns']
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
                            'numNonDegParts':data['numNonDegParts']
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