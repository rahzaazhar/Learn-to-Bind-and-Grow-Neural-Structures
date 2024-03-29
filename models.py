"""
Copyright (c) 2019-present NAVER Corp.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
#import torch.nn.functional.relu as relu
import torch
import logging
import torch.nn.functional as F
import torch.nn as nn
import copy

from modules.transformation import TPS_SpatialTransformerNetwork
from modules.feature_extraction import VGG_FeatureExtractor, RCNN_FeatureExtractor, ResNet_FeatureExtractor
from modules.sequence_modeling import BidirectionalLSTM
from modules.prediction import Attention


class sharedCNNModel(nn.Module):

    def __init__(self, opt, langdict):# added langdict-dictionary with lang:no of classes as key:value pairs
        super(sharedCNNModel, self).__init__()
        self.opt = opt
        self.stages = {'Trans': opt.Transformation, 'Feat': opt.FeatureExtraction,
                       'Seq': opt.SequenceModeling, 'Pred': opt.Prediction}
        #@azhar for multiple rnn heads
        self.rnn_lang = nn.ModuleDict()
        self.Predictions = nn.ModuleDict()

        """ Transformation """
        if opt.Transformation == 'TPS':
            self.Transformation = TPS_SpatialTransformerNetwork(
                F=opt.num_fiducial, I_size=(opt.imgH, opt.imgW), I_r_size=(opt.imgH, opt.imgW), I_channel_num=opt.input_channel)
        else:
            print('No Transformation module specified')

        """ FeatureExtraction """
        if opt.FeatureExtraction == 'VGG':
            self.FeatureExtraction = VGG_FeatureExtractor(opt.input_channel, opt.output_channel)
        elif opt.FeatureExtraction == 'RCNN':
            self.FeatureExtraction = RCNN_FeatureExtractor(opt.input_channel, opt.output_channel)
        elif opt.FeatureExtraction == 'ResNet':
            self.FeatureExtraction = ResNet_FeatureExtractor(opt.input_channel, opt.output_channel)
        else:
            raise Exception('No FeatureExtraction module specified')
        self.FeatureExtraction_output = opt.output_channel  # int(imgH/16-1) * 512
        self.AdaptiveAvgPool = nn.AdaptiveAvgPool2d((None, 1))  # Transform final (imgH/16-1) -> 1

        """ Sequence modeling"""
        if opt.SequenceModeling == 'BiLSTM':
            for k,v in langdict.items():
                self.rnn_lang[k] = nn.Sequential(
                BidirectionalLSTM(self.FeatureExtraction_output, opt.hidden_size, opt.hidden_size),
                BidirectionalLSTM(opt.hidden_size, opt.hidden_size, opt.hidden_size))
            self.SequenceModeling_output = opt.hidden_size
        else:
            print('No SequenceModeling module specified')
            self.SequenceModeling_output = self.FeatureExtraction_output
        '''for k,v in self.rnn_lang.items():
            print(k,v)'''
        """ Prediction """
        if opt.Prediction == 'CTC':
            for k,v in langdict.items():
                self.Predictions[k] = nn.Linear(self.SequenceModeling_output, v)
        elif opt.Prediction == 'Attn':
            for k,v in langdict.items():
                self.Predictions[k] = Attention(self.SequenceModeling_output, opt.hidden_size, v)
        else:
            raise Exception('Prediction is neither CTC or Attn')

    def forward(self, input, text, rnnhead, is_train=True):#@azhar added rnnhead argument to choose which head to use
        """ Transformation stage """
        if not self.stages['Trans'] == "None":
            input = self.Transformation(input)

        """ Feature extraction stage """
        visual_feature = self.FeatureExtraction(input)
        visual_feature = self.AdaptiveAvgPool(visual_feature.permute(0, 3, 1, 2))  # [b, c, h, w] -> [b, w, c, h]
        visual_feature = visual_feature.squeeze(3)
        """ Sequence modeling stage """
        if self.stages['Seq'] == 'BiLSTM':
            contextual_feature = self.rnn_lang[rnnhead](visual_feature)
        else:
            contextual_feature = visual_feature  # for convenience. this is NOT contextually modeled by BiLSTM

        """ Prediction stage """
        if self.stages['Pred'] == 'CTC':
            preds = self.Predictions[rnnhead](contextual_feature.contiguous())
        else:
            preds = self.Predictions[rnnhead](contextual_feature.contiguous(), text, is_train, batch_max_length=self.opt.batch_max_length)

        return preds


class SharedLSTMModel(nn.Module):

    def __init__(self, opt, langdict):
        super(SharedLSTMModel, self).__init__()
        self.opt = opt
        self.stages = {'Trans': opt.Transformation, 'Feat': opt.FeatureExtraction,
                       'Seq': opt.SequenceModeling, 'Pred': opt.Prediction}
        self.Predictions = nn.ModuleDict()

        """ Transformation """
        if opt.Transformation == 'TPS':
            self.Transformation = TPS_SpatialTransformerNetwork(
                F=opt.num_fiducial, I_size=(opt.imgH, opt.imgW), I_r_size=(opt.imgH, opt.imgW), I_channel_num=opt.input_channel)
        else:
            print('No Transformation module specified')

        """ FeatureExtraction """
        if opt.FeatureExtraction == 'VGG':
            self.FeatureExtraction = VGG_FeatureExtractor(opt.input_channel, opt.output_channel)
        elif opt.FeatureExtraction == 'RCNN':
            self.FeatureExtraction = RCNN_FeatureExtractor(opt.input_channel, opt.output_channel)
        elif opt.FeatureExtraction == 'ResNet':
            self.FeatureExtraction = ResNet_FeatureExtractor(opt.input_channel, opt.output_channel)
        else:
            raise Exception('No FeatureExtraction module specified')
        self.FeatureExtraction_output = opt.output_channel  # int(imgH/16-1) * 512
        self.AdaptiveAvgPool = nn.AdaptiveAvgPool2d((None, 1))  # Transform final (imgH/16-1) -> 1

        """ Sequence modeling"""
        if opt.SequenceModeling == 'BiLSTM':
            self.rnn_lang = nn.Sequential(
                BidirectionalLSTM(self.FeatureExtraction_output, opt.hidden_size, opt.hidden_size),
                BidirectionalLSTM(opt.hidden_size, opt.hidden_size, opt.hidden_size))
            self.SequenceModeling_output = opt.hidden_size
        else:
            print('No SequenceModeling module specified')
            self.SequenceModeling_output = self.FeatureExtraction_output

        """ Prediction """
        if opt.Prediction == 'CTC':
            for k,v in langdict.items():
                self.Predictions[k] = nn.Linear(self.SequenceModeling_output, v)
        elif opt.Prediction == 'Attn':
            for k,v in langdict.items():
                self.Predictions[k] = Attention(self.SequenceModeling_output, opt.hidden_size, v)
        else:
            raise Exception('Prediction is neither CTC or Attn')

    def forward(self, input, text, task, is_train=True):
        """ Transformation stage """
        if not self.stages['Trans'] == "None":
            input = self.Transformation(input)

        """ Feature extraction stage """
        visual_feature = self.FeatureExtraction(input)
        visual_feature = self.AdaptiveAvgPool(visual_feature.permute(0, 3, 1, 2))  # [b, c, h, w] -> [b, w, c, h]
        visual_feature = visual_feature.squeeze(3)

        """ Sequence modeling stage """
        if self.stages['Seq'] == 'BiLSTM':
            contextual_feature = self.rnn_lang(visual_feature)
        else:
            contextual_feature = visual_feature  # for convenience. this is NOT contextually modeled by BiLSTM

        """ Prediction stage """
        if self.stages['Pred'] == 'CTC':
            preds = self.Predictions[task](contextual_feature.contiguous())
        else:
            preds = self.Predictions[task](contextual_feature.contiguous(), text, is_train, batch_max_length=self.opt.batch_max_length)
        
        return preds

class SLSLstm(nn.Module):

    def __init__(self, opt, langdict):
        super(SLSLstm, self).__init__()
        self.opt = opt
        self.stages = {'Trans': opt.Transformation, 'Feat': opt.FeatureExtraction,
                       'Seq': opt.SequenceModeling, 'Pred': opt.Prediction}
        self.Predictions = nn.ModuleDict()
        self.rnn_lang = nn.ModuleDict()

        """ Transformation """
        if opt.Transformation == 'TPS':
            self.Transformation = TPS_SpatialTransformerNetwork(
                F=opt.num_fiducial, I_size=(opt.imgH, opt.imgW), I_r_size=(opt.imgH, opt.imgW), I_channel_num=opt.input_channel)
        else:
            print('No Transformation module specified')

        """ FeatureExtraction """
        if opt.FeatureExtraction == 'VGG':
            self.FeatureExtraction = VGG_FeatureExtractor(opt.input_channel, opt.output_channel)
        elif opt.FeatureExtraction == 'RCNN':
            self.FeatureExtraction = RCNN_FeatureExtractor(opt.input_channel, opt.output_channel)
        elif opt.FeatureExtraction == 'ResNet':
            self.FeatureExtraction = ResNet_FeatureExtractor(opt.input_channel, opt.output_channel)
        else:
            raise Exception('No FeatureExtraction module specified')
        self.FeatureExtraction_output = opt.output_channel  # int(imgH/16-1) * 512
        self.AdaptiveAvgPool = nn.AdaptiveAvgPool2d((None, 1))  # Transform final (imgH/16-1) -> 1

        """ Sequence modeling"""
        if opt.SequenceModeling == 'BiLSTM':
            self.Srnn_lang = nn.Sequential(
                BidirectionalLSTM(self.FeatureExtraction_output, opt.hidden_size, opt.hidden_size))

            for k,v in langdict.items():
                self.rnn_lang[k] = nn.Sequential(
                BidirectionalLSTM(opt.hidden_size, opt.hidden_size, opt.hidden_size))
            
            self.SequenceModeling_output = opt.hidden_size
        else:
            print('No SequenceModeling module specified')
            self.SequenceModeling_output = self.FeatureExtraction_output

        """ Prediction """
        if opt.Prediction == 'CTC':
            for k,v in langdict.items():
                self.Predictions[k] = nn.Linear(self.SequenceModeling_output, v)
        elif opt.Prediction == 'Attn':
            for k,v in langdict.items():
                self.Predictions[k] = Attention(self.SequenceModeling_output, opt.hidden_size, v)
        else:
            raise Exception('Prediction is neither CTC or Attn')

    def forward(self, input, text, task, is_train=True):
        """ Transformation stage """
        if not self.stages['Trans'] == "None":
            input = self.Transformation(input)

        """ Feature extraction stage """
        visual_feature = self.FeatureExtraction(input)
        visual_feature = self.AdaptiveAvgPool(visual_feature.permute(0, 3, 1, 2))  # [b, c, h, w] -> [b, w, c, h]
        visual_feature = visual_feature.squeeze(3)

        """ Sequence modeling stage """
        if self.stages['Seq'] == 'BiLSTM':
            contextual_feature = self.Srnn_lang(visual_feature)
            contextual_feature = self.rnn_lang[task](contextual_feature)
        else:
            contextual_feature = visual_feature  # for convenience. this is NOT contextually modeled by BiLSTM

        """ Prediction stage """
        if self.stages['Pred'] == 'CTC':
            preds = self.Predictions[task](contextual_feature.contiguous())
        else:
            preds = self.Predictions[task](contextual_feature.contiguous(), text, is_train, batch_max_length=self.opt.batch_max_length)
        
        return preds

class Flatten(nn.Module):
    def forward(self, input):
        return input.view(input.size(0), -1)

class GradCL(nn.Module):

    def __init__(self,template,sim_thres):
        super(GradCL,self).__init__()
        self.template = template # template of the first task with the output head
        self.super_network = nn.ModuleDict()
        self.task_count = 0
        self.tasks = []
        self.sim_thres = sim_thres
        self.sub_graphs = {}
        #for name, layer in template:
        for name, layer in template.items():
            self.super_network[name] = nn.ModuleDict()
        self.super_network['task_heads'] = nn.ModuleDict()
        #self.super_network['softmax'] = nn.ModuleDict()

    def  init_subgraph(self,new_task_name,datamode,new_head=None, point_to_task=0):
        #for layer_name, layer in self.template:
        if not new_head == None:
            if datamode == 'smnist' or datamode == 'pmnist':
                self.super_network['task_heads'][new_task_name] = nn.Linear(300,new_head).cuda()
            if datamode == 'CIFAR100':
                self.super_network['task_heads'][new_task_name] = nn.Linear(2048,new_head).cuda()
            #self.super_network['softmax'][new_task_name] = nn.Softmax(dim=1)
        else:
            self.super_network['task_heads'][new_task_name] = copy.copy(self.super_network['task_heads'][self.tasks[point_to_task]])
            #self.super_network['softmax'][new_task_name] = copy.copy(self.super_network['softmax'][self.tasks[point_to_task]])

        #self.super_network['task_head'][new_task_name] = nn.Linear(200,nclasses) 
        #self.sub_graphs[new_task_name] = {}
        for layer_name, layer in self.template.items():
            if self.task_count == 0:
                self.super_network[layer_name][new_task_name] = layer
                #self.sub_graphs[new_task_name][layer_name] = new_task_name

            else:
                self.super_network[layer_name][new_task_name] = copy.copy(self.super_network[layer_name][self.tasks[point_to_task]])
                #self.sub_graphs[new_task_name][layer_name] = self.tasks[point_to_task]
        self.task_count = self.task_count + 1
        self.tasks.append(new_task_name)

    def change_subgraph_pointer(self,source_task,dest_task):
        dest_task_index = self.tasks.index(dest_task)
        self.init_subgraph(source_task,dest_task_index)

    def save_model(self,path):
        torch.save(self.super_network,'super_network.pth')

    def load_model(self,path):
        self.super_network = torch.load(path)

    def grow_graph(self,new_task,selected_tasks,task_layerwise_sims):
        #print('Growing Task',new_task)
        self.sub_graphs[new_task] = {}
        most_similar_task = selected_tasks[0]
        selected_layers = []
        for task in selected_tasks:
            task_layerwise_sims[task] = {k: v for k, v in sorted(task_layerwise_sims[task].items(), key=lambda item: item[1], reverse=True)}
            #print('In grow_graph')
            #print('distribution over layers')
            logging.debug('distribution over layers')
            logging.debug('%s',task_layerwise_sims[task])
            for name, score in task_layerwise_sims[task].items():
                print(name+':'+str(score),end=' ')
            
            #print(task_layerwise_sims[task])
            print()
            cumulative_sim = 0
            for layer_name, sim in task_layerwise_sims[task].items():
                if cumulative_sim < self.sim_thres:
                    cumulative_sim += sim
                    selected_layers.append(layer_name)
            for layer_name in self.template.keys():
                if 'linear' in layer_name or 'conv2d' in layer_name:
                    if layer_name in selected_layers:
                        self.add_node(new_task,layer_name)
                        print(layer_name,' added')
                        logging.debug('%s added',layer_name)
                        self.sub_graphs[new_task][layer_name] = 'new'
                    else:
                        self.point_to_node(new_task,most_similar_task,layer_name)
                        print('binding to ',layer_name,' of',most_similar_task)
                        logging.debug('binding to %s of %s',layer_name,most_similar_task)
                        self.sub_graphs[new_task][layer_name] = layer_name+' of '+most_similar_task

    def get_layer_activations(self,x,task):
        out = {}
        for layer in self.super_network:
            x = self.super_network[layer][task](x)
            if 'linear' in layer or 'conv2d' in layer:
                out[layer] = relu(x)#.view(x.size(0),-1)
            if 'task_heads' in layer:
                out[layer] = x#.view(x.size(0),-1)

        return out

    def forward(self,x,task,get_layer_activations=False):
        if not get_layer_activations:
            for layer in self.super_network:
                x = self.super_network[layer][task](x)
                #print(layer,x)
            return x
        else:
            out = {}
            for layer in self.super_network:
                x = self.super_network[layer][task](x)
                if 'linear' in layer or 'conv2d' in layer:
                    out[layer] = F.relu(x)#.view(x.size(0),-1)
                if 'task_heads' in layer:
                    out[layer] = x#.view(x.size(0),-1)
            return out

    def add_node(self,task,layer):
        #self.super_network[layer][task] = self.super_network[layer]['task0']
        self.super_network[layer][task] = copy.deepcopy(self.template[layer])

    def point_to_node(self,source_task,dest_task,layer_name):
        self.super_network[layer_name][source_task] = copy.copy(self.super_network[layer_name][dest_task])


