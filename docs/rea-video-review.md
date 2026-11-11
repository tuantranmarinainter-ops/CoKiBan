# Học hỏi từ rea-video

Ngày khảo sát 11/11/2026. Revision 3669923645e3953632e7406a57fb883e0ba8a6e0.
Đã đọc README, aspects/camera.py, aspects/subject.py, entities.py, motion.py, phần global_motion/motion_summary của features.py và references/review.md. Đây là đánh giá mã nguồn, chưa chạy benchmark của rea-video.

## Phạm vi CoKiBan

Đầu vào là video và phụ đề tùy chọn. Sản phẩm cốt lõi là bản mô tả có bằng chứng về vật thể, nhân vật, bối cảnh, bố cục, hành động và chuyển động camera theo thời gian. 3JsStudio là bên tiêu thụ dữ liệu phân tích. Chất lượng CoKiBan đo bằng độ đúng và độ đầy đủ của mô tả.

## Những cơ chế có thể học

| Nguồn | Cơ chế đã đọc | Áp dụng đề xuất |
|---|---|---|
| [features.py](https://github.com/JuneYaooo/rea-video/blob/3669923645e3953632e7406a57fb883e0ba8a6e0/rea_video/features.py) | Track corner bằng Lucas–Kanade, kiểm forward/backward, fit similarity affine bằng RANSAC; đo dịch chuyển, scale, rotation, residual | Đo chuyển động hình ảnh nền theo shot, lưu độ tin cậy và vùng dùng để đo |
| [aspects/camera.py](https://github.com/JuneYaooo/rea-video/blob/3669923645e3953632e7406a57fb883e0ba8a6e0/rea_video/aspects/camera.py) | Tách measure và interpret, tổng hợp camera từ motion summary và nhận xét thị giác | Giữ measured, observed, inferred riêng, kèm frame bằng chứng |
| [entities.py](https://github.com/JuneYaooo/rea-video/blob/3669923645e3953632e7406a57fb883e0ba8a6e0/rea_video/entities.py) | Cast xuyên shot gồm characters/scenes/props, mô tả look và shot xuất hiện; ưu tiên review khi có | Registry ID ổn định cho mọi vật thể cần dựng, variant trang phục/trạng thái và quan hệ vật thể |
| [motion.py](https://github.com/JuneYaooo/rea-video/blob/3669923645e3953632e7406a57fb883e0ba8a6e0/rea_video/motion.py) | Pixel change theo ô, nhóm thời điểm/vị trí; events, static elements, continuous layer; crops; strip frames | Lấy thêm frame quanh sự kiện, mô tả bắt đầu/đỉnh/kết thúc và crop vật thể để tránh mất chi tiết |
| [aspects/subject.py](https://github.com/JuneYaooo/rea-video/blob/3669923645e3953632e7406a57fb883e0ba8a6e0/rea_video/aspects/subject.py) | Face, vùng nét qua Laplacian, fallback vùng giữa hình | Dùng như gợi ý vùng chủ thể, không coi là nhận diện đầy đủ mọi vật thể |
| [review.md](https://github.com/JuneYaooo/rea-video/blob/3669923645e3953632e7406a57fb883e0ba8a6e0/skills/rea-video/references/review.md) | Bắt buộc xem bằng chứng khi nguồn phân tích bất đồng, ghi rõ khi chưa xem ảnh | Hàng đợi review cho góc camera mơ hồ, vật che khuất, đổi nhân vật và điểm cắt chưa chắc |

## Giới hạn phải giữ rõ

Similarity transform mô tả biến đổi 2D của hình. Scale tăng chưa chứng minh dolly-in; có thể zoom, crop hậu kỳ hoặc vật thể tiến về máy. Dịch ảnh trái chưa tự động đồng nghĩa camera đi trái. Cần đối chiếu nền tĩnh, vật thể chuyển động, parallax, che khuất và biến đổi phối cảnh.

motion.py phục vụ rendered/code/motion-graphics shots. Cơ chế ô pixel đổi không phải object tracker 3D hay rig recovery. Easing suy từ activity chỉ là ước lượng. entities.py quản lý dữ liệu do VLM/agent tạo, không tự suy ra mesh/texture/rig từ video. Camera module chưa cung cấp đường camera world-space chính xác.

README công bố điểm accuracy cho phân loại cách sản xuất video; không dùng số đó làm độ chính xác nhận diện vật thể hoặc khôi phục camera của CoKiBan.

## Ưu tiên triển khai

1. Schema object registry + instance theo shot + camera timeline; evidence và uncertainty là trường bắt buộc khi review.
2. Tăng mẫu theo thời gian và quanh sự kiện; crop các vật nhỏ ở độ phân giải gốc.
3. Agent xem ảnh/clip, mô tả shape, parts, color, material appearance, relative size, pose, occlusion, interaction; cập nhật danh tính xuyên shot.
4. Thêm phép đo chuyển động nền bằng optical flow, loại vùng chữ/subtitle và vật chuyển động lớn, lưu fit quality; chưa đủ bằng chứng thì unknown.
5. Đối chiếu mô tả với ảnh và tạo review_tasks cho mâu thuẫn.
6. Xuất HTML/JSON trung lập và adapter cho 3JsStudio.

Bản cập nhật này chốt phạm vi và thiết kế. Các thuật toán optical flow, object tracking và tự gọi VLM là việc cần triển khai tiếp. Không sao chép mã rea-video trong lần cập nhật này.
