from ingest import Corner
from ingest import cornerList
from ingest import sortTransverseSegments
import operator
import numpy as np

"""
Description: extend a leg of a concave Corner in the given direction (non-degenerate partitioning)
Parameters: 
    -ext_corner (Corner)
    -corner_lists (list)
    -dir (number)
Output: Rhino.Geometry.Line
"""
def extendCurve(ext_corner,corner_lists,dir):
    #extract and sort the endpoints of the leg to be extended
    horver = ["horizontal","vertical"]
    
    #the vertex of the extension of the corner is going to be swallowed so the extend_point is whichever endpt!=vertex
    if(getattr(ext_corner,horver[dir])==ext_corner.next_edge):
        extend_point = ext_corner.next.vertex
    else: 
        extend_point = ext_corner.prev.vertex

    #direction of extension = vector from extend_point to ext_vertex
    vect = np.array(ext_corner.vertex)-np.array(extend_point)
    
    #calculate which direction to check for intersections in
    if(np.dot([1,1,1],vect)<0):
        oper = operator.lt #left, below
    else: 
        oper = operator.gt #right, above
    
    intersection_corner, ext_length, intersection_list = sortTransverseSegments(ext_corner, corner_lists, horver, dir, oper)
    end = tuple(ext_corner.vertex + vect/np.linalg.norm(vect)*ext_length)
    return (ext_corner.vertex,end), intersection_corner, intersection_list, horver

"""
Definitions:
Region A is the region formed from the extension of extend_point (in extendCurve)
Region B is the region formed by taking the chord as a standalone segment

Description: performs single non-degenerate "cut" or partition given the following paramaters
Parameters: 
    -ext_corner (Corner): a corner to extend from
    -dir (number): a direction of extension
    -chord (Rhino.Geometry.Line): the resultant chord from extension
    -intersection_corner (Corner): corner whose next_edge is intersected by chord
    -intersection_list (number): index of cornerList intersected
    -corner_lists (list)
    
Output: 
    -corner_lists: with updated list @ intersection_list and a new list (b_list) appended 
"""
def doPartition(ext_corner, chord, intersection_corner, intersection_list, corner_lists, dir):
    a_list = corner_lists[0] 
    intersection_vertex = chord[1]
    intersection_edge = intersection_corner.next_edge
    endpts = [intersection_edge[0],intersection_edge[1]]
    horver = ["horizontal","vertical"]


    ray = getattr(ext_corner,horver[dir])

    if(ray==ext_corner.next_edge):
        a_seg = (chord[0],ext_corner.next.vertex)
    else: 
        a_seg = (chord[0],ext_corner.prev.vertex)

    ab_shard = ((chord[1],endpts[0]),(chord[1],endpts[1]))
    
    #assert affiliation between ab_shard[0] and a_corner
    if(ab_shard[0][1]!=intersection_corner.next.vertex):
        ab_shard = ab_shard[::-1]
    if(ray==ext_corner.prev_edge):
        a_corner = Corner(a_seg, intersection_vertex, ab_shard[0])
        a_prev = ext_corner.prev 
        a_next = intersection_corner.next
        b_corner = Corner(ab_shard[1], intersection_vertex, chord)
        b_prev = intersection_corner 
        b_next = ext_corner
    elif(ray==ext_corner.next_edge):
        a_corner = Corner(ab_shard[1], intersection_vertex, a_seg)
        a_prev = intersection_corner 
        a_next = ext_corner.next
        b_corner = Corner(chord, intersection_vertex, ab_shard[0])
        b_prev = ext_corner
        b_next = intersection_corner.next
        
    a_list.stitch(a_prev, a_corner, a_next, True)
    a_list.head = a_corner
    a_list.tail = a_prev
    
    a_list.stitch(b_prev, b_corner, b_next, True)
    ext_corner.concave = False
    a_list.updateState()
    
    b_list = None
    if(intersection_list==0):
        b_list = cornerList()
        b_list.head = b_corner
        b_list.tail = b_prev
        b_list.updateState()
        corner_lists.append(b_list)
    else: 
        corner_lists.pop(intersection_list)
    
    return corner_lists, chord

"""
Description: recursive function to follow non-degenerate partitioning algorithm
Parameters: 
    -dir (number): denotes which curve to extend in extendCurve
    -corner_lists (list of cornerLists): holds initial cornerList data and subsequent intermediate partitions
    -regions: array holding k-partitions (currently k=4 always)
    -pattern (number): used to alternate direction of extension 
Output: None (appends to regions)
"""
def decompose(dir,corner_lists,regions,pattern):
    total_count = 0 
    ext_corner = None
    for i in range(len(corner_lists)):
        total_count+=corner_lists[i].concave_count
        if(corner_lists[i].concave_count>0 and ext_corner==None):
            current_corner = corner_lists[i].head
            while(current_corner.concave==False): 
                current_corner = current_corner.next
            corner_lists.insert(0,corner_lists.pop(i))
            ext_corner = current_corner
    if(total_count==0):
        for corner_list in corner_lists:
            edges, vertices = corner_list.iterLoop()
            vertices.append(vertices[0])
            regions.append(vertices)
    else: 
        chord, intersection_corner, intersection_list, horver = extendCurve(current_corner,corner_lists,dir)
        corner_lists, vertex = doPartition(current_corner, chord, intersection_corner, intersection_list, corner_lists, dir)
        if((pattern)%3==0):
            dir = (dir+1)%2
        decompose(dir,corner_lists,regions,pattern+1)
#        edges, vertex = iterLoop(corner_lists[0])
#        return edges, vertex