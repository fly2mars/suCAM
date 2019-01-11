import numpy as np
'''
'''
class suNode():
    def __init__(self):
        self.pre = []
        self.next = []
        self.data = []
        self.type = -1
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
        self.visited = []
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
    # construct self.matrix from simplified graph
    def get_matrix_from_graph(self):        
        n = len(self.nodes)
        M = np.zeros([n,n])
        for i in range(n):
            node = self.nodes[i]
            M[i][node.next] = 1
        return M.astype(int)
    def update_matrix(self):
        self.matrix = self.get_matrix_from_graph()
    # generate pocket graph by using dfs_combine_tree()
    def gen_pockets_graph(self):
        nodes = []
        self.dfs_combine_tree(0, [], nodes)
        pocket_graph = suGraph()
        pocket_graph.nodes = nodes
        pocket_graph.get_matrix_from_graph()
        
        return pocket_graph
    
    
    # deep first search for finding pockets
    # return node list can be used to construct a new graph
    def dfs_combine_tree(self, i, visited, nodes, parent_id=-1):
        if(len(visited)==0):
            visited = np.zeros(len(self.nodes)).astype(int)            
        visited[i] = 1   
        ori_node = self.nodes[i]
        edges = ori_node.pre + ori_node.next
        
        # root node
        if(parent_id == -1):
            node = suNode()
            node.data.append(i)
            nodes.append(node)   
        # make a new node for type-II
        #if(len(edges) > 2):
        if(ori_node.type == 2):   # set in to_reverse_delete_MST
            node = suNode()
            node.data.append(i)
            node.pre = [ parent_id ]
            nodes[parent_id].next.append(len(nodes))
            nodes.append(node)
            
        # combine node for type-I
        #if(len(edges) <= 2 and parent_id != -1):
        if(ori_node.type != 2 and parent_id != -1):
            nodes[-1].data.append(i)
      
    
        
        cur_id = len(nodes) - 1 
        for j in edges:            
            if visited[j] == 0:
                #if (len(edges)  > 2) and (self.nodes[j].get_number_of_path() <= 2):
                if (ori_node.type == 2 and self.nodes[j].type != 2):
                    #make one node for each pocket you want to combine
                    node = suNode()
                    node.pre.append(cur_id)
                    nodes.append(node)
                    nodes[cur_id].next.append(len(nodes) - 1)
                self.dfs_combine_tree(j, visited, nodes, cur_id)          
        
        return 
        
    # deep first search from node i to check if a node can be visited
    # use self.matrix
    def dfs_visit(self, i):
        if(len(self.visited)==0):
            self.visited = np.zeros(len(self.nodes)).astype(int)            
        self.visited[i] = 1
        
        ids = np.argwhere(self.matrix[i] == 1)           
        nex = list(ids.reshape(len(ids)) )
        ids = np.argwhere(self.matrix.T[i] == 1)
        pre = list(ids.reshape(len(ids)) )
        edges = nex + pre
        for j in edges:
            if self.visited[j] == 0:
                self.dfs_visit(j);
        return
    def is_connected(self):
        self.visited = []        
        self.dfs_visit(0)
        
        unvisited = np.argwhere(self.visited == 0)
        if(len(unvisited) == 0):
            return True
        return False
    
    
    def to_reverse_delete_MST(self):
        '''
        Use a reverse delete mehtod to construct minimum-weight spanning tree
        The diffences are:
    #    1. Only the type-II nodes are considered to be deleted
    #    2. We don't use the distance as a weight, because all neighbored  
    #       iso-contours have the similar distance. We remove an edge then
    #       test if the graph is still connected
        '''
        self.get_matrix_from_graph()
        
        nodes_type = {}
        #Matrix = self.matrix
        for i in range(len(self.nodes) ):
            ids = np.argwhere(self.matrix.T[i] == 1)
            pre = ids.reshape(len(ids))
            #only for type-II
            if len(self.nodes[i].pre) > 1:  
                nodes_type[i] = 2
                for idx in pre:
                    #remove idx and check connectivity of graph
                    self.matrix[idx][i] = 0
                    #print(self.matrix[i][idx])
                    #print(self.matrix)
                    if(not self.is_connected()):
                        #print("Not connected")
                        self.matrix[idx][i] = 1
            else:
                if(len(self.nodes[i].pre + self.nodes[i].next) > 2):
                    nodes_type[i] = 2
        #some information, like node type, is lost in this procedure
        self.init_from_matrix(self.matrix)      
        #so we need to rebuild the type info
        for i in nodes_type.keys():
            self.nodes[i].type = nodes_type[i]
        return

    def clear(self):
        self.matrix = np.array(0)
        self.visited = []
        return
    # @root_nodes: index list of all root nodes
    # Note: this algorithm can search classes from any node
    def classify_nodes_by_type(self, matrix, map_ij = []):
        self.init_from_matrix(matrix)
        #if(len(map_ij) != 0):
            #self.simplify_with_layer_info(map_ij)
        self.to_reverse_delete_MST()
        regions = []   #contour id groups
        pocket = []
        nodes_to_search = [0]   # outter contour
        
        done_ids = []
        while(len(nodes_to_search) != 0):
            idx = nodes_to_search.pop()                       
            if(self.nodes[idx].get_number_of_path() > 2):    #type_II node
                if(len(pocket) != 0):  # add last
                    regions.append(pocket.copy())   
                pocket.clear()
                #add itself as a single class
                pocket.append(idx)
                regions.append(pocket.copy())   
                pocket.clear()                
            else:
                pocket.append(idx)
                
            done_ids.append(idx)    
           
            #find other edges
            new_path = self.nodes[idx].pre + self.nodes[idx].next
            new_path = [x for x in new_path if (not x in done_ids) ]    #avoid re-enter
            if(len(new_path) == 0 and len(pocket) != 0): # end of path
                regions.append(pocket.copy())   
                pocket.clear()
            nodes_to_search += new_path                 
            
            #specify pocket id to node            
            if(len(regions) != 0):
                if(len(pocket) == 0):
                    self.nodes[idx].pocket_id = len(regions) - 1    # no new pocket
                else:
                    self.nodes[idx].pocket_id = len(regions)        # there's a new pocket.
            else:
                self.nodes[idx].pocket_id = 0            
        return regions    
    
    # test function
    def connect_node_by_spiral(self, sprials):
        edges = []
        #traverse from node[0]
        done_ids = []
        nodes_to_search = [0]   # outter contour        
        spiral_node = []
        for i in range(len(self.nodes)):
            node = self.nodes[i]
            if(node.get_number_of_path() > 2):
                #check next and pre
                pocket_id = node.pocket_id
                #done_ids.append(i)
                for pre in node.pre:
                    #done_ids.append([self.nodes[pre].pocket_id, pocket_id])
                    done_ids.append([pre, i])
                for next in node.next:
                    #done_ids.append([pocket_id, self.nodes[next].pocket_id])
                    done_ids.append([i, next])
        print(np.asarray(done_ids).reshape(len(done_ids),2) + [1,1])
        for n in done_ids:
            cn = [self.nodes[n[0]].pocket_id, self.nodes[n[1]].pocket_id]
            print(cn)
                
                
            
        return 
        
    # visualization functions
    def to_Mathematica(self, filepath):
        import re
        np.set_printoptions(threshold=np.inf)
        script = 'GraphPlot[DATA, VertexLabeling -> True, MultiedgeStyle -> True,  DirectedEdges -> True]'
        
        #sData = str(self.matrix)
        sData = str(self.get_matrix_from_graph())
        sData = sData.replace('\n', '')
        sData = sData.replace('[', '{')
        sData = sData.replace(']', '}')                
        sData = re.sub("\s+", ", ", sData)
        
        if(len(filepath) == 0):
            print(script.replace('DATA', sData))
        else:
            file = open(filepath,'w')
            file.write(script.replace('DATA', sData))
            file.close()
        return

if __name__ == '__main__':
    # test graph 
    N = 10
    M = np.random.randint(0,2,[N,N])    
    graph = suGraph()
    graph.init_from_matrix(M)
    graph.to_Mathematica("")
    graph.to_reverse_delete_MST()
    graph.init_from_matrix(graph.matrix)
    graph.to_Mathematica("")
    
    #nodes = []
    #graph.dfs_combine_tree(0, [], nodes)
    #new_graph = suGraph()
    #new_graph.nodes = nodes
    #new_graph.get_matrix_from_graph()
    pocket_graph = graph.gen_pockets_graph()
    pocket_graph.to_Mathematica("")
    for n in pocket_graph.nodes:
        print(n.data)
