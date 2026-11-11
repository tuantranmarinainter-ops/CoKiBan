# CoKiBan

Chuẩn bị kịch bản hình và bằng chứng tham khảo cho quy trình sản xuất video của [3JsStudio](https://github.com/tuantranmarinainter-ops/3JsStudio).

Video + SRT → frame và shot ứng viên → AI/người dùng phân tích → storyboard HTML + dữ liệu episode → 3JsStudio dựng Three.js/HyperFrames.

## Bản MVP

- Nhận video local và SRT tùy chọn, Python 3.10+ cùng FFmpeg/FFprobe trong PATH.
- Đọc timestamp từng frame, kể cả nguồn có tốc độ khung hình biến đổi.
- Phát hiện điểm cắt ứng viên; ảnh đầu/giữa/cuối từng shot, JSON giữ nguyên lời kể.
- Xuất HTML tự chứa ảnh, chia theo byte thực, mặc định dưới 25 MB mỗi file.
- `--all-frames` lưu mọi frame ra thư mục ảnh. HTML vẫn dùng ảnh đại diện từng shot để tiết kiệm dung lượng.
- AI/người xem điền hồ sơ vật thể, vị trí/hành động từng shot, timeline camera và quan sát có bằng chứng vào JSON; xuất lại HTML.
- `validate` kiểm tra liên kết ID, thời gian, tọa độ, frame bằng chứng và báo các phần chưa duyệt.
- Xuất dữ liệu nháp `episode.js`, `shots.js`, `narration.json`, `narration.txt` và bàn giao cho 3JsStudio.

Mô tả thị giác cần agent xem ảnh. Tool chưa tự gọi mô hình AI, chưa tạo audio hoặc video thành phẩm. Bộ export khớp quy ước dữ liệu được tài liệu hóa của 3JsStudio; phần engine timeline và composition của repo đích còn cần hoàn thiện.

## Chạy

```bash
python tools/cokiban.py analyze "video.mp4" --srt "video.vi.srt" --out outputs/demo
# Đọc docs/annotation-guide.md, xem ảnh và điền outputs/demo/analysis.json
python tools/cokiban.py validate outputs/demo/analysis.json
python tools/cokiban.py render outputs/demo/analysis.json --max-mb 25
python tools/cokiban.py export-3js outputs/demo/analysis.json --out outputs/episode-draft
```

Đưa thư mục episode-draft cùng frames và HTML tham chiếu cho Claude trong workspace 3JsStudio. Đọc `docs/3jsstudio-contract.md` trước khi nối vào episode. Tool yêu cầu thư mục output mới để bảo vệ kết quả đang có. Khi xử lý lỗi giữa chừng, thư mục đích chưa được công bố.

`--threshold 0.27` điều chỉnh độ nhạy; hạ để tìm thêm cut, tăng để giảm nhiễu. `--min-shot 0.15` gộp đoạn quá ngắn. Đây là ứng viên và cần duyệt. ID s001… được cố định trong JSON sau lần phân tích; khi sửa phải giữ ID cũ.

## Skill dành cho agent

Đọc `skills/video-to-storyboard/SKILL.md` để chạy quy trình phân tích và bàn giao. Đây là gói hướng dẫn trong repo; việc tích hợp vào danh mục skill của từng ứng dụng thực hiện riêng. Claude Code có thể đọc trực tiếp qua `CLAUDE.md`.

## Dữ liệu

[Hướng dẫn điền bốn phần và ví dụ](docs/annotation-guide.md). Với dữ liệu schema 1 cũ, tạo bản mới trong cùng thư mục để giữ đường dẫn frames: `python tools/cokiban.py migrate outputs/demo/analysis.json --out outputs/demo/analysis-v2.json`.


`analysis.json` giữ timestamp nguồn, ánh xạ frame, phụ đề, shot, registry nhân vật/bối cảnh, observations và reconstruction. Khoảng frame là [start_frame, end_frame_exclusive). `docs/3jsstudio-contract.md` ghi quy tắc ánh xạ. Mẫu trường được tạo trực tiếp bởi lệnh analyze.

Video, ảnh trích, audio và bản xuất nằm trong outputs/ và được gitignore. Repo chứa code và quy trình có thể dùng lại.

## Kiểm tra

```bash
python -m unittest discover -s tests -v
```
