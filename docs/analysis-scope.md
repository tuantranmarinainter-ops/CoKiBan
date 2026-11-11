# Đặc tả phân tích vật thể và camera

## Sản phẩm cần đạt

Bóc tách video thành shot và mô tả đủ chi tiết để người/agent khác hình dung, đối chiếu hoặc dựng lại cảnh. Dữ liệu phân tích phải độc lập với renderer. Mọi nhận định được nối tới frame/timecode, với phần chưa biết ghi rõ.

## Vật thể xuyên video

Mỗi object có id ổn định, loại (nhân vật/nhà/đạo cụ/địa hình/VFX), tên, hình dáng tổng thể, bộ phận, màu, vật liệu nhìn thấy, đặc điểm nhận diện, tỷ lệ tương đối, ảnh crop và các shot xuất hiện. Ghi variant khi đổi trang phục hoặc trạng thái. Mỗi instance theo shot ghi bbox chuẩn hóa 0–1, lớp tiền/trung/hậu cảnh, hướng nhìn, pose, mức che khuất và quan hệ với object khác. Bbox là tọa độ hình ảnh; tọa độ 3D đề xuất nằm trong reconstruction.

## Chuyển động vật thể

Ghi khoảng bắt đầu–kết thúc, trạng thái đầu/cuối, đường đi trên màn hình, đổi hướng, tốc độ tương đối, các sự kiện tiếp xúc (đặt chân, cầm, thả, va chạm). Chuyển động hình ảnh phải tách khỏi chuyển động camera để không gọi vật đứng yên là đang chạy chỉ vì camera pan.

## Camera mỗi shot

- Cỡ cảnh và góc nhìn tương đối với chủ thể, horizon, độ nghiêng roll, bố cục.
- Timeline gồm các đoạn đứng yên hoặc thay đổi, hướng chuyển động hình ảnh, mức scale/rotation, sự kiện bắt đầu/dừng/đổi hướng.
- Giả thuyết pan/tilt/track/dolly/orbit/zoom cùng bằng chứng và các khả năng khác còn phù hợp.
- measured chứa số đo 2D + phương pháp + đơn vị + độ phân giải đo; observed chứa mô tả thấy được; inferred chứa giả thuyết chuyển động máy; reconstruction chứa thông số dựng thử.
- Mỗi nhận định ghi frame_ids, confidence và review_status. Tránh số confidence giả chính xác; dùng low/medium/high cùng lý do.

## Kiểm chứng

Một shot chỉ reviewed khi đã xem ảnh/chuỗi ảnh đủ xác minh nhận định. Độ phủ frame trích xuất và frame đã quan sát là hai chỉ số riêng. Kiểm ID vật thể xuyên cut, nhầm nền/chủ thể, jump cut, transition và motion blur. Cần benchmark có ground truth camera/object khi đánh giá độ chính xác thuật toán.

## Tương thích MVP

Đây là thiết kế mở rộng. Hiện analysis.json còn các trường description, camera, action dạng chuỗi và actors/places. Chưa tự động chuyển chúng thành camera timeline hoặc object tracks. Cần nâng schema có migration trước khi thay định dạng code. Adapter export-3js giữ vai trò tiêu thụ kết quả đã phân tích.
