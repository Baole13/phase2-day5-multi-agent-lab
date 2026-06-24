# Design Submission

## Problem

Xây dựng một research assistant nhận câu hỏi dài, thu thập nguồn tham khảo, phân tích các ý chính, rồi viết câu trả lời cuối cùng có thể debug được. Hệ thống phải hỗ trợ hai chế độ:

- `baseline`: một agent xử lý toàn bộ yêu cầu trong một lần gọi.
- `multi-agent`: Supervisor điều phối Researcher, Analyst và Writer qua shared state.

Mục tiêu của bài lab không phải là tối ưu độ chính xác tuyệt đối, mà là chứng minh được cách tổ chức multi-agent, handoff qua state, guardrails cơ bản và benchmark so sánh với baseline.

## Why multi-agent?

Single-agent đủ nhanh để trả lời trực tiếp, nhưng thiếu ba lợi điểm quan trọng cho bài toán research:

- Thiếu tách vai trò: thu thập nguồn, phân tích và viết bị trộn trong một prompt nên khó kiểm tra từng bước.
- Thiếu traceability: khi câu trả lời sai, khó biết lỗi đến từ khâu tìm nguồn, suy luận hay tổng hợp.
- Thiếu khả năng benchmark theo bước: multi-agent cho phép đo route, số nguồn, số vòng lặp và quan sát failure mode rõ hơn.

Trong bài lab này, multi-agent hợp lý vì chất lượng quy trình và khả năng giải thích quan trọng hơn việc trả lời thật nhanh.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Chọn worker tiếp theo hoặc dừng workflow theo rule-based policy | `request`, `research_notes`, `analysis_notes`, `final_answer`, `iteration`, `errors` | cập nhật `route_history`, `iteration`, trace route | route sai, lặp vô hạn, fallback quá sớm |
| Researcher | Thu thập source và tạo ghi chú nghiên cứu ngắn gọn | `request.query`, `max_sources` | `sources`, `research_notes` | nguồn ít, nguồn mock yếu, research notes thiếu chiều sâu |
| Analyst | Chuyển research notes thành insight có cấu trúc | `request.query`, `research_notes`, `sources` | `analysis_notes` | phân tích quá chung chung, chưa phát hiện weak evidence rõ |
| Writer | Tổng hợp câu trả lời cuối cùng và nêu source references | `request.query`, `research_notes`, `analysis_notes` | `final_answer` | trả lời chung chung, fallback khi upstream thiếu dữ liệu |

## Shared state

| Field | Vai trò |
|---|---|
| `request` | Giữ query đầu vào và các tham số cơ bản như `max_sources`, `audience` |
| `iteration` | Đếm số lần supervisor route để chặn loop vô hạn |
| `route_history` | Ghi lại đường đi của workflow để trace và benchmark |
| `sources` | Danh sách nguồn do Researcher thu thập để các agent sau dùng lại |
| `research_notes` | Kết quả handoff từ Researcher sang Analyst/Writer |
| `analysis_notes` | Kết quả handoff từ Analyst sang Writer |
| `final_answer` | Đầu ra cuối cùng cho người dùng |
| `agent_results` | Nhật ký nội dung do từng agent sinh ra để debug từng bước |
| `trace` | Sự kiện tracing tối thiểu theo từng route và từng agent run |
| `errors` | Ghi lỗi hoặc dấu hiệu fail để supervisor quyết định fallback |
| `usage` | Ghi mode chạy, token và cost ước tính phục vụ benchmark |
| `completed` | Cờ dừng workflow an toàn |

## Routing policy

```text
start
  -> supervisor
      -> researcher   if chưa có research_notes
      -> analyst      if đã có research_notes nhưng chưa có analysis_notes
      -> writer       if đã có analysis_notes nhưng chưa có final_answer
      -> writer       if chạm max_iterations hoặc lỗi lặp lại
      -> done         if đã có final_answer hoặc workflow đã completed

researcher -> supervisor
analyst    -> supervisor
writer     -> supervisor -> done
```

Policy này ưu tiên tính ổn định và dễ debug cho lab hơn là routing thông minh bằng LLM.

## Guardrails

- Max iterations: dùng `Settings.max_iterations`, mặc định `6`
- Timeout: `Settings.timeout_seconds`, mặc định `60`
- Retry: chưa có retry đa tầng; client thật có thể thêm retry ở service layer
- Fallback: nếu chạm iteration limit hoặc có nhiều lỗi, Supervisor đẩy sang Writer để tạo câu trả lời fallback thay vì crash
- Validation: dùng Pydantic cho `ResearchQuery`, `ResearchState`, `SourceDocument`, `BenchmarkMetrics`

## Benchmark plan

### Queries

1. `Research GraphRAG state-of-the-art and write a 500-word summary`
2. `Compare single-agent and multi-agent workflows for customer support`
3. `Summarize production guardrails for LLM agents`

### Metrics

- Latency: wall-clock time của từng run
- Estimated cost: token cost ước tính nếu có provider thật; trong mock mode hiện tại là `0.0`
- Quality: chấm tay theo peer-review rubric, tập trung vào role clarity, state design, failure guard, benchmark và trace explanation
- Citation coverage: đánh giá định tính dựa trên việc Researcher có sinh `sources` và Writer có reference lại nguồn
- Failure mode: ghi nhận route lặp, answer quá chung, hoặc thiếu citation cụ thể

### Expected outcome

- Baseline nhanh hơn đáng kể.
- Multi-agent chậm hơn nhưng dễ giải thích hơn, có trace rõ và output có cấu trúc tốt hơn.
- Với mock mode, cost gần như bằng `0`; khi bật OpenAI/Tavily thật thì benchmark cost sẽ meaningful hơn.
