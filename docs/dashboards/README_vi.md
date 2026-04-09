# Bảng Điều Khiển MartialComp

## Giới Thiệu

Thư mục này chứa tài liệu đầy đủ về các bảng điều khiển (dashboard) khác nhau có sẵn trong ứng dụng MartialComp. Mỗi loại người dùng có một bảng điều khiển riêng biệt phù hợp với vai trò của mình, cung cấp các chức năng phù hợp với nhu cầu của họ.

## Các Loại Bảng Điều Khiển

MartialComp cung cấp nhiều bảng điều khiển, mỗi bảng được thiết kế cho một vai trò cụ thể:

1. [**Bảng Điều Khiển Vận Động Viên**](./participants/README.md) - Dành cho các võ sinh tham gia thi đấu
2. [**Bảng Điều Khiển Câu Lạc Bộ**](./clubs/README.md) - Dành cho quản lý và ban điều hành câu lạc bộ
3. [**Bảng Điều Khiển Liên Đoàn**](./federations/README.md) - Dành cho quản trị viên liên đoàn
4. [**Bảng Điều Khiển Trọng Tài/Giám Khảo**](./referees/README.md) - Dành cho trọng tài và giám khảo đánh giá các cuộc thi đấu
5. [**Bảng Điều Khiển Huấn Luyện Viên Đa Môn**](./coaches/README.md) - Dành cho huấn luyện viên quản lý nhiều bộ môn
6. [**Bảng Điều Khiển Thi Đấu Đối Kháng**](./combat/README.md) - Giao diện chuyên biệt cho quản lý thi đấu đối kháng

## Truy Cập Bảng Điều Khiển

Mỗi người dùng được tự động chuyển hướng đến bảng điều khiển tương ứng với vai trò của mình sau khi đăng nhập. Việc chuyển hướng được quản lý bởi hàm `dashboard` trong tệp `competitions/views/dashboard/base.py`.

## Cấu Trúc Chung của Bảng Điều Khiển

Tất cả các bảng điều khiển đều có chung cấu trúc:

- **Thanh tiêu đề**: Hiển thị tên người dùng, vai trò, và cho phép truy cập cài đặt và đăng xuất
- **Thanh bên**: Điều hướng đến các phần khác nhau của bảng điều khiển
- **Nội dung chính**: Hiển thị thông tin và chức năng cụ thể cho từng phần
- **Chân trang**: Thông tin về phiên bản ứng dụng và các liên kết hữu ích

## Tùy Chỉnh Bảng Điều Khiển

Người dùng có thể tùy chỉnh một số khía cạnh của bảng điều khiển:
- Chọn các widget hiển thị trên trang chủ
- Thứ tự hiển thị thông tin
- Tùy chọn thông báo

## Các Chức Năng Chung

Tất cả các bảng điều khiển đều cung cấp các chức năng cơ bản sau:
- Tổng quan với các thống kê chính
- Thông báo và cảnh báo
- Quản lý hồ sơ người dùng
- Lịch sự kiện sắp tới
- Truy cập tài liệu

## Hỗ Trợ Đa Ngôn Ngữ

Tất cả các bảng điều khiển đều hỗ trợ đa ngôn ngữ và có sẵn trong các ngôn ngữ sau:
- Tiếng Pháp (fr) - Ngôn ngữ mặc định
- Tiếng Anh (en)
- Tiếng Tây Ban Nha (es)
- Tiếng Ý (it)
- Tiếng Đức (de)
- Tiếng Na Uy (no)
- Tiếng Nhật (ja)
- Tiếng Trung (zh)
- Tiếng Hindi (hi)
- Tiếng Ả Rập (ar)
- Tiếng Swahili (sw)
- Tiếng Amharic (am)
- Tiếng Zulu (zu)
- Tiếng Yoruba (yo)
- Tiếng Bồ Đào Nha (pt)
- Tiếng Hàn (ko)

## Thiết Kế Kỹ Thuật

Các bảng điều khiển được triển khai sử dụng:
- Django cho phần backend
- HTML/CSS/JavaScript cho phần frontend
- Bootstrap cho bố cục tương thích đa thiết bị
- Công nghệ AJAX cho cập nhật động

## Tài Liệu Chi Tiết

Để biết thêm chi tiết về từng bảng điều khiển, vui lòng tham khảo các liên kết ở trên hoặc khám phá các thư mục con của thư mục này.
