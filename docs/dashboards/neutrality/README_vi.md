# Phân Tích Tính Khách Quan Của Trọng Tài

## Mục Tiêu

Module phân tích tính khách quan cho phép đánh giá một cách khách quan sự công bằng của từng trọng tài trong một cuộc thi đấu. Module tự động phát hiện các thiên lệch tiềm ẩn bằng cách so sánh điểm số được chấm theo nhiều tiêu chí thống kê.

Module này là một công cụ **đào tạo và cải tiến liên tục** dành cho trọng tài, không phải công cụ kỷ luật. Nó giúp mỗi trọng tài nhận thức được các xu hướng vô thức của mình nhằm nâng cao trình độ.

---

## Điểm Khách Quan (0-100)

Mỗi trọng tài nhận được một **điểm khách quan tổng thể** được tính trên thang 100 điểm. Điểm càng cao, trọng tài càng được đánh giá là công bằng.

Điểm được tính bằng cách trừ các khoản phạt từ điểm tối đa 100, theo 4 tiêu chí có trọng số:

| Tiêu chí | Trọng số | Mức phạt tối đa |
|----------|----------|------------------|
| Thiên lệch câu lạc bộ | 30% | -30 điểm |
| Thiên lệch quốc tịch | 25% | -25 điểm |
| Thiên lệch vị thế chấm điểm | 20% | -20 điểm |
| Sự đồng thuận với đồng nghiệp | 25% | -25 điểm |

### Mức độ rủi ro

| Điểm | Mức độ | Ý nghĩa |
|------|--------|----------|
| **80-100** | Rủi ro thấp (xanh lá) | Trọng tài chấm điểm nhất quán và công bằng |
| **60-79** | Rủi ro trung bình (cam) | Phát hiện một số xu hướng, cần theo dõi |
| **0-59** | Rủi ro cao (đỏ) | Phát hiện thiên lệch đáng kể, khuyến nghị đào tạo bổ sung |

---

## Tiêu Chí 1: Thiên Lệch Câu Lạc Bộ

### Nguyên tắc
Tiêu chí này so sánh điểm trung bình mà trọng tài chấm cho các vận động viên thuộc **câu lạc bộ của mình** so với các vận động viên **từ các câu lạc bộ khác**.

### Cách tính
```
Chênh lệch = Trung bình(điểm cho vận động viên cùng câu lạc bộ) - Trung bình(điểm cho các vận động viên khác)
```

### Ngưỡng phát hiện

| Chênh lệch (giá trị tuyệt đối) | Mức nghiêm trọng | Diễn giải |
|---------------------------------|-------------------|-----------|
| < 0,3 điểm | Trung tính | Không phát hiện thiên lệch |
| 0,3 đến 0,5 điểm | Nhẹ | Thiên vị hoặc bất lợi nhẹ |
| 0,5 đến 0,8 điểm | Trung bình | Xu hướng đáng kể cần theo dõi |
| > 0,8 điểm | Cao | Thiên lệch rõ rệt, khuyến nghị biện pháp khắc phục |

### Cách diễn giải
- **Giá trị dương** (+): trọng tài có xu hướng chấm điểm cao hơn cho vận động viên thuộc câu lạc bộ của mình
- **Giá trị âm** (-): trọng tài có xu hướng khắt khe hơn với vận động viên thuộc câu lạc bộ của mình (bù trừ quá mức)
- Cả hai trường hợp đều là thiên lệch cần được khắc phục

### Mức phạt trên điểm tổng thể

| Mức nghiêm trọng | Mức phạt |
|-------------------|----------|
| Trung tính | 0 điểm |
| Nhẹ | -10 điểm |
| Trung bình | -20 điểm |
| Cao | -30 điểm |

---

## Tiêu Chí 2: Thiên Lệch Quốc Tịch

### Nguyên tắc
Tiêu chí này so sánh điểm trung bình chấm cho các vận động viên có **cùng quốc tịch** với trọng tài so với các vận động viên **mang quốc tịch khác**.

### Cách tính
```
Chênh lệch = Trung bình(điểm cùng quốc tịch) - Trung bình(điểm quốc tịch khác)
```

### Ngưỡng phát hiện

| Chênh lệch (giá trị tuyệt đối) | Mức nghiêm trọng | Diễn giải |
|---------------------------------|-------------------|-----------|
| < 0,2 điểm | Trung tính | Không phát hiện thiên lệch |
| 0,2 đến 0,4 điểm | Nhẹ | Thiên vị hoặc bất lợi nhẹ |
| 0,4 đến 0,6 điểm | Trung bình | Xu hướng đáng kể |
| > 0,6 điểm | Cao | Thiên lệch rõ rệt |

### Cách diễn giải
- **Ngưỡng nghiêm ngặt hơn** so với thiên lệch câu lạc bộ, vì quốc tịch không nên có bất kỳ ảnh hưởng nào đến việc chấm điểm kỹ thuật
- **Giá trị dương**: thiên vị đối với quốc tịch của mình
- **Giá trị âm**: quá khắt khe đối với quốc tịch của mình

### Mức phạt trên điểm tổng thể

| Mức nghiêm trọng | Mức phạt |
|-------------------|----------|
| Trung tính | 0 điểm |
| Nhẹ | -8 điểm |
| Trung bình | -16 điểm |
| Cao | -25 điểm |

---

## Tiêu Chí 3: Thiên Lệch Vị Thế Chấm Điểm

### Nguyên tắc
Tiêu chí này so sánh **điểm trung bình tổng thể** của một trọng tài so với **điểm trung bình của tất cả trọng tài** trong cuộc thi. Tiêu chí này phát hiện các trọng tài có hệ thống quá rộng lượng hoặc quá khắt khe.

### Cách tính
```
Chênh lệch = Trung bình(tất cả điểm của trọng tài) - Trung bình(tất cả điểm của mọi trọng tài)
```

### Ngưỡng phát hiện

| Chênh lệch (giá trị tuyệt đối) | Mức nghiêm trọng | Diễn giải |
|---------------------------------|-------------------|-----------|
| < 0,2 điểm | Trung tính | Nằm trong mức trung bình, chấm điểm đã hiệu chuẩn |
| 0,2 đến 0,4 điểm | Nhẹ | Hơi rộng lượng hoặc hơi khắt khe |
| 0,4 đến 0,6 điểm | Trung bình | Rộng lượng hoặc khắt khe đáng kể |
| > 0,6 điểm | Cao | Rất rộng lượng hoặc rất khắt khe |

### Cách diễn giải
- **Giá trị dương** (+): trọng tài có hệ thống chấm điểm cao hơn mức trung bình (rộng lượng)
- **Giá trị âm** (-): trọng tài có hệ thống chấm điểm thấp hơn mức trung bình (khắt khe)
- Một trọng tài giỏi nằm trong phạm vi trung tính (chênh lệch < 0,2 điểm)

### Mức phạt trên điểm tổng thể

| Mức nghiêm trọng | Mức phạt |
|-------------------|----------|
| Trung tính | 0 điểm |
| Nhẹ | -5 điểm |
| Trung bình | -12 điểm |
| Cao | -20 điểm |

---

## Tiêu Chí 4: Sự Đồng Thuận Với Đồng Nghiệp

### Nguyên tắc
Tiêu chí này đo lường mức độ điểm số của một trọng tài **phù hợp với điểm của các trọng tài khác** cho cùng một bài biểu diễn. Một trọng tài có điểm liên tục khác biệt so với đồng nghiệp có thể gặp vấn đề về hiệu chuẩn hoặc thiên lệch.

### Cách tính
Cho mỗi bài biểu diễn được trọng tài chấm điểm:
```
Trung bình của các trọng tài khác = Trung bình(điểm của các trọng tài khác cho bài biểu diễn này)
Độ lệch = |Điểm của trọng tài - Trung bình của các trọng tài khác|
Mức đồng thuận riêng lẻ = max(0, 100 - (Độ lệch x 20))
```

**Điểm đồng thuận tổng thể** là trung bình cộng của tất cả các mức đồng thuận riêng lẻ.

### Diễn giải

| Mức đồng thuận | Ý nghĩa |
|----------------|----------|
| **90-100%** | Đồng thuận xuất sắc, chấm điểm rất nhất quán |
| **75-89%** | Đồng thuận tốt |
| **60-74%** | Đồng thuận chấp nhận được nhưng cần cải thiện |
| **< 60%** | Đồng thuận thấp, **kích hoạt cảnh báo** |

### Ảnh hưởng đến điểm tổng thể
Mức đồng thuận ảnh hưởng đến điểm khách quan thông qua cơ chế thưởng/phạt:
```
Điều chỉnh = (Mức đồng thuận - 50) / 2
```
- Mức đồng thuận 100%: thưởng +25 điểm
- Mức đồng thuận 50%: không thưởng không phạt
- Mức đồng thuận 0%: phạt -25 điểm

### Điều kiện
- Yêu cầu tối thiểu **3 bài biểu diễn** đã chấm điểm để phép tính có ý nghĩa thống kê
- Chỉ tính các điểm thực tế (không tính điểm luyện tập)

---

## Hệ Thống Cảnh Báo

Các cảnh báo được tự động tạo ra trong những trường hợp sau:

| Điều kiện | Cảnh báo |
|-----------|----------|
| Thiên lệch câu lạc bộ mức trung bình hoặc cao | "Phát hiện thiên lệch câu lạc bộ" kèm giá trị chênh lệch |
| Thiên lệch quốc tịch mức trung bình hoặc cao | "Phát hiện thiên lệch quốc tịch" kèm giá trị chênh lệch |
| Chỉ khi vị thế chấm điểm ở mức cao | "Vị thế cực đoan" kèm độ lệch so với mức trung bình |
| Mức đồng thuận < 60% | "Mức đồng thuận thấp với các trọng tài khác" |

Các cảnh báo được hiển thị trên trang chi tiết của từng trọng tài trong giao diện phân tích.

---

## Bảng Vinh Danh Các Trọng Tài Khách Quan Nhất

Sau khi phân tích, một **bảng xếp hạng** vinh danh 3 trọng tài đạt điểm khách quan cao nhất:

- **Hạng 1 (Vàng)**: Điểm khách quan cao nhất
- **Hạng 2 (Bạc)**: Điểm khách quan cao thứ hai
- **Hạng 3 (Đồng)**: Điểm khách quan cao thứ ba

Bảng xếp hạng này tôn vinh sự công bằng và khuyến khích tất cả trọng tài cùng nâng cao trình độ.

---

## Khuyến Nghị Dành Cho Trọng Tài

### Để cải thiện điểm khách quan

1. **Thiên lệch câu lạc bộ**: Hãy đặc biệt chú ý khi chấm điểm cho vận động viên thuộc câu lạc bộ của mình. Áp dụng các tiêu chí kỹ thuật giống nhau như đối với các vận động viên khác.

2. **Thiên lệch quốc tịch**: Chỉ tập trung vào kỹ thuật và phần trình diễn. Quốc tịch của vận động viên không được ảnh hưởng đến đánh giá của bạn.

3. **Vị thế chấm điểm**: Hiệu chuẩn điểm số theo đúng các tiêu chí đã quy định. Không quá rộng lượng, cũng không quá khắt khe. Khi nghi ngờ, hãy tham khảo thang điểm chính thức.

4. **Mức đồng thuận**: Nếu điểm của bạn thường xuyên khác biệt so với đồng nghiệp, điều đó có thể cho thấy vấn đề trong việc hiểu các tiêu chí đánh giá. Hãy tham gia các buổi hiệu chuẩn chấm điểm.

### Thực hành tốt

- Chấm điểm mỗi bài biểu diễn một cách độc lập, không xem điểm của các trọng tài khác
- Sử dụng toàn bộ dải thang điểm
- Không thay đổi điểm sau khi đã xem điểm của người khác
- Dành thời gian đánh giá riêng từng tiêu chí
- Khi mệt mỏi, hãy nghỉ ngơi để duy trì sự tập trung

---

## Quyền Truy Cập và Bảo Mật

- Phân tích tính khách quan chỉ dành cho **ban tổ chức cuộc thi** và **quản trị viên liên đoàn**
- Mỗi trọng tài có thể xem **kết quả của chính mình**
- Dữ liệu được tính toán **theo thời gian thực** từ các điểm số hiện có (không có dữ liệu khách quan nào được lưu trữ vĩnh viễn)
- Phân tích yêu cầu đủ số lượng điểm để đảm bảo độ tin cậy (tối thiểu 3 bài biểu diễn cho mức đồng thuận)
