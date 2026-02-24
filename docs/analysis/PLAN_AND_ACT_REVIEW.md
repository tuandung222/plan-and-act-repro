# Plan-and-Act (arXiv:2503.09572v3) - Review & Technical Deep Dive

Navigation:
- Reading hub: [`READING_GUIDE.md`](../READING_GUIDE.md)
- Reproduction roadmap: [`REPRODUCTION_PLAN.md`](../plans/REPRODUCTION_PLAN.md)
- Project README: [`README.md`](../../README.md)
- Notebook demo: [`notebooks/01_plan_and_act_real_tool_demo.ipynb`](../../notebooks/01_plan_and_act_real_tool_demo.ipynb)

## Paper Info
- Title: **Plan-and-Act: Improving Planning of Agents for Long-Horizon Tasks**
- arXiv: [2503.09572v3](https://arxiv.org/abs/2503.09572v3)
- Version used for this review: **v3 (22 Apr 2025)**
- Main domain: LLM-based web agents (long-horizon tasks)

## TL;DR
Paper này tách agent thành 2 vai trò rõ ràng:
- **Planner**: sinh kế hoạch cấp cao (high-level plan)
- **Executor**: biến từng bước kế hoạch thành action cụ thể trong môi trường

Điểm mấu chốt không chỉ là kiến trúc 2-agent, mà là **pipeline tạo dữ liệu synthetic cho Planner** (vì dữ liệu plan-quality rất thiếu). Với dynamic replanning + CoT, paper báo cáo:
- **57.58%** trên WebArena-Lite (SOTA tại thời điểm paper)
- **81.36%** text-only trên WebVoyager (SOTA text-only)

## 1. Bài toán paper giải quyết
LLM agent cho web task thường gặp 3 vấn đề:
1. Khó biến user intent thành chuỗi bước có cấu trúc.
2. Dễ "lạc chiến lược" khi task dài nhiều bước.
3. Môi trường web động, kế hoạch tĩnh dễ fail.

Theo paper, dùng một model vừa "nghĩ chiến lược" vừa "bấm click/type" gây quá tải nhận thức. Vì vậy cần tách planning và execution để giảm nhiễu vai trò.

## 2. Contribution chính
Từ phần Introduction + Method + Results, contribution thực tế gồm:

1. **Kiến trúc Plan-and-Act dạng modular 2-agent**
- Planner làm decomposition ở mức chiến lược.
- Executor chỉ tập trung grounding thành hành động cụ thể.

2. **Grounded Plan Generation**
- Thay vì yêu cầu LLM "bịa" plan từ query (dễ lệch môi trường), họ reverse-engineer plan từ trajectory thật.
- Gắn mỗi plan step với action span trong trajectory để plan có tính thực thi.

3. **Synthetic Plan Expansion quy mô lớn**
- Từ seed plan/query, sinh thêm **10,000** cặp query-plan (GPT-4o).
- Sau đó thêm **5,000** mẫu targeted augmentation dựa trên failure pattern.

4. **Dynamic Replanning + CoT**
- Replan sau mỗi bước dựa trên trạng thái mới.
- Bổ sung CoT cho cả Planner và Executor để tăng khả năng reasoning.

5. **Kết quả benchmark mạnh trên web-agent tasks**
- WebArena-Lite: lên tới **57.58%**.
- WebVoyager text-only: **81.36%**.

## 3. Kiến trúc kỹ thuật (phân tích sâu)

### 3.1 Planner
Input:
- User query
- (với dynamic mode) lịch sử plan/action + quan sát hiện tại

Output:
- Structured plan dạng step-by-step

Vai trò:
- Giữ "điều phối chiến lược" (control room)
- Dồn reasoning vào Planner để Executor không phải tự nghĩ high-level intent quá nhiều

### 3.2 Executor
Input:
- Plan step hiện tại
- HTML observation

Output:
- Action cụ thể (`Click`, `Type`, `Search`, `exit`, ...)

Vai trò:
- Grounding plan thành thao tác môi trường
- Không gánh phần decomposition chiến lược

### 3.3 Dynamic Replanning
Vấn đề của static plan:
- Không biết trước nội dung động (ví dụ kết quả search, lịch sử giao dịch, entity mới phát hiện)
- Dễ fail khi nhánh cũ không còn đúng

Giải pháp:
- Sau mỗi action, Planner nhận context mới và tạo plan mới.
- Plan đóng vai trò memory mang ngữ cảnh mới (không cần memory module riêng quá nặng).

### 3.4 CoT reasoning
- Planner và Executor đều được train/infer có reasoning trace.
- Mục tiêu: tăng chất lượng decision step-by-step, nhất là task dài và mơ hồ.

## 4. Pipeline dữ liệu synthetic (phần đặc sắc nhất)
Paper mạnh ở thiết kế data pipeline cho Planner.

### Stage A - Action Trajectory Generation (Sec 4.1)
- Sample query seed từ train set.
- Dùng LLM sinh query mới kiểu Alpaca-style.
- Demonstrator agent chạy query trong env để thu trajectory.
- ORM filter để giữ trajectory đạt yêu cầu.

Kết quả thực nghiệm dùng thêm **923 synthetic trajectories** cho Executor.

### Stage B - Grounded Plan Generation (Sec 4.2)
- Teacher LLM nhận trajectory thật.
- Sinh high-level plan + map step -> action index.

Điểm hay:
- Plan không "tưởng tượng", mà bám theo execution trace thật.
- Giảm mismatch giữa plan text và khả năng thực thi.

### Stage C - Synthetic Plan Expansion (Sec 4.3)
- Từ plan/query đã có, sinh thêm plan/query mới để tăng diversity.
- Thêm **10k** plan pairs (scale nhanh, paper báo < 1h với GPT-4o).
- Sau error analysis, sinh thêm **5k** targeted plans theo failure modes.

Nhận xét:
- Đây là "đòn bẩy" quan trọng nhất để Planner bớt overfit và tăng generalization.

## 5. Kết quả thực nghiệm và ý nghĩa

### 5.1 WebArena-Lite ablation (Table 1)
Một vài mốc quan trọng:
- No Planner (Base Executor): **9.85**
- + Synthetic Trajectories: tăng lên mức trung gian (tùy executor)
- + Plan Expansion: tăng rõ rệt
- + Targeted Augmentation: tiếp tục tăng
- + Dynamic Replanning: **53.94** (với Executor mạnh nhất ở cột cuối)
- + CoT (full Plan-and-Act): **57.58**

Thông điệp:
- Chỉ tăng action data cho Executor thì lợi ích sớm bão hòa.
- Chất lượng Planner + chất lượng plan data mới là bottleneck chính.

### 5.2 WebArena full benchmark (Table 3)
- Plan-and-Act (QWQ-32B): **48.15**
- Vượt/tiệm cận các baseline mạnh dùng GPT-4-based setup.

### 5.3 WebVoyager (Table 4)
- Plan-and-Act (Llama-3.1-8B): **58.08**
- Plan-and-Act (QWQ-32B): **81.36** (text-only SOTA theo paper)

Điểm đáng chú ý:
- Trên WebVoyager không có train set chuẩn, họ vẫn bootstrapping bằng synthetic trajectory + synthetic plan + CoT annotation.

## 6. Điều đặc sắc của paper
1. **Data-centric for planning**: không chỉ nói architecture, mà xử lý thẳng bài toán thiếu dữ liệu planning.
2. **Grounding rõ ràng**: map plan với action trajectory giúp plan "chạy được" thay vì chỉ "đọc hay".
3. **Dynamic replan đúng chỗ đau**: xử lý task phụ thuộc thông tin chỉ lộ ra trong runtime.
4. **Modular hóa tốt**: có thể thay model từng khối (Planner/Executor) và tái dùng pipeline.
5. **Hiệu quả chi phí dữ liệu**: paper claim 15k synthetic examples trong <1h (thay vì thu trajectory thủ công lâu hơn nhiều).

## 7. Hạn chế và rủi ro kỹ thuật
Theo paper + góc nhìn reproduce:

1. **Phụ thuộc teacher stack mạnh**
- GPT-4o, DeepSeek-R1-Distill-Llama-70B, WebRL actor/ORM...
- Chất lượng synthetic data phụ thuộc mạnh vào teacher quality.

2. **Dynamic replanning mỗi bước có thể tốn latency/cost**
- Paper cũng tự nêu nhược điểm này.

3. **Rủi ro bias từ synthetic loop**
- Nếu teacher/systematic bias, Planner học lại bias ở quy mô lớn.

4. **Khó so sánh tuyệt đối fair giữa setup khác model size**
- Có nhiều model backbone khác nhau (70B, 32B, 8B) ở các bảng.

5. **Reproducibility thực tế phụ thuộc môi trường benchmark**
- Web env thay đổi theo thời gian; replay exact trajectory không đơn giản.

## 8. Ý nghĩa cho người muốn implement/reproduce
Nếu bạn muốn reproduce nhanh và thực dụng:

1. **Đừng bắt đầu bằng model quá lớn**
- Làm proof-of-concept với 8B trước để xác thực pipeline dữ liệu.

2. **Ưu tiên dựng pipeline data trước architecture tuning**
- Stage B/C (grounded plan + expansion) là lõi thành công.

3. **Đo theo từng tầng ablation giống paper**
- `No planner -> Planner finetune -> +synthetic plan -> +targeted -> +replanning -> +CoT`

4. **Theo dõi metrics trung gian, không chỉ success rate cuối**
- Plan validity, step grounding accuracy, replan trigger quality, token cost/episode.

5. **Định nghĩa rõ khi nào cần replan**
- Paper replan mỗi bước; bản production nên có trigger để giảm chi phí.

## 9. Bản chất đóng góp khoa học (kết luận review)
Đây là một paper **thực dụng, engineering-heavy, data-centric** hơn là đề xuất thuật toán lý thuyết mới hoàn toàn.

Giá trị lớn nhất của paper không nằm ở ý tưởng "tách planner/executor" (đã có ở prior work), mà nằm ở:
- Cách họ làm cho planner thực sự học được bằng dữ liệu synthetic có grounding.
- Cách họ nối được 3 thứ: **data generation -> modular planning runtime -> benchmark gain**.

Nếu xét theo hướng "triển khai agent trong môi trường thật", paper này đáng đọc vì đưa ra một recipe tương đối rõ ràng để chuyển từ prompting thuần sang một pipeline trainable có thể mở rộng.

## Appendix - Key numbers (quick reference)
- WebArena-Lite (best): **57.58%** (Plan-and-Act + CoT)
- WebArena-Lite (dynamic replanning, pre-CoT): **53.94%**
- WebArena (full): **48.15%** (QWQ-32B variant)
- WebVoyager text-only (best): **81.36%**
- Synthetic data scale:
  - Extra trajectories: **923**
  - Plan expansion: **10,000**
  - Targeted augmentation: **5,000**
- WebArena-Lite train set referenced: **1,113** examples
- WebArena-Lite test tasks: **165**

## Notes for this repo
Review này được viết dựa trên:
- [`paper_assets/2503.09572v3.pdf`](../../paper_assets/2503.09572v3.pdf)
- [`paper_assets/2503.09572v3.html`](../../paper_assets/2503.09572v3.html)
