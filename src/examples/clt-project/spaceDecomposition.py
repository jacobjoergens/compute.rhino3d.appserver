import numpy as np
import sys
import operator


class Cell: 
    def __init__(self):
        self.height = 0 
        self.width = 0 
        self.N = None
        self.S = None
        self.W = None
        self.E = None 
        self.interior = False
        self.score = 0
        self.border = False

# def digestCurves(curve_data):
#     gridDict = {
#         'horizontal':{},
#         'vertical':{}
#     }
#     grid = []
#     minx = curve_data[0][0][0]
#     maxx = minx
#     miny = curve_data[0][0][1]
#     maxy = miny

#     for i in range(len(curve_data)):
#         vertices = curve_data[i]
#         vertices.pop(-1)
        
#         for j in range(len(vertices)):
#             prev_vertex = vertices[(j-1)%len(vertices)]
#             vertex = vertices[j]
#             if(prev_vertex[0]==vertex[0]):
#                 if(vertex[0]<minx):
#                     minx = vertex[0]
#                 elif(vertex[0]>maxx):
#                     maxx = vertex[0]

#                 if(vertex[0] in gridDict['vertical']):
#                     gridDict['vertical'][vertex[0]].append([prev_vertex[1],vertex[1]])
#                 else: 
#                     gridDict['vertical'][vertex[0]] = [[prev_vertex[1],vertex[1]]]
#             else: 
#                 if(vertex[1]<miny):
#                     miny = vertex[1]
#                 elif(vertex[1]>maxy):
#                     maxy = vertex[1]

#                 if(vertex[1] in gridDict['horizontal']):
#                     gridDict['horizontal'][vertex[1]].append([prev_vertex[0],vertex[0]])
#                 else:
#                     gridDict['horizontal'][vertex[1]] = [[prev_vertex[0],vertex[0]]]
                    
#     print(gridDict)
#     sys.stdout.flush()     

def digestCurves(curve_data):
    minx = curve_data[0][0][0]
    maxy = curve_data[0][0][1]

    xcomp = set()
    ycomp = set()

    vertices = []

    for i in range(len(curve_data)):
        start = len(vertices)
        vertices.extend(curve_data[i])
        vertices.pop(-1)
        
        for j in range(start, len(vertices)):
            vertex = vertices[j]
            xcomp.add(vertex[0])
            ycomp.add(vertex[1])
            
            if(vertex[0]<minx):
                minx = vertex[0]

            if(vertex[0]>maxy):
                maxy = vertex[0]
    
    return xcomp, ycomp, minx, maxy, vertices

def buildGrid(xcomp, ycomp, minx, maxy, vertices):
    grid = {}
    hkeys = sorted(list(xcomp))
    vkeys = sorted(list(ycomp), reverse = True)
    flow = 0 #format(0, '#0'+str(len(hkeys)+2)+'b')
    for i in range(len(vkeys)-1):
        for j in range(len(hkeys)-1): 
            cell = Cell()
            grid[(hkeys[j],vkeys[i],0)] = cell

    # print(grid)
    # sys.stdout.flush()
    for vertex in vertices: 
        if(tuple(vertex) in grid):
            grid[tuple(vertex)].border = True
    
    for i in range(len(vkeys)-1):
        for j in range(len(hkeys)-1):
            cell = grid[(hkeys[j], vkeys[i], 0)]
            
            if(i==0):
                cell.height = abs(maxy - vkeys[i])
            else: 
                cell.height = abs(vkeys[i+1] - vkeys[i])

            if(j==0):
                cell.width = abs(minx - hkeys[j])
            else: 
                cell.width = abs(hkeys[j+1] - hkeys[j])
                
            if(i>0):
                N = grid[(hkeys[j],vkeys[i-1],0)]
                N.S = cell
                cell.N = N
                cell.score += N.interior

            if(j>0):
                W = grid[(hkeys[j-1], vkeys[i], 0)]
                W.E = cell 
                cell.W = W
                cell.score += W.interior
            
            if(cell.border):
                if(j==0 and i==0):
                    flow = 1 
                else:
                    mask = 1 << (len(hkeys)-1-j)
                    flow ^= mask #flow = flow|int(('1'+'0'*j),2)
            
            print(i,j,flow)
            sys.stdout.flush()
            cell.interior = bool(bin(flow >> (len(hkeys)-1-j)).count('1')%2)
            #     if(i==0 and j==0): 
            #         cell.interior = True
            #     elif(i==0):
            #         cell.interior = not W.interior
            #     elif(j==0):
            #         cell.interior = not N.interior
            #     else:
            #         if(bin(flow).count('1')%2):
            #             cell.interior = True
            #         # if(cell.score>1):
            #         #     cell.interior = not(grid[(hkeys[j-1], vkeys[i-1], 0)].interior)
            #         # else: 
            #         #     cell.interior = bool(cell.score)
            # else: 
            #     if(bin(flow).count('1')%2 and j>0):
            #         cell.interior = True
                # if(i==0 and j==0):
                #     cell.interior = False
                # elif(i==0):
                #     cell.interior = W.interior
                # elif(j==0):
                #     cell.interior = N.interior 
                # else:
                #     cell.interior = N.interior or W.interior

            if(j>0):
                W.score += cell.interior

            if(i>0):
                N.score += cell.interior
            
        #     row += "("+str(i)+","+str(j)+") "+str(cell.score)+", "+str(cell.border)+"\t"
        # print(row)
        # sys.stdout.flush()
    for i in range(len(vkeys)-1):
        row = ""     
        for j in range(len(hkeys)-1):
            row+="("+str(j)+","+str(i)+") "+str(grid[(hkeys[j], vkeys[i], 0)].interior)+", "+str(grid[(hkeys[j], vkeys[i], 0)].score)+"\t"
        print(row)
    
    sys.stdout.flush()

    