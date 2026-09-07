"""Generate E0.5 PDFs for duplicate-pair relations not covered by E0.4."""
from __future__ import annotations

from pathlib import Path
import unicodedata

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    NumberObject,
    TextStringObject,
)
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas

from generate_duplicate_pdf_fixtures import (
    OUTPUT_DIR,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    draw_invisible_text,
    new_canvas,
    register_fonts,
)


def draw_shell_page(
    pdf: canvas.Canvas,
    fixture_id: str,
    title: str,
    *,
    page_number: int,
    page_total: int,
) -> None:
    pdf.setFillColor(HexColor("#F5F7FA"))
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#16324F"))
    pdf.rect(0, PAGE_HEIGHT - 86, PAGE_WIDTH, 86, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("FixtureArialBold", 17)
    pdf.drawString(42, PAGE_HEIGHT - 50, title)
    pdf.setFont("FixtureArial", 8)
    pdf.drawRightString(PAGE_WIDTH - 42, PAGE_HEIGHT - 50, fixture_id)

    pdf.setFillColor(HexColor("#FFF4D6"))
    pdf.roundRect(42, PAGE_HEIGHT - 132, PAGE_WIDTH - 84, 26, 5, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#6B4B00"))
    pdf.setFont("FixtureArialBold", 8.5)
    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        PAGE_HEIGHT - 123,
        "SYNTHETIC SECURITY FIXTURE - KHÔNG PHẢI TÀI LIỆU THẬT",
    )

    pdf.setStrokeColor(HexColor("#CCD6E0"))
    pdf.line(42, 64, PAGE_WIDTH - 42, 64)
    pdf.setFillColor(HexColor("#5A6875"))
    pdf.setFont("FixtureArial", 8)
    pdf.drawString(42, 48, "Quarantine-only fixture. Không đưa vào content DB hoặc serving index.")
    pdf.drawRightString(PAGE_WIDTH - 42, 48, f"Trang {page_number}/{page_total}")


def draw_body(pdf: canvas.Canvas, heading: str, lines: tuple[str, ...]) -> None:
    pdf.setFillColor(HexColor("#1E2933"))
    pdf.setFont("FixtureArialBold", 13)
    pdf.drawString(56, PAGE_HEIGHT - 184, heading)
    pdf.setFont("FixtureArial", 11)
    for index, line in enumerate(lines):
        pdf.drawString(56, PAGE_HEIGHT - 224 - index * 34, line)


def draw_review_box(pdf: canvas.Canvas, label: str, message: str, *, tone: str = "info") -> None:
    palette = {
        "safe": (HexColor("#E8F5EE"), HexColor("#19613B")),
        "warning": (HexColor("#FFF0F0"), HexColor("#A61B1B")),
        "info": (HexColor("#EAF2FF"), HexColor("#174EA6")),
    }
    background, foreground = palette[tone]
    pdf.setFillColor(background)
    pdf.roundRect(56, PAGE_HEIGHT - 460, PAGE_WIDTH - 112, 64, 7, fill=1, stroke=0)
    pdf.setFillColor(foreground)
    pdf.setFont("FixtureArialBold", 9)
    pdf.drawString(70, PAGE_HEIGHT - 420, label)
    pdf.setFont("FixtureArial", 9)
    pdf.drawString(70, PAGE_HEIGHT - 442, message)


def make_pdf(
    filename: str,
    fixture_id: str,
    title: str,
    pages: tuple[tuple[str, tuple[str, ...]], ...],
    *,
    author: str,
    subject: str,
    review: tuple[str, str, str] | None = None,
    watermark: str | None = None,
    visible_marker: str | None = None,
    link_url: str | None = None,
    hidden_marker: str | None = None,
) -> Path:
    path = OUTPUT_DIR / filename
    pdf = new_canvas(path, title=title, author=author, subject=subject)
    for page_number, (heading, lines) in enumerate(pages, start=1):
        draw_shell_page(
            pdf,
            fixture_id,
            title,
            page_number=page_number,
            page_total=len(pages),
        )
        draw_body(pdf, heading, lines)
        if watermark:
            pdf.saveState()
            pdf.setFillColor(HexColor("#D6E4F0"))
            pdf.setFont("FixtureArialBold", 30)
            pdf.translate(PAGE_WIDTH / 2, PAGE_HEIGHT / 2)
            pdf.rotate(28)
            pdf.drawCentredString(0, 0, watermark)
            pdf.restoreState()
        if visible_marker:
            pdf.setFillColor(HexColor("#A61B1B"))
            pdf.setFont("FixtureArialBold", 9)
            pdf.drawString(70, PAGE_HEIGHT - 505, visible_marker)
            if link_url:
                pdf.linkURL(
                    link_url,
                    (66, PAGE_HEIGHT - 514, PAGE_WIDTH - 66, PAGE_HEIGHT - 490),
                    relative=0,
                    thickness=1,
                    color=HexColor("#D92D20"),
                )
        if review:
            draw_review_box(pdf, review[0], review[1], tone=review[2])
        if hidden_marker:
            draw_invisible_text(pdf, hidden_marker, x=60, y=82)
        pdf.showPage()
    pdf.save()
    return path


def add_hidden_text_annotation(source: Path, target: Path, marker: str) -> Path:
    reader = PdfReader(source)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    annotation = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Text"),
            NameObject("/Rect"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(0), FloatObject(0)]),
            NameObject("/Contents"): TextStringObject(marker),
            NameObject("/F"): NumberObject(2),
        }
    )
    annotation_ref = writer._add_object(annotation)
    page = writer.pages[0]
    annotations = page.get("/Annots")
    if annotations is None:
        annotations = ArrayObject()
        page[NameObject("/Annots")] = annotations
    annotations.append(annotation_ref)
    with target.open("wb") as stream:
        writer.write(stream)
    return target


def generate() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    outputs: list[Path] = []

    unicode_heading = "Chuẩn hóa văn bản"
    unicode_nfc = "Dữ liệu được chuẩn hóa trước khi so sánh."
    unicode_nfd = unicodedata.normalize("NFD", unicode_nfc)
    outputs.append(make_pdf(
        "F11-dup006-unicode-nfc.pdf", "DUP-006", "Chuẩn hóa Unicode",
        ((unicode_heading, (unicode_nfc, "NFC là representation chuẩn của fixture bên trái.")),),
        author="Synthetic Lecturer 1", subject="Unicode NFC relation",
        review=("UNICODE PAIR", "Hai file phải được so sau Unicode normalization.", "info"),
    ))
    outputs.append(make_pdf(
        "F12-dup006-unicode-nfd.pdf", "DUP-006", "Chuẩn hóa Unicode",
        ((unicode_heading, (unicode_nfd, "NFC là representation chuẩn của fixture bên trái.")),),
        author="Synthetic Lecturer 2", subject="Unicode NFD relation",
        review=("UNICODE PAIR", "Hai file phải được so sau Unicode normalization.", "info"),
    ))

    outputs.append(make_pdf(
        "F13-dup007-punctuation-clean.pdf", "DUP-007", "Mảng và bộ nhớ",
        (("Khái niệm", ("Mảng: các phần tử được lưu liên tiếp.", "Ví dụ này hoàn toàn synthetic.")),),
        author="Synthetic Lecturer 1", subject="Punctuation clean",
        review=("CANONICAL TEXT", "Punctuation/spacing là diagnostic, không auto-merge.", "info"),
    ))
    outputs.append(make_pdf(
        "F14-dup007-punctuation-spacing-delta.pdf", "DUP-007", "Mảng và bộ nhớ",
        (("Khái niệm", ("Mảng - các phần tử được lưu  liên tiếp.", "Ví dụ này hoàn toàn synthetic.")),),
        author="Synthetic Lecturer 2", subject="Punctuation and whitespace delta",
        review=("CANONICAL TEXT", "Punctuation/spacing là diagnostic, không auto-merge.", "info"),
    ))

    ordered_pages = (
        ("Khái niệm", ("Hàng đợi tuân theo nguyên tắc vào trước ra trước.",)),
        ("Ví dụ", ("Bộ đệm tác vụ là một ví dụ minh họa.",)),
        ("Bài tập", ("Mô phỏng ba thao tác thêm và lấy phần tử.",)),
    )
    reordered_pages = (ordered_pages[0], ordered_pages[2], ordered_pages[1])
    outputs.append(make_pdf(
        "F15-dup009-page-order-original.pdf", "DUP-009", "Hàng đợi - ba phần", ordered_pages,
        author="Synthetic Lecturer 1", subject="Original page order",
    ))
    outputs.append(make_pdf(
        "F16-dup009-page-order-reordered.pdf", "DUP-009", "Hàng đợi - ba phần", reordered_pages,
        author="Synthetic Lecturer 2", subject="Reordered pages",
    ))

    header_pages = (("Danh sách liên kết", ("Danh sách liên kết gồm các nút nối với nhau.", "Mỗi nút giữ dữ liệu và liên kết kế tiếp.")),)
    outputs.append(make_pdf(
        "F17-dup010-header-clean.pdf", "DUP-010", "Danh sách liên kết", header_pages,
        author="Synthetic Lecturer 1", subject="Clean header relation",
        review=("HEADER PAIR", "Core content giống nhau; repeated header được tách riêng.", "info"),
    ))
    outputs.append(make_pdf(
        "F18-dup010-watermark-header-delta.pdf", "DUP-010", "Danh sách liên kết", header_pages,
        author="Synthetic Lecturer 2", subject="Watermark header delta",
        review=("HEADER PAIR", "Core content giống nhau; repeated header được tách riêng.", "info"),
        watermark="KHOA X - HỌC KỲ 1",
    ))

    outputs.append(make_pdf(
        "F19-dup011-revision-v1.pdf", "DUP-011", "Cây tìm kiếm nhị phân",
        (("Phiên bản 1", ("Phần này trình bày tìm kiếm và chèn nút.", "Không có nội dung về phép xóa.")),),
        author="Synthetic Lecturer 1", subject="Revision v1",
        review=("VERSION V1", "Giữ immutable khi có revision mới.", "safe"),
    ))
    outputs.append(make_pdf(
        "F20-dup011-revision-v2-added-section.pdf", "DUP-011", "Cây tìm kiếm nhị phân",
        (("Phiên bản 2", ("Phần này trình bày tìm kiếm và chèn nút.", "Bổ sung mục mới: phép xóa nút khỏi cây.")),),
        author="Synthetic Lecturer 1", subject="Revision v2 with added section",
        review=("VERSION V2", "Substantive addition cần new-version review.", "safe"),
    ))

    outputs.append(make_pdf(
        "F21-dup012-claim-on.pdf", "DUP-012", "Phân tích độ phức tạp",
        (("Claim ban đầu", ("Độ phức tạp của thao tác trong ví dụ là O(n).",)),),
        author="Synthetic Lecturer 1", subject="Academic claim O(n)",
        review=("CLAIM CHANGE", "Span nhỏ nhưng ý nghĩa học thuật lớn.", "warning"),
    ))
    outputs.append(make_pdf(
        "F22-dup012-claim-ologn.pdf", "DUP-012", "Phân tích độ phức tạp",
        (("Claim đã sửa", ("Sau khi đổi cấu trúc dữ liệu, độ phức tạp là O(log n).",)),),
        author="Synthetic Lecturer 1", subject="Academic claim O(log n)",
        review=("CLAIM CHANGE", "Span nhỏ nhưng ý nghĩa học thuật lớn.", "warning"),
    ))

    outputs.append(make_pdf(
        "F23-dup014-semester-hk1.pdf", "DUP-014", "Bài tập học kỳ",
        (("Học kỳ 1", ("Bài tập dùng bộ dữ liệu minh họa A.", "Deadline synthetic: tuần 5.")),),
        author="Synthetic Lecturer 1", subject="Semester HK1 variant",
        review=("SEMESTER VARIANT", "Không auto-merge assignment context.", "safe"),
    ))
    outputs.append(make_pdf(
        "F24-dup014-semester-hk2.pdf", "DUP-014", "Bài tập học kỳ",
        (("Học kỳ 2", ("Bài tập dùng bộ dữ liệu minh họa B.", "Deadline synthetic: tuần 7.")),),
        author="Synthetic Lecturer 2", subject="Semester HK2 variant",
        review=("SEMESTER VARIANT", "Không auto-merge assignment context.", "safe"),
    ))

    boilerplate = "Mục tiêu môn học. Quy định đánh giá."
    outputs.append(make_pdf(
        "F25-dup016-boilerplate-data-structures.pdf", "DUP-016", "Đề cương môn học",
        (("Thông tin chung", (boilerplate, "Nội dung cốt lõi: cấu trúc dữ liệu và giải thuật.")),),
        author="Synthetic Lecturer 1", subject="Data structures syllabus",
        review=("SHARED BOILERPLATE", "Core topic khác nên phải giữ riêng.", "warning"),
    ))
    outputs.append(make_pdf(
        "F26-dup016-boilerplate-databases.pdf", "DUP-016", "Đề cương môn học",
        (("Thông tin chung", (boilerplate, "Nội dung cốt lõi: cơ sở dữ liệu và truy vấn.")),),
        author="Synthetic Lecturer 2", subject="Database syllabus",
        review=("SHARED BOILERPLATE", "Core topic khác nên phải giữ riêng.", "warning"),
    ))

    annotation_pages = (("Bảng băm", ("Băm ánh xạ khóa tới vị trí lưu trữ.", "Nội dung nhìn thấy của hai file giống nhau.")),)
    annotation_base = make_pdf(
        "F27-dup019-annotation-clean.pdf", "DUP-019", "Bảng băm", annotation_pages,
        author="Synthetic Lecturer 1", subject="Clean annotation relation",
        review=("ANNOTATION PAIR", "Annotation inventory là một security surface.", "info"),
    )
    outputs.append(annotation_base)
    outputs.append(add_hidden_text_annotation(
        annotation_base,
        OUTPUT_DIR / "F28-dup019-hidden-annotation-delta.pdf",
        "[SYNTHETIC_AGENT_OVERRIDE_ANNOTATION]",
    ))

    metadata_pages = (("Heap", ("Heap hỗ trợ lấy phần tử ưu tiên.", "Nội dung nhìn thấy của hai file giống nhau.")),)
    outputs.append(make_pdf(
        "F29-dup020-metadata-clean.pdf", "DUP-020", "Heap", metadata_pages,
        author="Synthetic Lecturer 1", subject="Cấu trúc dữ liệu",
        review=("METADATA PAIR", "Metadata không phải instruction đáng tin.", "info"),
    ))
    outputs.append(make_pdf(
        "F30-dup020-metadata-instruction-delta.pdf", "DUP-020", "Heap", metadata_pages,
        author="Synthetic Lecturer 2", subject="[SYNTHETIC_SYSTEM_OVERRIDE_METADATA]",
        review=("METADATA PAIR", "Metadata không phải instruction đáng tin.", "info"),
    ))

    url_pages = (("Duyệt theo chiều rộng", ("Duyệt theo chiều rộng dùng một hàng đợi.", "Không cần truy cập mạng để đọc fixture.")),)
    outputs.append(make_pdf(
        "F31-dup021-url-clean.pdf", "DUP-021", "Duyệt đồ thị", url_pages,
        author="Synthetic Lecturer 1", subject="Clean URL relation",
        review=("URL PAIR", "Mọi URL mới phải được inventory và review.", "warning"),
    ))
    outputs.append(make_pdf(
        "F32-dup021-external-url-delta.pdf", "DUP-021", "Duyệt đồ thị", url_pages,
        author="Synthetic Lecturer 2", subject="External URL delta",
        review=("URL PAIR", "Mọi URL mới phải được inventory và review.", "warning"),
        visible_marker="[SYNTHETIC_EXTERNAL_EXFIL_URL]",
        link_url="https://example.invalid/synthetic-exfil-marker",
    ))

    invisible_pages = (("Bảng băm", ("Bảng băm xử lý va chạm bằng danh sách liên kết.", "Nội dung nhìn thấy của hai file giống nhau.")),)
    outputs.append(make_pdf(
        "F33-dup022-unicode-invisible-clean.pdf", "DUP-022", "Unicode security", invisible_pages,
        author="Synthetic Lecturer 1", subject="Clean Unicode invisible relation",
        review=("UNICODE SECURITY", "Format/control characters phải được inventory.", "warning"),
    ))
    outputs.append(make_pdf(
        "F34-dup022-unicode-invisible-delta.pdf", "DUP-022", "Unicode security", invisible_pages,
        author="Synthetic Lecturer 2", subject="Unicode invisible marker delta",
        review=("UNICODE SECURITY", "Format/control characters phải được inventory.", "warning"),
        hidden_marker="[\u200bSYNTHETIC_INVISIBLE_INSTRUCTION\u200b]",
    ))

    expected = {f"F{index:02d}" for index in range(11, 35)}
    observed = {path.name.split("-", 1)[0] for path in outputs}
    if observed != expected or len(outputs) != 24:
        raise RuntimeError(f"Unexpected E0.5 output set: {sorted(path.name for path in outputs)}")
    return outputs


if __name__ == "__main__":
    for output in generate():
        print(output.relative_to(OUTPUT_DIR.parents[2]))
