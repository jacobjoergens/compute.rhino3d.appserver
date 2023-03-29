import ingest 
import nondegenerateDecomposition
import degenerateDecomposition
import sys
import json

if __name__ == "__main__":
    input_json = sys.argv[1]
    input = json.loads(input_json)
    curve = input['crvPoints']
    k = input['k']
    corner_lists, max_extent = ingest.digestCurves(curve)
    concave_corners = ingest.findConcaveVertices(corner_lists)
    
    horizontal = ingest.findColinearVertices(corner_lists, concave_corners.copy(),0)
    vertical = ingest.findColinearVertices(corner_lists, concave_corners,1)
    intersections = ingest.findIntersections(horizontal,vertical)
    # # for i in range(len(corner_lists)):
    # #         print(i, corner_lists[i].length, corner_lists[i].concave_count)
    corner_lists, G = degenerateDecomposition.decompose(horizontal,vertical,intersections,corner_lists)
    
    regions = []
    nondegenerateDecomposition.decompose(0, corner_lists, regions, 0)
    data = {
        'regions': regions,
        'k': k
    }
    print(json.dumps(data))
    # serializedObj = json.dumps(intersections, cls=CustomEncoder)
    # print(json.dumps(degenerateDecomposition(horizontal,vertical,intersections).edges))
    # for corner_list in corner_lists: 
    #     print(corner_list.iterLoop())