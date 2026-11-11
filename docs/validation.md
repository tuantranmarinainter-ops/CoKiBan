# Kiểm chứng MVP

Ngày 11/11/2026, FFmpeg 7.1.5.

- Hai unittest PASS, kiểm SRT sai khoảng thời gian và bảo toàn cue giao nhiều shot khi export.
- Clip người dùng cung cấp dài 171,067 giây, 5132 frame, 93 cue SRT.
- Analyze tìm 126 shot ứng viên với threshold 0.27, min-shot 0.15.
- Khoảng frame phủ [0,5132), không hở hoặc chồng; tổng dur khớp duration nguồn.
- Thử max-mb=1 tạo 9 HTML, lớn nhất 985497 byte.
- Thử --all-frames trên clip tổng hợp 9 frame xuất đúng 9 ảnh.
- Export tạo episode.js, shots.js, narration.json/txt, reference.json và báo cáo draft.
- Kiểm trình duyệt đã thử bằng Playwright và Chromium hệ thống nhưng bị môi trường chặn socket, nên chưa xác minh giao diện bằng screenshot.

Các kiểm tra trên xác minh xử lý dữ liệu và tạo tài liệu. Shot candidates chưa được người dùng duyệt. Chưa render end-to-end bằng 3JsStudio do engine timeline/composition của repo đích chưa hoàn thiện ở revision tham chiếu.
