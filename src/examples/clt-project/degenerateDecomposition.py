import networkx as nx
import numpy as np
from itertools import combinations
from ingest import cornerList
import matplotlib.pyplot as plt
import sys
import base64
import io

def getDegCorners(deg_chord,dir):
    opdir = (dir+1)%2

    a_corner = deg_chord[0]
    b_corner = deg_chord[1]
    
    a_index = a_corner.list_index
    b_index = b_corner.list_index
    if(b_index==a_index):
        if(a_corner.vertex[opdir]!=a_corner.prev.vertex[opdir]):
            return b_corner, a_corner, b_index, a_index
        else: 
            return a_corner, b_corner, a_index, b_index
    else: 
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

def createBranches(independent_set):
    return None 

def getMaxIndependentSet(horizontal, vertical, intersections, corner_lists):
    k = 4
    max_sets = []
    independent_sets = set()
    G = None
    if(len(intersections)>0):
        G = nx.Graph()
        B = nx.Graph()
        b_dict = {}
        char = 65
        i = 0
        hz_intersects = set()
        b_top = []
        h_counter = 1 
        v_counter = 1 
        for ii in intersections:
            hz_intersects.add(ii[0])
            if(not G.has_node(ii[0])):
                G.add_node(ii[0],bipartite=0,label=f"H{h_counter}")
                h_counter+=1
            if(not G.has_node(ii[1])):
                G.add_node(ii[1],bipartite=1,label=f"V{v_counter}")
                v_counter+=1
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
        top, bottom =  nx.bipartite.sets(G, hz_intersects) 
        combined_elements = list(top)+list(bottom)
        combos = list(combinations(combined_elements, max(len(top),len(bottom))))
        for combo in combos: 
            if not any(G.has_edge(u,v) for u,v in combinations(combo, 2)):
                independent_sets.add(combo)

        for independent_set in list(independent_sets):
            max_sets.append(horizontal+vertical+list(independent_set))
    else: 
        max_sets = [horizontal+vertical] 

    if k>4: 
        for independent_set in max_sets:
            createBranches(independent_set)

    return max_sets, G, top, bottom, h_counter, v_counter

def generateGraphs(max_sets, G, top, bottom, horizontal, vertical, h_counter, v_counter):
    top_len = len(list(top))
    bottom_len = len(list(bottom))
    for j in range(len(horizontal)):
        G.add_node(horizontal[j],biparite=0,label=f"H{h_counter+j}")

    for k in range(len(vertical)):
        G.add_node(vertical[k],biparite=1,label=f"V{v_counter+k}")

    labels = nx.get_node_attributes(G, "label")
    node_list = list(G.nodes)
    pos = {}
    label_pos = {}

    max_part_len = max(top_len+len(horizontal),bottom_len+len(vertical))-1
    step = 9/max_part_len
    if(bottom_len>top_len):
        h,v = (bottom_len-top_len)/2*step,0
    elif(top_len>bottom_len):
        h,v = 0,(top_len-bottom_len)/2*step
    else: 
        h,v = 0,0
    for node, label in sorted(labels.items(),key=lambda i: int(i[1][1:])):
        if(label[0]=='H'):
            pos[node] = (0.1,h)
            label_pos[node] = (pos[node][0] - 0.2, pos[node][1])
            h+=step
        elif(label[0]=='V'):
            pos[node] = (0.9,v)
            label_pos[node] = (pos[node][0] + 0.2, pos[node][1])
            v+=step

    bipartite_figures = []
    for i in range(len(max_sets)):
        plt.figure(figsize=(2,9))
        node_color = {node: 'w' if node in max_sets[i] else 'none' for node in node_list}
        nx.draw_networkx_nodes(G, pos, node_size= min(200, 290-max_part_len*15),nodelist=node_list, node_shape='o', edgecolors='w', node_color=[node_color[node] for node in node_list])
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, edge_color='gray')
        nx.draw_networkx_labels(G, label_pos, labels, font_size=min(9, 9.9-max_part_len*0.15), font_family="monospace", font_color='w')
        plt.xlim(-0.25, 1.25)
        plt.axis('off')
        plt.gca().set_aspect(2/9)
        # Convert the plot to a SVG image in memory
        buf = io.BytesIO()
        plt.savefig(buf, bbox_inches='tight', format='svg', transparent=True)
        buf.seek(0)

        # Encode the SVG image as a base64 string
        b64_bytes = base64.b64encode(buf.read())
        bipartite_figures.append(b64_bytes.decode('utf-8'))
    return bipartite_figures

def decompose(max_set, corner_lists):
    horver = ["horizontal","vertical"]
    for deg_chord in max_set:
        chord_vector = np.array(deg_chord[1].vertex)-np.array(deg_chord[0].vertex)
        deg_dot = np.dot(chord_vector,[0,1,0])
        # convert normalized dot product to 0 or 1
        dir = int(abs(deg_dot / (np.linalg.norm(chord_vector))))
        #by construction, a_index<b_index or if equal a_corner precedes b_corner
        a_corner, b_corner, a_index, b_index = getDegCorners(deg_chord, dir)
       
        a_list = corner_lists[a_index]
        
        a_forward, a_backward = stageDegDecompGeometry(a_corner, horver, dir)
        b_forward, b_backward = stageDegDecompGeometry(b_corner, horver, dir)
        
        a0 = getattr(a_corner, a_backward)
        a1 = getattr(a_corner, a_forward)
        a2 = getattr(a1, a_forward)
        b0 = getattr(b_corner, b_backward)
        b1 = getattr(b_corner, b_forward)
        b2 = getattr(b1, b_forward)

        perp_dot = np.dot(np.array(a0.vertex)-np.array(a_corner.vertex),np.array(b0.vertex)-np.array(b_corner.vertex))
        if(perp_dot/np.linalg.norm(perp_dot)==1):
            if(a1==a_corner.next):
                a_line = [a0, a_corner, b_corner]
                b_line = [b2, b1, a1]
            else:
                a_line = [a2, a1, b1]
                b_line = [b0, b_corner, a_corner]
        else: 
            if(a1==a_corner.next):
                a_line = [a0,a_corner,b1]
                b_line = [b0,b_corner,a1]
            else: 
                a_line = [a2, a1, b_corner]
                b_line = [b2, b1, a_corner]

        a_seg = (a_line[1].vertex, a_line[2].vertex)
        b_seg = (b_line[1].vertex, b_line[2].vertex)
        a_line[1].next_edge = a_seg
        b_line[1].next_edge = b_seg

        """
        To add k>4 capability, need to somehow look ahead for 'magic' partitions and only allow those
        """

        a_list.stitch(a_line[0],a_line[1],a_line[2],False)
        a_list.head = a_line[0]
        a_list.tail = a_line[0].prev
        
        a_list.stitch(b_line[0], b_line[1], b_line[2],False)
        a_corner.concave = False
        b_corner.concave = False
        a_list.updateState(a_index)
        if(b_index==a_index):
            b_list = cornerList()
            b_list.head = b_line[0]
            b_list.tail = b_line[0].prev
            b_list.updateState(len(corner_lists))
            corner_lists.append(b_list)
        else: 
            corner_lists.pop(b_index)

    return corner_lists