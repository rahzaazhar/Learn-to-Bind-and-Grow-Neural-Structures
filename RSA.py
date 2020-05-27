import numpy as np
import torch.nn as nn
from scipy.spatial.distance import pdist, squareform
from scipy.stats import rankdata, spearmanr
#import pyrsa.data as rsd
#import pyrsa.rdm as rsr
#from torchvision.models._utils import IntermediateLayerGetter
from modelv1 import GradCL
class pyRSA():
    def __init__(self,patterns1,patterns2):
        
        self.patterns1 = rsd.Dataset(patterns1.detach().cpu().numpy())
        self.patterns2 = rsd.Dataset(patterns2.detach().cpu().numpy())

    def create_RDMs(self):
        self.rdm1 = rsr.calc_rdm(self.patterns1, method = 'correlation')
        self.rdm2 = rsr.calc_rdm(self.patterns2, method = 'correlation')

    def compute_RDM_similarity(self):
        self.dissimilarity = rsr.compare(self.rdm1,self.rdm2,method='spearman')[0][0]
        self.similarity = 1-self.dissimilarity

class RSA():
    def __init__(self,patterns1,patterns2):
        self.patterns1 = patterns1.detach().cpu().numpy()
        self.patterns2 = patterns2.detach().cpu().numpy()

    def create_RDMs(self):


        self.rdm1 = pdist(self.patterns1,'correlation')
        self.rdm1_square = squareform(self.rdm1)
        self.rdm2 = pdist(self.patterns2,'correlation')
        self.rdm2_square = squareform(self.rdm2)

    def rank_RDMs(self):
        self.rdm1_ranked = rankdata(self.rdm1,method='ordinal')
        self.rdm2_ranked = rankdata(self.rdm2,method='ordinal')
        print(self.rdm1_ranked)
        print(self.rdm2_ranked)

    def compute_RDM_similarity(self):
        #self.rank_RDMs()
        self.similarity, _ = spearmanr(self.rdm1,self.rdm2)
        self.dissimilarity = self.similarity

def test2():
    template = {'linear1_input':nn.Linear(32*32,300),'relu1':nn.ReLU(),'linear2':nn.Linear(300,300),'relu2':nn.ReLU(),
                'linear3':nn.Linear(300,300),'relu3':nn.ReLU()}
    model = GradCL(template,0.5)
    model.init_subgraph('task1',10)
    #new_model = IntermediateLayerGetter(model,{''})
    for module_name, module in model.named_children():
        print('module_name',module_name)
        for submodule_name, submodule in module.named_children():
            print('submodule_name',submodule_name)


def test1():
    obs1 = np.random.randn(5,10)
    obs2 = np.random.randn(5,10)
    rsa = RSA(obs1,obs2)
    pyrsa = pyRSA(obs1,obs2)
    rsa.create_RDMs()
    pyrsa.create_RDMs()
    '''print(rsa.rdm1_square)
    print(rsa.rdm1)
    print(rsa.rdm2_square)
    print(rsa.rdm2)'''
    rsa.compute_RDM_similarity()
    pyrsa.compute_RDM_similarity()
    print(rsa.similarity)
    print(pyrsa.similarity)


#test1()
