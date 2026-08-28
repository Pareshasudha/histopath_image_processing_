import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ---------------------------------------------------------
# Locate the NIfTI file
# ---------------------------------------------------------

project_root = Path(__file__).resolve().parents[2]

nifti_file = project_root / "DATA" / "NIFTI" / "patient_001.nii.gz"


# ---------------------------------------------------------
# Load NIfTI
# ---------------------------------------------------------

print(f"Loading: {nifti_file}")

nii = nib.load(str(nifti_file))

volume = nii.get_fdata()

print("\nNIfTI information")
print("-----------------")
print(f"Shape:   {volume.shape}")
print(f"Spacing: {nii.header.get_zooms()[:3]}")
print(f"Minimum intensity: {volume.min():.2f}")
print(f"Maximum intensity: {volume.max():.2f}")


# ---------------------------------------------------------
# Get middle slices
# ---------------------------------------------------------

x, y, z = volume.shape

axial_index = z // 2
coronal_index = y // 2
sagittal_index = x // 2


axial = volume[:, :, axial_index]
coronal = volume[:, coronal_index, :]
sagittal = volume[sagittal_index, :, :]


# ---------------------------------------------------------
# Display Axial slice
# ---------------------------------------------------------

plt.figure(figsize=(7, 7))

plt.imshow(
    np.rot90(axial),
    cmap="gray"
)

plt.title(f"Axial Slice {axial_index + 1}/{z}")
plt.axis("off")

plt.show()


# ---------------------------------------------------------
# Display Coronal slice
# ---------------------------------------------------------

plt.figure(figsize=(7, 7))

plt.imshow(
    np.rot90(coronal),
    cmap="gray"
)

plt.title(f"Coronal Slice {coronal_index + 1}/{y}")
plt.axis("off")

plt.show()


# ---------------------------------------------------------
# Display Sagittal slice
# ---------------------------------------------------------

plt.figure(figsize=(7, 7))

plt.imshow(
    np.rot90(sagittal),
    cmap="gray"
)

plt.title(f"Sagittal Slice {sagittal_index + 1}/{x}")
plt.axis("off")

plt.show()
