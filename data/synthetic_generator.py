"""Synthetic tabular data generator for development and unit tests only.

The generated values are simulations; they are not measured CIC-AndMal-2020
telemetry and must not be used as evidence for scientific benchmark claims.
"""

import hashlib
import json
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from config import STATIC_LABEL_MAP, DYNAMIC_LABEL_MAP, ALL_LABELS


def generate_synthetic_raw_andmal2020(
    root_dir: str = "./raw_data",
    samples_per_class: int = 300,
    static_dim: int = 300,
    dynamic_dim: int = 141,
    seed: int = 42
) -> None:
    """
    Generate a CIC-AndMal-shaped directory tree for development tests.
    
    Structure:
    raw_data/
      ├── Static/
      │   ├── CCCS-CIC-Benign-CSVs/
      │   │   ├── Ben0.csv ... Ben4.csv
      │   └── CCCS-CIC-Malicious-CSVs/
      │       ├── Adware.csv, Backdoor.csv, Banker.csv, Dropper.csv, FileInfector.csv,
      │       ├── NoCategory.csv, PUA.csv, Ransomware.csv, Riskware.csv, Scareware.csv,
      │       ├── SMS.csv, Spy.csv, Trojan.csv, Zeroday.csv
      └── Dynamic/
          └── AndMal2020-dynamic-BeforeAndAfterReboot/
              ├── {label}_before_reboot_Cat.csv
              └── {label}_after_reboot_Cat.csv
    """
    np.random.seed(seed)
    static_benign_dir = os.path.join(root_dir, "Static", "CCCS-CIC-Benign-CSVs")
    static_malware_dir = os.path.join(root_dir, "Static", "CCCS-CIC-Malicious-CSVs")
    dynamic_dir = os.path.join(root_dir, "Dynamic", "AndMal2020-dynamic-BeforeAndAfterReboot")

    os.makedirs(static_benign_dir, exist_ok=True)
    os.makedirs(static_malware_dir, exist_ok=True)
    os.makedirs(dynamic_dir, exist_ok=True)

    print(
        f"[Synthetic Generator] Generating DEVELOPMENT-ONLY simulated files in {root_dir}..."
    )

    # 1. Generate Static Benign Files (Ben0..Ben4)
    benign_samples_per_file = max(samples_per_class // 5, 60)
    for b_idx in range(5):
        filename = f"Ben{b_idx}.csv"
        file_path = os.path.join(static_benign_dir, filename)
        sample_ids = [f"BENIGN_{b_idx}_{i:05d}" for i in range(benign_samples_per_file)]
        # Binary sparse static features (permissions/intents/API calls)
        features = np.random.binomial(n=1, p=0.08, size=(benign_samples_per_file, static_dim))
        cols = ["Sample_ID"] + [f"static_feat_{j}" for j in range(static_dim)]
        df = pd.DataFrame(features, columns=cols[1:])
        df.insert(0, "Sample_ID", sample_ids)
        df.to_csv(file_path, index=False)

    # 2. Generate Static Malicious Files
    static_malware_stems = [
        "Adware", "Backdoor", "Banker", "Dropper", "FileInfector",
        "NoCategory", "PUA", "Ransomware", "Riskware", "Scareware",
        "SMS", "Spy", "Trojan", "Zeroday"
    ]
    for stem in static_malware_stems:
        file_path = os.path.join(static_malware_dir, f"{stem}.csv")
        n_samples = samples_per_class if stem != "Riskware" else samples_per_class * 2  # Riskware is large
        sample_ids = [f"{stem.upper()}_{i:05d}" for i in range(n_samples)]
        # Slightly denser binary features with class-specific bias
        stable_hash = int(hashlib.sha256(stem.encode("utf-8")).hexdigest()[:8], 16)
        bias = (stable_hash % 100) / 1000.0
        features = np.random.binomial(n=1, p=min(0.12 + bias, 0.4), size=(n_samples, static_dim))
        cols = ["Sample_ID"] + [f"static_feat_{j}" for j in range(static_dim)]
        df = pd.DataFrame(features, columns=cols[1:])
        df.insert(0, "Sample_ID", sample_ids)
        df.to_csv(file_path, index=False)

    # 3. Generate Dynamic Files (Before and After Reboot)
    # Dynamic feature names (system calls, network, battery, memory, cpu)
    dynamic_stems = list(DYNAMIC_LABEL_MAP.keys())
    for d_stem in dynamic_stems:
        for phase in ["before", "after"]:
            filename = f"{d_stem}_{phase}_reboot_Cat.csv"
            file_path = os.path.join(dynamic_dir, filename)
            # Find matching static stem for aligned Sample_IDs
            if d_stem == "benign":
                n_samples = max(samples_per_class // 5, 60) * 5
                sample_ids = []
                for b_idx in range(5):
                    for i in range(max(samples_per_class // 5, 60)):
                        sample_ids.append(f"BENIGN_{b_idx}_{i:05d}")
            else:
                matching_static = [s for s, can in STATIC_LABEL_MAP.items() if can == DYNAMIC_LABEL_MAP[d_stem] and not s.startswith("Ben")]
                matched_stem = matching_static[0] if matching_static else d_stem.capitalize()
                n_samples = samples_per_class if matched_stem != "Riskware" else samples_per_class * 2
                sample_ids = [f"{matched_stem.upper()}_{i:05d}" for i in range(n_samples)]

            # Dynamic numerical features (counts, rates, memory bytes) with class-specific gaussian modes
            stable_hash = int(
                hashlib.sha256(d_stem.encode("utf-8")).hexdigest()[:8], 16
            )
            class_mean = (stable_hash % 50) / 10.0 + (1.5 if phase == "after" else 0.5)
            features = np.random.exponential(scale=class_mean, size=(n_samples, dynamic_dim))
            cols = ["Sample_ID"] + [f"dyn_metric_{j}" for j in range(dynamic_dim)]
            df = pd.DataFrame(features, columns=cols[1:])
            df.insert(0, "Sample_ID", sample_ids)
            df.to_csv(file_path, index=False)

    with open(os.path.join(root_dir, "SYNTHETIC_DATASET.json"), "w", encoding="utf-8") as handle:
        json.dump(
            {
                "synthetic": True,
                "intended_use": "development_and_unit_tests_only",
                "not_valid_for": "CIC-AndMal-2020 benchmark claims",
                "seed": seed,
                "samples_per_class": samples_per_class,
                "static_dim": static_dim,
                "dynamic_dim": dynamic_dim,
            },
            handle,
            indent=2,
        )
    print("[Synthetic Generator] Generated development-only simulated data tree.")


if __name__ == "__main__":
    generate_synthetic_raw_andmal2020()
