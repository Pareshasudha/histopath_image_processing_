
from pathlib import Path
from collections import defaultdict
import pydicom

root = (
    Path.home()
    / "Downloads"
    / "TCIA_Data_Retriever_windows_amd64"
    / "qin_breast_dce_mri"
)

manifests = {
    "NIfTI Visit 1": set(),
    "Matlab Visit 1": set()
}

series_data = defaultdict(list)

print("SCANNING DICOM FILES...")

for file in root.rglob("*"):

    if not file.is_file():
        continue

    try:
        ds = pydicom.dcmread(str(file), force=True)

        description = str(
            getattr(ds, "SeriesDescription", "")
        )

        # Collect manifest references
        if description in manifests:

            def collect(dataset):
                for element in dataset:
                    if element.VR == "SQ":
                        for item in element.value:
                            collect(item)

                    elif element.keyword == "ReferencedSOPInstanceUID":
                        manifests[description].add(str(element.value))

            collect(ds)
            continue

        # Collect MRI acquisition information
        if getattr(ds, "Modality", "") != "MR":
            continue

        series_uid = str(
            getattr(ds, "SeriesInstanceUID", "")
        )

        series_data[series_uid].append({
            "series_number": getattr(ds, "SeriesNumber", "N/A"),
            "description": description,
            "sop_uid": str(getattr(ds, "SOPInstanceUID", "")),
            "acquisition_time": getattr(ds, "AcquisitionTime", "N/A"),
            "image_type": getattr(ds, "ImageType", "N/A"),
            "temporal_position": getattr(ds, "TemporalPositionIdentifier", "N/A"),
            "contrast_agent": getattr(ds, "ContrastBolusAgent", "N/A"),
            "contrast_start": getattr(ds, "ContrastBolusStartTime", "N/A"),
        })

    except Exception:
        continue


# Compare complete manifest sets
print("\n" + "=" * 70)
print("MANIFEST COMPARISON")
print("=" * 70)

nifti_refs = manifests["NIfTI Visit 1"]
matlab_refs = manifests["Matlab Visit 1"]

print("NIfTI references:", len(nifti_refs))
print("Matlab references:", len(matlab_refs))
print("Exactly identical:", nifti_refs == matlab_refs)

print("Only in NIfTI:", len(nifti_refs - matlab_refs))
print("Only in Matlab:", len(matlab_refs - nifti_refs))


# Acquisition summary
print("\n" + "=" * 70)
print("MRI SERIES ACQUISITION SUMMARY")
print("=" * 70)

for uid, images in sorted(
    series_data.items(),
    key=lambda item: int(item[1][0]["series_number"])
):

    first = images[0]

    referenced_count = sum(
        image["sop_uid"] in nifti_refs
        for image in images
    )

    print("\nSeries:", first["series_number"])
    print("Description:", first["description"])
    print("Images:", len(images))
    print("Images referenced by manifest:", referenced_count)
    print("Acquisition Time:", first["acquisition_time"])
    print("Image Type:", first["image_type"])
    print("Temporal Position:", first["temporal_position"])
    print("Contrast Agent:", first["contrast_agent"])
    print("Contrast Start Time:", first["contrast_start"])
