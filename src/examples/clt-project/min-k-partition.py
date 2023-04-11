import ingest 
import nondegenerateDecomposition
import degenerateDecomposition
import sys
import json
import asyncio
import websockets
import signal 
import socket
import queue 
import os

sys.stdout.flush()

corner_lists = None
k = 0

def stagePartitioning(input):
    global corner_lists, k
    curve = input['crvPoints']
    k = input['k']
    # deg_set_num = input['deg_set_num']
    corner_lists, max_extent = ingest.digestCurves(curve)
    concave_corners = ingest.findConcaveVertices(corner_lists)
    
    horizontal = ingest.findColinearVertices(corner_lists, concave_corners.copy(),0)
    vertical = ingest.findColinearVertices(corner_lists, concave_corners,1)
    intersections = ingest.findIntersections(horizontal,vertical)
    max_sets, G, top, bottom, h_counter, v_counter = degenerateDecomposition.getMaxIndependentSet(horizontal,vertical,intersections,corner_lists)
    bipartite_figures = degenerateDecomposition.generateGraphs(max_sets, G, top, bottom, horizontal, vertical, h_counter, v_counter)
    return max_sets, bipartite_figures

def getPartition(max_set): 
    global corner_lists, k
    corner_lists = degenerateDecomposition.decompose(max_set,corner_lists)
    
    regions = []
    nondegenerateDecomposition.decompose(0, corner_lists, regions, k)
    data = {
        'regions': regions,
        'k': k
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
            max_sets, bipartite_figures = stagePartitioning(params[0])
            message = {'type': 'stage', 
                       'message': {
                            'max_sets': len(max_sets), 
                            'bipartite_figures':bipartite_figures}}
            await websocket.send(json.dumps(message))
        elif action == 'get':
            data = getPartition(max_sets[params[0]])
            message = {'type': 'get', 
                       'message': f"length of corner_list at index {params[0]}: {len(data['regions'])}",
                       'body': data}
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