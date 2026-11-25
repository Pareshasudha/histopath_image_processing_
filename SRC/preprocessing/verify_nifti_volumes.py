
from pathlib import Path
import SimpleITK as sitk
import numpy as np

FOLDER = Path(
    r"C:\Users\Aryan gupta\histopath_image_processing_\DATA\processed\BC01\dynamic_volumes"
)

files = sorted(FOLDER.glob("*.nii.gz"))

print("\nVERIFYING RECONSTRUCTED NIFTI VOLUMES")
print("=" * 75)

reference_spacing = None
reference_origin = None
reference_direction = None

for file in files:

    image = sitk.ReadImage(str(file))
    array = sitk.GetArrayFromImage(image)

    print(f"\nFile: {file.name}")
    print(f"Dimensions (X,Y,Z): {image.GetSize()}")
    print(f"Spacing: {image.GetSpacing()}")
    print(f"Origin: {image.GetOrigin()}")
    print(f"Intensity range: {array.min()} to {array.max()}")
    print(f"Mean intensity: {array.mean():.3f}")
    print(f"Standard deviation: {array.std():.3f}")

    if reference_spacing is None:
        reference_spacing = image.GetSpacing()
        reference_origin = image.GetOrigin()
        reference_direction = image.GetDirection()

    else:
        assert image.GetSpacing() == reference_spacing
        assert np.allclose(image.GetOrigin(), reference_origin)
        assert np.allclose(
            image.GetDirection(), reference_direction
        )

    assert image.GetSize() == (320, 320, 128)

print("\n" + "=" * 75)
print(f"Total files verified: {len(files)}")
print("ALL GEOMETRY CHECKS PASSED")
