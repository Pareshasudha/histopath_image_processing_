
from pathlib import Path
from collections import defaultdict
import numpy as np
import pydicom

root = (
    Path.home()
    / "Downloads"
    / "TCIA_Data_Retriever_windows_amd64"
    / "qin_breast_dce_mri"
)

series_data = defaultdict(list)

print("CHECKING DCE VOLUME GEOMETRY...")

for file in root.rglob("*"):

    if not file.is_file():
        continue

    try:
        ds = pydicom.dcmread(
            str(file),
            stop_before_pixels=True,
            force=True
        )

        if getattr(ds, "Modality", "") != "MR":
            continue

        uid = str(ds.SeriesInstanceUID)

        if "twist_20s_dyn_TRA" not in str(
            getattr(ds, "SeriesDescription", "")
        ):
            continue

        orientation = np.array(
            ds.ImageOrientationPatient,
            dtype=float
        )

        position = np.array(
            ds.ImagePositionPatient,
            dtype=float
        )

        row_direction = orientation[:3]
        col_direction = orientation[3:]

        normal = np.cross(row_direction, col_direction)

        projection = float(np.dot(position, normal))

        series_data[uid].append({
            "series": int(ds.SeriesNumber),
            "description": str(ds.SeriesDescription),
            "position": projection,
            "rows": int(ds.Rows),
            "columns": int(ds.Columns),
            "pixel_spacing": tuple(map(float, ds.PixelSpacing)),
            "orientation": tuple(orientation),
            "sop_uid": str(ds.SOPInstanceUID)
        })

    except Exception:
        continue


print("\n" + "=" * 75)
print("PER-SERIES GEOMETRY")
print("=" * 75)

reference_positions = None

for uid, images in sorted(
    series_data.items(),
    key=lambda item: item[1][0]["series"]
):

    images.sort(key=lambda x: x["position"])

    positions = np.array([
        image["position"] for image in images
    ])

    unique_positions = np.unique(
        np.round(positions, 4)
    )

    differences = np.diff(positions)

    median_spacing = (
        np.median(differences)
        if len(differences) else float("nan")
    )

    first = images[0]

    print("\nSeries:", first["series"])
    print("Description:", first["description"])
    print("Image count:", len(images))
    print("Unique slice positions:", len(unique_positions))
    print("Dimensions:", first["rows"], "x", first["columns"])
    print("Pixel spacing:", first["pixel_spacing"])
    print("Slice spacing (median):", round(median_spacing, 4))
    print("Position range:", round(positions.min(), 3),
          "to", round(positions.max(), 3))

    if reference_positions is None:
        reference_positions = unique_positions
        print("Reference geometry established.")

    else:
        same_count = (
            len(reference_positions) == len(unique_positions)
        )

        if same_count:
            difference = np.max(
                np.abs(reference_positions - unique_positions)
            )
            print("Maximum position difference from first series:",
                  round(float(difference), 4), "mm")
        else:
            print("WARNING: Different number of unique slice positions!")


print("\n" + "=" * 75)
print("TOTAL DYNAMIC SERIES:", len(series_data))
print("TOTAL DYNAMIC IMAGES:",
      sum(len(images) for images in series_data.values()))
print("=" * 75)
