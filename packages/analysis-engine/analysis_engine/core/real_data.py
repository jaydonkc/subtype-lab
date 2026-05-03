from __future__ import annotations

import hashlib
import io
import ssl
import urllib.request
import zipfile
from dataclasses import dataclass
from importlib import resources

import certifi
import pandas as pd


WDBC_DATA_URL = "https://cdn.uci-ics-mlr-prod.aws.uci.edu/17/breast%2Bcancer%2Bwisconsin%2Bdiagnostic.zip"
WDBC_DATASET_ID = "wdbc"
WDBC_FEATURE_NAMES = [
    "radius_mean",
    "texture_mean",
    "perimeter_mean",
    "area_mean",
    "smoothness_mean",
    "compactness_mean",
    "concavity_mean",
    "concave_points_mean",
    "symmetry_mean",
    "fractal_dimension_mean",
    "radius_se",
    "texture_se",
    "perimeter_se",
    "area_se",
    "smoothness_se",
    "compactness_se",
    "concavity_se",
    "concave_points_se",
    "symmetry_se",
    "fractal_dimension_se",
    "radius_worst",
    "texture_worst",
    "perimeter_worst",
    "area_worst",
    "smoothness_worst",
    "compactness_worst",
    "concavity_worst",
    "concave_points_worst",
    "symmetry_worst",
    "fractal_dimension_worst",
]


@dataclass(frozen=True)
class PublicDataset:
    dataset_id: str
    dataset_hash: str
    matrix: pd.DataFrame
    metadata: pd.DataFrame
    source: dict[str, str]


def load_wdbc_dataset() -> PublicDataset:
    """Load the UCI Breast Cancer Wisconsin Diagnostic benchmark.

    The endpoint tries UCI first so the demo can honestly show a public-data
    import. If that live download fails, it falls back to the bundled snapshot
    so the hackathon demo does not depend on a third-party outage.
    """

    try:
        raw = fetch_wdbc_data()
        loaded_from = "uci_live_download"
    except Exception:
        raw = bundled_wdbc_data()
        loaded_from = "bundled_snapshot"
    return parse_wdbc_data(raw, loaded_from)


def fetch_wdbc_data() -> bytes:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(
        WDBC_DATA_URL,
        headers={"User-Agent": "SubtypeLab research demo"},
    )
    with urllib.request.urlopen(request, timeout=8, context=ssl_context) as response:
        archive = response.read()
    with zipfile.ZipFile(io.BytesIO(archive)) as dataset_zip:
        return dataset_zip.read("wdbc.data")


def bundled_wdbc_data() -> bytes:
    return (resources.files("analysis_engine.data.uci_wdbc") / "wdbc.data").read_bytes()


def parse_wdbc_data(raw: bytes, loaded_from: str) -> PublicDataset:
    frame = pd.read_csv(
        io.BytesIO(raw),
        header=None,
        names=["source_id", "diagnosis", *WDBC_FEATURE_NAMES],
    )
    sample_ids = [f"WDBC_{i + 1:03d}" for i in range(len(frame))]
    matrix = frame[WDBC_FEATURE_NAMES].copy()
    matrix.index = sample_ids

    metadata = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "diagnosis_label": frame["diagnosis"].map({"M": "malignant", "B": "benign"}),
            "dataset_source": "UCI Breast Cancer Wisconsin Diagnostic",
        }
    ).set_index("sample_id")

    return PublicDataset(
        dataset_id=WDBC_DATASET_ID,
        dataset_hash=hashlib.sha256(raw).hexdigest(),
        matrix=matrix,
        metadata=metadata,
        source={
            "name": "UCI Breast Cancer Wisconsin Diagnostic",
            "url": "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
            "doi": "10.24432/C5DW2B",
            "license": "CC BY 4.0",
            "loaded_from": loaded_from,
            "notes": "Real numeric morphology features from digitized breast FNA images; not gene expression data.",
        },
    )
