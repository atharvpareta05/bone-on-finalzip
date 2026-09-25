import io
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms

from backend.app.config import settings

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_model: Optional[nn.Module] = None


def get_inference_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )


def load_model() -> nn.Module:
    global _model
    if _model is not None:
        return _model

    if not settings.model_path.exists():
        raise FileNotFoundError(f"Champion model checkpoint not found: {settings.model_path}")

    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)

    # Safe PyTorch loading as audited in Phase 1
    checkpoint = torch.load(settings.model_path, map_location=DEVICE, weights_only=True)
    model.load_state_dict(checkpoint["model"])
    model.to(DEVICE)
    model.eval()

    _model = model
    return _model


def get_risk_band(probability: float) -> str:
    """Return plain-language risk band matching CareLens clinical thresholds."""
    if probability >= 0.70:
        return "High Risk"
    elif probability >= 0.35:
        return "Borderline / Indeterminate"
    else:
        return "Low Risk"


def run_inference_and_gradcam(image: Image.Image) -> Tuple[str, float, str, Image.Image]:
    """
    Port of CareLens verified Grad-CAM saliency extraction on ResNet-50 layer4[-1].
    Returns (prediction_label, cancer_probability, risk_band, overlay_image).
    """
    model = load_model()
    transform = get_inference_transform()
    tensor = transform(image).unsqueeze(0).to(DEVICE)

    activations = []
    gradients = []

    def forward_hook(module, inp, out):
        activations.append(out)

    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0])

    target_layer = model.layer4[-1]
    handle_fwd = target_layer.register_forward_hook(forward_hook)
    handle_bwd = target_layer.register_full_backward_hook(backward_hook)

    model.eval()
    model.zero_grad()

    logits = model(tensor)
    probabilities = torch.softmax(logits, dim=1)[0]
    cancer_prob = float(probabilities[1].item())
    pred_label = "Cancer / Tumor Detected" if cancer_prob >= 0.5 else "No Malignancy Detected"
    risk_band = get_risk_band(cancer_prob)

    # Backpropagate target class 1 (cancer saliency)
    loss = logits[0, 1]
    loss.backward()

    handle_fwd.remove()
    handle_bwd.remove()

    if not activations or not gradients:
        raise RuntimeError("Failed capturing activation maps or gradients during Grad-CAM.")

    act = activations[0].detach()
    grad = gradients[0].detach()

    weights = grad.mean(dim=(2, 3), keepdim=True)
    cam = torch.clamp((weights * act).sum(dim=1), min=0).squeeze().cpu().numpy()
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

    # Create 224x224 heatmap array
    cam_resized = Image.fromarray((cam * 255).astype(np.uint8)).resize((224, 224), Image.Resampling.BILINEAR)
    cam_np = np.array(cam_resized) / 255.0

    # Crop and resize base image to match 224x224 center crop
    base_resized = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224)])(image)
    base_np = np.array(base_resized).astype(np.float32) / 255.0

    # Colorize with jet colormap and overlay (55% scan, 45% heatmap)
    colormap = plt.get_cmap("jet")
    heatmap_rgb = colormap(cam_np)[:, :, :3]
    overlay_np = np.clip(base_np * 0.55 + heatmap_rgb * 0.45, 0.0, 1.0)
    overlay_img = Image.fromarray((overlay_np * 255).astype(np.uint8))

    return pred_label, cancer_prob, risk_band, overlay_img
