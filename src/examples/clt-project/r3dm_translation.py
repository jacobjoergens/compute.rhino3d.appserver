import rhino3dm as rh
from itertools import chain
from itertools import combinations
import operator 
from operator import itemgetter
import networkx as nx
import sys
import compute_rhino3d.Util
import compute_rhino3d.AreaMassProperties
import json
import numpy as np
import matplotlib.pyplot as plt
import enumMatchings


compute_rhino3d.Util.url = "http://localhost:8081/"

#returns the index of the minimum element in an array
def argmin(a):
    return min(enumerate(a), key=itemgetter(1))[0]
    
#returns the index of the maximum element in an array
def argmax(a):
    return max(enumerate(a), key=itemgetter(1))[0]
    
#returns the index of an element in a if it is equal to an element in b
def argeq(a,b):
    a_index = None
    for i in range(len(b)):
        for j in range(len(a)):
            if(abs(b[i][0]-a[j][0])<0.1 and abs(b[i][1]-a[j][1])<0.1):
                a_index = j
    return a_index

 
"""
Description:
-a Corner is a data structure that stores information on the vertices between edges of an input curve
"""
class Corner:

    """
    Description: defines a corner object
    Parameters: 
        -vertex (Rhino.Geometry.Point3D): a point defined by x, y and z components
        -leg_a, leg_b (Rhino.Geometry.Line): a line defined by start and end points
    Assignments: 
        -leg_a: corner's trailing edge
        -leg_b: corner's forward edge
        -horizontal/vertical: calculates and stores which leg is which
        -prev/next (corners): null (by default)
        -concave: false (by default)
    """
    #TODO Look into making subclasses for prev and next that store edge and hor/ver info
    def __init__(self, leg_a, vertex, leg_b):
        self.prev = None
        self.vertex = vertex
        self.next = None
        self.prev_edge = leg_a
        self.next_edge = leg_b
        self.assignLegs(leg_a,leg_b)
        self.concave = False 
    
    """
    Description: assigns a pair of edges horizontal/vertical labels, there will always be one of each
    Parameters: leg_a, leg_b (Rhino.Geometry.Line)
    Output: vertical, horizontal (Rhino.Geometry.Line) 
    """
    def assignLegs(self,leg_a,leg_b):
        endpts = [leg_a.From, leg_a.To]
        if(endpts[0].X==endpts[1].X):
            vertical = leg_a
            horizontal = leg_b
        else: 
            vertical = leg_b 
            horizontal = leg_a
        self.vertical = vertical
        self.horizontal = horizontal

"""
Description: a doubly-linked list of Corner objects corresponding to the vertices of a single curve
"""
class cornerList: 
    """
    Description: initiate an empty doubly-linked list 
    """
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0
        self.concave_count = 0 
        self.colinear_pairs = 0 
        self.exterior = False #true if this corner list represents is an exterior curve

    """
    Description: appends a new Corner to the end of the doubly-linked list
    Parameters: new_corner (Corner)
    """    
    def make(self, new_corner): 
        if(self.tail==None):  #if the list is empty set head and tail to new_corner
            self.head = new_corner
            self.tail = new_corner
        else: #otherwise follow logic to insert new_corner at end
            new_corner.prev = self.tail #link new_corner to current tail
            self.tail.next = new_corner 
            self.tail = new_corner #update tail to new_corner
            self.tail.next = self.head #link new_corner to head
            self.head.prev = self.tail
        self.length+=1 

    """
    Description: insert a new Corner between any two extant corners
    Parameters: 
        -prev_corner (Corner): update the "next" attributes of an existing corner to match new_corner's
        -new_corner (Corner): a new corner with prev_edge and next_edge predefined
        -next_corner (Corner): update the "prev" attributes of an existing corner to match new_corner's
    """
    def stitch(self, prev_corner, new_corner, next_corner): 
        #handle horizontal/vertical pointers
        horver = ["horizontal","vertical"] 
        if(getattr(next_corner,horver[0])!=next_corner.prev_edge):
            horver = horver[::-1]
        #link next_corner to new_corner
        next_corner.prev = new_corner
        next_corner.prev_edge = new_corner.next_edge
        new_corner.next = next_corner
        #link prev_corner to new_corner
        prev_corner.next = new_corner
        prev_corner.next_edge = new_corner.prev_edge
        new_corner.prev = prev_corner
        #update horizontal/vertical attributes
        # setattr(next_corner,horver[0],new_corner.next_edge)
        # setattr(prev_corner,horver[1],new_corner.prev_edge)
        next_corner.assignLegs(next_corner.prev_edge,next_corner.next_edge)
        prev_corner.assignLegs(prev_corner.prev_edge,prev_corner.next_edge)

    """
    Description: traverse list and recount/update list-level attributes
    """  
    def updateState(self):
        start = self.head
        current_corner = start.next
        #reset list-level attributes
        self.length = 1
        self.concave_count = 1*start.concave
        #traverse and update
        while current_corner != start:
            self.length+=1
            self.concave_count+=1*current_corner.concave
            current_corner = current_corner.next
    
    """
    Description: debugging helper function, traverses a given cornerList and outputs two arrays holding edges and vertices
    Parameters: 
        -corners (cornerList)
    Output: 
        -edges (list): array of line segments
        -vertices (list): array of vertices
    """
    def iterLoop(self): 
        current_corner = self.head
        edges = []
        vertices = []
        
        for i in range(self.length):
            edges.append(current_corner.next_edge)
            vertices.append(current_corner.vertex)
            current_corner = current_corner.next
        return edges, vertices
    

class Intersection:
    def __init__(self,point,l1,l2):
        self.point = point
        self.l1 = l1
        self.l2 = l2


def point(point):
    return np.array([point.X,point.Y,point.Z])

def line(line):
    return np.array([point(line.From),point(line.To)])

def lineToVector(line):
    return point(line.From)-point(line.To)
"""
Description: get the xy extents of the input geometry
Parameters: vertices (list): a list of vertices from an input curve
Outputs: 
    -bottom_left_index (number): the index of the input param corresponding to the bottom-left vertex
    -max_extent (string): indicates which side of a hypothetical bounding rectangle is greatest
"""        
def calculateExtents(vertices):
    sorted_indices = [i[0] for i in sorted(enumerate(vertices), key=lambda x:(x[1][0],x[1][1]))]
    bottom_left_index = sorted_indices[0]
    bottom_left = vertices[bottom_left_index]
    top_right = vertices[sorted_indices[-1]]
    if(abs(bottom_left[0]-top_right[0])==abs(bottom_left[1]-top_right[1])):
        max_extent = "square"
    elif(abs(bottom_left[0]-top_right[0]>abs(bottom_left[1]-top_right[1]))):
        max_extent = "x"
    else: 
        max_extent = "y"
    return bottom_left_index, max_extent

# def lineToVector(line):
#     vector = np.array([line.To.X,line.To.Y,line.To.Z])-np.array([line.From.X,line.From.Y,line.From.Z])
#     return vector

def crossProduct(line1,line2,normalized):
    vec1 = lineToVector(line1)
    vec2 = lineToVector(line2)
    cross = np.cross(vec1,vec2)
    if normalized and np.linalg.norm(cross)!=0:
        return cross/np.linalg.norm(cross) 
    else:
        return cross
"""
Description: build corner_lists from input curves 
Parameters: curves (list of Rhino.Geometry.NurbsCurves)
Output: 
    -corner_lists (list of cornerLists): 
        I. create a cornerList for each input curve
            a. construct Corners from each vertex
                i. determine whether a given vertex is concave
    -max_extent: prevailing dimension of the input curves
"""    
def digestCurves(curve_data):
    curves = []
    input_vertices = []
    input_edges = []
    areas = []
    json_dict = json.loads(curve_data)
    for i in range(len(json_dict)):
        points = rh.Point3dList(len(json_dict[i]))
        input_vertices.append([])
        input_edges.append([])# curves.append(rh.NurbsCurve.Create(False, 1, json_dict[points]))
        for j in range(len(json_dict[i])):
            points.Add(*json_dict[i][j])
            input_vertices[i].append(json_dict[i][j])
            if(j>0):
                input_edges[i].append(rh.Line(points[j-1],points[j]))
        curves.append(rh.NurbsCurve.Create(False,1,points))
        areas.append(compute_rhino3d.AreaMassProperties.Compute(curves[i])['Area'])
    

    corner_lists = []

    #push largest curve to index 0 
    if(len(curves)>1):
        max_area_index = argmax(areas)
        if(max_area_index!=0):
            curves.insert(0,curves.pop(max_area_index))
            input_vertices.insert(0,input_vertices.pop(max_area_index))
            input_edges.insert(0,input_edges.pop(max_area_index))

    for i in range(len(curves)): #loop through curves
        vertices = input_vertices[i]
        edges = input_edges[i]
        corner_lists.append(cornerList()) 
        vertices.pop(-1) #if an input curve is closed (which it must be) then the last vertex is the same as the first
        
        #the bottom leftmost vertex must be convex 
        leftmost, extent = calculateExtents(vertices)
        if(i==0): 
            corner_lists[0].exterior = True #set the curve with greatest area to be an exterior curve
            max_extent = extent #set max_extent from prevailing dimension of the largest curve

        #calculate the direction at the bottom leftmost vertex from the input curve 
        rhrule = crossProduct(edges[(leftmost-1)%len(vertices)],edges[leftmost%len(vertices)],True)[2]
        
        #set direction conventions 
        if((corner_lists[i].exterior==True and rhrule==-1) or (corner_lists[i].exterior==False and rhrule==1)):
            flow = -1
        else: 
            flow = 1

        for j in range(len(vertices)): #loop through vertices in input curve (backwards if flow is -1) 
            V = vertices[(leftmost+j*flow)%len(vertices)] 
            
            if(flow==-1):
                next_edge = edges[(leftmost+(j+1)*flow)%len(vertices)]
                prev_edge = edges[(leftmost+j*flow)%len(vertices)]
            else:
                next_edge = edges[(leftmost+j*flow)%len(vertices)]
                prev_edge = edges[(leftmost+(j-1)*flow)%len(vertices)]

            #perform right-hand rule at each vertex
            z = crossProduct(prev_edge,next_edge,True) 
            dot = np.dot(z,np.array([0,0,1]))
            # labelled_edges.append(sorted(gh.EndPoints(next_edge),key=lambda coor: (coor[0],coor[1])))
            new_corner = Corner(prev_edge, V, next_edge)
            
            #if the direction is not the same as the first vertex, then this vertex is concave
            if(dot==-1):
                # concave.append(V)
                new_corner.concave=True
                corner_lists[i].concave_count+=1

            #add new corner to cornerList
            corner_lists[i].make(new_corner)
    return corner_lists, max_extent

"""
Description: traverse through corner_lists and append concave corners to output array
Parameters: corner_lists (list of cornerLists)
Output: concave_corners (list of Corners)
"""
def findConcaveVertices(corner_lists):
    concave_corners = []
    i = 0
    for list in corner_lists:
        current_corner = list.head
        if(current_corner.concave):
            concave_corners.append(current_corner)
        current_corner = current_corner.next
        while(current_corner!=list.head):
            if(current_corner.concave):
                concave_corners.append(current_corner)
            current_corner = current_corner.next
        i+=1
    return concave_corners

"""
Description: within a given list of concave vertices, find colinear pairs for degenerate decomposition
Parameters: concave_corners (list of Corners)
Output: colinear_pairs (dictionary): colinear pairs stored under appropriate horizontal/vertical key
"""
def findColinearVertices(concave_corners, dir):
    opdir = (dir+1)%2
    horver = ['horizontal','vertical']
    colinear_chords = []
    concave_sort = sorted(concave_corners, key=lambda c: (c.vertex[dir], c.vertex[opdir])) 
    a = concave_sort[0]
    i = 1 
    while(i<len(concave_sort)):
        matched = False 
        if(a.next_edge==getattr(a, horver[opdir])):
            attr = "next"
        else: 
            attr = "prev"
        b = concave_sort[i]
        if(getattr(a,attr)!=b and round(a.vertex[dir],6)==round(b.vertex[dir],6)):
            pair_vector = np.array(b.vertex)-np.array(a.vertex)
            attr_vector = np.array(getattr(a,attr).vertex)-np.array(a.vertex)
            dot = np.dot(pair_vector,attr_vector)
            if(dot/np.linalg.norm(dot)):
                matched = True
        if(matched):
            colinear_chords.append(rh.Line(rh.Point3d(*a.vertex),rh.Point3d(*b.vertex)))
            if(i==len(concave_sort)-1):
              break
            a = concave_sort[i+1]
            i+=2
        else:
            a = b
            i+=1
    return colinear_chords

def findIntersections(horizontal_chords,vertical_chords):
    intersections = []
    h_remove = set()
    v_remove = set()
    for i in range(len(horizontal_chords)):
        iter_pts = [horizontal_chords[i].From,horizontal_chords[i].To]
        iter_pts.sort(key=lambda coor:coor.X)
        for j in range(len(vertical_chords)):
            compare_pts = [vertical_chords[j].From,vertical_chords[j].To]
            compare_pts.sort(key=lambda coor:coor.Y)
            if(round(iter_pts[0].X,6)<=round(compare_pts[0].X,6)<=round(iter_pts[1].X,6)): 
                if(round(compare_pts[0].Y,6)<=round(iter_pts[0].Y,6)<=round(compare_pts[1].Y,6)):
                    pt = rh.Point3d(compare_pts[0].X,iter_pts[0].Y,0)
                    intersect = [horizontal_chords[i], vertical_chords[j], {"point":pt}]
                    h_remove.add(horizontal_chords[i])
                    v_remove.add(vertical_chords[j])
                    intersections.append(intersect)
                    # print(i,"matches at ",j,"th vertical")
    
    for chord in list(h_remove):
        horizontal_chords.remove(chord)
    for chord in list(v_remove):
        vertical_chords.remove(chord)

    return intersections

"""
TODO may have lost the progress I made after changing the name of this function, 
need to go back and think about whether sorting segments is an improvement to the current method
"""
"""
Description: 
Parameters: 
    -corner (Corner): the concave corner undergoing extension
    -corner_lists (list of cornerList)
    -horver (string): direction of extension ("horizontal" or "vertical")
    -dir (number): the direction of extension (0 or 1)
    -oper (operator): determines the direction to check for intersection (left/right, up/down)
Output: 
    -intersection_corner (Corner): the corner whose next_edge is intersected by the extension
    -ext_length (number): magnitude for LineSDL
    -intersection_list (number): index for which cornerList contains the intersection corner
"""
def sortTransverseSegments(corner, corner_lists, horver, dir, oper):
    opdir = (dir+1)%2 #get transverse direction 
    horver = horver[opdir] #determine whether transverse direction is horizontal or vertical 
    intersection_corner = None
    intersection_list = None
    ext_length = 0
    
    
    for i in range(len(corner_lists)): 
        if(i==0): #for the first cornerList 
            current_corner = corner.next.next #remove the next two edges 
            clip = 3 #and the previous two edges from consideration 
        else: 
            current_corner = corner_lists[i].head
            clip = 0
        
        for j in range(corner_lists[i].length-clip):
            current_edge = getattr(current_corner,horver)
            
            #can skip every other vertex because we only care about those whose next_edge is transverse to the direction of extension
            if(current_edge!=current_corner.prev_edge): 
                endpts = [current_edge.From, current_edge.To]
                opend = sorted(endpts, key=lambda x: x[opdir])
                if(oper(endpts[0][dir],corner.vertex[dir])): #only consider segments that lie in the relevant direction 
                    if(opend[0][opdir]<=corner.vertex[opdir] and opend[1][opdir]>=corner.vertex[opdir]): #and those that are intersectable
                        current_distance = abs(endpts[0][dir]-corner.vertex[dir]) 
                        if(intersection_corner==None): #on first intersection
                            intersection_corner = current_corner
                            ext_length = abs(endpts[0][dir]-corner.vertex[dir])
                            intersection_list = i
                        elif(ext_length>current_distance): #check if subsequent intersection is closer
                            intersection_corner = current_corner
                            ext_length = current_distance
                            intersection_list = i
            current_corner = current_corner.next
    return intersection_corner, ext_length, intersection_list

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
    vect = ext_corner.vertex-extend_point
    
    #calculate which direction to check for intersections in
    if(rh.Geometry.Vector3d.DotProduct(rh.Vector3d(1,1,1).vector,vect.vector)<0):
        oper = operator.lt #left, below
    else: 
        oper = operator.gt #right, above
    
    intersection_corner, ext_length, intersection_list = sortTransverseSegments(ext_corner, corner_lists, horver, dir, oper)
    end = ext_corner.vertex + vect/vect.length*ext_length 
    return rh.Line(ext_corner.vertex,end), intersection_corner, intersection_list, horver

"""
Description: builds a curve from a list of corners
"""
def cornersToCurve(corner_list): 
    segments = []
    curcorner = corner_list.head
    for i in range(corner_list.length): 
        segments.append(curcorner.next_edge)
        curcorner = curcorner.next
    joiner = rh.Geometry.CurveJoiner()
    for seg in segments:
        joiner.AddCurve(seg)

    # Join the curves and get the resulting list of joined curves
    joined_curves = joiner.JoinCurves()
    return joined_curves
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
    endpts = [intersection_edge.From,intersection_edge.To]
    horver = ["horizontal","vertical"]


    ray = getattr(ext_corner,horver[dir])

    joiner = rh.Geometry.CurveJoiner()
    joiner.AddCurve(chord)
    joiner.AddCurve(ray)

    # Join the curves and get the resulting list of joined curves
    a_seg = joiner.JoinCurves()
    ab_shard = [rh.Line(chord[1],endpts.start),rh.Line(chord[1],endpts.end)]
    
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
        
    a_list.stitch(a_prev, a_corner, a_next)
    a_list.head = a_corner
    a_list.tail = a_prev
    
    a_list.stitch(b_prev, b_corner, b_next)
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
def nonDegenerateDecomposition(dir,corner_lists,regions,pattern):
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
            regions.append(cornersToCurve(corner_list))
    else: 
        chord, intersection_corner, intersection_list, horver = extendCurve(current_corner,corner_lists,dir)
        corner_lists, vertex = doPartition(current_corner, chord, intersection_corner, intersection_list, corner_lists, dir)
        if((pattern)%3==0):
            dir = (dir+1)%2
        nonDegenerateDecomposition(dir,corner_lists,regions,pattern+1)
#        edges, vertex = iterLoop(corner_lists[0])
#        return edges, vertex

def getDegCorners(corner_lists,deg_chord,dir):
    a_corner = None
    b_corner = None
    from_rounded = [round(coor,6) for coor in point(deg_chord.From)]
    to_rounded = [round(coor,6) for coor in point(deg_chord.To)]
    for i in range(len(corner_lists)):
        current_corner = corner_lists[i].head
        for j in range(corner_lists[i].length):
            current_rounded = [round(coor,6) for coor in current_corner.vertex]
            if(current_rounded==from_rounded or current_rounded==to_rounded):
                if(a_corner==None):
                    a_corner = current_corner
                    a_index= i
                else:
                    b_corner = current_corner
                    b_index = i
                    if(b_index==a_index):
                        if(dir==0):
                            return a_corner, b_corner, a_index, b_index
                        else: 
                            return b_corner, a_corner, b_index, a_index
                    else: 
                        return a_corner, b_corner, a_index, b_index
            current_corner = current_corner.next
    return a_corner, b_corner, a_index, b_index

def stageDegDecompGeometry(corner, horver, dir):
    par = getattr(corner, horver[dir])
    if(corner.next_edge==par):
        forward = "next"
        backward = "prev"
    else: 
        forward = "prev"
        backward = "next"
    print(forward,backward)
    return forward, backward

def degenerateDecomposition(horizontal, vertical, intersections, corner_lists):
    independent_sets = set()
    if(len(intersections)>0):
        G = nx.Graph()
        for ii in intersections:
            G.add_node(ii[0],bipartite=0)
            G.add_node(ii[1],bipartite=1)
        G.add_edges_from(intersections)

        top, bottom =  nx.bipartite.sets(G)
        combined_elements = list(top)+list(bottom)
        combos = list(combinations(combined_elements, len(top)))
        independent_sets.add(combos.pop(0))
        independent_sets.add(combos.pop(-1))
        for combo in combos: 
            if not any(G.has_edge(u,v) for u,v in combinations(combo, 2)):
                independent_sets.add(combo)
        max_set = horizontal+vertical+list(list(independent_sets)[-1])  
    else: 
        max_set = horizontal+vertical    
    """ 
    For now just take the last item
    will handle the different decomp options later
    """
    horver = ["horizontal","vertical"]
    for i in range(len(corner_lists)):
            print(i, corner_lists[i].length)
    # edg, vert = corner_lists[1].iterLoop()
    # print(vert)        
    for deg_chord in max_set:
        # get dot product
        chord_vector = lineToVector(deg_chord)
        deg_dot = np.dot(chord_vector,[0,1,0])
        # normalize dot product
        dir = int(abs(deg_dot / (np.linalg.norm(chord_vector))))
        #by construction, a_index<b_index or if equal a_corner precedes b_corner
        a_corner, b_corner, a_index, b_index = getDegCorners(corner_lists, deg_chord, dir)
        a_list = corner_lists[a_index]
        a_forward, a_backward = stageDegDecompGeometry(a_corner, horver, dir)
        b_forward, b_backward = stageDegDecompGeometry(b_corner, horver, dir)
        
        
        a0 = getattr(a_corner, a_backward)
        a1 = getattr(a_corner, a_forward)
        a2 = getattr(a1, a_forward)
        b0 = getattr(b_corner, b_backward)
        b1 = getattr(b_corner, b_forward)
        b2 = getattr(b1, b_forward)

        # print('aindex:',a_index, 'bindex:',b_index)
        if(dir==0):
            print(a_corner.vertex, b_corner.vertex)
        
        perp_dot = np.dot(np.array(a0.vertex)-np.array(a_corner.vertex),np.array(b0.vertex)-np.array(b_corner.vertex))
        if(perp_dot/np.linalg.norm(perp_dot)==1):
            if(a_index==b_index):
                print("q1", "dir:", dir)
                a_line = [a2, a1, b1]
                b_line = [b0, b_corner, a_corner]
            else: 
                print("q4", "dir:", dir)
                a_line = [a0, a_corner, b_corner]
                b_line = [b2, b1, a1]
                
        else: 
            if(a_index==b_index):
                secondary_dot = np.dot(np.array(a2.vertex)-np.array(a1.vertex),np.array(b2.vertex)-np.array(b1.vertex))
                print(secondary_dot)
                if(secondary_dot/np.linalg.norm(secondary_dot)==1):
                    print('q2.2')
                    a_line = [a0,a_corner,b1]
                    b_line = [b0,b_corner,a1]
                else: 
                    print('q2.1')
                    a_line = [a2, a1, b_corner]
                    b_line = [b2, b1, a_corner]
            else: 
                print("q3", "dir:", dir)
                a_line = [a0, a_corner, b1]
                b_line = [b0, b_corner, a1]
        # should be good till here at least 

        a_seg = rh.Line(rh.Point3d(*a_line[1].vertex), rh.Point3d(*a_line[2].vertex))
        b_seg = rh.Line(rh.Point3d(*b_line[1].vertex), rh.Point3d(*b_line[2].vertex))
        a_line[1].next_edge = a_seg
        b_line[1].next_edge = b_seg

        a_list.stitch(a_line[0],a_line[1],a_line[2])
        a_list.head = a_line[1]
        a_list.tail = a_line[0]
        
        a_list.stitch(b_line[0], b_line[1], b_line[2])
        a_corner.concave = False
        b_corner.concave = False
        a_list.updateState()
        
        if(b_index==a_index):
            b_list = cornerList()
            b_list.head = b_line[1]
            b_list.tail = b_line[0]
            b_list.updateState()
            corner_lists.append(b_list)
        else: 
            corner_lists.pop(b_index)
        # a_list.updateState()
        for i in range(len(corner_lists)):
            print(i, corner_lists[i].length)
    # return corner_lists, G

    
"""
Main: 
I. digestCurves
II. find horziontal colinear vertices 
III. find vertical colinear vertices 
IV. if any exist, construct chords between cogrid vertices
V. Decompose
    a. Degenerate Decomposition 
        i. find maximum matching of a bipartite graph
    b. Non-degenerate Decomposition 
        i. extend curve at each concave vertex (choice between horizontal 
            and vertical can be random but favor whichever direction is parallel 
            with the longest length of the bounding box) 
        ii. doPartition 
            -create new vertex
            -traverse cornerslist in one direction until new region is closed 
                -while traversing, pop corners from old list and insert into new list
"""
    
class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Intersection):
            return {"__class__":'Intersection', 
                    "point":point(o.point).tolist(), 
                    "l1":line(o.l1).tolist(), 
                    "l2":line(o.l2).tolist()}
        return super().default(o)

def plotGraph(graph,ax,title):    
    # pos=[(ii[0],ii[1]) for ii in graph.nodes()]
    pos = nx.bipartite_layout(graph, horizontal)
    # pos_dict=dict(zip(graph.nodes(),pos))
    nx.draw(graph,pos=pos,ax=ax,with_labels=True)
    ax.set_title(title)
    return   

if __name__ == "__main__":
    curve = sys.argv[1]
    # curve = json.dumps()
    print("hello")
    corner_lists, max_extent = digestCurves(curve)
    print("digested")
    concave_corners = findConcaveVertices(corner_lists)
    horizontal = findColinearVertices(concave_corners,1)
    vertical = findColinearVertices(concave_corners,0)
    
    intersections = findIntersections(horizontal,vertical)
    print(len(intersections))
    degenerateDecomposition(horizontal,vertical,intersections,corner_lists)
    # serializedObj = json.dumps(intersections, cls=CustomEncoder)
    # print(json.dumps(degenerateDecomposition(horizontal,vertical,intersections).edges))
    # for corner_list in corner_lists: 
    #     print(corner_list.iterLoop())
    



#regions = []
#nonDegenerateDecomposition(bias_dir, corner_lists, regions, 0)



