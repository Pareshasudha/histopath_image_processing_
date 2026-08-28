import nibabel as nib
import numpy as np
import plotly.graph_objects as go
from pathlib import Path


# ---------------------------------------------------------
# Locate NIfTI file
# ---------------------------------------------------------

project_root = Path(__file__).resolve().parents[2]

nifti_file = (
    project_root
    / "DATA"
    / "NIFTI"
    / "patient_001.nii.gz"
)


# ---------------------------------------------------------
# Load NIfTI
# ---------------------------------------------------------

print(f"Loading: {nifti_file}")

nii = nib.load(str(nifti_file))

volume = nii.get_fdata()

print(f"Original volume shape: {volume.shape}")


# ---------------------------------------------------------
# Normalize intensity
# ---------------------------------------------------------

volume = volume.astype(np.float32)

volume -= volume.min()

if volume.max() > 0:
    volume /= volume.max()


# ---------------------------------------------------------
# Downsample for interactive visualization
# ---------------------------------------------------------

# This makes the 3D visualization faster.

step = 3

volume_small = volume[::step, ::step, ::step]

print(f"Visualization volume shape: {volume_small.shape}")


# ---------------------------------------------------------
# Create coordinate grid
# ---------------------------------------------------------

x, y, z = np.indices(volume_small.shape)


# ---------------------------------------------------------
# Keep only brighter voxels
# ---------------------------------------------------------

threshold = 0.25

mask = volume_small > threshold

x = x[mask]
y = y[mask]
z = z[mask]

values = volume_small[mask]


# ---------------------------------------------------------
# Create 3D scatter plot
# ---------------------------------------------------------

fig = go.Figure(
    data=go.Scatter3d(
        x=x,
        y=y,
        z=z,

        mode="markers",

        marker=dict(
            size=1.5,
            color=values,
            opacity=0.25,
            colorscale="Gray"
        )
    )
)


# ---------------------------------------------------------
# Layout
# ---------------------------------------------------------

fig.update_layout(
    title="3D CT/MRI Volume",

    scene=dict(
        xaxis_title="X",
        yaxis_title="Y",
        zaxis_title="Z",

        aspectmode="data"
    ),

    margin=dict(
        l=0,
        r=0,
        b=0,
        t=40
    )
)


# ---------------------------------------------------------
# Show
# ---------------------------------------------------------

fig.show()