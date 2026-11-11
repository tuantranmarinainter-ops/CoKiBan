# Hợp đồng bàn giao CoKiBan → 3JsStudio

Đã đối chiếu repo đích tại commit a9c33b3834cd1c0e95b7ebddc9a05e845a885237, ngày 11/11/2026.
Nguồn kiểm tra: CLAUDE.md, HANDOFF.md, tools/ref.py, tools/snap.js, episodes/_template/narration.json và cây thư mục.

## Phân chia trách nhiệm

CoKiBan chuẩn bị bằng chứng và mô tả. 3JsStudio dựng cảnh, nhân vật R6, môi trường, giọng đọc, animation và render bằng Three.js/HyperFrames.

Repo đích đã có ref.py lấy frame giữa mỗi shot, contact sheet và báo cáo nhịp. CoKiBan bổ sung ảnh đầu/giữa/cuối, frame timestamp, dữ liệu mô tả có thể sửa, HTML giới hạn dung lượng và export. Mã ref.py không được sao chép; tool local được viết riêng, có thể dùng MP4 đã tải từ pipeline hiện có.

## Ánh xạ

| CoKiBan | 3JsStudio | Điều kiện |
|---|---|---|
| actors, places | EPISODE.actors, EPISODE.places | AI điền theo API thật của engine |
| shot.id, dur, type, at, who, sfx | SHOTS | Giữ id; dur theo nguồn, không ép 140 shot |
| shot.lines | SHOTS.line khi chỉ giao một cue | Nhiều cue giữ trong reference.json; cần quyết định tách hoặc bổ sung mapper |
| subtitles | narration.json.lines | line, who, text, start, end, dur; source=reference-srt |
| description, camera, action, lighting, continuity | reference.json | Chỉ dẫn để Claude dựng, chưa phải executable camera track |
| source.frame_times | reference.json | Giữ thời gian nguồn cho VFR; renderer đích có thể sample lại ở 30 fps |

narration.json có dry=true, timing_source=reference-srt vì chưa kèm audio TTS. Không đánh dấu đây là kết quả giọng đọc đã tổng hợp. Cue vượt video được giữ nguyên và cảnh báo; người dựng cần xác minh trước khi chốt. TTS mới có thời lượng khác phải retime shot.

Không gán phụ đề vào SHOTS.text vì text dành cho chữ nổi đặc biệt. Type chưa phân tích dùng establish tạm và được liệt kê trong integration-status.json. Cần hoàn thiện trước khi sản xuất.

## Trạng thái thực tế repo đích

Có engine/r6.js, engine/winter.js và demo; tools/snap.js dùng renderAt(t), __ready, capture=1. Tài liệu đặt mục tiêu stage.js, timeline.js, engine/shots.js, episode template và HyperFrames composition nhưng cây repo chưa có các module này ở revision đã kiểm. Export hiện là bộ dữ liệu nháp để agent tiếp tục triển khai. Chưa có phép thử render end-to-end trong 3JsStudio.

Theo hướng dẫn đích, dùng hf-seek, e.detail.time, waitUntil cho việc bất đồng bộ, window.THREE, asset tải trước seek và RNG có seed. R6 dùng Y-up, mặt +Z, tay phải -X, đơn vị stud và cao khoảng 5.2. Không đổi đơn vị sang mét mà thiếu bước quy đổi.

Repo đích ưu tiên sáng tác ý tưởng riêng. Trường hợp người dùng yêu cầu tái dựng clip để benchmark phải ghi riêng mục tiêu benchmark và nguồn tham chiếu trong bàn giao. Không tự đổi câu chuyện theo một mục tiêu khác.

## Cải tiến tiếp theo

- UI chỉnh cut và mô tả, ổn định ID qua lần phân tích lại.
- Duyệt frame đầy đủ trong HTML có phân trang theo byte.
- Kiểm schema actors/places/animation sau khi engine timeline của 3JsStudio tồn tại.
- Đối chiếu render theo shot và chấm sai lệch bố cục.
