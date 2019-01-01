import numpy as np
'''
'''
class suNode():
    def __init__(self):
        self.pre = []
        self.next = []
        self.pocket_id = -1      # for connection between pocket   
    def get_number_of_path(self):
        return len(self.pre) + len(self.next)
    
        
'''
suGraph can be initialized by a relationaship matrix.
It aslo provides functions for clasification and visualizing
example:
    g = suGraph()
    g.init_from_matrix(R)
    g.classify_nodes_by_type(matrix) #classi
    g.to_Mathematica()  # to export graphPlot data for Mathematica
'''
class suGraph():
    def __init__(self):
        self.matrix = np.array(0)
        self.nodes = []
        return
    def init_from_matrix(self, matrix):
        self.matrix = matrix        
        self.nodes.clear()
        for i in range(len(matrix)):
            node = suNode()
            ids = np.argwhere(matrix[i] == 1)           
            node.next += list(ids.reshape(len(ids)) )
            ids = np.argwhere(matrix.T[i] == 1)
            node.pre += list(ids.reshape(len(ids)) )
            self.nodes.append(node)                 
       
    def clear(self):
        self.matrix = np.array(0)
        return
    # @root_nodes: index list of all root nodes
    # Note: this algorithm can search classes from any node
    def classify_nodes_by_type(self, matrix):
        self.init_from_matrix(matrix)
        regions = []   #contour id groups
        pocket = []
        nodes_to_search = [0]   # outter contour
        
        done_ids = []
        while(len(nodes_to_search) != 0):
            idx = nodes_to_search.pop()            
           
            if(self.nodes[idx].get_number_of_path() > 2):    #type_II node
                if(len(pocket) != 0):
                    regions.append(pocket.copy())   
                pocket.clear()
                #add itself as a single class
                pocket.append(idx)
                regions.append(pocket.copy())   
                pocket.clear()
                done_ids.append(idx)
            else:
                pocket.append(idx)
                done_ids.append(idx)
                
            #specify pocket id to node
            self.nodes[idx].pocket_id = len(regions) - 1
            #find other edges
            new_path = self.nodes[idx].pre + self.nodes[idx].next
            new_path = [x for x in new_path if (not x in done_ids) ]    #avoid re-enter
            if(len(new_path) == 0 and len(pocket) != 0):
                regions.append(pocket.copy())   
                pocket.clear()
            nodes_to_search += new_path                 
        return regions    
    
    # visualization functions
    def to_Mathematica(self, filepath):
        np.set_printoptions(threshold=np.inf)
        script = 'GraphPlot[DATA, VertexLabeling -> True, MultiedgeStyle -> True(*,  DirectedEdges -> True*)]'
       
        sData = str(self.matrix)
        sData = sData.replace('\n', '')
        sData = sData.replace('[', '{')
        sData = sData.replace(']', '}')
        sData = sData.replace(' ', ', ')
        if(len(filepath) == 0):
            print(script.replace('DATA', sData))
        else:
            file = open(filepath,'w')
            file.write(script.replace('DATA', sData))
            file.close()
        return
