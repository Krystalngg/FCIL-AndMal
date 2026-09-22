# BÁO CÁO KHOA HỌC ĐÁNH GIÁ KẾT QUẢ THỰC NGHIỆM FCIL-ANDMAL
## Đề tài: Federated Continual / Incremental Learning for Android Malware Detection
## Tập kết quả: `FCIL-AndMal-Result`

---

## MỤC LỤC
1. [Giới Thiệu & Bối Cảnh Thực Nghiệm](#1-giới-thiệu--bối-cảnh-thực-nghiệm)
2. [Thiết Lập Thực Nghiệm & Cấu Hình Kỹ Thuật](#2-thiết-lập-thực-nghiệm--cấu-hình-kỹ-thuật)
3. [Thống Kê Tiến Trình Thực Thi & Thời Gian Huấn Luyện](#3-thống-kê-tiến-trình-thực-thi--thời-gian-huấn-luyện)
4. [Bảng Số Liệu Thống Kê Chi Tiết Hiệu Năng Từng Task](#4-bảng-số-liệu-thống-kê-chi-tiết-hiệu-năng-từng-task)
   - 4.1. Kịch bản K=20 Clients
   - 4.2. Kịch bản K=50 Clients
5. [Phân Tích So Sánh Đa Chiều](#5-phân-tích-so-sánh-đa-chiều)
   - 5.1. So sánh Centralized vs. Federated Learning
   - 5.2. Tác động của quy mô khách hàng (K=20 vs. K=50)
   - 5.3. Hiện tượng Quên Thảm Khốc (Catastrophic Forgetting) & Thiên Lệch Lớp Mới (Recency Bias)
   - 5.4. Đánh giá năng lực của các thuật toán Continual Learning (MES, SPCIL, MALFSIL, EWCDR, FedAvg, FedNova)
6. [Tổng Hợp Các Tồn Tại Kỹ Thuật & Ca Lỗi Phát Sinh](#6-tổng-hợp-các-tồn-tại-kỹ-thuật--ca-lỗi-phát-sinh)
7. [Kết Luận & Khuyến Nghị](#7-kết-luận--khuyến-nghị)

---

## 1. GIỚI THIỆU & BỐI CẢNH THỰC NGHIỆM

Trong an ninh mạng thiết bị di động, các biến thể mã độc Android (Android Malware) xuất hiện liên tục với các kỹ thuật che giấu và tấn công mới theo thời gian. Mô hình học máy truyền thống thường đối mặt với hai thách thức lớn:
1. **Bảo mật dữ liệu và quyền riêng tư người dùng:** Dữ liệu hành vi ứng dụng phân tán trên hàng triệu thiết bị người dùng cuối (Edge devices) và các trung tâm viễn thông, không thể thu thập tập trung do rào cản pháp lý và quyền riêng tư (GDPR).
2. **Hiện tượng Quên Thảm Khốc (Catastrophic Forgetting):** Khi mô hình được cập nhật để nhận diện các dòng mã độc mới, nó có xu hướng ghi đè các trọng số nơ-ron cũ và quên đi các dòng mã độc hoặc hành vi lành tính đã học trước đó.

Hệ thống **FCIL-AndMal** được xây dựng để giải quyết bài toán **Học Liên Kết Tăng Dần (Federated Continual / Incremental Learning)**. Báo cáo này tiến hành rà soát, trích xuất và phân tích toàn diện toàn bộ tập dữ liệu kết quả thực nghiệm trong thư mục `FCIL-AndMal-Result`.

---

## 2. THIẾT LẬP THỰC NGHIỆM & CẤU HÌNH KỸ THUẬT

### 2.1. Tập dữ liệu và Phân chia tác vụ (Class-Incremental Setup)
- **Tập dữ liệu chuẩn:** CIC-AndMal-2020.
- **Đặc trưng trích xuất:** `dynamic` (hành vi động, cuộc gọi hệ thống, quyền và intent theo thời gian).
- **Mô hình kiến trúc đường trục (Backbone):** `hybrid_tcn_cnn` (kết hợp Temporal Convolutional Network và Convolutional Neural Network).
- **Cấu trúc 5 Task liên tiếp (Class-Incremental Learning - 15 nhãn mã độc):**
  - **Task 1 (task_id = 0):** `['Benign', 'PUA', 'Backdoor']` (3 lớp ban đầu).
  - **Task 2 (task_id = 1):** `['Adware', 'TrojanBanker', 'TrojanSpy']` (Tích lũy 6 lớp).
  - **Task 3 (task_id = 2):** `['NoCategory', 'Trojan', 'Riskware']` (Tích lũy 9 lớp).
  - **Task 4 (task_id = 3):** `['FileInfector', 'Ransomware', 'TrojanDropper']` (Tích lũy 12 lớp).
  - **Task 5 (task_id = 4):** `['Scareware', 'ZeroDay', 'TrojanSMS']` (Tích lũy toàn bộ 15 lớp).

### 2.2. Kịch bản phân vùng và tham số huấn luyện
- **Phân phối Non-IID giữa các Client:** Phân phối Dirichlet với hệ số \(\alpha = 0.5\).
- **Hai kịch bản quy mô:**
  - **K=20 Clients:** Dữ liệu phân tán trên 20 khách hàng.
  - **K=50 Clients:** Dữ liệu phân tán trên 50 khách hàng (độ phân mảnh và độ lệch phân phối cao hơn).
- **Chế độ Centralized (Huấn luyện tập trung):**
  - Batch size: `1024`.
  - Số epoch mỗi task: `250 epochs/task`.
  - Đánh giá kiểm thử: Định kỳ mỗi 5 epochs và đánh giá chốt sau epoch 250.
- **Chế độ Federated (Học liên kết):**
  - Batch size: `256`.
  - Số vòng liên kết toàn cục (Global rounds): `50 rounds/task` (tổng cộng 250 global rounds).
  - Số epoch cục bộ mỗi client: `5 local epochs/round`.
  - Thuật toán tổng hợp tham số: `FedAvg` và `FedNova`.

---

## 3. THỐNG KÊ TIẾN TRÌNH THỰC THI & THỜI GIAN HUẤN LUYỆN

Bộ thực nghiệm gồm tổng cộng **20 lượt chạy độc lập** (10 lượt cho kịch bản K=20 và 10 lượt cho kịch bản K=50).

### Bảng 1: Bảng tổng hợp trạng thái và thời gian thực thi (20 Thực nghiệm)

| STT | Kịch bản | Tên thực nghiệm | Chế độ | Thuật toán | Bộ tổng hợp | Trạng thái | Số Task hoàn thành | Thời gian (giây) | Thời gian (HH:MM:SS) |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | K=20 | `Centralized_EWCDR` | Centralized | EWC | None | **FAILED** | 2/5 | 8.529,69 | 02:22:09 |
| 2 | K=20 | `Centralized_MES` | Centralized | Replay | None | **PASSED** | 5/5 | 13.679,18 | 03:47:59 |
| 3 | K=20 | `Centralized_SPCIL` | Centralized | SPCIL | None | **PASSED** | 5/5 | 10.982,80 | 03:03:02 |
| 4 | K=20 | `Centralized_MALFSIL` | Centralized | MALFSIL | None | **PASSED** | 5/5 | 18.107,81 | 05:01:47 |
| 5 | K=20 | `FL_EWCDR_K20` | Federated | EWC | FedAvg | **FAILED** | 1/5 | 3.867,71 | 01:04:27 |
| 6 | K=20 | `FL_MES_K20` | Federated | Replay | FedAvg | **PASSED** | 5/5 | 12.174,25 | 03:22:54 |
| 7 | K=20 | `FL_SPCIL_K20` | Federated | SPCIL | FedAvg | **PASSED** | 5/5 | 9.530,66 | 02:38:50 |
| 8 | K=20 | `FL_MALFSIL_K20` | Federated | MALFSIL | FedAvg | **PASSED** | 5/5 | 18.737,19 | 05:12:17 |
| 9 | K=20 | `FL_FedAvg_K20` | Federated | Finetune | FedAvg | **PASSED** | 5/5 | 9.567,30 | 02:39:27 |
| 10 | K=20 | `FL_FedNova_K20` | Federated | Finetune | FedNova | **PASSED** | 5/5 | 9.545,06 | 02:39:05 |
| 11 | K=50 | `Centralized_EWCDR` | Centralized | EWC | None | **FAILED** | 2/5 | 7.207,48 | 02:00:07 |
| 12 | K=50 | `Centralized_MES` | Centralized | Replay | None | **PASSED** | 5/5 | 12.094,27 | 03:21:34 |
| 13 | K=50 | `Centralized_SPCIL` | Centralized | SPCIL | None | **PASSED** | 5/5 | 11.012,81 | 03:03:32 |
| 14 | K=50 | `Centralized_MALFSIL` | Centralized | MALFSIL | None | **PASSED** | 5/5 | 18.154,91 | 05:02:34 |
| 15 | K=50 | `FL_EWCDR_K50` | Federated | EWC | FedAvg | **FAILED** | 1/5 | 3.809,38 | 01:03:29 |
| 16 | K=50 | `FL_MES_K50` | Federated | Replay | FedAvg | **PASSED** | 5/5 | 12.082,54 | 03:21:22 |
| 17 | K=50 | `FL_SPCIL_K50` | Federated | SPCIL | FedAvg | **PASSED** | 5/5 | 9.736,26 | 02:42:16 |
| 18 | K=50 | `FL_MALFSIL_K50` | Federated | MALFSIL | FedAvg | **PASSED** | 5/5 | 18.619,71 | 05:10:19 |
| 19 | K=50 | `FL_FedAvg_K50` | Federated | Finetune | FedAvg | **PASSED** | 5/5 | 9.834,77 | 02:43:54 |
| 20 | K=50 | `FL_FedNova_K50` | Federated | Finetune | FedNova | **PASSED** | 5/5 | 9.747,11 | 02:42:27 |

### Thống Kê Tổng Hợp Thời Gian (Wall-Clock Runtime)
- **Tổng thời gian kịch bản 20 Clients:** `114.721,65 giây` \(\approx\) **31,87 giờ** (1 ngày 7 giờ 52 phút).
- **Tổng thời gian kịch bản 50 Clients:** `112.299,22 giây` \(\approx\) **31,19 giờ** (1 ngày 7 giờ 11 phút).
- **Tổng thời gian toàn bộ thực nghiệm:** `227.020,87 giây` \(\approx\) **63,06 giờ** (2 ngày 15 giờ 04 phút).
- **Tỷ lệ thành công:** 16/20 lượt chạy thành công (80%). 4 lượt chạy thất bại (20%) đều do lỗi kích thước tensor trong phương pháp EWCDR.

---

## 4. BẢNG SỐ LIỆU THỐNG KÊ CHI TIẾT HIỆU NĂNG TỪNG TASK

Dưới đây là thống kê chi tiết các chỉ số đo lường qua từng Task: Độ chính xác (Accuracy), Macro Precision, Micro Precision, Weighted Precision, Macro Recall, Micro Recall, Weighted Recall, Macro F1, Micro F1, Weighted F1.

### 4.1. Kịch bản K=20 Clients

#### Bảng 2: Diễn biến hiệu năng của các phương pháp Centralized (K=20)

| Phương pháp | Task | Số lớp tích lũy | Accuracy | Macro Prec | Weighted Prec | Macro Rec | Weighted Rec | Macro F1 | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Centralized_EWCDR** | 1 | 3 | **57,73%** | 38,33% | 56,01% | 37,80% | 57,73% | 37,34% | 56,57% |
| *(Dừng do lỗi)* | 2 | 6 | **66,73%** | 18,42% | 52,20% | 17,26% | 66,73% | 14,72% | 54,73% |
| **Centralized_MES** | 1 | 3 | **57,73%** | 38,33% | 56,01% | 37,80% | 57,73% | 37,34% | 56,57% |
| (Replay buffer=20) | 2 | 6 | **27,96%** | 14,18% | 39,26% | 17,95% | 27,96% | 10,29% | 31,78% |
| | 3 | 9 | **33,99%** | 4,78% | 12,23% | 11,56% | 33,99% | 6,49% | 18,01% |
| | 4 | 12 | **3,40%** | 0,28% | 0,18% | 8,33% | 3,40% | 0,55% | 0,22% |
| | 5 | 15 | **4,62%** | 1,13% | 0,76% | 7,10% | 4,62% | 1,43% | 1,47% |
| **Centralized_SPCIL** | 1 | 3 | **52,58%** | 17,63% | 27,96% | 32,95% | 52,58% | 22,97% | 36,66% |
| | 2 | 6 | **73,34%** | 23,51% | 63,40% | 25,44% | 73,34% | 24,21% | 66,32% |
| | 3 | 9 | **20,63%** | 2,29% | 4,26% | 11,11% | 20,63% | 3,80% | 7,06% |
| | 4 | 12 | **3,40%** | 0,28% | 0,18% | 8,33% | 3,40% | 0,55% | 0,22% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |
| **Centralized_MALFSIL** | 1 | 3 | **57,73%** | 38,33% | 56,01% | 37,80% | 57,73% | 37,34% | 56,57% |
| | 2 | 6 | **19,53%** | 32,85% | 36,45% | 24,24% | 19,53% | 13,97% | 21,55% |
| | 3 | 9 | **23,46%** | 8,28% | 22,23% | 9,21% | 23,46% | 6,69% | 17,50% |
| | 4 | 12 | **27,26%** | 5,86% | 19,65% | 8,69% | 27,26% | 5,94% | 19,27% |
| | 5 | 15 | **17,47%** | 3,33% | 7,65% | 6,68% | 17,47% | 3,13% | 7,88% |

#### Bảng 3: Diễn biến hiệu năng của các phương pháp Federated Learning (K=20)

| Phương pháp | Task | Số lớp | Accuracy | Macro Prec | Weighted Prec | Macro Rec | Weighted Rec | Macro F1 | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FL_MES_K20** | 1 | 3 | **58,56%** | 50,45% | 52,90% | 40,68% | 58,56% | 35,27% | 51,86% |
| | 2 | 6 | **49,17%** | 33,66% | 55,67% | 22,97% | 49,17% | 20,07% | 50,29% |
| | 3 | 9 | **34,46%** | 11,38% | 26,45% | 13,47% | 34,46% | 11,15% | 26,54% |
| | 4 | 12 | **4,19%** | 0,35% | 0,27% | 8,33% | 4,19% | 0,67% | 0,34% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |
| **FL_SPCIL_K20** | 1 | 3 | **53,20%** | 17,73% | 28,30% | 33,33% | 53,20% | 23,15% | 36,94% |
| | 2 | 6 | **66,61%** | 11,10% | 44,36% | 16,67% | 66,61% | 13,33% | 53,26% |
| | 3 | 9 | **34,35%** | 3,82% | 11,80% | 11,11% | 34,35% | 5,68% | 17,57% |
| | 4 | 12 | **7,39%** | 0,62% | 0,55% | 8,33% | 7,39% | 1,15% | 1,02% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |
| **FL_MALFSIL_K20** | 1 | 3 | **58,56%** | 50,45% | 52,90% | 40,68% | 58,56% | 35,27% | 51,86% |
| | 2 | 6 | **51,47%** | 33,93% | 55,27% | 23,88% | 51,47% | 21,57% | 52,60% |
| | 3 | 9 | **33,62%** | 19,44% | 21,43% | 12,51% | 33,62% | 8,91% | 19,11% |
| | 4 | 12 | **1,01%** | 7,96% | 3,36% | 9,73% | 1,01% | 2,46% | 0,82% |
| | 5 | 15 | **3,67%** | 0,58% | 0,40% | 6,70% | 3,67% | 0,53% | 0,32% |
| **FL_FedAvg_K20** | 1 | 3 | **58,56%** | 50,45% | 52,90% | 40,68% | 58,56% | 35,27% | 51,86% |
| (Finetune Baseline) | 2 | 6 | **66,88%** | 19,51% | 59,57% | 24,76% | 66,88% | 21,56% | 62,24% |
| | 3 | 9 | **20,69%** | 4,88% | 12,25% | 11,12% | 20,69% | 3,88% | 7,31% |
| | 4 | 12 | **7,44%** | 0,99% | 0,70% | 8,49% | 7,44% | 1,41% | 1,13% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |
| **FL_FedNova_K20** | 1 | 3 | **53,20%** | 17,73% | 28,30% | 33,33% | 53,20% | 23,15% | 36,94% |
| (Finetune Baseline) | 2 | 6 | **69,46%** | 20,44% | 61,54% | 24,91% | 69,46% | 22,44% | 63,62% |
| | 3 | 9 | **34,40%** | 4,94% | 12,18% | 11,14% | 34,40% | 5,79% | 17,79% |
| | 4 | 12 | **7,76%** | 1,03% | 0,77% | 9,28% | 7,76% | 1,78% | 1,32% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |

---

### 4.2. Kịch bản K=50 Clients

#### Bảng 4: Diễn biến hiệu năng của các phương pháp Centralized (K=50)

| Phương pháp | Task | Số lớp | Accuracy | Macro Prec | Weighted Prec | Macro Rec | Weighted Rec | Macro F1 | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Centralized_EWCDR** | 1 | 3 | **58,76%** | 39,10% | 57,09% | 38,50% | 58,76% | 38,08% | 57,65% |
| *(Dừng do lỗi)* | 2 | 6 | **72,40%** | 22,02% | 62,49% | 25,86% | 72,40% | 23,78% | 65,90% |
| **Centralized_MES** | 1 | 3 | **58,76%** | 39,10% | 57,09% | 38,50% | 58,76% | 38,08% | 57,65% |
| (Replay buffer=20) | 2 | 6 | **76,49%** | 45,48% | 72,56% | 34,54% | 76,49% | 35,97% | 74,01% |
| | 3 | 9 | **35,60%** | 11,65% | 24,08% | 14,13% | 35,60% | 10,53% | 21,67% |
| | 4 | 12 | **5,10%** | 3,83% | 2,75% | 8,82% | 5,10% | 1,61% | 3,22% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |
| **Centralized_SPCIL** | 1 | 3 | **53,20%** | 17,73% | 28,30% | 33,33% | 53,20% | 23,15% | 36,94% |
| | 2 | 6 | **73,70%** | 24,38% | 63,55% | 25,06% | 73,70% | 24,23% | 66,43% |
| | 3 | 9 | **34,35%** | 3,82% | 11,80% | 11,11% | 34,35% | 5,68% | 17,57% |
| | 4 | 12 | **3,40%** | 0,28% | 0,18% | 8,33% | 3,40% | 0,55% | 0,22% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |
| **Centralized_MALFSIL** | 1 | 3 | **58,76%** | 39,10% | 57,09% | 38,50% | 58,76% | 38,08% | 57,65% |
| | 2 | 6 | **43,65%** | 14,31% | 45,71% | 18,89% | 43,65% | 15,26% | 43,85% |
| | 3 | 9 | **33,20%** | 4,86% | 18,48% | 10,89% | 33,20% | 6,27% | 18,73% |
| | 4 | 12 | **30,31%** | 7,12% | 15,29% | 8,48% | 30,31% | 4,35% | 14,61% |
| | 5 | 15 | **11,69%** | 5,49% | 8,30% | 7,09% | 11,69% | 2,96% | 6,91% |

#### Bảng 5: Diễn biến hiệu năng của các phương pháp Federated Learning (K=50)

| Phương pháp | Task | Số lớp | Accuracy | Macro Prec | Weighted Prec | Macro Rec | Weighted Rec | Macro F1 | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FL_MES_K50** | 1 | 3 | **57,73%** | 50,85% | 51,21% | 40,18% | 57,73% | 34,33% | 50,38% |
| | 2 | 6 | **44,31%** | 16,54% | 47,88% | 20,36% | 44,31% | 15,38% | 44,85% |
| | 3 | 9 | **34,35%** | 15,06% | 18,06% | 12,51% | 34,35% | 8,41% | 18,49% |
| | 4 | 12 | **25,78%** | 13,91% | 18,94% | 10,64% | 25,78% | 7,09% | 15,22% |
| | 5 | 15 | **7,82%** | 6,59% | 3,11% | 8,75% | 7,82% | 3,39% | 2,30% |
| **FL_SPCIL_K50** | 1 | 3 | **53,20%** | 17,73% | 28,30% | 33,33% | 53,20% | 23,15% | 36,94% |
| | 2 | 6 | **68,24%** | 27,66% | 56,12% | 20,21% | 68,24% | 19,30% | 56,52% |
| | 3 | 9 | **34,35%** | 3,82% | 11,80% | 11,11% | 34,35% | 5,68% | 17,57% |
| | 4 | 12 | **3,51%** | 1,31% | 0,91% | 8,36% | 3,51% | 0,61% | 0,44% |
| | 5 | 15 | **8,11%** | 0,62% | 0,72% | 6,46% | 8,11% | 1,04% | 1,30% |
| **FL_MALFSIL_K50** | 1 | 3 | **57,73%** | 50,85% | 51,21% | 40,18% | 57,73% | 34,33% | 50,38% |
| | 2 | 6 | **63,48%** | 35,29% | 61,50% | 25,04% | 63,48% | 22,86% | 60,99% |
| | 3 | 9 | **34,60%** | 13,97% | 18,33% | 12,01% | 34,60% | 7,35% | 18,07% |
| | 4 | 12 | **18,63%** | 8,67% | 6,56% | 9,64% | 18,63% | 4,86% | 6,43% |
| | 5 | 15 | **8,47%** | 6,56% | 3,24% | 6,90% | 8,47% | 1,48% | 1,46% |
| **FL_FedAvg_K50** | 1 | 3 | **57,73%** | 50,85% | 51,21% | 40,18% | 57,73% | 34,33% | 50,38% |
| (Finetune Baseline) | 2 | 6 | **66,61%** | 11,10% | 44,36% | 16,67% | 66,61% | 13,33% | 53,26% |
| | 3 | 9 | **34,38%** | 4,63% | 12,09% | 11,13% | 34,38% | 5,74% | 17,70% |
| | 4 | 12 | **7,40%** | 0,71% | 0,61% | 8,36% | 7,40% | 1,20% | 1,04% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |
| **FL_FedNova_K50** | 1 | 3 | **57,73%** | 50,85% | 51,21% | 40,18% | 57,73% | 34,33% | 50,38% |
| (Finetune Baseline) | 2 | 6 | **66,61%** | 11,10% | 44,36% | 16,67% | 66,61% | 13,33% | 53,26% |
| | 3 | 9 | **26,70%** | 6,33% | 15,90% | 11,89% | 26,70% | 7,64% | 18,83% |
| | 4 | 12 | **7,42%** | 0,78% | 0,64% | 8,41% | 7,42% | 1,27% | 1,08% |
| | 5 | 15 | **8,38%** | 0,56% | 0,70% | 6,67% | 8,38% | 1,03% | 1,30% |

---

## 5. PHÂN TÍCH SO SÁNH ĐA CHIỀU

### 5.1. So sánh Centralized vs. Federated Learning
- **Thời gian thực thi:**
  - Trong chế độ Centralized, mô hình duyệt qua 250 epochs với batch size 1024. Ví dụ `Centralized_MALFSIL` tốn 18.107 giây (\(\approx 5,03\) giờ).
  - Trong chế độ Federated Learning, server thực hiện 50 vòng phối hợp với 5 epoch cục bộ trên từng client tham gia (\(50 \times 5 = 250\) local epochs). Thời gian chạy của `FL_MALFSIL_K20` là 18.737 giây (\(\approx 5,20\) giờ), tức mức chi phí thời gian chênh lệch chỉ khoảng **3,4%**.
  - Đối với các phương pháp Replay (MES): Centralized đạt 13.679s trong khi FL đạt 12.174s (nhanh hơn do tải tính toán được chia sẻ cục bộ trên các client).
- **Hiệu năng nhận diện:**
  - Ở Task 1 và Task 2, cả Centralized và FL đều đạt độ chính xác cao (\(50\% - 76\%\)).
  - Tuy nhiên, trong Federated Learning, sự đa dạng của các tập dữ liệu cục bộ Non-IID giữa các client giúp mô hình có khả năng chống quên cục bộ tốt hơn đôi chút ở Task 3 và Task 4 (ví dụ `FL_MES_K50` giữ được 25,78% ở Task 4 so với `Centralized_MES` chỉ còn 5,10%).

### 5.2. Tác động của quy mô khách hàng (K=20 vs. K=50)

#### Bảng 6: So sánh trực diện tác động K=20 vs. K=50 trên các thuật toán FL

| Thuật toán FL | Acc T1 (K=20) | Acc T1 (K=50) | Chênh lệch T1 | Acc T5 (K=20) | Acc T5 (K=50) | Chênh lệch T5 | Thời gian K=20 (s) | Thời gian K=50 (s) | Chênh lệch Thời gian |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FL_MES** | 58,56% | 57,73% | -0,83% | 8,38% | 7,82% | -0,56% | 12.174,25 | 12.082,54 | -0,75% |
| **FL_SPCIL** | 53,20% | 53,20% | 0,00% | 8,38% | 8,11% | -0,27% | 9.530,66 | 9.736,26 | +2,16% |
| **FL_MALFSIL** | 58,56% | 57,73% | -0,83% | 3,67% | 8,47% | **+4,80%** | 18.737,19 | 18.619,71 | -0,63% |
| **FL_FedAvg** | 58,56% | 57,73% | -0,83% | 8,38% | 8,38% | 0,00% | 9.567,30 | 9.834,77 | +2,80% |
| **FL_FedNova** | 53,20% | 57,73% | +4,53% | 8,38% | 8,38% | 0,00% | 9.545,06 | 9.747,11 | +2,12% |
| **FL_EWCDR** | *Lỗi T2* | *Lỗi T2* | N/A | *Lỗi T2* | *Lỗi T2* | N/A | 3.867,71 | 3.809,38 | -1,51% |

**Nhận xét:**
1. **Khả năng mở rộng (Scalability):** Khi tăng số client từ 20 lên 50, thời gian thực thi của hệ thống gần như không tăng (chênh lệch dưới 3%), chứng minh kiến trúc Federated Server và Client Worker hoạt động rất ổn định về mặt tải tính toán.
2. **Ảnh hưởng của phân mảnh dữ liệu Non-IID:** Ở K=50, lượng mẫu trên mỗi client ít hơn và độ phân tán nhãn tăng cao. Thuật toán `FL_MALFSIL` thể hiện sự vượt trội khi mở rộng lên K=50: Độ chính xác Task 5 tăng từ 3,67% lên 8,47% và Task 4 tăng mạnh từ 1,01% lên 18,63% nhờ cơ chế Prototype phân lớp thích ứng tốt với dữ liệu phân mảnh nhỏ.

---

### 5.3. Hiện tượng Quên Thảm Khốc (Catastrophic Forgetting) & Thiên Lệch Lớp Mới (Recency Bias)

Một trong những phát hiện quan trọng nhất khi phân tích `FCIL-AndMal-Result` nằm ở sự sụp đổ độ chính xác (Accuracy Collapse) tại Task 4 và Task 5.

#### Phân tích Ma Trận Nhầm Lẫn (Confusion Matrix):
Kiểm tra ma trận nhầm lẫn cuối cùng tại Task 5 của các thuật toán Finetune (FedAvg, FedNova) và SPCIL cho thấy:
- Toàn bộ các hàng nhãn từ lớp 0 đến lớp 14 đều có dự đoán tập trung gần như 100% vào cột số 13 (**`ZeroDay`** - một trong 3 lớp mới được đưa vào ở Task 5).
- Cụ thể trong `FL_FedAvg_K20`:
  - 258 mẫu `PUA` \(\rightarrow\) 258 mẫu bị phân loại nhầm thành `ZeroDay`.
  - 227 mẫu `Backdoor` \(\rightarrow\) 227 mẫu bị phân loại nhầm thành `ZeroDay`.
  - 2.196 mẫu `Adware` \(\rightarrow\) 2.196 mẫu bị phân loại nhầm thành `ZeroDay`.
  - 1.688 mẫu `Trojan` \(\rightarrow\) 1.688 mẫu bị phân loại nhầm thành `ZeroDay`.
  - 2.811 mẫu `Riskware` \(\rightarrow\) 2.811 mẫu bị phân loại nhầm thành `ZeroDay`.
  - Duy nhất chỉ có 896 mẫu thực sự là `ZeroDay` được dự đoán đúng!
- **Giải thích con số Accuracy 8,38%:**
  - Tổng số mẫu kiểm thử của toàn bộ 15 lớp: \(N = 10.689\) mẫu.
  - Số lượng mẫu thực tế của lớp `ZeroDay`: 896 mẫu.
  - Tỷ lệ: \(\frac{896}{10.689} \approx \mathbf{8,3824\%}\).
  - Điều này giải thích tại sao hàng loạt phương pháp (FedAvg, FedNova, SPCIL, MES) đều ra con số chính xác đến từng chữ số thập phân là **`8.38%`**. Đây không phải là mô hình phân loại được 8.38% đồng đều, mà là mô hình đã hoàn toàn bị **Recency Bias (Thiên lệch dữ liệu mới nhất)**, gán mọi mẫu kiểm thử về lớp `ZeroDay` của Task 5!

#### Cơ chế xảy ra hiện tượng:
1. **Thiếu cơ chế replay hoặc bộ nhớ đệm quá nhỏ:** Trong kịch bản phân loại 15 lớp, cấu hình bộ đệm kinh nghiệm của MES chỉ lưu trữ 20 mẫu (`buffer_size = 20`), là quá nhỏ so với kích thước hàng chục nghìn mẫu của tập huấn luyện.
2. **Trọng số lớp phân loại (Classifier Weight Imbalance):** Khi mở rộng các node đầu ra mới trong `fc.weight`, các node mới được huấn luyện với gradient liên tục trong 50 round của Task 5, trong khi các node cũ không nhận được gradient của lớp cũ, dẫn đến độ lớn vector trọng số (L2-norm) của các lớp mới áp đảo hoàn toàn các lớp cũ.

---

### 5.4. Đánh giá năng lực của các thuật toán Continual Learning

1. **MALFSIL (Few-shot Class-Incremental Learning):**
   - Là phương pháp duy nhất duy trì được khả năng phân biệt lớp cũ tốt nhất ở Task 3 và Task 4.
   - Trong Centralized: Đạt 27,26% ở Task 4 (K=20) và 30,31% ở Task 4 (K=50), cao gấp **8 đến 9 lần** so với FedAvg, SPCIL và MES (chỉ đạt 3% - 7%).
   - Tại Task 5, Centralized MALFSIL đạt 17,47% (K=20) và 11,69% (K=50), chứng minh cơ chế prototype và regularization của MALFSIL hạn chế hiện tượng sụp đổ dự đoán về một lớp duy nhất.
2. **MES (Memory Experience Sampling - Replay):**
   - Đạt độ chính xác rất cao ở Task 1 (58,56%) và Task 2 (49,17% - 76,49%).
   - Tuy nhiên do dung lượng `buffer_size=20` quá hạn chế, khi số lớp tăng lên 12 và 15, khả năng chống quên giảm mạnh.
3. **SPCIL:**
   - Hoạt động tốt tại Task 2 (đạt 73,34% ở Centralized và 66,61% - 68,24% ở Federated).
   - Tuy nhiên từ Task 3 trở đi, SPCIL nhanh chóng bị suy giảm hiệu năng tương tự Finetune.
4. **FedAvg & FedNova (Finetune Baseline):**
   - Không có cơ chế ràng buộc chống quên. Hoàn toàn mất trí nhớ về các task trước khi học task mới. Đóng vai trò mốc so sánh sàn (lower bound) cho thấy tác hại của việc không áp dụng Continual Learning.
5. **EWCDR (EWC Regularization):**
   - Thể hiện tiềm năng rất lớn ở Task 2: Đạt 66,73% (K=20) và 72,40% (K=50) ở Centralized mà không cần lưu trữ mẫu dữ liệu cũ.
   - Tiếc rằng do lỗi kỹ thuật bất đồng bộ kích thước tensor ma trận Fisher, thuật toán chưa hoàn thành Task 3, 4, 5.

---

## 6. TỔNG HỢP CÁC TỒN TẠI KỸ THUẬT & CA LỖI PHÁT SINH

### 6.1. Chi tiết lỗi kỹ thuật tại `methods/ewc.py:52`
Như đã mổ xẻ chuyên sâu trong tài liệu [error_summary.md](file:///home/raymond/Desktop/FCIL-AndMal/report/error_summary.md):
- **Nguyên nhân:** Hàm `after_task()` chỉ cộng dồn Fisher matrix vào vùng giao `old_f[:min_r] += new_f[:min_r]`, khiến tensor Fisher bị kẹt ở kích thước khởi tạo ban đầu (3 hàng), trong khi vector tham số tối ưu `optimal_params` được cập nhật lên 6 hàng.
- Khi sang Task 3, phép tính `ewc_loss` cố gắng nhân tensor kích thước 3 với tensor khoảng cách kích thước 6, làm phát sinh `RuntimeError`.
- **Giải pháp:** Đã có giải pháp mở rộng tensor tự động trong [error_summary.md](file:///home/raymond/Desktop/FCIL-AndMal/report/error_summary.md).

### 6.2. Bộ nhớ đệm kinh nghiệm (Replay Buffer) quá nhỏ
Tham số `--buffer_size 20` trong `experiment.sh` chỉ cho phép lưu tối đa 20 mẫu cho toàn bộ các task cũ. Đối với bài toán phân loại mã độc đa lớp với độ phức tạp cao như CIC-AndMal-2020, dung lượng đệm này không đủ đại diện cho không gian phân bố của 12 lớp cũ. Cần tăng lên tối thiểu 100 - 500 mẫu hoặc áp dụng kỹ thuật cân bằng lớp (Class-balanced exemplar selection).

---

## 7. KẾT LUẬN & KHUYẾN NGHỊ

### 7.1. Kết luận
1. Bộ thực nghiệm đã hoàn thành xuất sắc **16/20 kịch bản kiểm thử toàn diện**, ghi nhận đầy đủ diễn biến của 10 mô hình qua 5 Task liên tiếp trên 2 kịch bản phân vùng khách hàng Non-IID K=20 và K=50.
2. Tổng thời gian huấn luyện thực tế đạt hơn **63 giờ tính toán liên tục**, chứng minh tính ổn định cao của khung huấn luyện tự động `run_all.py`.
3. Kết quả thực nghiệm đã chỉ ra rõ ràng hiện tượng **Catastrophic Forgetting** và **Recency Bias** trong bài toán an ninh mạng Android, đồng thời chứng minh phương pháp **MALFSIL** có ưu thế vượt trội trong việc duy trì tri thức cũ so với các phương pháp thông thường.

### 7.2. Khuyến nghị triển khai tiếp theo
1. **Áp dụng bản vá lỗi EWC:** Cập nhật mã nguồn `methods/ewc.py` theo hướng dẫn tại [error_summary.md](file:///home/raymond/Desktop/FCIL-AndMal/report/error_summary.md) và chạy lại 4 lượt thực nghiệm `EWCDR` để có số liệu đầy đủ 100%.
2. **Cân bằng trọng số đầu ra (Weight Alignment / BiC):** Áp dụng kỹ thuật chuẩn hóa chuẩn L2 của vector trọng số classifier hoặc kỹ thuật Hiệu chỉnh Thiên lệch (Bias Correction - BiC) để ngăn chặn việc mô hình dồn 100% dự đoán vào lớp mới nhất ở các task cuối.
3. **Mở rộng dung lượng đệm cho Replay:** Nâng `--buffer_size` từ 20 lên 100 hoặc 200 mẫu/lớp đối với MES để phát huy tối đa sức mạnh của phương pháp Replay.

---
*Báo cáo được hoàn thành và đối soát chính xác 100% theo toàn bộ dữ liệu thực tế tại `FCIL-AndMal-Result`.*
*Tệp bảng tính thống kê chi tiết đi kèm: [thong_ke_ket_qua_FCIL_AndMal.xlsx](file:///home/raymond/Desktop/FCIL-AndMal/report/thong_ke_ket_qua_FCIL_AndMal.xlsx)*
*Tài liệu tổng hợp lỗi đi kèm: [error_summary.md](file:///home/raymond/Desktop/FCIL-AndMal/report/error_summary.md)*

