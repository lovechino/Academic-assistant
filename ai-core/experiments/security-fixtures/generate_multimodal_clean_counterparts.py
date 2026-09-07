"""Generate clean matched counterparts for the E0.4 image/OCR security fixtures."""
from __future__ import annotations

from PIL import Image, ImageDraw

from generate_duplicate_pdf_fixtures import (
    OUTPUT_DIR,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    TMP_DIR,
    draw_shell,
    finish,
    image_font,
    new_canvas,
    register_fonts,
)


def make_image_only_clean_counterpart():
    image_path = TMP_DIR / "image-only-clean-content.png"
    image = Image.new("RGB", (1400, 820), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((40, 40, 1360, 780), radius=28, fill="#FFFFFF", outline="#CBD5E1", width=4)
    draw.text((90, 95), "Minh họa hàng đợi", font=image_font(52, bold=True), fill="#16324F")
    draw.text((90, 190), "Phần tử vào trước sẽ được lấy ra trước.", font=image_font(34), fill="#1E2933")
    image.save(image_path)

    path = OUTPUT_DIR / "F35-dup023-image-only-clean-counterpart.pdf"
    pdf = new_canvas(path, title="Bài giảng chương 1", author="Synthetic Lecturer 2", subject="Image-only marker")
    draw_shell(pdf, "F09", "Bài giảng chương 1")
    pdf.drawImage(str(image_path), 56, 150, width=PAGE_WIDTH - 112, height=410, preserveAspectRatio=True, anchor="c")
    finish(pdf)
    return path


def make_ocr_clean_counterpart():
    image_path = TMP_DIR / "ocr-safe-render-clean-counterpart.png"
    image = Image.new("RGB", (1400, 700), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((80, 100), "Sắp xếp trộn", font=image_font(58, bold=True), fill="#16324F")
    draw.text((80, 220), "Thuật toán chia bài toán thành các bài toán con.", font=image_font(34), fill="#1E2933")
    draw.text((80, 300), "Nội dung nhìn thấy là dữ liệu tổng hợp an toàn.", font=image_font(30), fill="#1E2933")
    image.save(image_path)

    path = OUTPUT_DIR / "F36-dup024-ocr-text-clean-counterpart.pdf"
    pdf = new_canvas(
        path,
        title="Sắp xếp trộn",
        author="Synthetic Lecturer 2",
        subject="OCR text-layer mismatch marker",
    )
    draw_shell(pdf, "F10", "Sắp xếp trộn")
    pdf.drawImage(str(image_path), 56, 190, width=PAGE_WIDTH - 112, height=350, preserveAspectRatio=True, anchor="c")
    finish(pdf)
    return path


def generate():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    outputs = [make_image_only_clean_counterpart(), make_ocr_clean_counterpart()]
    if {path.name.split("-", 1)[0] for path in outputs} != {"F35", "F36"}:
        raise RuntimeError("Unexpected E0.6 output set")
    return outputs


if __name__ == "__main__":
    for output in generate():
        print(output.relative_to(OUTPUT_DIR.parents[2]))
