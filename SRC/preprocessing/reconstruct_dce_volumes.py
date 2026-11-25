
from pathlib import Path
from collections import defaultdict

import pydicom
import SimpleITK as sitk
import numpy as np


# ============================================================
# 1. DEFINE PATHS
# ============================================================

DICOM_FOLDER = Path(
    r"C:\Users\Aryan gupta\Downloads\TCIA_Data_Retriever_windows_amd64\qin_breast_dce_mri"
)

OUTPUT_FOLDER = Path(
    r"C:\Users\Aryan gupta\histopath_image_processing_\DATA\processed\BC01\dynamic_volumes"
)

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. GROUP DICOM FILES BY SERIES INSTANCE UID
# ============================================================

print("\nREADING DICOM FILES...")

series_files = defaultdict(list)

for file_path in DICOM_FOLDER.glob("*.dcm"):

    try:
        ds = pydicom.dcmread(
            str(file_path),
            stop_before_pixels=True,
            force=True
        )

        # Keep only dynamic MR images
        if getattr(ds, "Modality", "") != "MR":
            continue

        description = str(
            getattr(ds, "SeriesDescription", "")
        )

        if "twist_20s_dyn_TRA" not in description:
            continue

        uid = str(ds.SeriesInstanceUID)

        series_files[uid].append(file_path)

    except Exception as e:
        print(f"Skipping {file_path.name}: {e}")


print(f"Total dynamic series found: {len(series_files)}")


# ============================================================
# 3. SORT AND RECONSTRUCT EACH SERIES
# ============================================================

print("\nRECONSTRUCTING 3D VOLUMES...\n")

for series_index, (uid, files) in enumerate(
    series_files.items(), start=1
):

    print("=" * 60)

    # Read metadata to identify series number and timepoint
    first_ds = pydicom.dcmread(
        str(files[0]),
        stop_before_pixels=True,
        force=True
    )

    series_number = int(first_ds.SeriesNumber)

    description = str(
        getattr(first_ds, "SeriesDescription", "")
    )

    print(f"Series number: {series_number}")
    print(f"Description: {description}")
    print(f"Images found: {len(files)}")

    # Sort slices using ImagePositionPatient and orientation
    orientation = np.array(
        first_ds.ImageOrientationPatient,
        dtype=float
    )

    row_direction = orientation[:3]
    column_direction = orientation[3:]

    slice_normal = np.cross(
        row_direction,
        column_direction
    )

    slice_positions = []

    for file_path in files:

        ds = pydicom.dcmread(
            str(file_path),
            stop_before_pixels=True,
            force=True
        )

        position = np.array(
            ds.ImagePositionPatient,
            dtype=float
        )

        projection = np.dot(
            position,
            slice_normal
        )

        slice_positions.append(
            (projection, file_path)
        )

    # Sort by physical slice position
    slice_positions.sort(key=lambda x: x[0])

    sorted_files = [
        str(item[1]) for item in slice_positions
    ]

    # Check for duplicate slice positions
    positions = np.array(
        [item[0] for item in slice_positions]
    )

    if len(np.unique(np.round(positions, 4))) != len(files):
        raise ValueError(
            f"Duplicate slice positions in series {series_number}"
        )

    # Reconstruct using SimpleITK
    reader = sitk.ImageSeriesReader()

    reader.SetFileNames(sorted_files)

    image = reader.Execute()

    # Verify reconstructed volume
    size = image.GetSize()
    spacing = image.GetSpacing()
    origin = image.GetOrigin()
    direction = image.GetDirection()

    print(f"Volume dimensions (X,Y,Z): {size}")
    print(f"Voxel spacing (mm): {spacing}")
    print(f"Origin: {origin}")

    if size != (320, 320, 128):
        raise ValueError(
            f"Unexpected dimensions in series {series_number}: {size}"
        )

    # Save NIfTI volume
    output_path = OUTPUT_FOLDER / (
        f"series_{series_number:02d}.nii.gz"
    )

    sitk.WriteImage(
        image,
        str(output_path),
        True
    )

    print(f"SAVED: {output_path}")


# ============================================================
# 4. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DCE RECONSTRUCTION COMPLETED")
print("=" * 60)

saved_files = list(OUTPUT_FOLDER.glob("*.nii.gz"))

print(f"Total NIfTI volumes saved: {len(saved_files)}")
print(f"Output directory: {OUTPUT_FOLDER}")

for file in sorted(saved_files):
    print(file.name)

print("\nDONE!")
