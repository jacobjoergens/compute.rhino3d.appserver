import networkx as nx
import numpy as np
from itertools import combinations
from ingest import cornerList

def getDegCorners(corner_lists,deg_chord,dir):
    opdir = (dir+1)%2
    a_corner = None
    b_corner = None
    from_rounded = [round(coor,6) for coor in deg_chord[0]]
    to_rounded = [round(coor,6) for coor in deg_chord[1]]
    for i in range(len(corner_lists)):
        current_corner = corner_lists[i].head
        for j in range(corner_lists[i].length):
            current_rounded = [round(coor,6) for coor in current_corner.vertex]
            if(current_rounded==from_rounded or current_rounded==to_rounded):
                if(a_corner==None):
                    a_corner = current_corner
                    a_index= i
                    mark = j
                else:
                    b_corner = current_corner
                    b_index = i
                    if(b_index==a_index):
                        if(a_corner.vertex[opdir]!=a_corner.prev.vertex[opdir]):
                            return b_corner, a_corner, a_index, b_index
                        # if(j-mark<corner_lists[i].length/2):
                        #     return a_corner, b_corner, a_index, b_index
                        # else: 
                        #     return b_corner, a_corner, b_index, a_index
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
    return forward, backward

def decompose(horizontal, vertical, intersections, corner_lists):
    independent_sets = set()
    if(len(intersections)>0):
        G = nx.Graph()
        B = nx.Graph()
        b_dict = {}
        char = 65
        i = 0
        hz_intersects = set()
        b_top = []
        for ii in intersections:
            hz_intersects.add(ii[0])
            G.add_node(ii[0],bipartite=0)
            G.add_node(ii[1],bipartite=1)
            if(ii[0] not in b_dict):
                b_dict[ii[0]]=chr(char)
                b_top.append(chr(char))
                char+=1
            if(ii[1] not in b_dict):
                b_dict[ii[1]]=i
                i+=1
            B.add_node(b_dict[ii[0]],bipartite=0 if isinstance(b_dict[ii[0]], str) else 1)
            B.add_node(b_dict[ii[1]],bipartite=1 if isinstance(b_dict[ii[1]], int) else 0)
            B.add_edge(b_dict[ii[0]],b_dict[ii[1]])
        G.add_edges_from(intersections)
        top, bottom =  nx.bipartite.sets(G, hz_intersects) #nx.bipartite.sets(G, hz_intersects)
        combined_elements = list(top)+list(bottom)
        combos = list(combinations(combined_elements, max(len(top),len(bottom))))
        for combo in combos: 
            # print(combo)
            # if(top.difference(combo)==top or bottom.difference(combo)==bottom):
            #     print('culling')
            #     continue
            if not any(G.has_edge(u,v) for u,v in combinations(combo, 2)):
                independent_sets.add(combo)
        max_set = horizontal+vertical+list(list(independent_sets)[-1]) #taking last for now, change later when allowing different max covers
    else: 
        max_set = horizontal+vertical   
    
    """ 
    For now just take the last item
    will handle the different decomp options later
    """
    horver = ["horizontal","vertical"]
    # print(len(max_set))
    for deg_chord in max_set:
        # print(deg_chord)
        # get dot 
        chord_vector = np.array(deg_chord[1])-np.array(deg_chord[0])
        deg_dot = np.dot(chord_vector,[0,1,0])
        # normalize dot product
        dir = int(abs(deg_dot / (np.linalg.norm(chord_vector))))
        #by construction, a_index<b_index or if equal a_corner precedes b_corner
        a_corner, b_corner, a_index, b_index = getDegCorners(corner_lists, deg_chord, dir)
        # print(a_corner.vertex,b_corner.vertex)
        a_list = corner_lists[a_index]
        a_forward, a_backward = stageDegDecompGeometry(a_corner, horver, dir)
        b_forward, b_backward = stageDegDecompGeometry(b_corner, horver, dir)
        
        
        a0 = getattr(a_corner, a_backward)
        a1 = getattr(a_corner, a_forward)
        a2 = getattr(a1, a_forward)
        b0 = getattr(b_corner, b_backward)
        b1 = getattr(b_corner, b_forward)
        b2 = getattr(b1, b_forward)
        
        # print(a_corner.vertex, a1.vertex, a0.vertex)
        # print('__________')
        # print(b_corner.vertex,b1.vertex,b0.vertex)
        perp_dot = np.dot(np.array(a0.vertex)-np.array(a_corner.vertex),np.array(b0.vertex)-np.array(b_corner.vertex))
        if(perp_dot/np.linalg.norm(perp_dot)==1):
            if(a_index==b_index):
                # print('q1')
                a_line = [a2, a1, b1]
                b_line = [b0, b_corner, a_corner]
            else: 
                # print('q4')
                a_line = [a0, a_corner, b_corner]
                b_line = [b2, b1, a1]
                
        else: 
            if(a_index==b_index):
                # secondary_dot = np.dot(np.array(a2.vertex)-np.array(a1.vertex),np.array(b2.vertex)-np.array(b1.vertex))
                # if(secondary_dot/abs(secondary_dot)==1):
                if(a1==a_corner.next):
                    # print('q2.1')
                    a_line = [a0,a_corner,b1]
                    b_line = [b0,b_corner,a1]
                else: 
                    # print('q2.2',dir)
                    a_line = [a2, a1, b_corner]
                    b_line = [b2, b1, a_corner]
            else: 
                # print('q3')
                a_line = [a0, a_corner, b1]
                b_line = [b0, b_corner, a1]

        a_seg = (a_line[1].vertex, a_line[2].vertex)
        b_seg = (b_line[1].vertex, b_line[2].vertex)
        a_line[1].next_edge = a_seg
        b_line[1].next_edge = b_seg

        a_list.stitch(a_line[0],a_line[1],a_line[2],False)
        a_list.head = a_line[1]
        a_list.tail = a_line[0]
        
        a_list.stitch(b_line[0], b_line[1], b_line[2],False)
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
        # for i in range(len(corner_lists)):
        #     print(i, dir, corner_lists[i].length, corner_lists[i].concave_count)
    return corner_lists, G