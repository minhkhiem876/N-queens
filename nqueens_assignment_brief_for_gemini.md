# BRIEF CHO GEMINI — Bài tập lớn số 1: SAT Encoding cho N-Queens

> Tài liệu này là bản giao việc (task brief). Hãy đọc toàn bộ trước khi làm. Làm theo thứ tự các giai đoạn, **dừng lại báo cáo và chờ xác nhận ở mỗi checkpoint** (đánh dấu `[CHECKPOINT]`).
> Ngôn ngữ giao tiếp với người dùng: **tiếng Việt**. Ngôn ngữ của code, comment, README và báo cáo khoa học: **tiếng Anh**.

---

## 0. Vai trò và bối cảnh

Bạn là trợ lý kỹ thuật giúp một sinh viên (làm **cá nhân**) hoàn thành **Bài tập lớn số 1** môn *Các vấn đề hiện đại của Khoa học máy tính* (HK I, năm học 2026–2027, VNU University of Engineering and Technology).

- Chủ đề đã chọn: **N-Queens solver bằng SAT encoding** (không làm Sudoku).
- Sản phẩm cần có: (1) **mã nguồn** trong một GitHub repository, (2) **kết quả thực nghiệm** (CSV, bảng, hình), (3) **báo cáo** dạng bài báo khoa học theo mẫu Elsevier.

Thông tin chưa biết, **hãy hỏi người dùng ở đầu phiên** (tối đa một lượt hỏi gộp):
- Họ tên, mã số sinh viên, giảng viên hướng dẫn (điền vào báo cáo).
- Hạn nộp.
- URL GitHub repository **của chính sinh viên** (ký hiệu `<STUDENT_REPO_URL>`; dùng cho mục *Data availability*).
- Cấu hình máy chạy thực nghiệm (CPU, RAM, OS) và có license học thuật Gurobi/CPLEX hay không.
- Có dùng Overleaf hay biên dịch LaTeX cục bộ.

---

## 1. Tài liệu tham khảo

### 1.1. Repository mẫu (chỉ để tham khảo ý tưởng)

**https://github.com/Duongsuny/nQueens-SAT**

Repo gồm các file độc lập: `binomial.py`, `binary.py`, `sequential.py`, `commander.py`, `product.py`, `playground.py`. Mỗi file là một script riêng.

Những điểm đã quan sát được trong `binomial.py` và `product.py` (hai file đã đọc):

- Cách đánh số biến `x(i,j) = i*n + j + 1` và cách giải mã model thành bàn cờ là hợp lý.
- `product.py` dùng biến global (`n`, `new_variables_count`). Hàm `generate_matrix` tính `q = ceil(n / p)` bằng `n` của cả bàn cờ thay vì độ dài của đường đang mã hóa, nên các đường chéo ngắn sinh thừa biến phụ.
- Với tập hơn 10 biến, `product.py` gọi binary encoding cho các biến hàng/cột, nên đó là bản **lai** chứ không phải product thuần.
- Số bit tính bằng `math.log(x, 2)` có thể sai do sai số số thực. Nên dùng `(k-1).bit_length()`.
- Script chạy ngay khi import (n cứng, `print(clauses)` trong binomial); thời gian đo từ lúc import, lẫn cả thời gian sinh CNF và thời gian giải; không có timeout, không đo bộ nhớ, không kiểm tra nghiệm.

**Quy tắc:** KHÔNG sao chép nguyên văn. Viết lại theo kiến trúc ở mục 3. Nếu dùng ý tưởng nào, ghi nguồn trong README.

### 1.2. Các file người dùng có thể đính kèm cùng brief này

| File | Dùng để làm gì |
|---|---|
| `Assignment_1_-_requirements.pdf` | Yêu cầu chính thức của đề bài |
| `Mau_xay_dung_bao_cao_BTL_so_1_và_BTL_so_2.pdf` | **Mẫu báo cáo**: bài báo "Exact SAT Solving for the Two-Dimensional Bandwidth Minimization Problem" (Elsevier, Discrete Optimization). Bắt chước **cấu trúc, văn phong, cách trình bày bảng/hình/ablation**, không bắt chước nội dung 2DBMP |
| `An_optimized_SAT_approach_solving_N-Queens_problem.pdf` | Báo cáo N-Queens của một khóa trước (đọc để hiểu bài toán và 4 encoding; **có một số lỗi**, xem mục 2.4) |
| `sat (1).pdf` | Tài liệu SAT (có thể là slide môn học); đối chiếu thêm phần encoding nếu có |

Nếu file nào chưa được đính kèm, hãy yêu cầu người dùng đính kèm thay vì tự đoán nội dung.

---

## 2. Yêu cầu của đề bài (tóm tắt chính xác)

1. Làm **cá nhân**, chọn N-Queens.
2. Cài đặt solver giải N-Queens bằng **SAT**, dùng thư viện **PySAT** (hoặc gọi SAT solver trực tiếp không qua PySAT). SAT solver gợi ý: **CaDiCaL, Glucose, Kissat, CryptoMiniSat**.
3. **So sánh SAT với các phương pháp giải chính xác khác:** **CPLEX CP, CPLEX MIP, Gurobi, CP-SAT** (OR-Tools).
4. Khuyến khích cài các encoding **AMO/ALO**: **binary, commander, product, sequential counter**.
5. Thực nghiệm trên **instance kích thước lớn**.
6. Báo cáo viết như **bài báo khoa học**, theo mẫu Elsevier, LaTeX `\documentclass[a4paper,fleqn]{cas-sc}`.
7. Báo cáo phải có mục **Data availability** trỏ tới GitHub repository chứa mã nguồn và kết quả thực nghiệm.
8. Được khuyến khích tự thiết kế cấu trúc và cách trình bày kết quả.

### 2.4. Lỗi/điểm cần tránh rút ra từ báo cáo N-Queens cũ

- Báo cáo cũ nói "exactly one queen in each row, column, **and diagonal**". Sai: đường chéo chỉ cần **AMO** (at most one), không cần ALO.
- Cài đặt dùng n là bình phương/lập phương của 2–11 (4, 8, 9, 16, …, 1331): chọn n tùy tiện. Dùng dãy n đều hơn (mục 6).
- Cần tách thời gian sinh CNF, thời gian giải, và ghi nhận bộ nhớ.
- N-Queens với n ≥ 4 luôn có nghiệm (và có công thức dựng trực tiếp), nên cần diễn giải thận trọng: kết quả đo hiệu năng solver, không phải "cách tốt nhất để giải N-Queens".

---

## 3. Kiến trúc repository (bắt buộc theo cấu trúc này, có thể thêm file phụ)

```
nqueens-sat/
├── README.md                  # cài đặt, cách chạy, cách tái lập kết quả, link báo cáo
├── requirements.txt
├── LICENSE (tùy chọn)
├── src/nqueens/
│   ├── __init__.py
│   ├── board.py               # var(i,j), liệt kê hàng/cột/đường chéo, verify(), print_board()
│   ├── cnf_builder.py         # build_cnf(n, amo_name, symmetry=False, redundant_alo=True)
│   ├── encodings/
│   │   ├── __init__.py        # REGISTRY = {"pairwise":..., "seq":..., ...}
│   │   ├── pairwise.py        # còn gọi là binomial
│   │   ├── sequential.py      # sequential counter (Sinz)
│   │   ├── binary.py          # bitwise
│   │   ├── commander.py       # tự cài (không có trong PySAT)
│   │   ├── product.py         # tự cài (không có trong PySAT)
│   │   └── pysat_wrappers.py  # ladder, totalizer,... qua pysat.card.CardEnc
│   ├── sat_runner.py          # chạy solver PySAT + solver ngoài (Kissat, CryptoMiniSat)
│   └── baselines/
│       ├── cpsat_model.py
│       ├── gurobi_model.py
│       ├── cplex_mip_model.py
│       └── cplex_cp_model.py
├── scripts/
│   ├── run_single.py          # CLI chạy 1 cấu hình, in 1 dòng JSON
│   ├── run_benchmark.py       # chạy lưới cấu hình, mỗi lần là 1 subprocess, ghi CSV
│   ├── count_solutions.py     # kiểm tra đúng đắn bằng đếm nghiệm
│   └── make_tables_figs.py    # sinh bảng và hình từ CSV
├── tests/
│   ├── test_amo.py
│   └── test_solutions.py
├── results/
│   ├── raw/                   # CSV/JSONL thô, KHÔNG sửa tay
│   ├── tables/
│   └── figures/
└── report/
    ├── main.tex               # cas-sc
    ├── refs.bib
    └── figures/
```

### 3.1. Giao diện chung cho mọi encoding

```python
from pysat.formula import IDPool

def amo(lits: list[int], pool: IDPool) -> list[list[int]]:
    """Return CNF clauses enforcing at most one literal in `lits` is true.
    New auxiliary variables MUST be obtained from `pool` (never from globals)."""

def alo(lits: list[int]) -> list[list[int]]:
    return [list(lits)]
```

`build_cnf` dùng `IDPool(start_from=n*n + 1)` để mọi biến phụ không đụng biến `x`. Không dùng biến global đếm biến phụ.

### 3.2. Biến và ràng buộc N-Queens

- Biến quyết định: `x(i,j) = i*n + j + 1`, với `0 ≤ i,j < n`. `x(i,j)` true ⇔ có quân hậu ở ô `(i,j)`.
- Mỗi **hàng**: ALO + AMO (exactly one).
- Mỗi **cột**: AMO; ALO là ràng buộc dư thừa (n quân, n cột, AMO ở hàng ⇒ ALO ở cột theo nguyên lý chuồng bồ câu). Dùng cờ `redundant_alo` để làm ablation.
- Mỗi **đường chéo chính** (`i - j = d`, `d ∈ [-(n-1), n-1]`) và **chéo phụ** (`i + j = s`, `s ∈ [0, 2n-2]`): **chỉ AMO**, và chỉ cho đường có độ dài ≥ 2.
- Phá đối xứng (tùy chọn, `symmetry=True`): thêm một clause `x(0,0) ∨ x(0,1) ∨ … ∨ x(0, ceil(n/2)-1)` (quân ở hàng đầu nằm nửa trái, hợp lệ nhờ phép đối xứng gương ngang). Khi **đếm toàn bộ nghiệm**, phải tắt phá đối xứng.

### 3.3. Đặc tả từng AMO encoding (cho k biến `x1..xk`)

| Tên | Đặc tả | Clause | Biến phụ |
|---|---|---|---|
| `pairwise` | với mọi `i<j`: `(¬xi ∨ ¬xj)` | `C(k,2)` | 0 |
| `seq` (Sinz) | biến phụ `s1..s_{k-1}`. Clause: `(¬x1 ∨ s1)`; với `1<i<k`: `(¬xi ∨ si)`, `(¬s_{i-1} ∨ si)`, `(¬xi ∨ ¬s_{i-1})`; và `(¬xk ∨ ¬s_{k-1})`. Xử lý riêng k=1 (không cần clause) và k=2 | `3k−4` | `k−1` |
| `binary` (bitwise) | `m = ceil(log2 k)` bit `y1..ym`. Gán mỗi `xi` một mã nhị phân khác nhau; với mỗi bit j: `(¬xi ∨ yj)` nếu bit j của mã i bằng 1, ngược lại `(¬xi ∨ ¬yj)` | `k·m` | `m` |
| `commander` | chia thành nhóm cỡ ~3 (có thể cấu hình). Mỗi nhóm G có biến commander `c_G`. Trong nhóm: pairwise AMO. Với mỗi `x ∈ G`: `(¬x ∨ c_G)`. Sau đó AMO **đệ quy** trên tập commander (khi còn ≤ 3–4 phần tử thì dùng pairwise). Biến thể "hai chiều" (thêm `c_G → OR(G)` và `¬c_G → ¬x`) để làm ablation tùy chọn | O(k) | O(k) |
| `product` | `p = ceil(sqrt k)`, `q = ceil(k/p)`. Xếp k biến lên lưới `p×q`; biến phụ `u1..up` (hàng) và `v1..vq` (cột). Với `x` ở ô `(a,b)`: `(¬x ∨ ua)`, `(¬x ∨ vb)`. Sau đó AMO **đệ quy** trên `u` và trên `v` (đủ nhỏ thì pairwise). Phải là product thuần, không lai binary; nếu có biến thể lai thì đặt tên khác | ≈ `2k + 4√k` | ≈ `2√k` |
| `ladder`, `totalizer`,… | gọi `pysat.card.CardEnc.atmost(lits, bound=1, top_id=pool.top, encoding=EncType.<...>)`; sau khi gọi phải cập nhật lại `pool` theo `cnf.nv` để không trùng id | tùy loại | tùy loại |

Lưu ý về PySAT (hãy **xác minh** trong phiên bản đang cài bằng `from pysat.card import EncType; print(list(EncType))`): theo hiểu biết hiện tại, PySAT cung cấp `pairwise`, `seqcounter`, `bitwise`, `ladder`, `totalizer` và vài loại khác, nhưng **không có commander và product** — hai loại này phải tự cài.

Với toàn bộ bài toán: có khoảng `6n` "đường" (n hàng + n cột + ~2(2n−3) đường chéo), tổng độ dài ~`4n²`. Với encoding tuyến tính, tổng clause là Θ(n²); với pairwise là Θ(n³). Đưa phân tích này vào báo cáo và đối chiếu với số đo thực tế.

---

## 4. Các giai đoạn thực hiện

### Giai đoạn 0 — Chuẩn bị
- Hỏi người dùng các thông tin ở mục 0.
- Tạo môi trường Python (venv), `requirements.txt`: `python-sat`, `ortools`, `gurobipy`, `docplex`, `pycryptosat` (tùy chọn), `numpy`, `pandas`, `matplotlib`, `psutil`, `pytest`.
- Kissat: cần binary riêng; giao tiếp qua file DIMACS. Hướng dẫn người dùng cách cài, **không** giả định đã có.
- Gurobi và CPLEX: bản miễn phí/community theo hiểu biết hiện tại giới hạn khoảng 1000–2000 biến (chỉ chạy được n nhỏ). Yêu cầu người dùng xác nhận license học thuật; nếu không có, ghi rõ giới hạn trong báo cáo thay vì bỏ qua âm thầm. **Đừng khẳng định con số giới hạn như sự thật chắc chắn; hãy bảo người dùng kiểm tra.**

`[CHECKPOINT 0]` Xác nhận môi trường và license trước khi sang giai đoạn 1.

### Giai đoạn 1 — Nền tảng và tính đúng đắn
1. `board.py`: `var(i,j,n)`, `lines(n)` (liệt kê hàng, cột, đường chéo độ dài ≥ 2), `decode(model,n)`, `verify(board)` kiểm tra **độc lập** (đúng n quân, không trùng hàng/cột/chéo), `print_board`.
2. Cài `pairwise` và `seq`, `cnf_builder.build_cnf`.
3. `tests/test_amo.py`: với mỗi encoding và mỗi `k ∈ [1..10]`, kiểm tra bằng brute force: với mọi gán 2^k cho biến gốc, CNF (sau khi chiếu bỏ biến phụ, tức tồn tại gán biến phụ thỏa) thỏa được **khi và chỉ khi** số biến true ≤ 1.
4. `scripts/count_solutions.py`: đếm toàn bộ nghiệm bằng cách thêm **blocking clause chỉ trên biến x** (không dùng biến phụ), tắt phá đối xứng. So sánh với dãy A000170: `n=4:2, 5:10, 6:4, 7:40, 8:92, 9:352, 10:724`. Kiểm tra `n=2,3` là UNSAT.

`[CHECKPOINT 1]` Toàn bộ test phải qua trước khi tiếp tục.

### Giai đoạn 2 — Các encoding còn lại
- Cài `binary`, `commander`, `product`, và wrapper `ladder`, `totalizer`.
- Mỗi encoding phải qua `test_amo.py` và `count_solutions.py`.
- Ghi lại số biến/clause thực đo và đối chiếu với công thức mục 3.3 (in bảng nhỏ cho một vài n).

`[CHECKPOINT 2]`

### Giai đoạn 3 — Baseline ILP/CP
Tất cả baseline là bài toán **khả thi** (không hàm mục tiêu), cùng timeout, cùng số thread, thời gian tính cả lúc dựng mô hình.

- **CP-SAT (OR-Tools):**
  - Mô hình hoán vị: `q[i] ∈ [0,n)`, `AddAllDifferent(q)`, `AddAllDifferent([q[i]+i])`, `AddAllDifferent([q[i]-i])`.
  - Mô hình nhị phân: `x[i][j]` + `AddExactlyOne`/`AddAtMostOne`. (Để so sánh công bằng với SAT.)
  - `num_workers=1` cho bảng chính; thêm một dòng đa luồng riêng, ghi rõ.
- **Gurobi (MIP):** `x[i][j]` nhị phân; tổng hàng = 1; tổng cột = 1; tổng mỗi đường chéo ≤ 1; `Threads=1`, `TimeLimit`.
- **CPLEX MIP** (`docplex.mp`): cùng mô hình nhị phân.
- **CPLEX CP** (`docplex.cp`): mô hình hoán vị với `all_diff`; `Workers=1`, `TimeLimit`.

`[CHECKPOINT 3]` Kiểm tra mỗi baseline trả nghiệm đúng bằng `verify()` với n nhỏ.

### Giai đoạn 4 — Hạ tầng thực nghiệm
- `run_single.py` (CLI): tham số `--method {sat,cpsat,gurobi,cplex_mip,cplex_cp}`, `--amo`, `--solver`, `--n`, `--timeout`, `--seed`, `--symmetry`, `--no-redundant-alo`; in **một dòng JSON**.
- `run_benchmark.py`: chạy lưới cấu hình; **mỗi lần chạy là một subprocess riêng với timeout cứng** (một số solver của PySAT như CaDiCaL không ngắt giữa chừng được, nên không dựa vào `interrupt()`); ghi CSV vào `results/raw/`. Cho phép **resume** (bỏ qua cấu hình đã có trong CSV).
- Schema CSV (mỗi dòng một lần chạy):

```
run_id, timestamp, n, method, amo, solver, seed, symmetry, redundant_alo,
num_vars, num_clauses, t_encode_s, t_solve_s, t_total_s, peak_mem_mb,
status, verified, timeout_s, solver_version, machine_id
```

  `status ∈ {SAT, UNSAT, TIMEOUT, MEMOUT, ERROR}`. `verified` là kết quả `verify()` trên nghiệm trả về (bắt buộc true với mọi dòng `SAT`).
- Đo `t_encode` và `t_solve` tách bạch; đo bộ nhớ đỉnh (`psutil` hoặc `resource.getrusage` của process con).
- Ghi lại cấu hình máy và phiên bản từng solver vào một file `results/raw/environment.json`.

`[CHECKPOINT 4]` Chạy thử nhỏ (n ≤ 16) để kiểm tra pipeline trước khi chạy lưới lớn.

### Giai đoạn 5 — Chạy thực nghiệm
Xem thiết kế ở mục 6. Chạy nền, lưu CSV liên tục. **Tuyệt đối không bịa hoặc chỉnh tay số liệu.** Nếu một cấu hình không chạy được (license, bộ nhớ, thiếu solver), ghi rõ lý do và báo người dùng.

### Giai đoạn 6 — Bảng, hình, báo cáo
- `make_tables_figs.py` đọc CSV, sinh bảng (LaTeX) và hình (PDF/PNG, matplotlib).
- Viết báo cáo theo mục 7. **Mọi con số trong báo cáo phải truy được về CSV.**
- Hoàn thiện README, nhắc cách tái lập từng bảng/hình.

---

## 5. Quy tắc làm việc

1. Không sao chép code repo mẫu; viết lại theo kiến trúc mục 3.
2. Không bịa số liệu, không "ước lượng" kết quả thay cho chạy thật. Thiếu dữ liệu thì nói rõ.
3. Mọi encoding qua kiểm tra đúng đắn (test + đếm nghiệm) **trước** khi dùng vào thực nghiệm.
4. Không dùng biến global mutable cho đếm biến/clause; luôn dùng `IDPool`.
5. Mỗi checkpoint: tóm tắt đã làm gì, kết quả test, việc kế tiếp; chờ người dùng xác nhận.
6. Khi không chắc về một sự thật kỹ thuật (API PySAT, giới hạn license, tên solver trong PySAT), **hãy xác minh bằng cách chạy lệnh/đọc tài liệu** hoặc nói rõ là chưa chắc.
7. Giữ nguyên danh sách phương pháp bắt buộc: SAT (nhiều encoding, nhiều solver), CP-SAT, CPLEX CP, CPLEX MIP, Gurobi.
8. Diễn giải kết quả thận trọng: chỉ nêu những gì dữ liệu cho thấy; nêu rõ hạn chế (một máy, số seed hữu hạn, N-Queens luôn có nghiệm).
9. Nếu dùng công cụ AI hỗ trợ viết, cần có mục *Declaration of generative AI* trong báo cáo (theo mẫu).

---

## 6. Thiết kế thực nghiệm

### 6.1. Instance
- Dãy n gợi ý: `8, 16, 32, 64, 100, 128, 200, 256, 400, 512, 1000`; tiếp tục tăng cho đến khi mọi phương pháp đều TIMEOUT/MEMOUT.
- Timeout: **600 s** cho lưới chính; **3600 s** cho một số điểm khó (giống bài mẫu). Thống nhất với người dùng.
- Lặp **3–5 seed** cho mỗi cấu hình có tính ngẫu nhiên (solver SAT, CP-SAT); báo cáo median (và min/max nếu cần).

### 6.2. Nhóm thí nghiệm
1. **E1 – So sánh AMO encoding** (cố định một solver, ví dụ CaDiCaL): `pairwise, seq, binary, commander, product, ladder, totalizer`. Ghi `num_vars`, `num_clauses`, `t_encode`, `t_solve`, bộ nhớ.
2. **E2 – So sánh SAT solver** (cố định encoding tốt nhất ở E1): Glucose, CaDiCaL, Kissat, CryptoMiniSat (và có thể MapleChrono).
3. **E3 – Ablation:** có/không phá đối xứng; có/không ALO dư thừa cho cột; (tùy chọn) commander một chiều vs hai chiều.
4. **E4 – SAT vs ILP/CP:** SAT cấu hình tốt nhất vs CP-SAT (hoán vị và nhị phân), CPLEX CP, CPLEX MIP, Gurobi.
5. **E5 – (tùy chọn)** N-Queens có đặt sẵn một số quân (completion problem): bài toán khó hơn, giúp so sánh solver có ý nghĩa.

### 6.3. Bảng và hình
- Bảng tổng hợp SAT/TIMEOUT/MEMOUT cho mỗi phương pháp theo n (kiểu Table 4, 7 của bài mẫu).
- Cactus plot: số instance giải được theo thời gian (kiểu Figure 4 của bài mẫu).
- Thời gian giải theo n (thang log), cho từng encoding và từng solver.
- Số clause và số biến theo n cho từng encoding.
- Bảng chi tiết từng instance đưa vào Appendix.
- Lưu ý hiện tượng cần giải thích: pairwise sinh ~Θ(n³) clause nên có thể **hết bộ nhớ trước khi tới solver** ở n lớn → phải ghi MEMOUT, không chỉ TIMEOUT. Nếu cần, sinh DIMACS bằng generator ghi thẳng ra file thay vì giữ toàn bộ clause trong RAM.

---

## 7. Báo cáo khoa học (Elsevier `cas-sc`)

Template: `\documentclass[a4paper,fleqn]{cas-sc}` (có trên Overleaf: "Elsevier CAS Single Column"). Bám cấu trúc bài mẫu 2DBMP:

1. **Title, Authors, Affiliation, Abstract, Keywords** (Abstract nêu: bài toán, phương pháp, quy mô thực nghiệm, kết quả chính, một câu về phạm vi/hạn chế).
2. **Introduction:** bài toán N-Queens, ứng dụng, vì sao dùng SAT, đóng góp, bố cục bài.
3. **Background:**
   - 2.1 Định nghĩa bài toán và **mô hình ILP** (biến, ràng buộc hàng/cột/chéo).
   - 2.2 Related work: backtracking, local search, CP, các SAT encoding cho N-Queens, AMO encodings (Sinz, Klieber–Kwon, Chen, bitwise).
4. **SAT-based approach:**
   - 3.1 Tổng quan encoding (biến, ràng buộc).
   - 3.2 Các AMO/ALO encoding: ý tưởng, ví dụ nhỏ, số biến/clause, độ phức tạp.
   - 3.3 Phá đối xứng.
   - 3.4 Tính đúng đắn (phát biểu lemma/proposition ngắn; chứng minh gọn, có thể đưa vào Appendix).
5. **Computational experiments:**
   - 4.1 Experimental setup (máy, phiên bản solver, timeout, số lần chạy, cách đo thời gian/bộ nhớ).
   - 4.2 Ablation AMO encoding và phá đối xứng.
   - 4.3 So sánh SAT solver.
   - 4.4 So sánh với CP-SAT, CPLEX CP, CPLEX MIP, Gurobi.
6. **Conclusion:** kết quả chính, hạn chế (một máy, số seed, N-Queens luôn có nghiệm), hướng mở rộng.
7. **CRediT authorship contribution statement; Declaration of competing interest; Data availability; Declaration of generative AI (nếu dùng).**
8. **Appendix:** chứng minh đúng đắn, bảng chi tiết kết quả.
9. **References** (BibTeX).

**Data availability** phải có câu dạng:
> The source code and benchmark result files used in this paper are available at `<STUDENT_REPO_URL>`.

(Thay `<STUDENT_REPO_URL>` bằng URL repo của sinh viên. Repo mẫu `https://github.com/Duongsuny/nQueens-SAT` chỉ là tham khảo, **không** phải nơi lưu sản phẩm của sinh viên.)

Văn phong: học thuật, câu ngắn, mô tả đúng những gì dữ liệu cho thấy; tránh khẳng định tuyệt đối khi chỉ có một máy và số seed hữu hạn (xem cách bài mẫu tự giới hạn phạm vi kết luận).

---

## 8. Tiêu chí hoàn thành (Definition of Done)

- [ ] Repo đúng cấu trúc mục 3; `README.md` hướng dẫn cài và tái lập từng bảng/hình.
- [ ] Ít nhất 5 AMO encoding chạy được (pairwise, sequential, binary, commander, product), tất cả qua test và đếm nghiệm A000170.
- [ ] Ít nhất 3 SAT solver được so sánh (trong đó có CaDiCaL và Glucose; thêm Kissat/CryptoMiniSat nếu cài được).
- [ ] Đủ 4 baseline: CP-SAT, CPLEX CP, CPLEX MIP, Gurobi (hoặc ghi rõ lý do và giới hạn nếu thiếu license).
- [ ] CSV thô trong `results/raw/`, mọi bảng/hình sinh tự động từ CSV.
- [ ] Mọi nghiệm trả về đều qua `verify()`.
- [ ] Báo cáo LaTeX `cas-sc` biên dịch được, đủ các mục ở mục 7, có link GitHub của sinh viên trong *Data availability*.
- [ ] Không có số liệu nào trong báo cáo không truy được về CSV.

---

## 9. Câu mở đầu đề xuất cho phiên làm việc

Hãy bắt đầu bằng cách: (1) xác nhận bạn đã hiểu brief và liệt kê các giả định, (2) đặt một lượt câu hỏi gộp cho các thông tin ở mục 0, (3) đề xuất kế hoạch theo ngày dựa trên hạn nộp, rồi chờ người dùng xác nhận trước khi bắt đầu Giai đoạn 0.
