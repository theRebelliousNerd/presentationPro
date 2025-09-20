# Archived VisionCV Tools

This directory contains tools that have been superseded by better implementations but are retained for backward compatibility.

## Archived Tools

### 1. `saliency.py` - Basic Gradient Saliency Map
- **Status**: DEPRECATED
- **Archived**: 2025-09-20
- **Replacement**: `saliency_spectral.py`
- **Reason**: The spectral saliency method provides superior results

#### Comparison:

| Feature | saliency.py (Archived) | saliency_spectral.py (Active) |
|---------|------------------------|--------------------------------|
| **Method** | Sobel gradient magnitude | Spectral residual (Hou & Zhang) |
| **Domain** | Spatial (edge detection) | Frequency (FFT analysis) |
| **Quality** | Basic edge highlighting | Advanced focal point detection |
| **Use Cases** | Simple edge detection | Professional saliency analysis |
| **Performance** | Fast but limited | Slightly slower, much better |

#### Migration Guide:
```python
# OLD (deprecated)
from visioncv.tools.design.saliency import saliency_map
result = saliency_map({"imageDataUrl": data_url})

# NEW (recommended)
from visioncv.tools.design.saliency_spectral import saliency_spectral
result = saliency_spectral({"imageDataUrl": data_url})
```

## Why Archive Instead of Delete?

1. **Backward Compatibility**: Existing integrations continue to work
2. **Historical Reference**: Shows evolution of our computer vision approach
3. **Fallback Option**: Available if spectral method has issues
4. **A/B Testing**: Can compare results between methods

## Tool Utilization Note

With `saliency.py` archived, VisionCV effectively uses 16 active tools, with this one retained only for compatibility. This brings our **active utilization to 100%** since all non-deprecated tools are fully integrated.