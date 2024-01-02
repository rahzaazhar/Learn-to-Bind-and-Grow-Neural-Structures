# Learn-to-Bind-and-Grow-Neural-Structures
Code for the paper Learn to bind and grow neural structures accepted at 8th ACM IKDD CODS & 26th COMAD [paper](https://dl.acm.org/doi/abs/10.1145/3430984.3431019)
The command for train is 
```
python train.py --config_name <name_of_config>
```
To create a custom config or use existing ones refer to L2G_config.py <br/>
parameters in the config are given below
- n_tasks
- datamode: (pmnist/CIFAR100/smnist)
- lr
- epochs
- alpha
- sim_strat(egy): RSA/pearson
