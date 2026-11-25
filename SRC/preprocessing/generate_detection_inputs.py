
from pathlib import Path
import SimpleITK as sitk
import numpy as np


# ============================================================
# 1. PATHS
# ============================================================

INPUT_FOLDER = Path(
    r"C:\Users\Aryan gupta\histopath_image_processing_\DATA\processed\BC01\dynamic_volumes"
)

OUTPUT_FOLDER = Path(
    r"C:\Users\Aryan gupta\histopath_image_processing_\DATA\processed\BC01\detection_inputs"
)

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. DEFINE DYNAMIC ACQUISITION TIMES
#    Times are in seconds, from your DICOM inspection.
# ============================================================

ACQUISITION_TIMES = {
    8: 69.7,
    11: 89.9,
    13: 110.0,
    15: 130.2,
    17: 150.4,
    19: 170.5,
    21: 190.7,
    23: 210.8,
    25: 231.0,
    27: 251.2,
    29: 271.3,
    31: 291.5,
    33: 311.7,
    35: 331.8,
    37: 352.0,
    39: 372.1,
    41: 392.3,
    43: 412.5,
    45: 432.6,
    47: 452.8,
    49: 473.0,
    51: 493.1,
    53: 513.3,
    55: 533.4,
    57: 553.6,
    59: 573.8,
    61: 593.9
}

PRE_SERIES = 8
REFERENCE_SERIES = 11

POST_SERIES = [
    s for s in ACQUISITION_TIMES if s >= REFERENCE_SERIES
]


# ============================================================
# 3. LOAD NIFTI VOLUME
# ============================================================

def load_volume(series_number):

    file_path = INPUT_FOLDER / f"series_{series_number:02d}.nii.gz"

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    image = sitk.ReadImage(str(file_path))

    array = sitk.GetArrayFromImage(image).astype(np.float32)

    print(
        f"Loaded series {series_number}: "
        f"{image.GetSize()}"
    )

    return image, array


# ============================================================
# 4. AFFINE REGISTRATION
#    Align each volume to the first post-contrast image.
# ============================================================


def register_to_reference(moving_image, fixed_image):

    # Ensure both images are 3D float32 images
    moving_image = sitk.Cast(
        moving_image,
        sitk.sitkFloat32
    )

    fixed_image = sitk.Cast(
        fixed_image,
        sitk.sitkFloat32
    )

    # Check dimensions
    if moving_image.GetDimension() != 3:
        raise ValueError("Moving image is not 3D.")

    if fixed_image.GetDimension() != 3:
        raise ValueError("Fixed image is not 3D.")

    # Initialize affine transformation
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image,
        moving_image,
        sitk.AffineTransform(3),
        sitk.CenteredTransformInitializerFilter.GEOMETRY
    )

    registration = sitk.ImageRegistrationMethod()

    registration.SetMetricAsMattesMutualInformation(
        numberOfHistogramBins=50
    )

    registration.SetMetricSamplingStrategy(
        registration.RANDOM
    )

    registration.SetMetricSamplingPercentage(
        0.10,
        seed=42
    )

    registration.SetInterpolator(
        sitk.sitkLinear
    )

    registration.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10
    )

    registration.SetOptimizerScalesFromPhysicalShift()

    registration.SetShrinkFactorsPerLevel(
        [4, 2, 1]
    )

    registration.SetSmoothingSigmasPerLevel(
        [2, 1, 0]
    )

    registration.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    registration.SetInitialTransform(
        initial_transform,
        inPlace=False
    )

    final_transform = registration.Execute(
        fixed_image,
        moving_image
    )

    registered_image = sitk.Resample(
        moving_image,
        fixed_image,
        final_transform,
        sitk.sitkLinear,
        0.0,
        sitk.sitkFloat32
    )

    print(
        "Registration metric:",
        registration.GetMetricValue()
    )

    return registered_image



# ============================================================
# 5. LOAD FIRST POST-CONTRAST IMAGE
# ============================================================

print("\nLOADING REFERENCE IMAGE...")

reference_image, t1_post_raw = load_volume(
    REFERENCE_SERIES
)

reference_image = sitk.Cast(
    reference_image,
    sitk.sitkFloat32
)


# ============================================================
# 6. REGISTER PRE-CONTRAST IMAGE
# ============================================================

print("\nREGISTERING PRE-CONTRAST IMAGE...")

pre_image, _ = load_volume(PRE_SERIES)

pre_registered = register_to_reference(
    pre_image,
    reference_image
)

pre_array = sitk.GetArrayFromImage(
    pre_registered
).astype(np.float32)


# ============================================================
# 7. CALCULATE PRE-CONTRAST 95TH PERCENTILE
# ============================================================

p95 = float(np.percentile(pre_array, 95))

if not np.isfinite(p95) or p95 <= 0:
    raise ValueError("Invalid pre-contrast 95th percentile.")

print("\nPre-contrast P95:", p95)


# ============================================================
# 8. NORMALIZE T1_POST
# ============================================================

print("\nGENERATING T1_POST...")

t1_post = t1_post_raw / p95


# ============================================================
# 9. CALCULATE DCE_IN
#
#    DCE-in = (first post - pre) / time interval
#    Time is expressed in minutes.
# ============================================================

print("\nGENERATING DCE_IN...")

delta_time = (
    ACQUISITION_TIMES[REFERENCE_SERIES]
    - ACQUISITION_TIMES[PRE_SERIES]
) / 60.0

if delta_time <= 0:
    raise ValueError("Invalid acquisition time interval.")

dce_in = (
    t1_post_raw - pre_array
) / delta_time

# Normalize by pre-contrast P95
dce_in = dce_in / p95


# ============================================================
# 10. CALCULATE DCE_OUT
#
#     Voxel-wise linear regression slope across
#     all post-contrast volumes.
#
#     DCE-out = slope of signal intensity over time.
#     Time is expressed in minutes.
# ============================================================

print("\nGENERATING DCE_OUT...")

times = np.array(
    [
        (ACQUISITION_TIMES[s] -
         ACQUISITION_TIMES[REFERENCE_SERIES]) / 60.0
        for s in POST_SERIES
    ],
    dtype=np.float64
)

number_of_volumes = len(POST_SERIES)

sum_y = np.zeros_like(t1_post_raw, dtype=np.float64)
sum_ty = np.zeros_like(t1_post_raw, dtype=np.float64)

for index, series_number in enumerate(POST_SERIES):

    print(
        f"\nProcessing post-contrast series "
        f"{series_number} ({index + 1}/{number_of_volumes})"
    )

    moving_image, _ = load_volume(series_number)

    if series_number == REFERENCE_SERIES:

        registered_image = reference_image

    else:

        registered_image = register_to_reference(
            moving_image,
            reference_image
        )

    volume_array = sitk.GetArrayFromImage(
        registered_image
    ).astype(np.float64)

    time_value = times[index]

    sum_y += volume_array
    sum_ty += time_value * volume_array


# Linear regression slope:
#
# slope = sum((t - mean_t) * (S - mean_S))
#         ---------------------------------
#              sum((t - mean_t)^2)

mean_t = np.mean(times)

sum_t_centered_squared = np.sum(
    (times - mean_t) ** 2
)

if sum_t_centered_squared == 0:
    raise ValueError("Cannot calculate DCE-out slope.")

mean_y = sum_y / number_of_volumes

dce_out = (
    sum_ty - mean_t * sum_y
) / sum_t_centered_squared

# Normalize by pre-contrast P95
dce_out = dce_out / p95


# ============================================================
# 11. SAVE THREE OUTPUT VOLUMES
# ============================================================

print("\nSAVING OUTPUT FILES...")

outputs = {
    "T1_post.nii.gz": t1_post,
    "DCE_in.nii.gz": dce_in,
    "DCE_out.nii.gz": dce_out
}

for filename, array in outputs.items():

    output_image = sitk.GetImageFromArray(
        array.astype(np.float32)
    )

    output_image.CopyInformation(reference_image)

    output_path = OUTPUT_FOLDER / filename

    sitk.WriteImage(
        output_image,
        str(output_path),
        True
    )

    print(f"SAVED: {output_path}")


# ============================================================
# 12. FINAL VERIFICATION
# ============================================================

print("\n" + "=" * 65)
print("DETECTION INPUT GENERATION COMPLETED")
print("=" * 65)

for filename in outputs:

    path = OUTPUT_FOLDER / filename

    image = sitk.ReadImage(str(path))
    array = sitk.GetArrayFromImage(image)

    print(f"\nFile: {filename}")
    print("Dimensions:", image.GetSize())
    print("Spacing:", image.GetSpacing())
    print("Intensity range:", array.min(), "to", array.max())
    print("Mean:", array.mean())
    print("Standard deviation:", array.std())

print("\nAll three files generated.")
print("Output folder:", OUTPUT_FOLDER)
