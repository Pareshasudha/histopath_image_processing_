
from pathlib import Path
import pydicom

root = (
    Path.home()
    / "Downloads"
    / "TCIA_Data_Retriever_windows_amd64"
    / "qin_breast_dce_mri"
)

target_descriptions = [
    "NIfTI Visit 1",
    "Matlab Visit 1"
]

print("INSPECTING REFERENCE SERIES")
print("=" * 70)

for file in root.rglob("*"):

    if not file.is_file():
        continue

    try:
        ds = pydicom.dcmread(
            str(file),
            stop_before_pixels=True,
            force=True
        )

        description = str(
            getattr(ds, "SeriesDescription", "")
        )

        if description in target_descriptions:

            print("\nFile:", file.name)
            print("Series Description:", description)
            print("Patient ID:", getattr(ds, "PatientID", "N/A"))
            print("Study Date:", getattr(ds, "StudyDate", "N/A"))
            print("Modality:", getattr(ds, "Modality", "N/A"))
            print("SOP Class UID:", getattr(ds, "SOPClassUID", "N/A"))
            print("Transfer Syntax:", getattr(
                getattr(ds, "file_meta", None),
                "TransferSyntaxUID",
                "N/A"
            ))
            print("Rows:", getattr(ds, "Rows", "N/A"))
            print("Columns:", getattr(ds, "Columns", "N/A"))
            print("Number of Frames:", getattr(ds, "NumberOfFrames", "N/A"))
            print("Image Type:", getattr(ds, "ImageType", "N/A"))
            print("Series UID:", getattr(ds, "SeriesInstanceUID", "N/A"))

    except Exception:
        pass
