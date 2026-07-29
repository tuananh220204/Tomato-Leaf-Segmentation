import torch
import torch.nn as nn
import torch.nn.functional as F

class DiceLoss(nn.Module):
    def __init__(self, smooth=1.0):
        super(DiceLoss, self).__init__()
        self.smooth = smooth

    def forward(self, preds, targets):
        preds = torch.sigmoid(preds)
        
        # Flatten label and prediction tensors
        preds = preds.view(-1)
        targets = targets.view(-1)
        
        intersection = (preds * targets).sum()                            
        dice = (2.*intersection + self.smooth) / (preds.sum() + targets.sum() + self.smooth)  
        
        return 1 - dice

class BCEDiceLoss(nn.Module):
    def __init__(self, bce_weight=0.5, dice_weight=0.5, pos_weight: float | None = None):
        super(BCEDiceLoss, self).__init__()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight
        self.pos_weight_scalar = pos_weight
        self.dice = DiceLoss()

    def forward(self, preds, targets):
        if self.pos_weight_scalar is not None:
            pw = torch.tensor(
                [self.pos_weight_scalar], device=preds.device, dtype=preds.dtype
            )
            bce_loss = F.binary_cross_entropy_with_logits(
                preds, targets, pos_weight=pw
            )
        else:
            bce_loss = F.binary_cross_entropy_with_logits(preds, targets)
        dice_loss = self.dice(preds, targets)
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss


class TverskyLoss(nn.Module):
    """
    Tversky Loss for binary segmentation.
    Generalization of Dice/Jaccard; controls false positives vs false negatives.
    Better for small/rare objects (lesions) than standard Dice.
    
    Formula: Tversky = TP / (TP + alpha*FP + beta*FN)
    - alpha=beta=0.5 → Dice loss
    - alpha < beta → penalize false negatives more
    - alpha > beta → penalize false positives more
    """
    
    def __init__(self, alpha=0.5, beta=0.5, smooth=1.0):
        super(TverskyLoss, self).__init__()
        self.alpha = alpha
        self.beta = beta
        self.smooth = smooth
    
    def forward(self, preds, targets):
        preds = torch.sigmoid(preds)
        preds = preds.view(-1)
        targets = targets.view(-1)
        
        tp = (preds * targets).sum()
        fp = (preds * (1 - targets)).sum()
        fn = ((1 - preds) * targets).sum()
        
        tversky = (tp + self.smooth) / (tp + self.alpha * fp + self.beta * fn + self.smooth)
        return 1 - tversky


class FocalTverskyLoss(nn.Module):
    """
    Focal Tversky Loss: combines Focal with Tversky for very small/hard lesions.
    Recommended when lesion region is <5% of image or hard to segment.
    
    Args:
        alpha, beta: Tversky coefficients (see TverskyLoss)
        gamma: Focal parameter (higher = more focus on hard examples)
    """
    
    def __init__(self, alpha=0.5, beta=0.5, gamma=2.0, smooth=1.0):
        super(FocalTverskyLoss, self).__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.smooth = smooth
    
    def forward(self, preds, targets):
        preds = torch.sigmoid(preds)
        preds = preds.view(-1)
        targets = targets.view(-1)
        
        tp = (preds * targets).sum()
        fp = (preds * (1 - targets)).sum()
        fn = ((1 - preds) * targets).sum()
        
        tversky = (tp + self.smooth) / (tp + self.alpha * fp + self.beta * fn + self.smooth)
        focal_tversky = (1 - tversky) ** self.gamma
        return focal_tversky

def calculate_iou(preds, targets, threshold=0.5, smooth=1e-6):
    preds = torch.sigmoid(preds)
    preds = (preds > threshold).float()
    
    intersection = (preds * targets).sum()
    union = preds.sum() + targets.sum() - intersection
    
    iou = (intersection + smooth) / (union + smooth)
    return iou.item()

def calculate_dice(preds, targets, threshold=0.5, smooth=1e-6):
    preds = torch.sigmoid(preds)
    preds = (preds > threshold).float()
    
    intersection = (preds * targets).sum()
    dice = (2. * intersection + smooth) / (preds.sum() + targets.sum() + smooth)
    return dice.item()
