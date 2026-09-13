from __future__ import annotations

import torch.nn as nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


def create_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    if num_classes < 2:
        raise ValueError("EfficientNet classifier requires at least two classes.")
    weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = efficientnet_b0(weights=weights)
    input_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(input_features, num_classes)
    return model


def freeze_backbone(model: nn.Module) -> None:
    for parameter in model.features.parameters():
        parameter.requires_grad = False
    for parameter in model.classifier.parameters():
        parameter.requires_grad = True


def unfreeze_deep_blocks(model: nn.Module, block_count: int) -> None:
    if block_count <= 0:
        return
    for block in list(model.features.children())[-block_count:]:
        for parameter in block.parameters():
            parameter.requires_grad = True


def parameter_groups(model: nn.Module, backbone_lr: float, classifier_lr: float) -> list[dict[str, object]]:
    backbone = [parameter for parameter in model.features.parameters() if parameter.requires_grad]
    classifier = [parameter for parameter in model.classifier.parameters() if parameter.requires_grad]
    groups: list[dict[str, object]] = []
    if backbone:
        groups.append({"params": backbone, "lr": backbone_lr})
    groups.append({"params": classifier, "lr": classifier_lr})
    return groups

