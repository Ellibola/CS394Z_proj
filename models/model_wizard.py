import torch
import torch.nn as nn
import torch.nn.functional as F
from models.CNN_Online import CNN_online_MNIST_V1

def model_wizard(
        dataset:str="mnist", 
        bit_w:int=32, 
        bit_a:int=32, 
        version:str='V1', 
        device=torch.device('cpu')
    ):
    if dataset=='mnist':
        if (bit_w==32)&(bit_a==32)&(version=='V1'):
            return CNN_online_MNIST_V1().to(device)
        else:
            raise NotImplementedError
    else:
        raise NotImplementedError