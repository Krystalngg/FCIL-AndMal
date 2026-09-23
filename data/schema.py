"""Shared schema rules for prepared CIC-AndMal tabular datasets."""

from typing import Iterable, List, Optional

import pandas as pd


# These columns identify or describe a sample; they are not model inputs.
NON_FEATURE_COLUMNS = frozenset({
    "sample_id",
    "hash",
    "category",
    "family",
    "label",
    "reboot_phase",
    "split_group_id",
})


def get_feature_columns(
    df: pd.DataFrame,
    additional_exclusions: Optional[Iterable[str]] = None,
) -> List[str]:
    """Return model feature columns while excluding identifiers and annotations."""
    excluded = set(NON_FEATURE_COLUMNS)
    if additional_exclusions is not None:
        excluded.update(str(column).casefold() for column in additional_exclusions)
    return [column for column in df.columns if str(column).casefold() not in excluded]


def drop_raw_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Remove source annotations while preserving an identity-only split group."""
    cleaned = df.copy()
    hash_columns = [
        column for column in cleaned.columns if str(column).casefold() == "hash"
    ]
    if hash_columns and "Split_Group_ID" not in cleaned.columns:
        # Preserve APK/application identity solely for group-disjoint splitting;
        # schema rules guarantee that it is never used as a model feature.
        cleaned["Split_Group_ID"] = cleaned[hash_columns[0]].astype(str)
    columns_to_drop = [
        column
        for column in cleaned.columns
        if str(column).casefold() in {"hash", "category", "family"}
    ]
    # A deep copy also consolidates wide CSV frames before annotation columns
    # are added, avoiding pandas fragmentation warnings on the real dataset.
    return cleaned.drop(columns=columns_to_drop, errors="ignore").copy()
