from dataclasses import dataclass, replace

@dataclass
class L2BG_Config():

    #re: Resources
    
    exp_name: str
    config_name: str
    exp_dir: str
    datamode: str
    n_tasks: int = 5
    lr: float = 0.01
    batch_size: int = 64
    sim_strat: str = 'RSA'
    freeze_past: bool = False
    epochs: int = 5
    alpha: float = 0.5


#config1 To find out whwther a randomly grown network performs worse than RSA strategy 
config1 = L2BG_Config(exp_name='Random_growth',exp_dir='L2G_graphs/',datamode='smnist',sim_strat='random_growth',
						config_name='config2')
#config2 To train on CIFAR100 using RSA_sim
config2 = L2BG_Config(exp_name='RSA_sim',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
						config_name='config2')
#config3 train task one for more iterations and subsequent tasks for lesser iterations select + most dissimilar task (10-5)
config3 = L2BG_Config(exp_name='RSA_sim_1',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
						config_name='config3')
#config4 train task one for more iterations and subsequent tasks for lesser iterations + select most similar task (10-5)
config4 = L2BG_Config(exp_name='RSA_sim_2',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
						config_name='config4')
#config5 To train on datasets by freezing weights of previous tasks
config5 = L2BG_Config(exp_name='RSA_sim_2_freeze',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
						config_name='config5',freeze_past=True)
#config 6 To train 10 CIFAR Tasks each for 10 epochs wo freeze
config6 = L2BG_Config(exp_name='CIFAR100_10',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
						config_name='config6',n_tasks=10)
#config 7 To train 10 CIFAR Tasks each for 10 epochs w freeze
config7 = L2BG_Config(exp_name='CIFAR100_10_freeze',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
						config_name='config7',freeze_past=True,n_tasks=10)
#config_CIFAR100_alpha config_pmnist_alpha config_pmnist_alpha 
#above configs are to study the effect of alpha on model selection and accuracy
config_CIFAR100_alpha = {}
config_pmnist_alpha = {}
config_smnist_alpha = {}
alphas = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
for al in alphas:
  config_CIFAR100_alpha['alpha'+str(al)] = L2BG_Config(exp_name='alpha'+str(al)+'_CIFAR100',exp_dir='L2GB_exps/',datamode='CIFAR100',sim_strat='RSA',
                                                  config_name='config_CIFAR100_alpha',n_tasks=10,alpha=al,epochs=5)
  config_pmnist_alpha['alpha'+str(al)] = L2BG_Config(exp_name='alpha'+str(al)+'_pmnist',exp_dir='L2GB_exps/',datamode='pmnist',sim_strat='RSA',
                                                  config_name='config_pmnist_alpha',n_tasks=10,alpha=al,epochs=5)
  config_pmnist_alpha['alpha'+str(al)] = L2BG_Config(exp_name='alpha'+str(al)+'_smnist',exp_dir='L2GB_exps/',datamode='smnist',sim_strat='RSA',
                                                  config_name='config_smnist_alpha',n_tasks=10,alpha=al,epochs=5)





########################tests and sanity checks#################################### 
config_pmnist_test = L2BG_Config(exp_name='pmnist_test',exp_dir='L2G_graphs/',datamode='pmnist',sim_strat='RSA',
                        config_name='config_pmnist',freeze_past=False,n_tasks=2,epochs=1)

config_CIFAR100_test = L2BG_Config(exp_name='CIFAR100_test',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
                        config_name='config_pmnist',freeze_past=False,n_tasks=2,epochs=1)

config_smnist_test = L2BG_Config(exp_name='smnist_test',exp_dir='L2G_graphs/',datamode='smnist',sim_strat='RSA',
                        config_name='config_pmnist',freeze_past=False,n_tasks=2,epochs=1)

#config 8 To train VDD_test 
config8 = L2BG_Config(exp_name='VDD_test',exp_dir='L2G_graphs/',datamode='VDD',sim_strat='RSA',
                        config_name='config8',freeze_past=False,n_tasks=2,epochs=1)

#config_san_1 To check if freezing is working or not
config_san_1 = L2BG_Config(exp_name='freezing_check',exp_dir='L2G_graphs/',datamode='CIFAR100',sim_strat='RSA',
                        config_name='config_san_1',freeze_past=True,n_tasks=2,epochs=1)