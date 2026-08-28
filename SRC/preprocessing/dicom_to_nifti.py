import SimpleITK as sitk
from pathlib import Path


def dicom_series_to_nifti(dicom_folder, output_file):
    dicom_folder = Path(dicom_folder)
    output_file = Path(output_file)

    print(f"Reading DICOM series from:")
    print(dicom_folder)

    # Find all DICOM series in the folder
    series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(dicom_folder))

    if not series_ids:
        raise RuntimeError(
            f"No DICOM series found in {dicom_folder}"
        )

    print(f"\nFound {len(series_ids)} DICOM series.")

    # Process the first series
    series_id = series_ids[0]

    print(f"Using series ID:")
    print(series_id)

    # Get filenames using DICOM metadata.
    # This does NOT depend on filenames.
    dicom_files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(
        str(dicom_folder),
        series_id
    )

    print(f"\nNumber of slices: {len(dicom_files)}")

    if len(dicom_files) < 2:
        raise RuntimeError(
            "Only one DICOM slice was found. "
            "A 3D volume requires multiple slices."
        )

    # Read the complete series
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(dicom_files)

    image = reader.Execute()

    print("\n3D volume information:")
    print(f"Size:     {image.GetSize()}")
    print(f"Spacing:  {image.GetSpacing()}")
    print(f"Origin:   {image.GetOrigin()}")
    print(f"Direction:{image.GetDirection()}")

    # Make sure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save as NIfTI
    sitk.WriteImage(image, str(output_file))

    print("\nConversion successful!")
    print(f"Saved to:")
    print(output_file)


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[2]

    dicom_folder = project_root / "DATA" / "DICOM" / "patient_001"

    output_file = project_root / "DATA" / "NIFTI" / "patient_001.nii.gz"

    dicom_series_to_nifti(
        dicom_folder,
        output_file
    )