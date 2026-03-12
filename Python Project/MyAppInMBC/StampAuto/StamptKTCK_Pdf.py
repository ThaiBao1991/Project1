import fitz
import sys
import os

# Lấy danh sách PDF từ command line
pdf_paths = sys.argv[1:]
if not pdf_paths:
    print("Vui lòng truyền đường dẫn file PDF.")
    sys.exit(1)

stamp_image = r"C:\Users\12953 bao\Desktop\condauBao.png"

# Tạo PDF nhỏ chứa stamp
stamp_doc = fitz.open()
img = fitz.Pixmap(stamp_image)
img_width, img_height = img.width, img.height

# Tạo trang PDF tạm bằng kích thước ảnh gốc (sẽ scale sau khi chèn)
stamp_page = stamp_doc.new_page(width=img_width, height=img_height)
stamp_page.insert_image(fitz.Rect(0, 0, img_width, img_height), filename=stamp_image)
stamp_pdf_path = r"C:\Users\12953 bao\Desktop\stamp_temp.pdf"
stamp_doc.save(stamp_pdf_path)
stamp_doc.close()

# Xử lý từng PDF
for pdf_path in pdf_paths:
    if not os.path.exists(pdf_path):
        print(f"File không tồn tại: {pdf_path}")
        continue

    doc = fitz.open(pdf_path)

    for page in doc:
        text_instances = page.search_for("Xác nhận")
        for inst in text_instances:
            x0, y0, x1, y1 = inst

            # Scale stamp dựa trên width chữ “Xác nhận”
            width_text = x1 - x0
            scale = width_text / img_width
            w = img_width * scale
            h = img_height * scale

            # Rectangle chèn stamp phía dưới chữ, cách 2 điểm
            stamp_rect = fitz.Rect(x0, y1 + 2, x0 + w, y1 + 2 + h)

            # Chèn PDF stamp
            stamp_doc = fitz.open(stamp_pdf_path)
            page.show_pdf_page(stamp_rect, stamp_doc, 0)
            stamp_doc.close()

    # Lưu file mới
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_pdf = os.path.join(os.path.dirname(pdf_path), f"{base_name}_stamped.pdf")
    doc.save(output_pdf)
    doc.close()
    print(f"Đã đóng dấu xong: {output_pdf}")

print("Hoàn tất tất cả file!")
