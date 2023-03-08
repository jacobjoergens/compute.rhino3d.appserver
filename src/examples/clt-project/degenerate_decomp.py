
from itertools import chain
from itertools import groupby
import math
import operator 
from operator import itemgetter
import networkx as nx

G = nx.Graph()
print("Hello world!")
print(G)

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
Definition:
    a Corner is a data structure that contains information on the intersection 
    between two line segments and how 
"""
class Corner:
    def __init__(self, leg_a, vertex, leg_b):
        self.prev = None
        self.vertex = vertex
        self.next = None
        self.prev_edge = leg_a
        self.next_edge = leg_b
        self.vertical, self.horizontal = self.assignLegs(leg_a,leg_b)
        self.concave = False 
        self.xcol = None
        self.ycol = None 
        
    def assignLegs(self,leg_a,leg_b):
        endpts = gh.EndPoints(leg_a)
        if(endpts[0][0]==endpts[1][0]):
            vertical = leg_a
            horizontal = leg_b
        else: 
            vertical = leg_b 
            horizontal = leg_a
        return vertical,horizontal

class cornerList: 
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0
        self.concave_count = 0 
        self.colinear_pairs = 0 
        self.interior = True 
        
    def make(self, new_corner): 
        if(self.tail==None):
            self.head = new_corner
            self.tail = new_corner
        else: 
            new_corner.prev = self.tail 
            self.tail.next = new_corner 
            self.tail = new_corner
            self.tail.next = self.head
            self.head.prev = self.tail
        self.length+=1

    def stitch(self, prev_corner, new_corner, next_corner): 
        horver = ["horizontal","vertical"]
        if(getattr(next_corner,horver[0])!=next_corner.prev_edge):
            horver = horver[::-1]
        next_corner.prev = new_corner
        next_corner.prev_edge = new_corner.next_edge
        new_corner.next = next_corner
        prev_corner.next = new_corner
        prev_corner.next_edge = new_corner.prev_edge
        new_corner.prev = prev_corner
        setattr(next_corner,horver[0],new_corner.next_edge)
        setattr(prev_corner,horver[1],new_corner.prev_edge)
        next_corner.assignLegs(next_corner.prev_edge,next_corner.next_edge)
        prev_corner.assignLegs(prev_corner.prev_edge,prev_corner.next_edge)
        
    def updateState(self):
        start = self.head
        current_corner = start.next
        self.length = 1
        self.concave_count = 1*start.concave
        while current_corner != start:
            self.length+=1
            self.concave_count+=1*current_corner.concave
            current_corner = current_corner.next
    
#    def reverseCorners(self):
#        print("Reversing intersection list")
#        current = self.head
#        for i in range(self.length):
#            tmp = current.prev
#            current.prev = current.next
#            current.next = tmp
#            tmp_edge = current.prev_edge
#            current.prev_edge = current.next_edge
#            current.next_edge = tmp_edge
#            current = current.next
#        self.tail = self.head.prev
        
def drawBounding(vertices):
    sorted_indices = [i[0] for i in sorted(enumerate(vertices), key=lambda x:(x[1][0],x[1][1]))]
    bottom_left = vertices[sorted_indices[0]]
    top_right = vertices[sorted_indices[-1]]
    bounding = gh.Rectangle2Pt(gh.XYPlane(bottom_left),bottom_left,top_right,0).rectangle
    return bounding, sorted_indices[0]

"""
A leftmost point must be convex.
Call that vertex V, the previous one is U and the next one is W.
Find the vectors a = U - V and b = W - V. Compute the cross-product of a and b 
Then continue around the polygon. At each vertex do the same computation If the result has
 the same sign as the first, it's concave, else convex.
"""    
def filterConcaveVertices(curve):
    print("Curve: ", curve)
    concave = []
    labelled_edges = []
    if(len(curve)>1):
        max_area_index = argmax(gh.Area(curve).area)
        curve.insert(0,curve.pop(max_area_index))
    corner_lists = []
    for i in range(len(curve)):
        corner_lists.append(cornerList())
        if(i==0):
            corner_lists[0].interior = False
        edges, vertices = gh.Explode(curve[i],False)
        vertices.pop(-1)
        bounding, leftmost = drawBounding(vertices)
        
        if(i==0 and gh.CrossProduct(edges[(leftmost-1)%len(vertices)],edges[leftmost%len(vertices)],True).vector[2]==-1):
            flow = -1
        elif(i>0 and gh.CrossProduct(edges[(leftmost-1)%len(vertices)],edges[leftmost%len(vertices)],True).vector[2]==1):
            flow = -1
        else: 
            flow = 1
            
        
        for j in range(len(vertices)):
            V = vertices[(leftmost+j*flow)%len(vertices)]
            
            if(flow==-1):
                next_edge = edges[(leftmost+(j+1)*flow)%len(vertices)]
                prev_edge = edges[(leftmost+j*flow)%len(vertices)]
            else:
                next_edge = edges[(leftmost+j*flow)%len(vertices)]
                prev_edge = edges[(leftmost+(j-1)*flow)%len(vertices)]
            z = gh.CrossProduct(prev_edge,next_edge,True).vector
            dot = gh.DotProduct(z,gh.UnitZ(1),True)
            labelled_edges.append(sorted(gh.EndPoints(next_edge),key=lambda coor: (coor[0],coor[1])))
            new_corner = Corner(prev_edge, V, next_edge)
            
            if(dot==-1):
                concave.append(V)
                new_corner.concave=True
                corner_lists[i].concave_count+=1
            corner_lists[i].make(new_corner)
    print("Concave: ",concave)        
    return concave, labelled_edges, corner_lists, bounding

def findCogridVertices(concave, ind):
    sorted_concave = sorted(concave, key=lambda coor: (coor[ind], coor[(ind+1)%2])) 
    mark = sorted_concave[0]
    matched = False
    colinear = []
    for i in range(1,len(sorted_concave)):
        if(mark[ind]==sorted_concave[i][ind]):
            colinear.append([mark,sorted_concave[i]])
        mark = sorted_concave[i]
    return colinear 
        
def constructChords(cogrid_pairs, labelled_edges):
    chords = []
    for i in range(len(cogrid_pairs)): 
        for j in range(len(cogrid_pairs[i])-1):
            if([cogrid_pairs[i][j],cogrid_pairs[i][j+1]] not in labelled_edges):
                if([cogrid_pairs[i][j+1],cogrid_pairs[i][j]] not in labelled_edges):
                    chords.append(gh.Line(cogrid_pairs[i][j],cogrid_pairs[i][j+1]))
    return chords
 
def sortTransverseSegments(corner, corner_lists, horver, dir, oper):
    opdir = (dir+1)%2
    base = getattr(corner,horver[dir])
    horver = horver[opdir]
    base_endpts = sorted(gh.EndPoints(base),key=lambda x:x[dir])
    mid = (base_endpts[0][dir]+base_endpts[1][dir])/2
    trans = []
    intersection_corner = None
    intersection_list = None
    ext_length = 0
    
    
    for i in range(len(corner_lists)): 
        if(i==0):
            current_corner = corner.next.next
            clip = 3
        else: 
            current_corner = corner_lists[i].head
            clip = 0
        
        for j in range(corner_lists[i].length-clip):
            current_edge = getattr(current_corner,horver)
            
            if(current_edge!=current_corner.prev_edge):
                endpts = gh.EndPoints(current_edge)
                opend = sorted(endpts, key=lambda x: x[opdir])
                if(oper(endpts[0][dir],corner.vertex[dir])):
                    if(opend[0][opdir]<=corner.vertex[opdir] and opend[1][opdir]>=corner.vertex[opdir]):
                        current_distance = abs(endpts[0][dir]-corner.vertex[dir])
                        if(intersection_corner==None):
                            intersection_corner = current_corner
                            ext_length = abs(endpts[0][dir]-corner.vertex[dir])
                            intersection_list = i
                        elif(ext_length>current_distance):
                            intersection_corner = current_corner
                            ext_length = current_distance
                            intersection_list = i
            current_corner = current_corner.next
    return intersection_corner, ext_length, intersection_list
                
def extendCurve(ext_corner,corner_lists,dir):
    horver = ["horizontal","vertical"]
    endpts = sorted(gh.EndPoints(getattr(ext_corner,horver[dir])),key = lambda x: x[dir])
    vertex = ext_corner.vertex
    
    if(vertex==endpts[0]):
        extend_point = endpts[1]
    else: 
        extend_point = endpts[0]
    
    vect = gh.Vector2Pt(extend_point,vertex,False)
    
    if(gh.DotProduct(gh.VectorXYZ(1,1,1).vector,vect.vector,True)<0):
        oper = operator.lt
    else: 
        oper = operator.gt
    
    intersection_corner, ext_length, intersection_list = sortTransverseSegments(ext_corner, corner_lists, horver, dir, oper)
    return gh.LineSDL(vertex,vect.vector,ext_length), intersection_corner, intersection_list, horver

def updateColCounts(shortlist, longlist, corner, dir):
    col = getattr(corner,dir)
    if(col!=None):
        if(shortlist.get(col)==None):
            comp_corner = longlist.get(col)
            setattr(comp_corner,ycol,None)
            setattr(corner,ycol,None)
            shortlist.colinear_count-=1
            longlist.colinear_count-=1
            
def updateColinearCorners(a_list, b_list):
    if(a_list.length>=b_list.length):
        shortlist = b_list
        longlist = a_list
    else: 
        shortlist = a_list
        longlist = b_list
    curcorn = shortlist.head
    for i in range(shortlist.length): 
        updateColCounts(shortlist, longlist, curcorn, 'ycol')
        updateColCounts(shortlist, longlist, curcorn, 'xcol')
        curcorn = curcorn.next

def cornersToCurve(corner_list): 
    segments = []
    curcorner = corner_list.head
    for i in range(corner_list.length): 
        segments.append(curcorner.next_edge)
        curcorner = curcorner.next
    curve = gh.JoinCurves(segments,False)
    #print(curve)
    return curve
"""
Definitions:
leg_a: vertex edge parallel to chord 
leg_b: vertex edge perpindicular to chord
Region A is the region formed by joining the chord leg a
Region B is the region formed by taking the chord as a standalone segment

"""
def doPartition(ext_corner, chord, intersection_corner, intersection_list, corner_lists, horver, dir):
    opdir = (dir+1)%2
    a_list = corner_lists[0]
    intersection_vertex = chord[1]
    intersection_edge = intersection_corner.next_edge
    endpts = gh.EndPoints(intersection_edge)
    
    ray = getattr(ext_corner,horver[dir])
    a_seg = gh.JoinCurves([chord,ray],False)
    ab_shard = [gh.Line(chord[1],endpts.start),gh.Line(chord[1],endpts.end)]
    
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
    
    return corner_lists, b_list, chord
    
def iterLoop(corners): 
    current_corner = corners.head
    edges = []
    vertices = []
    
    for i in range(corners.length):
        edges.append(current_corner.next_edge)
        vertices.append(current_corner.vertex)
        current_corner = current_corner.next
    return edges, vertices

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
        corner_lists, b_list, vertex = doPartition(current_corner, chord, intersection_corner, intersection_list, corner_lists, horver, dir)
        if((pattern)%3==0):
            dir = (dir+1)%2
        nonDegenerateDecomposition(dir,corner_lists,regions,pattern+1)
#        edges, vertex = iterLoop(corner_lists[0])
#        return edges, vertex
"""
Main: 
I. filterConcaveVertices
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

concave, labelled_edges, corner_lists, bounding = filterConcaveVertices(curve)
x_col = findCogridVertices(concave, 0)
y_col = findCogridVertices(concave, 1)
deconstruct_bound = gh.DeconstuctRectangle(bounding)
if(deconstruct_bound.x_interval>=deconstruct_bound.y_interval):
    bias_dir=0
    cogrid_pairs = x_col+y_col
else: 
    bias_dir=1
    cogrid_pairs = y_col+x_col

regions = []
nonDegenerateDecomposition(bias_dir, corner_lists, regions, 0)