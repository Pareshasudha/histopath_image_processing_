
from pathlib import Path
from collections import defaultdict
import pydicom

root = (
    Path.home()
    / "Downloads"
    / "TCIA_Data_Retriever_windows_amd64"
    / "qin_breast_dce_mri"
)

# Store all BC01 series, without filtering by study date
series_data = defaultdict(list)
patient_counts = defaultdict(int)

total_readable = 0

print("Scanning downloaded DICOM files...")

for file in root.rglob("*"):
    if not file.is_file():
        continue

    try:
        ds = pydicom.dcmread(
            str(file),
            stop_before_pixels=True,
            force=True
        )

        if not hasattr(ds, "SOPInstanceUID"):
            continue

        total_readable += 1

        patient_id = str(getattr(ds, "PatientID", "UNKNOWN"))
        patient_counts[patient_id] += 1

        if "BC01" not in patient_id:
            continue

        study_date = str(getattr(ds, "StudyDate", "UNKNOWN"))
        study_uid = str(getattr(ds, "StudyInstanceUID", "UNKNOWN"))
        series_uid = str(getattr(ds, "SeriesInstanceUID", "UNKNOWN"))

        series_data[
            (study_date, study_uid, series_uid)
        ].append(ds)

    except Exception:
        continue

print("\nTotal readable DICOM files:", total_readable)

print("\nPATIENT-WISE FILE COUNTS")
print("=" * 60)

for patient, count in sorted(patient_counts.items()):
    print(patient, ":", count)

print("\nALL BC01 STUDIES AND SERIES")
print("=" * 100)

for (date, study_uid, series_uid), images in sorted(
    series_data.items(),
    key=lambda x: (x[0][0], int(getattr(x[1][0], "SeriesNumber", 0)))
):
    ds = images[0]

    print("\nStudy date:", date)
    print("Series number:", getattr(ds, "SeriesNumber", "N/A"))
    print("Description:", getattr(ds, "SeriesDescription", "N/A"))
    print("Image count:", len(images))
    print("Series UID:", series_uid)

print("\nTotal BC01 series:", len(series_data))
