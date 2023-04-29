import numpy as np
import sys
import operator

class Corner: 
    def __init__(self, prev, vertex, next): 
        self.vertex = np.array(vertex)
        self.prev = prev
        self.next = next 
        self.list_index = None 
        self.concave = False

    def assignLegs(self):  
        self.prev_edge = [self,self.prev]
        self.next_edge = [self,self.next]
        if(self.prev_edge[0].vertex[0]==self.prev_edge[1].vertex[0]):
            self.vertical = self.prev_edge
            self.horizontal = self.next_edge
        else: 
            self.vertical = self.next_edge
            self.horizontal = self.prev_edge
        
class Curve: 
    def __init__(self, head=None):
        self.head = None 
        self.tail = None 
        self.length = 0
        self.horizontal_edges = []
        self.vertical_edges = []
        self.concave_corners = []

    def assignLegs(self, corner): 
        corner.assignLegs()
        self.horizontal_edges.append(corner.horizontal)
        self.vertical_edges.append(corner.vertical)
        
    def add(self, new_corner, list_index):
        if(self.tail==None):
            self.head = new_corner
            self.tail = new_corner
        else: 
            new_corner.prev = self.tail
            self.tail.next = new_corner
            self.tail = new_corner
            self.tail.next = self.head
            self.head.prev = self.tail
        
        if(new_corner.concave): 
            self.concave_corners.append(new_corner)

        self.length+=1 
        if(new_corner.prev and new_corner.prev!=self.head):
            self.assignLegs(new_corner.prev)
        new_corner.list_index = list_index

    """
    Description: traverse list and recount/update list-level attributes
    """  
    def updateState(self, list_index):
        start = self.head
        start.list_index = list_index
        current_corner = start.next
        #reset list-level attributes
        self.length = 1
        self.concave_corners = [start] if start.concave else []
        self.horizontal_edges = [start.horizontal]
        self.vertical_edges = [start.vertical]
        #traverse and update
        while current_corner != start:
            if(current_corner.concave):
                self.concave_corners.append(current_corner)

            self.horizontal_edges.append(current_corner.horizontal)
            self.vertical_edges.append(current_corner.vertical)
            current_corner.list_index = list_index
            self.length+=1
            current_corner = current_corner.next

    def branch(self, a, knot, b, list_index):
        b.next = knot
        knot.prev = b
        knot.next = a
        a.prev = knot
        branch = Curve(head=a)
        branch.assignLegs(a)
        branch.assignLegs(knot)
        branch.assignLegs(b)
        branch.updateState(list_index)
        return branch
        
def digestCurves(curve_data, areas):
    curves = []
    
    if(len(curve_data)>1):
        curve_data.insert(0,curve_data.pop(np.argmax(areas)))
        curve_data[0].reverse()

    for i in range(len(curve_data)): 
        vertices = curve_data[i]
        vertices.pop(-1)
        bottom_left_index = [i[0] for i in sorted(enumerate(vertices), key=lambda x:(x[1][0],x[1][1]))][0]
        vertices = vertices[bottom_left_index:]+vertices[:bottom_left_index]
        curve = Curve()

        for j in range(len(vertices)): 
            if(j==len(vertices)-1):
                corner = Corner(curve.tail, vertices[j], curve.head)
            else:
                corner = Corner(curve.tail, vertices[j], None)

            
            prev_vertex = np.array(vertices[(j-1)%len(vertices)])
            next_vertex = np.array(vertices[(j+1)%len(vertices)])
            z = np.cross(prev_vertex-corner.vertex,next_vertex-corner.vertex)
            z/= np.linalg.norm(z)
            dot = np.dot(z,np.array([0,0,1]))
            if(dot==-1):
                corner.concave = True

            curve.add(corner, i)

        curve.assignLegs(curve.head)
        curve.assignLegs(curve.tail)

        curves.append(curve)

    return curves

def sortPerpindicular(corner, dir, sign, curves): 
    opdir = (dir+1)%2
    relevant_set = "vertical_edges" if dir==0 else "horizontal_edges"
    relevant_edges = []
    if(sign<0): 
        oper = operator.lt
    else: 
        oper = operator.gt 
    
    for curve in curves: 
        relevant_edges.extend(list(filter(lambda seg: oper(seg[0].vertex[dir],corner.vertex[dir])
                                 and min(seg[0].vertex[opdir],seg[1].vertex[opdir])<=corner.vertex[opdir]<=max(seg[0].vertex[opdir],seg[1].vertex[opdir]),
                                 list(getattr(curve,relevant_set)))))

    return relevant_edges

def degenerateExtension(curves,intersection_corner):

    return 

def nonDegenerateExtension(curves):
    return 

def extendCurve(edge, curves, dir):
    corner = edge[0]
    opdir = (dir+1)%2
    vec = edge[1].vertex-edge[0].vertex 
    sign = vec/np.linalg.norm(vec)

    relevant_edges = sortPerpindicular(corner, dir, sign, curves)
    for i in range(len(relevant_edges)):
        if(corner.vertex[opdir]==edge[0].vertex[opdir]):
            #degenerate
            degenerateExtension(curves,edge[0])
        elif(corner.vertex[opdir]==edge[1].vertex[opdir]):
            #degenerate
            degenerateExtension(curves,edge[1])
        else: 
            #nondegenerate
            nonDegenerateExtension()
def addChords(corner, curves): 
    h1_chord, h2_chord = extendCurve(corner.horizontal, curves, 0)
    v1_chord, v2_chord = extendCurve(corner.vertical, curves, 1)

def decompose(curves): 
    for curve in curves: 
        for corner in curve.concave_corners: 
            addChords(corner)
    

