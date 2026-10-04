#!/usr/bin/env python3
"""
Supplementary Evaluation Script for Missing FL Checkpoints
===========================================================
Tự động quét các thư mục thí nghiệm Federated Learning trong EXPERIMENT/:
1. Tìm tất cả các checkpoint trọng số chưa được đánh giá (round 10, 20, 30, 40 của từng task).
2. Load mô hình tương ứng và chạy ContinualEvaluator trên tập held-out test split.
3. Bổ sung các mốc đánh giá vào file .jsonl, _metrics.csv và .log theo đúng chuẩn của project.
4. Tự động gọi generate_post_training_plots để vẽ lại Learning Curves chi tiết theo round/epoch!
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import csv
import glob
import json
from datetime import datetime
from typing import Dict, List, Any

import torch
import numpy as np
import pandas as pd

from config.config import ModelConfig
from data.dataset import load_heldout_test_set
from models.fcil_model import FCILNet
from training.evaluator import ContinualEvaluator
from utils.metrics import primary_classification_metrics, format_classification_metrics
from utils.device import resolve_device
from main import generate_post_training_plots


def evaluate_fl_experiment(exp_dir: str, device_str: str = "cpu") -> None:
    exp_dir_path = Path(exp_dir)
    exp_name = exp_dir_path.name
    print(f"\n{'='*70}\nProcessing FL Experiment: {exp_name}\n{'='*70}")

    config_path = exp_dir_path / "experiment_config.json"
    if not config_path.is_file():
        print(f"[Warning] experiment_config.json not found in {exp_dir}, skipping.")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        cfg_dict = json.load(f)

    model_cfg = ModelConfig(**cfg_dict["model"])
    prepared_data_dir = cfg_dict["scenario"]["prepared_data_dir"]
    feature_type = cfg_dict["scenario"]["feature_type"]

    # Load test set
    test_X, test_y = load_heldout_test_set(prepared_data_dir, feature_type)
    model_cfg.input_dim = int(test_X.shape[1])
    evaluator = ContinualEvaluator(test_X, test_y)

    device = resolve_device(device_str)

    # Load existing jsonl records
    jsonl_path = exp_dir_path / f"{exp_name}.jsonl"
    existing_records = []
    evaluated_steps = set()

    if jsonl_path.is_file():
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        existing_records.append(rec)
                        if "step" in rec and rec["step"] is not None:
                            evaluated_steps.add(rec["step"])
                    except Exception:
                        pass

    new_records = []
    log_messages = []

    # Check each task
    for task_id in range(5):
        task_dir = exp_dir_path / "checkpoints" / f"task_{task_id + 1:02d}"
        if not task_dir.is_dir():
            continue

        # Look for checkpoints 10, 20, 30, 40, 50
        for local_round in [10, 20, 30, 40, 50]:
            global_step = task_id * 50 + local_round
            ckpt_name = f"round_{local_round:04d}_weights.pt"
            ckpt_path = task_dir / ckpt_name

            if not ckpt_path.is_file():
                continue

            if global_step in evaluated_steps:
                print(f"  Task {task_id + 1} | Round {local_round} (Global {global_step}): already evaluated.")
                continue

            print(f"  Evaluating Task {task_id + 1} | Round {local_round} (Global {global_step}) from {ckpt_name}...")
            state = torch.load(ckpt_path, map_location=device)

            model = FCILNet(model_cfg).to(device)
            current_classes = state.get("current_classes", (task_id + 1) * 3)
            if current_classes > model.current_classes:
                model.expand_classes(current_classes - model.current_classes)

            model.load_state_dict(state["model_state_dict"])
            model.eval()

            eval_res = evaluator.evaluate_all_seen_tasks(model, task_id)
            primary_metrics = primary_classification_metrics(eval_res)

            context = (
                f"FL Task {task_id + 1} | Global Round {global_step} "
                f"(task round {local_round}/50) | Interim Test"
            )
            record = {
                "event": "test_evaluation",
                "context": context,
                "metrics": primary_metrics,
                "step": global_step,
                "task_id": task_id,
                "round_id": global_step,
                "is_task_final": False,
                "timestamp": datetime.now().isoformat(),
                "experiment": exp_name,
            }
            new_records.append(record)
            evaluated_steps.add(global_step)

            log_msg = f"{context} | {format_classification_metrics(primary_metrics)}"
            log_messages.append(log_msg)
            print(f"    --> {log_msg}")

    if not new_records:
        print(f"All checkpoints already evaluated for {exp_name}.")
    else:
        print(f"Appending {len(new_records)} newly evaluated checkpoints to logs...")
        all_records = existing_records + new_records
        all_records.sort(key=lambda r: (r.get("step") or 0))

        # Rewrite jsonl in sorted order
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for rec in all_records:
                f.write(json.dumps(rec) + "\n")

        # Rewrite _metrics.csv
        metrics_csv_path = exp_dir_path / f"{exp_name}_metrics.csv"
        csv_rows = []
        metric_keys = [
            "accuracy", "precision_macro", "recall_macro", "f1_macro",
            "precision_micro", "recall_micro", "f1_micro",
            "precision_weighted", "recall_weighted", "f1_weighted"
        ]
        fieldnames = ["timestamp", "step", "task_id", "round_id"] + metric_keys

        for rec in all_records:
            if rec.get("event") == "test_evaluation" and "metrics" in rec:
                row = {
                    "timestamp": rec.get("timestamp", datetime.now().isoformat()),
                    "step": rec.get("step"),
                    "task_id": rec.get("task_id"),
                    "round_id": rec.get("round_id"),
                }
                for mk in metric_keys:
                    row[mk] = rec["metrics"].get(mk, "")
                csv_rows.append(row)

        with open(metrics_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in csv_rows:
                writer.writerow(r)

        # Append to log file
        log_path = exp_dir_path / f"{exp_name}.log"
        if log_path.is_file():
            with open(log_path, "a", encoding="utf-8") as f:
                for msg in log_messages:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]} - {exp_name} - INFO - {msg}\n")

    # Generate post training plots
    print(f"Regenerating learning curve plots for {exp_name}...")
    generate_post_training_plots(str(exp_dir_path), exp_name, mode="federated")
    print(f"Completed {exp_name} successfully!")


def main():
    root_dir = PROJECT_ROOT / "EXPERIMENT"
    client_dirs = [root_dir / "20clients", root_dir / "50clients"]

    # 1. Evaluate all FL experiments
    for c_dir in client_dirs:
        if not c_dir.is_dir():
            continue
        fl_experiments = sorted([d for d in c_dir.iterdir() if d.is_dir() and d.name.startswith("FL_")])
        for fl_exp in fl_experiments:
            try:
                evaluate_fl_experiment(str(fl_exp))
            except Exception as e:
                print(f"[Error] Failed to process {fl_exp.name}: {e}")

    # 2. Also regenerate plots for Centralized experiments to ensure plots exist
    for c_dir in client_dirs:
        if not c_dir.is_dir():
            continue
        cent_experiments = sorted([d for d in c_dir.iterdir() if d.is_dir() and d.name.startswith("Centralized_")])
        for cent_exp in cent_experiments:
            print(f"\nRegenerating plots for Centralized: {cent_exp.name}...")
            try:
                generate_post_training_plots(str(cent_exp), cent_exp.name, mode="centralized")
            except Exception as e:
                print(f"[Warning] Failed to generate plots for {cent_exp.name}: {e}")

    print("\n" + "="*70)
    print("ALL SUPPLEMENTARY EVALUATIONS AND PLOTS COMPLETED CLEANLY!")
    print("="*70)


if __name__ == "__main__":
    main()
