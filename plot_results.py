def plot_alpha_graphs(dir_path,title,to_plot='avg_acc'):
  l = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
  legend = []
  fig = plt.figure(figsize=(12,10))
  for al in l:
    dump = torch.load(dir_path+'alpha'+str(al)+'_CIFAR100res.pth')
    x = dump['x']
    y = dump[to_plot]
    plt.plot(x,y)
    legend.append('aplha'+str(al))
  plt.legend(legend,loc='center left', bbox_to_anchor=(1, 0.5))
  plt.xlabel('tasks')
  plt.ylabel(to_plot)
  plt.title(title)
  plt.savefig(path+to_plot+'vsalpha.png')