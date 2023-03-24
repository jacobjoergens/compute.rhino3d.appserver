import compute_rhino3d.Util
import compute_rhino3d.AreaMassProperties
import numpy as np
import rhino3dm as rh
import json
import operator

compute_rhino3d.Util.url = "http://localhost:8081/"
 
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
        endpts = [leg_a[0], leg_a[1]]
        if(endpts[0][0]==endpts[1][0]):
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
        self.exterior = False #true if this corner list represents is an exterior curve
        self.horizontal_edges = set()
        self.vertical_edges = set()

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
        self.horizontal_edges.add(new_corner.horizontal)
        self.vertical_edges.add(new_corner.vertical)

    """
    Description: insert a new Corner between any two extant corners
    Parameters: 
        -prev_corner (Corner): update the "next" attributes of an existing corner to match new_corner's
        -corner (Corner): a new corner with prev_edge and next_edge predefined
        -next_corner (Corner): update the "prev" attributes of an existing corner to match new_corner's
    """
    def stitch(self, prev_corner, corner, next_corner, new): 
        #handle horizontal/vertical pointers
        horver = ["horizontal","vertical"] 
        if(getattr(next_corner,horver[0])!=next_corner.prev_edge):
            horver = horver[::-1]
        #link next_corner to new_corner
        next_corner.prev = corner
        next_corner.prev_edge = corner.next_edge
        corner.next = next_corner
        #link prev_corner to new_corner
        prev_corner.next = corner
        prev_corner.next_edge = corner.prev_edge
        corner.prev = prev_corner
        #update horizontal/vertical attributes
        # setattr(next_corner,horver[0],new_corner.next_edge)
        # setattr(prev_corner,horver[1],new_corner.prev_edge)
        next_corner.assignLegs(next_corner.prev_edge,next_corner.next_edge)
        prev_corner.assignLegs(prev_corner.prev_edge,prev_corner.next_edge)
        if(not new):
            corner.assignLegs(corner.prev_edge, corner.next_edge)

    """
    Description: traverse list and recount/update list-level attributes
    """  
    def updateState(self):
        start = self.head
        current_corner = start.next
        #reset list-level attributes
        self.length = 1
        self.concave_count = 1*start.concave
        self.horizontal_edges = {start.horizontal}
        self.vertical_edges = {start.vertical}
        #traverse and update
        while current_corner != start:
            self.length+=1
            self.concave_count+=1*current_corner.concave
            current_corner = current_corner.next
            self.horizontal_edges.add(current_corner.horizontal)
            self.vertical_edges.add(current_corner.vertical)
    
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
    areas = np.array([])
    json_dict = json.loads(curve_data)
    for i in range(len(json_dict)):
        points = rh.Point3dList(len(json_dict[i]))
        input_vertices.append([])
        input_edges.append([])# curves.append(rh.NurbsCurve.Create(False, 1, json_dict[points]))
        for j in range(len(json_dict[i])):
            points.Add(*json_dict[i][j])
            input_vertices[i].append(tuple(json_dict[i][j]))
            if(j>0):
                input_edges[i].append((input_vertices[i][j-1],input_vertices[i][j]))
        curves.append(rh.NurbsCurve.Create(False,1,points))
        areas = np.append(areas, compute_rhino3d.AreaMassProperties.Compute(curves[i])['Area'])
    

    corner_lists = []

    #push largest curve to index 0 
    if(len(curves)>1):
        max_area_index = np.argmax(areas)
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
        trailing = edges[(leftmost-1)%len(vertices)]
        leading = edges[leftmost%len(vertices)]
        rhrule = np.cross(np.array(trailing[1])-np.array(trailing[0]),np.array(leading[1])-np.array(leading[0]))[2]
        rhrule = rhrule/abs(rhrule)
        
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
            z = np.cross(np.array(prev_edge[1])-np.array(prev_edge[0]),np.array(next_edge[1])-np.array(next_edge[0]))
            z = z/np.linalg.norm(z)
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

def sortTransverseSegments(corner, corner_lists, dir, oper):
    edges = []
    opdir = (dir+1)%2
    intersection_corner = None
    intersection_list = None
    ext_length = None
    for corner_list in corner_lists: 
        if(dir==0): #direction of extension
            relevant = "vertical_edges"
        else: 
            relevant = "horizontal_edges"
        edges.extend(list(filter(lambda seg: oper(seg[0][dir],corner.vertex[dir])
                                 and min(seg[0][opdir],seg[1][opdir])<=corner.vertex[opdir]<=max(seg[0][opdir],seg[1][opdir]),
                                 list(getattr(corner_list,relevant)))))
    if(oper==operator.gt):
        edges.sort(key=lambda seg:seg[0][dir])
    else:
        edges.sort(key=lambda seg:-seg[0][dir])
    if(len(edges)>0):
        for i in range(len(corner_lists)):
            if(edges[0] in getattr(corner_lists[i],relevant)):
                intersection_list=i
                ext_length = abs(corner.vertex[dir]-edges[0][0][dir])
                break
        current_corner = corner_lists[intersection_list].head
        for j in range(corner_lists[intersection_list].length):
            if(current_corner.next_edge==edges[0]):
                intersection_corner=current_corner
                break
            current_corner = current_corner.next
    return intersection_corner, ext_length, intersection_list

"""
Description: within a given list of concave vertices, find colinear pairs for degenerate decomposition
Parameters: concave_corners (list of Corners)
Output: colinear_pairs (dictionary): colinear pairs stored under appropriate horizontal/vertical key
"""
def findColinearVertices(corner_lists, concave_corners, dir):
    opdir = (dir+1)%2
    horver = ['horizontal','vertical']
    colinear_chords = []
    colinear_dict = {}
    for corner in concave_corners:
        coor = round(corner.vertex[opdir],6)
        if(coor not in colinear_dict):
            colinear_dict[coor]=[]
        colinear_dict[coor].append(corner)

    while(len(concave_corners)>0):
        colinear_array = colinear_dict[round(concave_corners[0].vertex[opdir],6)]
        a_corner = colinear_array[0]
        if(getattr(a_corner,horver[dir])==a_corner.next_edge):
            extension = np.array(a_corner.vertex)-np.array(a_corner.next.vertex)
        else: 
            extension = np.array(a_corner.vertex)-np.array(a_corner.prev.vertex)
        ext_dot = np.dot(extension,np.array([1,1,1]))
        if(ext_dot<0):
            oper = operator.lt
        else:
            oper = operator.gt
        b_corners = list(filter(lambda corner: oper(corner.vertex[dir],a_corner.vertex[dir]),colinear_array[1:]))
        if(len(b_corners)>0):
            b_corners = sorted(b_corners, key=lambda corner:(ext_dot/np.linalg.norm(ext_dot))*corner.vertex[dir])
            b_corner = b_corners[0]
            pair_vect = np.array(b_corner.vertex)-np.array(a_corner.vertex)
            __, ext_length, __ = sortTransverseSegments(a_corner, corner_lists, dir, oper)
            
            if(ext_length and ext_length>=abs(pair_vect[dir])):
                colinear_chords.append((a_corner.vertex,b_corner.vertex))
                colinear_array.remove(a_corner)
                colinear_array.remove(b_corner)
                concave_corners.remove(a_corner)
                concave_corners.remove(b_corner)
            else:
                colinear_array.remove(a_corner)
                concave_corners.remove(a_corner)
        else: 
            colinear_array.remove(a_corner)
            concave_corners.remove(a_corner)
    # print(len(colinear_chords))
    return colinear_chords

def findIntersections(horizontal_chords,vertical_chords):
    intersections = []
    h_remove = set()
    v_remove = set()
    for i in reversed(range(len(horizontal_chords))):
        iter_pts = [horizontal_chords[i][0],horizontal_chords[i][1]]
        iter_pts.sort(key=lambda coor:coor[0])
        for j in reversed(range(len(vertical_chords))):
            compare_pts = [vertical_chords[j][0],vertical_chords[j][1]]
            compare_pts.sort(key=lambda coor:coor[1])
            if(round(iter_pts[0][0],6)<=round(compare_pts[0][0],6)<=round(iter_pts[1][0],6)): 
                if(round(compare_pts[0][1],6)<=round(iter_pts[0][1],6)<=round(compare_pts[1][1],6)):
                    pt = rh.Point3d(compare_pts[0][0],iter_pts[0][1],0)
                    intersect = [horizontal_chords[i], vertical_chords[j], {"point":pt}]
                    h_remove.add(horizontal_chords[i])
                    v_remove.add(vertical_chords[j])
                    intersections.append(intersect)

    for chord in h_remove:
        horizontal_chords.remove(chord)
    for chord in v_remove:
        vertical_chords.remove(chord)

    return intersections