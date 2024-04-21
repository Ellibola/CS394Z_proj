import torch 
import torch.nn as nn
import torch.nn.functional as F

class NN_Online(nn.Module):
    def __init__(self) -> None:
        super(NN_Online, self).__init__()
        self.features, self.classifiers = self._module_compose()
        self.alpha = torch.ones(len(self.classifiers)) / (len(self.classifiers))

    def _module_compose(self)->list[list[nn.Module], list[nn.Module]]:
        raise NotImplementedError
    
    def set_hyper_params(self, beta:float, s:float):
        assert (beta<1)&(beta>0), "Invalid beta value:{}".format(beta)
        assert (s<1)&(s>0), "Invalid s value:{}".format(s)
        self.beta, self.s = beta, s
    
    def forward(self, x:torch.Tensor):
        # The input should be a batched 2D image
        assert len(x.shape)==4, "The input should be a batched 2D image"
        pred_final = 0
        for i, (module, classifier) in enumerate(zip(self.features, self.classifiers)):
            x = module(x)
            pred = classifier(x)
            pred_final += F.softmax(pred, dim=1) * self.alpha[i]
        return pred_final

    def forward_train(self, x: torch.Tensor, target: torch.Tensor):
        # The input should be a batched 2D image
        assert len(x.shape)==4, "The input should be a batched 2D image"
        # Calculate the features and loss
        prediction_list = []
        for i, (module, classifier) in enumerate(zip(self.features, self.classifiers)):
            x = module(x)
            pred = classifier(x.clone())
            prediction_list.append(pred)
            if i==0:
                loss = F.cross_entropy(pred, target) * self.alpha[i].detach()
            else:
                loss += F.cross_entropy(pred, target) * self.alpha[i].detach()
        # Compose the final prediction
        with torch.no_grad():
            pred_final = 0.0
            for i, pred in enumerate(prediction_list):
                pred_final += F.softmax(pred, dim=1) * self.alpha[i].detach()
        return loss, pred_final, prediction_list
    
    def step(self, x: torch.Tensor, target: torch.Tensor, optimizer: torch.optim.Optimizer):
        # Update trainable parameters
        self.train()
        optimizer.zero_grad()
        loss, pred_final, prediction_list = self.forward_train(x, target)
        loss.backward()
        optimizer.step()
        # Update alpha
        self._alpha_update(prediction_list, target)
        return loss.detach(), pred_final

    def _alpha_update(self, pred_list:list[torch.Tensor], target: torch.Tensor):
        assert len(self.alpha) == len(pred_list), "The length of alpha is not equal to that of the prediction list"
        for i, pred in enumerate(pred_list):
            self.alpha[i] = torch.maximum(
                self.alpha[i] * (self.beta ** F.cross_entropy(pred, target)), 
                torch.tensor(self.s / len(self.classifiers))
                )
        # Normalize the alpha
        self.alpha = self.alpha.div(self.alpha.sum())
        