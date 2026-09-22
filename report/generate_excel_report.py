import os
import json
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def format_seconds(secs):
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

TASK_NAMES = {
    1: "Task 1 (Benign, PUA, Backdoor)",
    2: "Task 2 (Adware, TrojanBanker, TrojanSpy)",
    3: "Task 3 (NoCategory, Trojan, Riskware)",
    4: "Task 4 (FileInfector, Ransomware, TrojanDropper)",
    5: "Task 5 (Scareware, ZeroDay, TrojanSMS)",
}

CUMULATIVE_CLASSES = {1: 3, 2: 6, 3: 9, 4: 12, 5: 15}

def build_excel_report():
    report_dir = "/home/raymond/Desktop/FCIL-AndMal/report"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    report_dir = os.path.join(base_dir, "report")
    os.makedirs(report_dir, exist_ok=True)
    out_path = os.path.join(report_dir, "thong_ke_ket_qua_FCIL_AndMal.xlsx")
    out_path = os.path.join(report_dir, "FCIL_AndMal.xlsx")

    run_summary_path = "/home/raymond/Desktop/FCIL-AndMal/FCIL-AndMal-Result/EXPERIMENT/run_summary.json"
    # Locate run_summary.json
    candidate_summaries = [
        os.path.join(base_dir, "EXPERIMENT", "run_summary.json"),
        os.path.join(base_dir, "FCIL-AndMal-Result", "EXPERIMENT", "run_summary.json"),
    ]
    run_summary_path = next((p for p in candidate_summaries if os.path.isfile(p)), candidate_summaries[-1])
    with open(run_summary_path) as f:
        run_summary_data = json.load(f)

    path_20c = "/home/raymond/Desktop/FCIL-AndMal/FCIL-AndMal-Result/EXPERIMENT/20clients/evaluation_results.xlsx"
    path_50c = "/home/raymond/Desktop/FCIL-AndMal/FCIL-AndMal-Result/EXPERIMENT/50clients/evaluation_results.xlsx"
    # Locate evaluation_results.xlsx
    candidate_20c = [
        os.path.join(base_dir, "EXPERIMENT", "20clients", "evaluation_results.xlsx"),
        os.path.join(base_dir, "FCIL-AndMal-Result", "EXPERIMENT", "20clients", "evaluation_results.xlsx"),
    ]
    path_20c = next((p for p in candidate_20c if os.path.isfile(p)), candidate_20c[-1])

    candidate_50c = [
        os.path.join(base_dir, "EXPERIMENT", "50clients", "evaluation_results.xlsx"),
        os.path.join(base_dir, "FCIL-AndMal-Result", "EXPERIMENT", "50clients", "evaluation_results.xlsx"),
    ]
    path_50c = next((p for p in candidate_50c if os.path.isfile(p)), candidate_50c[-1])

    xl_20c = pd.ExcelFile(path_20c)
    xl_50c = pd.ExcelFile(path_50c)

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styling definitions (Clean, monochrome/grayscale, no colors)
    font_header = Font(name="Arial", size=10, bold=True, color="000000")
    font_data = Font(name="Arial", size=10, color="000000")
    font_bold = Font(name="Arial", size=10, bold=True, color="000000")
    
    fill_header = PatternFill(fill_type="solid", start_color="EAEAEA", end_color="EAEAEA")
    fill_subtotal = PatternFill(fill_type="solid", start_color="F5F5F5", end_color="F5F5F5")
    
    thin_side = Side(style="thin", color="CCCCCC")
    double_bottom = Side(style="double", color="000000")
    thick_bottom = Side(style="medium", color="000000")
    
    border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    border_header = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thick_bottom)
    border_subtotal = Border(left=thin_side, right=thin_side, top=thin_side, bottom=double_bottom)

    align_left = Alignment(horizontal="left", vertical="center")
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    def auto_fit_columns(ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                if cell.number_format and "%" in cell.number_format and isinstance(cell.value, (int, float)):
                    val = f"{cell.value * 100:.2f}%"
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    # -------------------------------------------------------------
    # SHEET 1: Tong_Quan_Thuc_Nghiem
    # -------------------------------------------------------------
    ws1 = wb.create_sheet(title="Tong_Quan_Thuc_Nghiem")
    ws1.views.sheetView[0].showGridLines = True

    ws1.append(["BẢNG TỔNG HỢP TIẾN TRÌNH THỰC NGHIỆM VÀ THỜI GIAN CHẠY (FCIL-AndMal Benchmark)"])
    ws1.cell(row=1, column=1).font = Font(name="Arial", size=12, bold=True)
    ws1.append([]) # Blank line

    headers1 = [
        "STT", "Kịch bản", "Tên thực nghiệm (Case)", "Chế độ (Mode)", "Thuật toán (Method)",
        "Bộ tổng hợp (Aggregator)", "Số Clients (K)", "Trạng thái", "Số Task hoàn thành",
        "Thời gian chạy (Giây)", "Thời gian chạy (HH:MM:SS)", "Ghi chú thực thi"
    ]
    ws1.append(headers1)
    header_row_idx = 3

    stt = 1
    total_time_20c = 0
    total_time_50c = 0

    for scenario in ["20clients", "50clients"]:
        for run in run_summary_data[scenario]:
            status = "PASSED" if run["success"] else "FAILED"
            completed_tasks = "2/5 (Bị gián đoạn)" if not run["success"] else "5/5 (Hoàn thành)"
            aggregator = "FedNova" if "FedNova" in run["case"] else ("FedAvg" if run["mode"] == "federated" else "None")
            notes = "Dừng do lỗi tensor size mismatch ở Task 3 (ewc.py:52)" if not run["success"] else "Hoàn thành toàn bộ 5 tasks"
            
            elapsed = run["elapsed"]
            if scenario == "20clients":
                total_time_20c += elapsed
            else:
                total_time_50c += elapsed

            row_data = [
                stt,
                "K=20 Clients" if scenario == "20clients" else "K=50 Clients",
                run["case"],
                run["mode"].capitalize(),
                run["method"].upper(),
                aggregator,
                run["clients"],
                status,
                completed_tasks,
                round(elapsed, 2),
                format_seconds(elapsed),
                notes
            ]
            ws1.append(row_data)
            stt += 1

    # Formatting sheet 1
    for col_idx in range(1, len(headers1) + 1):
        c = ws1.cell(row=header_row_idx, column=col_idx)
        c.font = font_header
        c.fill = fill_header
        c.border = border_header
        c.alignment = align_center

    for r_idx in range(header_row_idx + 1, ws1.max_row + 1):
        for c_idx in range(1, len(headers1) + 1):
            cell = ws1.cell(row=r_idx, column=c_idx)
            cell.font = font_data
            cell.border = border_cell
            if c_idx in [1, 7]:
                cell.alignment = align_center
            elif c_idx in [2, 4, 6, 8, 9]:
                cell.alignment = align_center
            elif c_idx == 10:
                cell.alignment = align_right
                cell.number_format = "#,##0.00"
            elif c_idx == 11:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    # Summary row for total time
    ws1.append([])
    ws1.append(["Tổng thời gian kịch bản 20 clients:", "", "", "", "", "", "", "", "", round(total_time_20c, 2), format_seconds(total_time_20c), f"~{total_time_20c/3600:.2f} giờ (1 ngày 7 giờ 52 phút)"])
    ws1.append(["Tổng thời gian kịch bản 50 clients:", "", "", "", "", "", "", "", "", round(total_time_50c, 2), format_seconds(total_time_50c), f"~{total_time_50c/3600:.2f} giờ (1 ngày 7 giờ 11 phút)"])
    ws1.append(["TỔNG CỘNG TOÀN BỘ BENCHMARK (20 LƯỢT CHẠY):", "", "", "", "", "", "", "", "", round(total_time_20c + total_time_50c, 2), format_seconds(total_time_20c + total_time_50c), f"~{(total_time_20c + total_time_50c)/3600:.2f} giờ (2 ngày 15 giờ 04 phút)"])

    for r_idx in range(ws1.max_row - 2, ws1.max_row + 1):
        for c_idx in range(1, len(headers1) + 1):
            cell = ws1.cell(row=r_idx, column=c_idx)
            cell.font = font_bold
            if c_idx == 10:
                cell.number_format = "#,##0.00"
                cell.alignment = align_right
            elif c_idx == 11:
                cell.alignment = align_center

    auto_fit_columns(ws1)

    # -------------------------------------------------------------
    # HELPER FOR DETAIL SHEETS (K20 and K50)
    # -------------------------------------------------------------
    headers_detail = [
        "STT", "Thực nghiệm", "Chế độ", "Thuật toán", "Task ID", "Tên Task & Các họ mã độc",
        "Số lớp tích lũy", "Accuracy", "Macro Precision", "Micro Precision", "Weighted Precision",
        "Macro Recall", "Micro Recall", "Weighted Recall", "Macro F1", "Micro F1", "Weighted F1"
    ]

    def populate_detail_sheet(ws, xl_file, title_text):
        ws.views.sheetView[0].showGridLines = True
        ws.append([title_text])
        ws.cell(row=1, column=1).font = Font(name="Arial", size=12, bold=True)
        ws.append([])
        ws.append(headers_detail)
        h_row = 3

        for col_idx in range(1, len(headers_detail) + 1):
            c = ws.cell(row=h_row, column=col_idx)
            c.font = font_header
            c.fill = fill_header
            c.border = border_header
            c.alignment = align_center

        stt_counter = 1
        for sheet_name in xl_file.sheet_names:
            df = xl_file.parse(sheet_name)
            exp_label = df["text"].iloc[0] if "text" in df.columns else sheet_name
            method = df["method"].iloc[0].upper() if "method" in df.columns else "N/A"
            setting = df["setting"].iloc[0].capitalize() if "setting" in df.columns else "N/A"

            for _, r in df.iterrows():
                t_id = int(r["task_id"])
                t_name = TASK_NAMES.get(t_id, f"Task {t_id}")
                cum_cls = CUMULATIVE_CLASSES.get(t_id, t_id * 3)

                row_vals = [
                    stt_counter,
                    exp_label,
                    setting,
                    method,
                    t_id,
                    t_name,
                    cum_cls,
                    r["accuracy"],
                    r["precision_macro"],
                    r["precision_micro"],
                    r["precision_weighted"],
                    r["recall_macro"],
                    r["recall_micro"],
                    r["recall_weighted"],
                    r["f1_macro"],
                    r["f1_micro"],
                    r["f1_weighted"],
                ]
                ws.append(row_vals)
                stt_counter += 1

        for r_idx in range(h_row + 1, ws.max_row + 1):
            for c_idx in range(1, len(headers_detail) + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.font = font_data
                cell.border = border_cell
                if c_idx in [1, 3, 4, 5, 7]:
                    cell.alignment = align_center
                elif c_idx >= 8:
                    cell.alignment = align_right
                    cell.number_format = "0.00%"
                else:
                    cell.alignment = align_left

        auto_fit_columns(ws)

    # SHEET 2: K20_Chi_Tiet_Cac_Task
    ws2 = wb.create_sheet(title="K20_Chi_Tiet_Cac_Task")
    populate_detail_sheet(ws2, xl_20c, "BẢNG KẾT QUẢ THỐNG KÊ CHI TIẾT TỪNG TASK - KỊCH BẢN K=20 CLIENTS")

    # SHEET 3: K50_Chi_Tiet_Cac_Task
    ws3 = wb.create_sheet(title="K50_Chi_Tiet_Cac_Task")
    populate_detail_sheet(ws3, xl_50c, "BẢNG KẾT QUẢ THỐNG KÊ CHI TIẾT TỪNG TASK - KỊCH BẢN K=50 CLIENTS")

    # -------------------------------------------------------------
    # SHEET 4: So_Sanh_Hieu_Nang
    # -------------------------------------------------------------
    ws4 = wb.create_sheet(title="So_Sanh_Hieu_Nang")
    ws4.views.sheetView[0].showGridLines = True
    ws4.append(["BẢNG SO SÁNH HIỆU NĂNG TỔNG HỢP VÀ SUY GIẢM ĐỘ CHÍNH XÁC (ACCURACY TRAJECTORY & DROP)"])
    ws4.cell(row=1, column=1).font = Font(name="Arial", size=12, bold=True)
    ws4.append([])

    headers4 = [
        "STT", "Kịch bản", "Thực nghiệm", "Chế độ", "Thuật toán",
        "Trạng thái", "Acc Task 1", "Acc Task 2", "Acc Task 3", "Acc Task 4", "Acc Task 5",
        "Macro F1 Task 1", "Macro F1 Task 5", "Mức suy giảm Acc (T1 - T5)", "Thời gian chạy"
    ]
    ws4.append(headers4)
    h4_row = 3

    for col_idx in range(1, len(headers4) + 1):
        c = ws4.cell(row=h4_row, column=col_idx)
        c.font = font_header
        c.fill = fill_header
        c.border = border_header
        c.alignment = align_center

    def extract_trajectory_data(scenario_name, xl_file, summary_list):
        rows = []
        # Build map of elapsed times
        elapsed_map = {item["case"]: (item["success"], item["elapsed"]) for item in summary_list}

        for sheet_name in xl_file.sheet_names:
            df = xl_file.parse(sheet_name)
            exp_text = df["text"].iloc[0] if "text" in df.columns else sheet_name
            method = df["method"].iloc[0].upper()
            setting = df["setting"].iloc[0].capitalize()

            # Match run case
            matched_case = None
            for c_name in elapsed_map:
                if c_name in exp_text or (method.lower() in c_name.lower() and setting.lower() in c_name.lower()):
                    matched_case = c_name
                    break
            
            success, elapsed = elapsed_map.get(matched_case, (True, 0))
            status = "PASSED" if success else "FAILED (Task 2)"

            accs = {int(r["task_id"]): r["accuracy"] for _, r in df.iterrows()}
            f1s = {int(r["task_id"]): r["f1_macro"] for _, r in df.iterrows()}

            acc_t1 = accs.get(1, None)
            acc_t2 = accs.get(2, None)
            acc_t3 = accs.get(3, None)
            acc_t4 = accs.get(4, None)
            acc_t5 = accs.get(5, None)

            f1_t1 = f1s.get(1, None)
            f1_t5 = f1s.get(5, None)

            drop = (acc_t1 - acc_t5) if (acc_t1 is not None and acc_t5 is not None) else None

            rows.append([
                scenario_name, exp_text, setting, method, status,
                acc_t1, acc_t2, acc_t3, acc_t4, acc_t5,
                f1_t1, f1_t5, drop, format_seconds(elapsed)
            ])
        return rows

    all_traj = extract_trajectory_data("K=20 Clients", xl_20c, run_summary_data["20clients"]) + \
               extract_trajectory_data("K=50 Clients", xl_50c, run_summary_data["50clients"])

    for idx, r_data in enumerate(all_traj, start=1):
        ws4.append([idx] + r_data)

    for r_idx in range(h4_row + 1, ws4.max_row + 1):
        for c_idx in range(1, len(headers4) + 1):
            cell = ws4.cell(row=r_idx, column=c_idx)
            cell.font = font_data
            cell.border = border_cell
            if c_idx in [1, 2, 4, 5, 6, 15]:
                cell.alignment = align_center
            elif c_idx in range(7, 15):
                cell.alignment = align_right
                if cell.value is not None:
                    cell.number_format = "0.00%"
                else:
                    cell.value = "N/A (Lỗi)"
                    cell.alignment = align_center
            else:
                cell.alignment = align_left

    auto_fit_columns(ws4)

    # -------------------------------------------------------------
    # SHEET 5: So_Sanh_K20_vs_K50
    # -------------------------------------------------------------
    ws5 = wb.create_sheet(title="So_Sanh_K20_vs_K50")
    ws5.views.sheetView[0].showGridLines = True
    ws5.append(["BẢNG SO SÁNH TRỰC DIỆN TÁC ĐỘNG CỦA QUY MÔ CLIENTS (K=20 vs K=50) CHO CÁC THUẬT TOÁN FL"])
    ws5.cell(row=1, column=1).font = Font(name="Arial", size=12, bold=True)
    ws5.append([])

    headers5 = [
        "STT", "Thuật toán FL", "Phương thức (IL Method)", "Bộ tổng hợp",
        "K20 Acc Task 1", "K50 Acc Task 1", "Chênh lệch Task 1 (K50 - K20)",
        "K20 Acc Task 5", "K50 Acc Task 5", "Chênh lệch Task 5 (K50 - K20)",
        "K20 Macro F1 T5", "K50 Macro F1 T5",
        "K20 Thời gian (giây)", "K50 Thời gian (giây)", "Chênh lệch Thời gian (%)"
    ]
    ws5.append(headers5)
    h5_row = 3

    for col_idx in range(1, len(headers5) + 1):
        c = ws5.cell(row=h5_row, column=col_idx)
        c.font = font_header
        c.fill = fill_header
        c.border = border_header
        c.alignment = align_center

    # FL Algorithms mapping
    fl_algos = [
        ("FL_MES", "Replay", "FedAvg", "FL_MES_K20_FEDERATED_DY_7e8c17f", "FL_MES_K50_FEDERATED_DY_dd9169f", "FL_MES_K20", "FL_MES_K50"),
        ("FL_SPCIL", "SPCIL", "FedAvg", "FL_SPCIL_K20_FEDERATED__cbc5020", "FL_SPCIL_K50_FEDERATED__9603139", "FL_SPCIL_K20", "FL_SPCIL_K50"),
        ("FL_MALFSIL", "MALFSIL", "FedAvg", "FL_MALFSIL_K20_FEDERATE_8b7e3a1", "FL_MALFSIL_K50_FEDERATE_9841979", "FL_MALFSIL_K20", "FL_MALFSIL_K50"),
        ("FL_FedAvg", "Finetune", "FedAvg", "FL_FedAvg_K20_FEDERATED_3f79074", "FL_FedAvg_K50_FEDERATED_b4aeda0", "FL_FedAvg_K20", "FL_FedAvg_K50"),
        ("FL_FedNova", "Finetune", "FedNova", "FL_FedNova_K20_FEDERATE_368a496", "FL_FedNova_K50_FEDERATE_c616f98", "FL_FedNova_K20", "FL_FedNova_K50"),
        ("FL_EWCDR", "EWC", "FedAvg", None, None, "FL_EWCDR_K20", "FL_EWCDR_K50"),
    ]

    time_map_20 = {item["case"]: item["elapsed"] for item in run_summary_data["20clients"]}
    time_map_50 = {item["case"]: item["elapsed"] for item in run_summary_data["50clients"]}

    stt5 = 1
    for name, m_name, agg, s20, s50, c20, c50 in fl_algos:
        t20 = time_map_20.get(c20, 0)
        t50 = time_map_50.get(c50, 0)
        time_diff = (t50 - t20) / t20 if t20 > 0 else 0

        if s20 and s50 and s20 in xl_20c.sheet_names and s50 in xl_50c.sheet_names:
            df20 = xl_20c.parse(s20)
            df50 = xl_50c.parse(s50)

            acc20_t1 = df20[df20["task_id"] == 1]["accuracy"].values[0]
            acc50_t1 = df50[df50["task_id"] == 1]["accuracy"].values[0]
            diff_t1 = acc50_t1 - acc20_t1

            acc20_t5 = df20[df20["task_id"] == 5]["accuracy"].values[0]
            acc50_t5 = df50[df50["task_id"] == 5]["accuracy"].values[0]
            diff_t5 = acc50_t5 - acc20_t5

            f1_20_t5 = df20[df20["task_id"] == 5]["f1_macro"].values[0]
            f1_50_t5 = df50[df50["task_id"] == 5]["f1_macro"].values[0]

            row5 = [
                stt5, name, m_name, agg,
                acc20_t1, acc50_t1, diff_t1,
                acc20_t5, acc50_t5, diff_t5,
                f1_20_t5, f1_50_t5,
                round(t20, 2), round(t50, 2), time_diff
            ]
        else:
            row5 = [
                stt5, name, m_name, agg,
                "Lỗi (Task 2)", "Lỗi (Task 2)", "N/A",
                "Lỗi (Task 2)", "Lỗi (Task 2)", "N/A",
                "N/A", "N/A",
                round(t20, 2), round(t50, 2), time_diff
            ]
        ws5.append(row5)
        stt5 += 1

    for r_idx in range(h5_row + 1, ws5.max_row + 1):
        for c_idx in range(1, len(headers5) + 1):
            cell = ws5.cell(row=r_idx, column=c_idx)
            cell.font = font_data
            cell.border = border_cell
            if c_idx in [1, 2, 3, 4]:
                cell.alignment = align_center
            elif c_idx in [5, 6, 7, 8, 9, 10, 11, 12]:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = "0.00%"
                    cell.alignment = align_right
                else:
                    cell.alignment = align_center
            elif c_idx in [13, 14]:
                cell.number_format = "#,##0.00"
                cell.alignment = align_right
            elif c_idx == 15:
                cell.number_format = "+0.00%;-0.00%;0.00%"
                cell.alignment = align_right

    auto_fit_columns(ws5)

    # -------------------------------------------------------------
    # SHEET 6: Tong_Hop_Loi_Chay
    # -------------------------------------------------------------
    ws6 = wb.create_sheet(title="Tong_Hop_Loi_Chay")
    ws6.views.sheetView[0].showGridLines = True
    ws6.append(["BẢNG TỔNG HỢP VÀ CHI TIẾT CÁC CA LỖI THỰC THI (ERROR SUMMARY MATRIX)"])
    ws6.cell(row=1, column=1).font = Font(name="Arial", size=12, bold=True)
    ws6.append([])

    headers6 = [
        "STT", "Tên thực nghiệm", "Kịch bản", "Chế độ", "Thời điểm phát sinh lỗi",
        "Thời gian chạy trước khi dừng", "Tệp mã nguồn gây lỗi", "Dòng code", "Loại biệt lệ (Exception)",
        "Thông báo lỗi chi tiết", "Nguyên nhân kỹ thuật gốc rễ", "Giải pháp khắc phục"
    ]
    ws6.append(headers6)
    h6_row = 3

    for col_idx in range(1, len(headers6) + 1):
        c = ws6.cell(row=h6_row, column=col_idx)
        c.font = font_header
        c.fill = fill_header
        c.border = border_header
        c.alignment = align_center

    error_cases = [
        (
            1, "Centralized_EWCDR", "K=20 Clients", "Centralized",
            "Bắt đầu Task 3/5 (Epoch 1/250)", "8529.69s (02:22:09)",
            "methods/ewc.py", "Dòng 52", "RuntimeError",
            "The size of tensor a (3) must match the size of tensor b (6) at non-singleton dimension 0",
            "Trong Class-Incremental Learning, số lượng classes mở rộng từ 3 -> 6 -> 9. Hàm after_task trong ewc.py chỉ tích lũy vùng giao old_f[:min_r] += new_f[:min_r] mà không mở rộng kích thước fisher_dict. Khi sang Task 3, diff có 6 hàng nhưng f chỉ có 3 hàng.",
            "Khắc phục bằng cách tự động mở rộng tensor fisher_dict bằng torch.zeros_like hoặc tensor mới khi param/optimal_params mở rộng kích thước."
        ),
        (
            2, "FL_EWCDR_K20", "K=20 Clients", "Federated",
            "Bắt đầu Task 2 (Round 1/50, Local Client 0)", "3867.71s (01:04:27)",
            "methods/ewc.py", "Dòng 52", "RuntimeError",
            "The size of tensor a (3) must match the size of tensor b (6) at non-singleton dimension 0",
            "Tương tự như Centralized, trong federated training, sau Task 1 (3 classes), khi bước sang Task 2 (mở rộng lên 6 classes), client compute_loss gặp mismatch kích thước giữa fisher matrix đã lưu (3) và hiệu tham số diff (6).",
            "Cùng áp dụng giải pháp mở rộng Fisher information tensor tương thích đa kích thước lớp."
        ),
        (
            3, "Centralized_EWCDR", "K=50 Clients", "Centralized",
            "Bắt đầu Task 3/5 (Epoch 1/250)", "7207.48s (02:00:07)",
            "methods/ewc.py", "Dòng 52", "RuntimeError",
            "The size of tensor a (3) must match the size of tensor b (6) at non-singleton dimension 0",
            "Hoàn toàn tương đồng với kịch bản K=20. Mô hình hoàn tất trọn vẹn Task 1 và Task 2, gặp lỗi tức thì khi bắt đầu vòng huấn luyện Task 3.",
            "Cùng áp dụng giải pháp mở rộng Fisher tensor trong after_task và compute_loss."
        ),
        (
            4, "FL_EWCDR_K50", "K=50 Clients", "Federated",
            "Bắt đầu Task 2 (Round 1/50, Local Client 0)", "3809.38s (01:03:29)",
            "methods/ewc.py", "Dòng 52", "RuntimeError",
            "The size of tensor a (3) must match the size of tensor b (6) at non-singleton dimension 0",
            "Hoàn toàn tương đồng với kịch bản FL K=20. Lỗi xuất hiện ngay tại vòng liên kết đầu tiên của Task mới khi tính toán EWC loss của Client.",
            "Cùng áp dụng giải pháp mở rộng Fisher tensor trong after_task và compute_loss."
        )
    ]

    for ec in error_cases:
        ws6.append(list(ec))

    for r_idx in range(h6_row + 1, ws6.max_row + 1):
        for c_idx in range(1, len(headers6) + 1):
            cell = ws6.cell(row=r_idx, column=c_idx)
            cell.font = font_data
            cell.border = border_cell
            if c_idx in [1, 3, 4, 5, 6, 8, 9]:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    auto_fit_columns(ws6)

    # Save workbook
    wb.save(out_path)
    print(f"Excel report successfully generated at: {out_path}")

if __name__ == "__main__":
    build_excel_report()

