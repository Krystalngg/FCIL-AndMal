# BÁO CÁO PHÂN TÍCH VÀ TỔNG HỢP LỖI THỰC THI (ERROR SUMMARY)
## Dự án: FCIL-AndMal (Federated Continual / Incremental Learning for Android Malware)

---

## 1. TỔNG QUAN CÁC TRƯỜNG HỢP GẶP LỖI

Trong quá trình thực thi bộ chuẩn benchmark tự động gồm 20 lượt chạy thực nghiệm (10 lượt kịch bản 20 Clients và 10 lượt kịch bản 50 Clients) trên tập dữ liệu **CIC-AndMal-2020** với mô hình đường trục **Hybrid TCN-CNN**, có **4 lượt chạy gặp lỗi nghiêm trọng dẫn đến gián đoạn chương trình (FAILED)**.

Tất cả các ca lỗi này đều xuất hiện độc quyền ở phương pháp **EWCDR (Elastic Weight Consolidation with Distillation & Replay - triển khai tại `methods/ewc.py`)**.

### Bảng Thống Kê Các Lượt Chạy Bị Lỗi

| STT | Tên thực nghiệm | Kịch bản phân vùng | Chế độ | Thời điểm phát sinh lỗi | Thời gian chạy trước khi dừng | Tệp mã nguồn gây lỗi | Biệt lệ (Exception) |
| :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| 1 | **Centralized_EWCDR** | K=20 Clients | Centralized | Bước vào Task 3/5 (Epoch 1/250) | 8.529,69 giây (02:22:09) | `methods/ewc.py:52` | `RuntimeError` |
| 2 | **FL_EWCDR_K20** | K=20 Clients | Federated | Bắt đầu Task 2 (Round 1/50, Client 0) | 3.867,71 giây (01:04:27) | `methods/ewc.py:52` | `RuntimeError` |
| 3 | **Centralized_EWCDR** | K=50 Clients | Centralized | Bước vào Task 3/5 (Epoch 1/250) | 7.207,48 giây (02:00:07) | `methods/ewc.py:52` | `RuntimeError` |
| 4 | **FL_EWCDR_K50** | K=50 Clients | Federated | Bắt đầu Task 2 (Round 1/50, Client 0) | 3.809,38 giây (01:03:29) | `methods/ewc.py:52` | `RuntimeError` |

---

## 2. TRACEBACK VÀ THÔNG BÁO LỖI CHI TIẾT

### 2.1. Lỗi Trong Chế Độ Huấn Luyện Tập Trung (Centralized)
Trích xuất từ log `FCIL-AndMal-Result/EXPERIMENT/20clients/_logs/Centralized_EWCDR.stdout.log` (và tương tự tại `50clients`):

```text
2026-09-04 16:46:43,625 - Centralized_EWCDR_CENTRALIZED_DYNAMIC_EWC - INFO - Centralized Task 2 | Continual Avg Accuracy: 39.12% | Avg Forgetting: 57.73%
2026-09-04 16:46:43,991 - Centralized_EWCDR_CENTRALIZED_DYNAMIC_EWC - INFO - -------- Task 3/5: ['NoCategory', 'Trojan', 'Riskware'] (Classes 6) --------
Traceback (most recent call last):
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/main.py", line 501, in <module>
    main()
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/main.py", line 495, in main
    final_results = trainer.train_all_tasks(epochs_per_task=args.rounds_per_task)
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/training/trainer.py", line 189, in train_all_tasks
    loss, loss_dict = self.il_method.compute_loss(
        model=self.model,
        x=bx,
        y=by,
        criterion=self.criterion,
        task_id=task_id,
        device=self.device
    )
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/methods/ewc.py", line 52, in compute_loss
    ewc_loss += (f[:min_rows] * (diff ** 2)).sum()
RuntimeError: The size of tensor a (3) must match the size of tensor b (6) at non-singleton dimension 0
```

### 2.2. Lỗi Trong Chế Độ Học Liên Kết (Federated Learning)
Trích xuất từ log `FCIL-AndMal-Result/EXPERIMENT/20clients/_logs/FL_EWCDR_K20.stdout.log` (và tương tự tại `FL_EWCDR_K50`):

```text
============================================================
Task 2: Starting FL with 16 clients
============================================================
Traceback (most recent call last):
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/main.py", line 501, in <module>
    main()
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/main.py", line 417, in main
    task_metrics = server.run_task(
        task_id=task_id,
        n_new_classes=3,
        client_ids=task_cids,
        train_loaders=train_loaders,
        n_rounds=args.rounds_per_task,
        n_epochs=args.local_epochs,
    )
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/federated/server.py", line 269, in run_task
    metrics = self.run_round(
        client_ids,
        train_loaders,
        n_epochs=n_epochs,
        **kwargs
    )
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/federated/server.py", line 194, in run_round
    metrics = self.clients[cid].local_train(
        train_loaders[cid],
        n_epochs=n_epochs,
        **kwargs
    )
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/federated/client.py", line 86, in local_train
    metrics = self.strategy.train_task(
        train_loader,
        n_epochs=n_epochs,
        **kwargs
    )
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/federated/il_strategy_adapter.py", line 85, in train_task
    loss, _ = self.il_method.compute_loss(
        model=self.model,
        x=bx,
        y=by,
        criterion=self.criterion,
        task_id=task_id,
        device=self.device,
    )
  File "/Users/MAC/Desktop/AQ/FCIL-AndMal/methods/ewc.py", line 52, in compute_loss
    ewc_loss += (f[:min_rows] * (diff ** 2)).sum()
RuntimeError: The size of tensor a (3) must match the size of tensor b (6) at non-singleton dimension 0
```

---

## 3. NGUYÊN NHÂN KỸ THUẬT GỐC RỄ (ROOT CAUSE ANALYSIS)

Lỗi bắt nguồn từ sự bất đồng bộ giữa kích thước của **Ma trận Thông tin Fisher tích lũy (`self.fisher_dict`)** và **Tham số tối ưu đã lưu (`self.optimal_params`)** khi mạng nơ-ron mở rộng số lớp phân loại (Class-Incremental Learning) qua các Task liên tiếp.

### 3.1. Cơ chế mở rộng lớp trong Class-Incremental Learning
Mô hình `FCILNet` được huấn luyện qua 5 task, mỗi task bổ sung 3 họ mã độc mới vào đầu ra phân loại (`classifier.fc.weight` và `classifier.fc.bias`):
- **Task 0 (Task 1):** 3 lớp `['Benign', 'PUA', 'Backdoor']` \(\rightarrow\) Kích thước trọng số đầu ra: `[3, in_features]`.
- **Task 1 (Task 2):** Bổ sung 3 lớp `['Adware', 'TrojanBanker', 'TrojanSpy']` \(\rightarrow\) Kích thước trọng số đầu ra: `[6, in_features]`.
- **Task 2 (Task 3):** Bổ sung 3 lớp `['NoCategory', 'Trojan', 'Riskware']` \(\rightarrow\) Kích thước trọng số đầu ra: `[9, in_features]`.

### 3.2. Sai sót trong việc cập nhật ma trận Fisher tại `methods/ewc.py:108-120`

Xem xét đoạn mã nguồn trong hàm `after_task()` của `methods/ewc.py`:

```python
# methods/ewc.py lines 107-121:
# Accumulate with previous Fisher matrices
if not self.fisher_dict:
    self.fisher_dict = {k: v.cpu().clone() for k, v in fisher_accum.items()}
else:
    for name in fisher_accum:
        if name in self.fisher_dict:
            old_f = self.fisher_dict[name]
            new_f = fisher_accum[name].cpu()
            min_r = min(old_f.shape[0], new_f.shape[0])
            old_f[:min_r] += new_f[:min_r]
            self.fisher_dict[name] = old_f

# Save optimal parameters
self.optimal_params = {name: p.data.cpu().clone() for name, p in model.named_parameters()}
```

**Phân tích chi tiết từng bước:**
1. **Sau Task 0 (Task 1 hoàn thành):**
   - `self.fisher_dict` rỗng, nên được khởi tạo trực tiếp từ `fisher_accum`.
   - Trọng số phân loại `fc.weight` trong `fisher_dict` có kích thước **`[3, in_features]`**.
   - `self.optimal_params['fc.weight']` có kích thước **`[3, in_features]`**.
2. **Trong Task 1 (Task 2 đang chạy):**
   - Trọng số hiện tại `param` có kích thước `[6, in_features]`.
   - `p_star` có kích thước `[3, in_features]`.
   - `min_rows = min(param.shape[0], p_star.shape[0]) = min(6, 3) = 3`.
   - `diff = param[:3] - p_star[:3]` \(\rightarrow\) kích thước `[3, in_features]`.
   - `f = self.fisher_dict[name]` có kích thước `[3, in_features]`.
   - `f[:3]` có kích thước `[3, in_features]`. Phép nhân `f[:min_rows] * (diff ** 2)` thực hiện được vì cả 2 cùng có kích thước `[3, in_features]`. Do đó Task 2 chạy thành công trọn vẹn!
3. **Sau Task 1 (Task 2 kết thúc, gọi `after_task`):**
   - Mô hình lúc này có kích thước `[6, in_features]`. `fisher_accum` có kích thước `[6, in_features]`.
   - Đoạn mã cập nhật Fisher:
     ```python
     old_f = self.fisher_dict[name]   # Kích thước CŨ là [3, in_features]
     new_f = fisher_accum[name].cpu() # Kích thước MỚI là [6, in_features]
     min_r = min(old_f.shape[0], new_f.shape[0]) # min(3, 6) = 3
     old_f[:min_r] += new_f[:min_r]   # Chỉ cộng 3 hàng đầu
     self.fisher_dict[name] = old_f   # Gán lại old_f vẫn CHỈ CÓ KÍCH THƯỚC [3, in_features]!
     ```
     \(\rightarrow\) **`self.fisher_dict['fc.weight']` VẪN CHỈ CÓ 3 HÀNG, KHÔNG HỀ ĐƯỢC MỞ RỘNG LÊN 6 HÀNG!**
   - Nhưng ngay dòng 120:
     ```python
     self.optimal_params = {name: p.data.cpu().clone() for name, p in model.named_parameters()}
     ```
     \(\rightarrow\) **`self.optimal_params['fc.weight']` ĐÃ ĐƯỢC LƯU VỚI KÍCH THƯỚC ĐẦY ĐỦ LÀ `[6, in_features]`!**
4. **Khi bước vào Task 2 (Task 3 bắt đầu):**
   - Mô hình mở rộng lên 9 lớp: `param.shape[0] = 9`.
   - `p_star` lấy từ `optimal_params`: `p_star.shape[0] = 6`.
   - Tại dòng 49 của `methods/ewc.py`:
     ```python
     min_rows = min(param.shape[0], p_star.shape[0])  # min(9, 6) = 6!
     diff = param[:min_rows] - p_star[:min_rows]       # Kích thước: [6, in_features]
     ```
   - Tại dòng 52:
     ```python
     ewc_loss += (f[:min_rows] * (diff ** 2)).sum()
     ```
     - `f` lấy từ `self.fisher_dict['fc.weight']`, vốn **chỉ có 3 hàng**!
     - Biểu thức `f[:6]` trên một tensor chỉ có 3 hàng sẽ trả về tensor **có 3 hàng** (kích thước `[3, in_features]`).
     - `diff ** 2` có kích thước **`[6, in_features]`**.
     - PyTorch cố gắng nhân phần tử (element-wise multiplication) giữa tensor kích thước 3 và tensor kích thước 6:
     \(\rightarrow\) **BÙNG NỔ LỖI: `RuntimeError: The size of tensor a (3) must match the size of tensor b (6) at non-singleton dimension 0`**.

---

## 4. GIẢI PHÁP SỬA LỖI TRIỆT ĐỂ (CODE FIX)

Để khắc phục hoàn toàn lỗi này trên tất cả các tác vụ Class-Incremental Learning, cần sửa đồng thời 2 vị trí trong `methods/ewc.py`:

### Vị trí 1: Mở rộng kích thước của `fisher_dict` trong `after_task()`
Khi tham số mô hình tăng số chiều đầu ra (`new_f.shape[0] > old_f.shape[0]`), tensor Fisher cũ phải được mở rộng kích thước (concatenate hoặc tạo tensor mới) để chứa các giá trị Fisher của các lớp mới, thay vì giữ nguyên kích thước cũ.

### Vị trí 2: Phòng vệ đa chiều trong `compute_loss()`
Biến `min_rows` phải lấy giá trị nhỏ nhất của cả 3 yếu tố: `param.shape[0]`, `p_star.shape[0]`, và `f.shape[0]`.

### Mã Nguồn Sửa Đổi Cụ Thể (`methods/ewc.py`)

```python
# --------------------------------------------------------------------------
# SỬA ĐỔI 1: methods/ewc.py (Hàm compute_loss, dòng 48-56)
# --------------------------------------------------------------------------
# Thay thế:
#     min_rows = min(param.shape[0], p_star.shape[0])
#     if param.dim() > 1:
#         diff = param[:min_rows] - p_star[:min_rows]
#         ewc_loss += (f[:min_rows] * (diff ** 2)).sum()
#     else:
#         diff = param[:min_rows] - p_star[:min_rows]
#         ewc_loss += (f[:min_rows] * (diff ** 2)).sum()

# BẰNG ĐOẠN MÃ AN TOÀN:
                    # Lấy min_rows của cả param, p_star và fisher f
                    min_rows = min(param.shape[0], p_star.shape[0], f.shape[0])
                    diff = param[:min_rows] - p_star[:min_rows]
                    ewc_loss += (f[:min_rows] * (diff ** 2)).sum()

# --------------------------------------------------------------------------
# SỬA ĐỔI 2: methods/ewc.py (Hàm after_task, dòng 110-118)
# --------------------------------------------------------------------------
# Thay thế đoạn cập nhật fisher:
#         else:
#             for name in fisher_accum:
#                 if name in self.fisher_dict:
#                     old_f = self.fisher_dict[name]
#                     new_f = fisher_accum[name].cpu()
#                     min_r = min(old_f.shape[0], new_f.shape[0])
#                     old_f[:min_r] += new_f[:min_r]
#                     self.fisher_dict[name] = old_f

# BẰNG ĐOẠN MÃ MỞ RỘNG TENSOR ĐẦY ĐỦ:
        else:
            for name in fisher_accum:
                if name in self.fisher_dict:
                    old_f = self.fisher_dict[name]
                    new_f = fisher_accum[name].cpu()
                    if new_f.shape[0] > old_f.shape[0]:
                        # Mở rộng tensor cũ cho khớp kích thước mới
                        expanded_old = torch.zeros_like(new_f)
                        expanded_old[:old_f.shape[0]] = old_f
                        expanded_old += new_f
                        self.fisher_dict[name] = expanded_old
                    else:
                        min_r = min(old_f.shape[0], new_f.shape[0])
                        old_f[:min_r] += new_f[:min_r]
                        self.fisher_dict[name] = old_f
                else:
                    self.fisher_dict[name] = fisher_accum[name].cpu().clone()
```

---

## 5. TÁC ĐỘNG VÀ KHUYẾN NGHỊ

1. **Hiệu năng đã đo được của EWCDR trước khi lỗi:**
   - Trong `Centralized_EWCDR`: Task 1 đạt Accuracy **57.73%** (K=20) và **58.76%** (K=50). Task 2 đạt Accuracy **66.73%** (K=20) và **72.40%** (K=50).
   - Đây là mức Accuracy Task 2 rất khả quan (cao hơn hẳn Centralized MES đạt 27.96% ở K=20). Việc chương trình dừng ở Task 3 khiến chúng ta chưa ghi nhận được kết quả Task 4 và Task 5 của EWCDR.
2. **Khuyến nghị thực hiện sau khi áp dụng bản vá:**
   - Tiến hành chạy lại 4 thực nghiệm bị lỗi: `Centralized_EWCDR` (K20, K50) và `FL_EWCDR` (K20, K50) với mã nguồn đã vá để hoàn thiện 100% bảng kết quả chuẩn benchmark.

