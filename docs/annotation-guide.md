# Bốn phần phân tích hình ảnh

Đây là quy trình **AI/người xem frame và ghi chú**. Lệnh `analyze` tự tách shot ứng viên và frame, chưa nhận dạng vật thể hay đo quỹ đạo camera. Trường v2 rỗng là chưa phân tích, không phải kết quả âm tính. Giữ file `analysis.json` cùng thư mục `frames/`. Sau khi chỉnh, chạy `validate`, rồi `render` và `export-3js`.

## Cách điền

- `objects`: từ điển hồ sơ dùng chung, khóa là ID ổn định. Mỗi mục có `name`, `category`, `description` (hình, bộ phận, màu, vật liệu nhìn thấy, kích thước tương đối, đặc điểm nhận dạng), `frame_ids` là bằng chứng. Có thể bổ sung các trường chi tiết khác.
- `shots[].object_instances`: vật thể nào xuất hiện, mô tả vị trí, tư thế, hướng nhìn, che khuất, quan hệ và `frame_ids`. `bbox` tùy chọn `[x,y,width,height]` từ 0 đến 1 tính từ góc trên trái của ảnh. Đó là tọa độ ảnh, không phải tọa độ thế giới.
- `shots[].motion_events`: mỗi sự kiện chứa `object_id`, `start`, `end` giây tính từ đầu video, `description`, `frame_ids`; ghi hướng, tốc độ tương đối, tương tác và thay đổi trạng thái.
- `shots[].camera_timeline`: mỗi đoạn `start`, `end`, `framing`, `angle`, `movement`, `alternatives`, `frame_ids`. Ghi cách khung hình thay đổi trước; giả thuyết camera cần ghi bằng chứng và phương án khác. Không suy ra tiêu cự, độ sâu hay đường đi 3D chính xác từ chuyển động ảnh đơn thuần.
- `shots[].observations`: các nhận xét có `kind` = `measured` / `observed` / `inferred` / `reconstruction`, `text`, `confidence` = `low` / `medium` / `high`, `frame_ids`, `reason` và `review_status`. Không gắn nhãn observed cho điều chưa xem. `review.inspected_frames` liệt kê số frame thực sự đã quan sát; không điền toàn bộ chỉ vì đã trích xuất.

Khoảng shot theo frame là `[start_frame, end_frame_exclusive)`; thời gian camera/sự kiện nằm trong shot. `frame_ids` là số nguyên index bắt đầu từ 0, hình phải có trong `frames/`. Chạy với `--all-frames` nếu muốn tham chiếu bất kỳ frame nào. Các frame bằng chứng trong shot được nhúng vào HTML. HTML vẫn chia theo byte và có thể báo lỗi khi riêng một shot vượt ngưỡng: tăng ngưỡng hoặc giảm số frame/độ phân giải. `validate` kiểm tra cấu trúc và liệt kê phần chưa duyệt, **không chứng minh nhận xét đúng**.

Ví dụ minh họa giả định (không phải phân tích video thật):

```json
{
  "objects": {
    "house_01": {"name": "Nhà", "category": "object", "description": "Nhà nhỏ, mái đỏ, thân vàng; mô tả bổ sung theo ảnh", "frame_ids": [0, 12]}
  },
  "review": {"inspected_frames": [0, 12], "note": "Đã xem hai ảnh"},
  "shots": [{
    "id": "s001",
    "object_instances": [{"object_id": "house_01", "description": "Ở giữa khung hình", "bbox": [0.2, 0.1, 0.6, 0.8], "frame_ids": [0]}],
    "motion_events": [{"object_id": "house_01", "start": 0, "end": 0.4, "description": "Dịch sang phải trong ảnh", "frame_ids": [0, 12]}],
    "camera_timeline": [{"start": 0, "end": 0.4, "framing": "toàn cảnh", "angle": "ngang mắt", "movement": "chưa xác định", "alternatives": ["camera dịch", "vật thể dịch"], "frame_ids": [0, 12]}],
    "observations": [{"kind": "observed", "text": "Nhà ở gần giữa ảnh", "confidence": "high", "frame_ids": [0], "reason": "nhìn thấy", "review_status": "reviewed"}]
  }]
}
```

Ví dụ chỉ trình bày trường bổ sung: không thay thế toàn bộ `analysis.json`. Điền vào shot hiện có và dùng thời gian/frame thực tế. `reference.json` trong output 3JsStudio giữ toàn bộ bốn phần; chưa chuyển tự động thành tham số camera 3D hoặc animation. HTML và thư mục frames cần giao cùng output.
