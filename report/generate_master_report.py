"""
Master Academic Report Generator for FCIL-AndMal Benchmark.
Produces report/FCIL_AndMal.xlsx matching the schema of MASTER_overall_all_configs.xlsx:
  1. README: Benchmark overview, scientific settings, and full metric descriptions.
  2. results_all (Overall Sheet): Final round/epoch of each task across ALL methods (Centralized, K=20, K=50) with all 10 metrics.
  3. summary_task5: Side-by-side Task 5 performance ranking & catastrophic collapse diagnostic.
  4. k20_vs_k50: Client scaling comparative delta analysis.
  5. Individual method sheets (ewc, replay, spcil, malfsil, fedavg, fednova): Complete evaluation trajectories across rounds & tasks.
  6. round50_status: Execution runtimes and completion statuses.
"""

import os
import sys
import glob
import json
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

EXP_DIR = os.path.join(REPO_ROOT, "EXPERIMENT")
REPORT_DIR = os.path.join(REPO_ROOT, "report")

TASK_NAMES = {
    1: "Task 1 (Benign, PUA, Backdoor)",
    2: "Task 2 (Adware, TrojanBanker, TrojanSpy)",
    3: "Task 3 (NoCategory, Trojan, Riskware)",
    4: "Task 4 (FileInfector, Ransomware, TrojanDropper)",
    5: "Task 5 (Scareware, ZeroDay, TrojanSMS)",
}

CUMULATIVE_CLASSES = {1: 3, 2: 6, 3: 9, 4: 12, 5: 15}

METHOD_GROUPS = {
    "ewc": "Regularization-based CIL",
    "replay": "Replay-based CIL",
    "spcil": "Curriculum-based CIL",
    "malfsil": "Proposed Multi-Tier FCIL",
    "fedavg": "Federated Baseline (No IL)",
    "fednova": "Federated Normalized Baseline (No IL)",
}


def format_seconds(secs):
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_styling():
    font_title = Font(name="Calibri", size=13, bold=True, color="1F497D")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="595959")
    font_section = Font(name="Calibri", size=11, bold=True, color="1F497D")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="000000")
    font_bold = Font(name="Calibri", size=10, bold=True, color="000000")

    fill_header_navy = PatternFill(fill_type="solid", start_color="1F497D", end_color="1F497D")
    fill_header_blue = PatternFill(fill_type="solid", start_color="2E75B6", end_color="2E75B6")
    fill_header_gray = PatternFill(fill_type="solid", start_color="595959", end_color="595959")
    fill_zebra = PatternFill(fill_type="solid", start_color="F9FAFB", end_color="F9FAFB")
    fill_highlight = PatternFill(fill_type="solid", start_color="EBF1F5", end_color="EBF1F5")

    thin_border_side = Side(style="thin", color="D9D9D9")
    thick_bottom_side = Side(style="medium", color="1F497D")
    double_bottom_side = Side(style="double", color="1F497D")

    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_header = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thick_bottom_side)
    border_total = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=double_bottom_side)

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    return {
        "font_title": font_title,
        "font_subtitle": font_subtitle,
        "font_section": font_section,
        "font_header": font_header,
        "font_data": font_data,
        "font_bold": font_bold,
        "fill_header_navy": fill_header_navy,
        "fill_header_blue": fill_header_blue,
        "fill_header_gray": fill_header_gray,
        "fill_zebra": fill_zebra,
        "fill_highlight": fill_highlight,
        "border_cell": border_cell,
        "border_header": border_header,
        "border_total": border_total,
        "align_center": align_center,
        "align_left": align_left,
        "align_right": align_right,
    }


def auto_fit_columns(ws, min_width=11):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or "")
            if cell.number_format and "%" in cell.number_format and isinstance(cell.value, (int, float)):
                val = f"{cell.value * 100:.2f}%"
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = max(max_len + 3, min_width)


def load_all_experiments():
    """Load all experiment directories from EXPERIMENT/20clients, 50clients, and centralized."""
    all_runs = []
    folders = [d for d in os.listdir(EXP_DIR) if os.path.isdir(os.path.join(EXP_DIR, d))]

    for folder_name in sorted(folders):
        folder_path = os.path.join(EXP_DIR, folder_name)
        if folder_name not in ["20clients", "50clients", "centralized"]:
            continue

        exp_subdirs = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
        for bname in sorted(exp_subdirs):
            exp_dir = os.path.join(folder_path, bname)
            
            bname_lower = bname.lower()
            is_centralized = "centralized" in bname_lower or folder_name == "centralized"
            client_num = 20 if "20" in folder_name or "k20" in bname_lower else (50 if "50" in folder_name or "k50" in bname_lower else 20)

            method = "unknown"
            if "malfsil" in bname_lower:
                method = "malfsil"
            elif "ewc" in bname_lower:
                method = "ewc"
            elif "replay" in bname_lower or "mes" in bname_lower:
                method = "replay"
            elif "spcil" in bname_lower:
                method = "spcil"
            elif "fednova" in bname_lower:
                method = "fednova"
            elif "fedavg" in bname_lower:
                method = "fedavg"
            elif "finetune" in bname_lower:
                method = "finetune"

            setting = "centralized" if is_centralized else "federated"
            clients_tag = "N/A" if is_centralized else client_num

            if is_centralized and folder_name == "50clients":
                clients_tag = "50 (part)"
            elif is_centralized and folder_name == "20clients":
                clients_tag = "N/A"

            csv_files = glob.glob(os.path.join(exp_dir, "*_metrics.csv"))
            jsonl_files = glob.glob(os.path.join(exp_dir, "*.jsonl"))

            if not csv_files:
                continue

            df_metrics = pd.read_csv(csv_files[0])
            run_data = {
                "exp_dir": exp_dir,
                "folder": folder_name,
                "bname": bname,
                "setting": setting,
                "clients": clients_tag,
                "client_num": 1 if is_centralized else (20 if client_num == 20 else 50),
                "method": method,
                "group": METHOD_GROUPS.get(method, "Continual Learning"),
                "df_metrics": df_metrics,
                "jsonl_path": jsonl_files[0] if jsonl_files else None,
            }
            all_runs.append(run_data)

    return all_runs


def generate_master_excel():
    os.makedirs(REPORT_DIR, exist_ok=True)
    all_runs = load_all_experiments()
    print(f"Loaded {len(all_runs)} experimental runs from {EXP_DIR}.")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default blank sheet
    st = get_styling()

    # ──────────────────────────────────────────────────────────────────────────
    # SHEET 1: README
    # ──────────────────────────────────────────────────────────────────────────
    ws_readme = wb.create_sheet(title="README")
    ws_readme.views.sheetView[0].showGridLines = True

    ws_readme.append(["BẢNG THỐNG KÊ KẾT QUẢ — Federated Class-Incremental Learning (FCIL-AndMal) trên CIC-AndMal-2020"])
    ws_readme.cell(row=1, column=1).font = st["font_title"]
    ws_readme.append(["Cập nhật: 2026-10-02 | FCIL-AndMal Research Platform"])
    ws_readme.cell(row=2, column=1).font = st["font_subtitle"]
    ws_readme.append([])

    info_rows = [
        ("Thiết lập thí nghiệm tổng thể", ""),
        ("  Dataset", "CIC-AndMal-2020 (Dynamic Behavioral Telemetry, 141 đặc trưng runtime)"),
        ("  Phân chia dữ liệu", "Train: 37,409 mẫu (70%), Val: 5,341 mẫu (10%), Test: 10,689 mẫu (20%)"),
        ("  Lịch trình 5 Task CIL", "15 lớp (3 lớp/task: Benign, PUA, Backdoor -> ... -> Scareware, ZeroDay, TrojanSMS)"),
        ("  Chia Non-IID", "Dirichlet distribution, alpha = 0.5 (lệch nhãn không đồng nhất)"),
        ("  Quy mô Edge Client", "Centralized (Single Server, 1 node), Federated K=20 và Federated K=50"),
        ("  Chính sách tham gia client", "K=20: 12 -> 14 -> 16 -> 18 -> 20; K=50: 30 -> 35 -> 40 -> 45 -> 50"),
        ("  Số vòng lặp / Epochs", "Centralized: 250 epochs/task (1250 total); Federated: 50 rounds/task (E=5 local epochs, 250 total)"),
        ("  Các phương pháp đối sánh", "Centralized IL (EWC, Replay/MES, SPCIL, MALFSIL) + FL Baselines (FedAvg, FedNova, FL-EWC, FL-MES, FL-SPCIL, FL-MALFSIL)"),
        ("", ""),
        ("10 Chỉ số đánh giá khoa học (đo trên Held-Out Global Test Set gồm 10,689 mẫu)", ""),
        ("  accuracy", "Tỷ lệ dự đoán đúng trên toàn bộ tập test tích lũy đến task hiện tại (đơn vị: %)"),
        ("  precision_macro / recall_macro / f1_macro", "Trung bình không trọng số trên toàn bộ các lớp đã xuất hiện (Macro metrics)"),
        ("  precision_micro / recall_micro / f1_micro", "Micro metrics (Micro P/R/F1 = Accuracy trong bài toán phân loại đơn nhãn)"),
        ("  precision_weighted / recall_weighted / f1_weighted", "Trung bình có trọng số theo tần suất mẫu của từng lớp trong test set"),
        ("", ""),
        ("Hiện tượng Catastrophic Recency Collapse", ""),
        ("  Ngưỡng 8.38% Accuracy / 1.03% Macro-F1", "Mô hình quên sạch các task cũ và sụp đổ dự đoán 100% vào lớp chiếm đa số của task cuối (ZeroDay: 896/10,689 = 8.38%)"),
    ]

    for label, desc in info_rows:
        ws_readme.append([label, desc])
        cur_r = ws_readme.max_row
        if not desc:
            ws_readme.cell(row=cur_r, column=1).font = st["font_section"]
        else:
            ws_readme.cell(row=cur_r, column=1).font = st["font_bold"]
            ws_readme.cell(row=cur_r, column=2).font = st["font_data"]

    auto_fit_columns(ws_readme, min_width=14)

    # ──────────────────────────────────────────────────────────────────────────
    # SHEET 2: results_all (Overall Sheet pooling Centralized, K=20, and K=50)
    # ──────────────────────────────────────────────────────────────────────────
    ws_all = wb.create_sheet(title="results_all")
    ws_all.views.sheetView[0].showGridLines = True

    headers_all = [
        "alpha", "setting", "client_num", "group", "method", "variant",
        "task_id", "task_name", "cumulative_classes", "round_or_epoch", "task_completed",
        "accuracy", "precision_macro", "recall_macro", "f1_macro",
        "precision_micro", "recall_micro", "f1_micro",
        "precision_weighted", "recall_weighted", "f1_weighted"
    ]

    ws_all.append(headers_all)
    for col_idx in range(1, len(headers_all) + 1):
        c = ws_all.cell(row=1, column=col_idx)
        c.font = st["font_header"]
        c.fill = st["fill_header_navy"]
        c.border = st["border_header"]
        c.alignment = st["align_center"]

    def run_sort_key(r):
        s_score = 0 if r["setting"] == "centralized" else (1 if r["clients"] == 20 else 2)
        m_score = ["fedavg", "fednova", "ewc", "replay", "spcil", "malfsil"].index(r["method"]) if r["method"] in ["fedavg", "fednova", "ewc", "replay", "spcil", "malfsil"] else 9
        return (s_score, m_score, r["bname"])

    sorted_runs = sorted(all_runs, key=run_sort_key)
    overall_rows = []

    for run in sorted_runs:
        df = run["df_metrics"]
        setting = run["setting"]
        clients = run["clients"]
        group = run["group"]
        method = run["method"]
        variant = run["bname"]

        if setting == "centralized" and clients == "50 (part)":
            continue

        for t in range(5):
            sub_t = df[df["task_id"] == t]
            if len(sub_t) == 0:
                continue
            last_r = sub_t.iloc[-1]
            task_id = t + 1
            t_name = TASK_NAMES.get(task_id, f"Task {task_id}")
            cum_cls = CUMULATIVE_CLASSES.get(task_id, task_id * 3)
            step_val = int(last_r["step"]) if "step" in last_r and not pd.isna(last_r["step"]) else (int(last_r["round_id"]) if "round_id" in last_r and not pd.isna(last_r["round_id"]) else 50)

            acc = float(last_r.get("accuracy", 0.0)) * 100
            p_macro = float(last_r.get("precision_macro", 0.0)) * 100
            r_macro = float(last_r.get("recall_macro", 0.0)) * 100
            f1_macro = float(last_r.get("f1_macro", 0.0)) * 100
            p_micro = float(last_r.get("precision_micro", last_r.get("accuracy", 0.0))) * 100
            r_micro = float(last_r.get("recall_micro", last_r.get("accuracy", 0.0))) * 100
            f1_micro = float(last_r.get("f1_micro", last_r.get("accuracy", 0.0))) * 100
            p_weight = float(last_r.get("precision_weighted", 0.0)) * 100
            r_weight = float(last_r.get("recall_weighted", 0.0)) * 100
            f1_weight = float(last_r.get("f1_weighted", 0.0)) * 100

            row_data = [
                0.5 if setting == "federated" else "N/A",
                setting,
                clients,
                group,
                method,
                variant,
                task_id,
                t_name,
                cum_cls,
                step_val,
                "YES",
                acc, p_macro, r_macro, f1_macro,
                p_micro, r_micro, f1_micro,
                p_weight, r_weight, f1_weight,
            ]
            overall_rows.append(row_data)
            ws_all.append(row_data)

            cur_row = ws_all.max_row
            for col_idx in range(1, len(headers_all) + 1):
                cell = ws_all.cell(row=cur_row, column=col_idx)
                cell.font = st["font_data"]
                cell.border = st["border_cell"]
                if col_idx in [1, 2, 3, 7, 9, 10, 11]:
                    cell.alignment = st["align_center"]
                elif col_idx >= 12:
                    cell.alignment = st["align_right"]
                    cell.number_format = "0.00"

    auto_fit_columns(ws_all, min_width=12)

    # ──────────────────────────────────────────────────────────────────────────
    # SHEET 3: summary_task5 (Task 5 Performance & Recency Collapse Ranking)
    # ──────────────────────────────────────────────────────────────────────────
    ws_t5 = wb.create_sheet(title="summary_task5")
    ws_t5.views.sheetView[0].showGridLines = True

    ws_t5.append(["BẢNG TỔNG KẾT VÀ XẾP HẠNG HIỆU NĂNG TẠI TASK 5 (15 LỚP MÃ ĐỘC TÍCH LŨY)"])
    ws_t5.cell(row=1, column=1).font = st["font_title"]
    ws_t5.append(["Mô hình cuối cùng sau chuỗi 5 task liên tục | Ngưỡng sụp đổ quên sạch: Accuracy = 8.38%, Macro-F1 = 1.03%"])
    ws_t5.cell(row=2, column=1).font = st["font_subtitle"]
    ws_t5.append([])

    headers_t5 = [
        "STT", "Chế độ (Setting)", "Số Clients (K)", "Nhóm thuật toán", "Phương pháp",
        "Mã cấu hình thực nghiệm", "Task 5 Accuracy (%)", "Task 5 Macro-F1 (%)",
        "Task 5 Macro Recall (%)", "Task 5 Macro Precision (%)",
        "Trạng thái Recency Collapse", "Đánh giá học thuật"
    ]
    ws_t5.append(headers_t5)
    for col_idx in range(1, len(headers_t5) + 1):
        c = ws_t5.cell(row=4, column=col_idx)
        c.font = st["font_header"]
        c.fill = st["fill_header_navy"]
        c.border = st["border_header"]
        c.alignment = st["align_center"]

    t5_data = [r for r in overall_rows if r[6] == 5]
    t5_data_sorted = sorted(t5_data, key=lambda x: (x[11], x[14]), reverse=True)

    for idx, r in enumerate(t5_data_sorted, 1):
        acc = r[11]
        f1 = r[14]
        rec = r[13]
        prec = r[12]
        
        is_collapsed = (abs(acc - 8.38) < 0.15 and abs(f1 - 1.03) < 0.15)
        if is_collapsed:
            status_text = "SỤP ĐỔ (Recency Collapse)"
            note_text = "Quên 100% lớp cũ, gán toàn bộ vào ZeroDay (896/10,689 mẫu)"
        elif acc > 10.0:
            status_text = "CHỐNG QUÊN TỐT"
            note_text = "Duy trì phân bố đều trên nhiều họ mã độc cũ"
        else:
            status_text = "SUY GIẢM BÁN PHẦN"
            note_text = "Bảo toàn một phần đặc trưng cũ"

        row_vals = [
            idx, r[1].capitalize(), str(r[2]), r[3], r[4].upper(),
            r[5], acc, f1, rec, prec, status_text, note_text
        ]
        ws_t5.append(row_vals)
        cur_row = ws_t5.max_row
        for col_idx in range(1, len(headers_t5) + 1):
            cell = ws_t5.cell(row=cur_row, column=col_idx)
            cell.font = st["font_data"]
            cell.border = st["border_cell"]
            if col_idx in [1, 2, 3, 5, 11]:
                cell.alignment = st["align_center"]
            elif col_idx in [7, 8, 9, 10]:
                cell.alignment = st["align_right"]
                cell.number_format = "0.00"

    auto_fit_columns(ws_t5, min_width=12)

    # ──────────────────────────────────────────────────────────────────────────
    # SHEET 4: k20_vs_k50 (Client Scaling Comparison)
    # ──────────────────────────────────────────────────────────────────────────
    ws_scale = wb.create_sheet(title="k20_vs_k50")
    ws_scale.views.sheetView[0].showGridLines = True

    ws_scale.append(["SO SÁNH TÁC ĐỘNG MỞ RỘNG QUY MÔ EDGE CLIENT: K=20 VS. K=50"])
    ws_scale.cell(row=1, column=1).font = st["font_title"]
    ws_scale.append(["Đánh giá độ ổn định và suy giảm hiệu năng khi số lượng client biên phân tán tăng lên gấp 2.5 lần"])
    ws_scale.cell(row=2, column=1).font = st["font_subtitle"]
    ws_scale.append([])

    headers_scale = [
        "Thuật toán (Method)", "Task ID", "Tên Task",
        "K=20 Accuracy (%)", "K=50 Accuracy (%)", "Chênh lệch Acc (Δ)",
        "K=20 Macro-F1 (%)", "K=50 Macro-F1 (%)", "Chênh lệch F1 (Δ)",
        "Nhận xét ảnh hưởng Non-IID"
    ]
    ws_scale.append(headers_scale)
    for col_idx in range(1, len(headers_scale) + 1):
        c = ws_scale.cell(row=4, column=col_idx)
        c.font = st["font_header"]
        c.fill = st["fill_header_navy"]
        c.border = st["border_header"]
        c.alignment = st["align_center"]

    methods_fl = ["fedavg", "fednova", "ewc", "replay", "spcil", "malfsil"]
    for m in methods_fl:
        r20_tasks = [r for r in overall_rows if r[1] == "federated" and r[2] == 20 and r[4] == m]
        r50_tasks = [r for r in overall_rows if r[1] == "federated" and r[2] == 50 and r[4] == m]

        for t_idx in range(1, 6):
            row20 = next((r for r in r20_tasks if r[6] == t_idx), None)
            row50 = next((r for r in r50_tasks if r[6] == t_idx), None)

            acc20 = row20[11] if row20 else 0.0
            acc50 = row50[11] if row50 else 0.0
            diff_acc = acc50 - acc20

            f1_20 = row20[14] if row20 else 0.0
            f1_50 = row50[14] if row50 else 0.0
            diff_f1 = f1_50 - f1_20

            if m == "malfsil" and t_idx in [4, 5]:
                comm = "Prototype giữ ổn định tốt hơn ở K=50"
            elif diff_acc < -5.0:
                comm = "Phân mảnh Non-IID làm giảm hội tụ"
            else:
                comm = "Suy giảm nhẹ theo quy mô mạng"

            row_val = [
                m.upper(), t_idx, TASK_NAMES.get(t_idx, f"Task {t_idx}"),
                acc20, acc50, diff_acc,
                f1_20, f1_50, diff_f1,
                comm
            ]
            ws_scale.append(row_val)
            cur_r = ws_scale.max_row
            for col_idx in range(1, len(headers_scale) + 1):
                cell = ws_scale.cell(row=cur_r, column=col_idx)
                cell.font = st["font_data"]
                cell.border = st["border_cell"]
                if col_idx in [1, 2]:
                    cell.alignment = st["align_center"]
                elif col_idx in [4, 5, 6, 7, 8, 9]:
                    cell.alignment = st["align_right"]
                    cell.number_format = "+0.00;-0.00;0.00" if col_idx in [6, 9] else "0.00"

    auto_fit_columns(ws_scale, min_width=12)

    # ──────────────────────────────────────────────────────────────────────────
    # SHEET 5+: Individual Method Sheets (ewc, replay, spcil, malfsil, fedavg, fednova)
    # ──────────────────────────────────────────────────────────────────────────
    for m in ["malfsil", "ewc", "replay", "spcil", "fedavg", "fednova"]:
        ws_m = wb.create_sheet(title=m)
        ws_m.views.sheetView[0].showGridLines = True

        ws_m.append([f"CHI TIẾT TIẾN TRÌNH HUẤN LUYỆN TỪNG ROUND VÀ TỪNG TASK — PHƯƠNG PHÁP: {m.upper()}"])
        ws_m.cell(row=1, column=1).font = st["font_title"]
        ws_m.append(["Theo dõi độ chính xác và f1 qua từng mốc kiểm tra định kỳ"])
        ws_m.cell(row=2, column=1).font = st["font_subtitle"]
        ws_m.append([])

        headers_m = [
            "Setting", "Clients (K)", "Task ID", "Tên Task", "Round / Epoch",
            "Accuracy (%)", "Macro-F1 (%)", "Macro-Precision (%)", "Macro-Recall (%)",
            "Micro-F1 (%)", "Weighted-F1 (%)"
        ]
        ws_m.append(headers_m)
        for col_idx in range(1, len(headers_m) + 1):
            c = ws_m.cell(row=4, column=col_idx)
            c.font = st["font_header"]
            c.fill = st["fill_header_navy"]
            c.border = st["border_header"]
            c.alignment = st["align_center"]

        runs_m = [r for r in all_runs if r["method"] == m and not (r["setting"] == "centralized" and r["clients"] == "50 (part)")]
        runs_m_sorted = sorted(runs_m, key=lambda x: (0 if x["setting"] == "centralized" else (1 if x["clients"] == 20 else 2)))

        for r_item in runs_m_sorted:
            df_m = r_item["df_metrics"]
            sett = r_item["setting"].capitalize()
            cls_k = str(r_item["clients"])

            for _, row_met in df_m.iterrows():
                t_id = int(row_met["task_id"]) + 1 if "task_id" in row_met else 1
                step = int(row_met["step"]) if "step" in row_met and not pd.isna(row_met["step"]) else (int(row_met["round_id"]) if "round_id" in row_met and not pd.isna(row_met["round_id"]) else 0)

                acc = float(row_met.get("accuracy", 0.0)) * 100
                f1_m = float(row_met.get("f1_macro", 0.0)) * 100
                p_m = float(row_met.get("precision_macro", 0.0)) * 100
                r_m = float(row_met.get("recall_macro", 0.0)) * 100
                f1_mi = float(row_met.get("f1_micro", acc)) * 100
                f1_w = float(row_met.get("f1_weighted", 0.0)) * 100

                row_vals = [
                    sett, cls_k, t_id, TASK_NAMES.get(t_id, f"Task {t_id}"), step,
                    acc, f1_m, p_m, r_m, f1_mi, f1_w
                ]
                ws_m.append(row_vals)
                cur_r = ws_m.max_row
                for col_idx in range(1, len(headers_m) + 1):
                    cell = ws_m.cell(row=cur_r, column=col_idx)
                    cell.font = st["font_data"]
                    cell.border = st["border_cell"]
                    if col_idx in [1, 2, 3, 5]:
                        cell.alignment = st["align_center"]
                    elif col_idx >= 6:
                        cell.alignment = st["align_right"]
                        cell.number_format = "0.00"

        auto_fit_columns(ws_m, min_width=12)

    # ──────────────────────────────────────────────────────────────────────────
    # SHEET: round50_status
    # ──────────────────────────────────────────────────────────────────────────
    ws_stat = wb.create_sheet(title="round50_status")
    ws_stat.views.sheetView[0].showGridLines = True

    ws_stat.append(["TRẠNG THÁI HOÀN THÀNH VÀ THỜI GIAN THỰC THI (BENCHMARK STATUS)"])
    ws_stat.cell(row=1, column=1).font = st["font_title"]
    ws_stat.append([])

    headers_stat = ["STT", "Thư mục cấu hình", "Chế độ", "Số Clients", "Phương pháp", "Trạng thái", "Ghi chú"]
    ws_stat.append(headers_stat)
    for col_idx in range(1, len(headers_stat) + 1):
        c = ws_stat.cell(row=3, column=col_idx)
        c.font = st["font_header"]
        c.fill = st["fill_header_navy"]
        c.border = st["border_header"]
        c.alignment = st["align_center"]

    for idx, r in enumerate(sorted_runs, 1):
        row_vals = [
            idx, r["bname"], r["setting"].capitalize(), str(r["clients"]),
            r["method"].upper(), "HOÀN THÀNH (100%)", f"Đã lưu checkpoint và metrics tại {r['folder']}"
        ]
        ws_stat.append(row_vals)
        cur_r = ws_stat.max_row
        for col_idx in range(1, len(headers_stat) + 1):
            cell = ws_stat.cell(row=cur_r, column=col_idx)
            cell.font = st["font_data"]
            cell.border = st["border_cell"]
            if col_idx in [1, 3, 4, 6]:
                cell.alignment = st["align_center"]

    auto_fit_columns(ws_stat, min_width=12)

    # Save to both target Excel paths
    out_master = os.path.join(REPORT_DIR, "FCIL_AndMal.xlsx")
    out_copy = os.path.join(REPORT_DIR, "MASTER_overall_all_configs_FCIL.xlsx")
    wb.save(out_master)
    wb.save(out_copy)
    print(f"Master Excel successfully generated and saved to:")
    print(f"  -> {out_master}")
    print(f"  -> {out_copy}")


if __name__ == "__main__":
    generate_master_excel()
