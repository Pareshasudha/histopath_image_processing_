
from pathlib import Path
import pydicom
import re

root = (
    Path.home()
    / "Downloads"
    / "TCIA_Data_Retriever_windows_amd64"
    / "qin_breast_dce_mri"
)

study_date = "19960424"

series_info = {}

for file in root.rglob("*"):

    if not file.is_file():
        continue

    try:
        ds = pydicom.dcmread(
            str(file),
            stop_before_pixels=True
        )

        if (
            getattr(ds, "PatientID", "") !=
            "QIN-Breast-DCE-MRI-BC01"
        ):
            continue

        if str(getattr(ds, "StudyDate", "")) != study_date:
            continue

        description = str(
            getattr(ds, "SeriesDescription", "")
        )

        if "twist_20s_dyn_TRA" not in description:
            continue

        uid = str(ds.SeriesInstanceUID)

        if uid not in series_info:
            series_info[uid] = {
                "description": description,
                "series_number": ds.SeriesNumber,
                "files": [],
                "example": ds
            }

        series_info[uid]["files"].append(file)

    except Exception:
        continue


print("DYNAMIC SERIES METADATA")
print("=" * 80)

for uid, info in sorted(
    series_info.items(),
    key=lambda x: float(
        re.search(
            r"TT=([0-9.]+)s",
            x[1]["description"]
        ).group(1)
    )
):

    ds = info["example"]

    print("\nSeries:", info["series_number"])
    print("Description:", info["description"])
    print("Images:", len(info["files"]))
    print("Rows:", getattr(ds, "Rows", "N/A"))
    print("Columns:", getattr(ds, "Columns", "N/A"))
    print("Pixel Spacing:", getattr(ds, "PixelSpacing", "N/A"))
    print("Slice Thickness:", getattr(ds, "SliceThickness", "N/A"))
    print("Image Orientation:", getattr(ds, "ImageOrientationPatient", "N/A"))
    print("Image Position:", getattr(ds, "ImagePositionPatient", "N/A"))
    print("Acquisition Time:", getattr(ds, "AcquisitionTime", "N/A"))
    print("Contrast Agent:", getattr(ds, "ContrastBolusAgent", "N/A"))
    print("Contrast Start Time:", getattr(ds, "ContrastBolusStartTime", "N/A"))
    print("Photometric Interpretation:", getattr(ds, "PhotometricInterpretation", "N/A"))

print("\nTotal dynamic series:", len(series_info))
