
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

for file in root.rglob("*"):

    if not file.is_file():
        continue

    try:
        ds = pydicom.dcmread(str(file), force=True)

        description = str(
            getattr(ds, "SeriesDescription", "")
        )

        if description not in target_descriptions:
            continue

        print("\n" + "=" * 65)
        print("MANIFEST:", description)
        print("=" * 65)

        references = []

        def collect_references(dataset):

            for element in dataset:

                if element.VR == "SQ":

                    for item in element.value:
                        collect_references(item)

                elif element.keyword == "ReferencedSOPInstanceUID":
                    references.append(str(element.value))

        collect_references(ds)

        references = sorted(set(references))

        print("Total unique referenced images:", len(references))

        for uid in references[:10]:
            print(uid)

        if len(references) > 10:
            print("... remaining references omitted")

    except Exception:
        pass
