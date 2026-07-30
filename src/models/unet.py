import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

def build_unet_model(encoder_name='resnet50', encoder_weights='imagenet', in_channels=3, classes=1):
    """
    Build a U-Net model using segmentation_models_pytorch library.
    """
    model = smp.Unet(
        encoder_name=encoder_name,        
        encoder_weights=encoder_weights,     
        in_channels=in_channels,                  
        classes=classes,                      
    )
    return model
