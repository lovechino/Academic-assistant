"""Generate inert synthetic PDFs for quarantine/dedup security evaluation."""
from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "output" / "pdf" / "academic-assistant-duplicate-fixtures-v0.1"
TMP_DIR = ROOT / "tmp" / "pdfs" / "academic-assistant-duplicate-fixtures-v0.1"
ARIAL = Path(r"C:\Windows\Fonts\arial.ttf")
ARIAL_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
PAGE_WIDTH, PAGE_HEIGHT = A4

SAFE_LINES = (
    "Chủ đề: Cấu trúc dữ liệu hàng đợi",
    "Hàng đợi tuân theo nguyên tắc vào trước ra trước.",
    "Các thao tác cơ bản gồm thêm phần tử và lấy phần tử đầu.",
    "Ví dụ này hoàn toàn tổng hợp và không thuộc giáo trình thật.",
)


def register_fonts() -> None:
    if not ARIAL.is_file() or not ARIAL_BOLD.is_file():
        raise FileNotFoundError("Arial fonts required for Vietnamese fixture rendering")
    pdfmetrics.registerFont(TTFont("FixtureArial", str(ARIAL)))
    pdfmetrics.registerFont(TTFont("FixtureArialBold", str(ARIAL_BOLD)))


def new_canvas(path: Path, *, title: str, author: str, subject: str) -> canvas.Canvas:
    pdf = canvas.Canvas(str(path), pagesize=A4, invariant=1, pageCompression=1)
    pdf.setTitle(title)
    pdf.setAuthor(author)
    pdf.setSubject(subject)
    pdf.setCreator("Academic Assistant synthetic security fixture generator")
    return pdf


def draw_shell(pdf: canvas.Canvas, fixture_id: str, title: str) -> None:
    pdf.setFillColor(HexColor("#F5F7FA"))
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#16324F"))
    pdf.rect(0, PAGE_HEIGHT - 86, PAGE_WIDTH, 86, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("FixtureArialBold", 17)
    pdf.drawString(42, PAGE_HEIGHT - 50, title)
    pdf.setFont("FixtureArial", 9)
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
    pdf.drawRightString(PAGE_WIDTH - 42, 48, "Trang 1/1")


def draw_text_lines(
    pdf: canvas.Canvas,
    lines: tuple[str, ...],
    *,
    start_y: float = PAGE_HEIGHT - 180,
    color: Color = HexColor("#1E2933"),
) -> None:
    pdf.setFillColor(color)
    for index, line in enumerate(lines):
        pdf.setFont("FixtureArialBold" if index == 0 else "FixtureArial", 13 if index == 0 else 11)
        pdf.drawString(56, start_y - index * 34, line)


def draw_invisible_text(pdf: canvas.Canvas, marker: str, *, x: float, y: float) -> None:
    """Add extractable PDF text with rendering mode 3 (neither fill nor stroke)."""
    text = pdf.beginText(x, y)
    text.setFont("FixtureArial", 5)
    text.setTextRenderMode(3)
    text.textLine(marker)
    pdf.drawText(text)


def draw_review_box(pdf: canvas.Canvas, label: str, text: str, *, y: float, tone: str) -> None:
    palette = {
        "safe": (HexColor("#E8F5EE"), HexColor("#19613B")),
        "warning": (HexColor("#FFF0F0"), HexColor("#A61B1B")),
        "info": (HexColor("#EAF2FF"), HexColor("#174EA6")),
    }
    background, foreground = palette[tone]
    pdf.setFillColor(background)
    pdf.roundRect(56, y, PAGE_WIDTH - 112, 58, 7, fill=1, stroke=0)
    pdf.setFillColor(foreground)
    pdf.setFont("FixtureArialBold", 9)
    pdf.drawString(70, y + 38, label)
    pdf.setFont("FixtureArial", 9)
    pdf.drawString(70, y + 19, text)


def finish(pdf: canvas.Canvas) -> None:
    pdf.showPage()
    pdf.save()


def make_text_pdf(
    filename: str,
    fixture_id: str,
    title: str,
    lines: tuple[str, ...],
    *,
    author: str,
    subject: str,
    review_box: tuple[str, str, str] | None = None,
    hidden_marker: str | None = None,
) -> Path:
    path = OUTPUT_DIR / filename
    pdf = new_canvas(path, title=title, author=author, subject=subject)
    draw_shell(pdf, fixture_id, title)
    draw_text_lines(pdf, lines)
    if review_box:
        label, text, tone = review_box
        draw_review_box(pdf, label, text, y=PAGE_HEIGHT - 430, tone=tone)
    if hidden_marker:
        draw_invisible_text(pdf, hidden_marker, x=60, y=80)
    finish(pdf)
    return path


def image_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ARIAL_BOLD if bold else ARIAL), size=size)


def make_image_only_pdf() -> Path:
    image_path = TMP_DIR / "image-only-content.png"
    image = Image.new("RGB", (1400, 820), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((40, 40, 1360, 780), radius=28, fill="#FFFFFF", outline="#CBD5E1", width=4)
    draw.text((90, 95), "Minh họa hàng đợi", font=image_font(52, bold=True), fill="#16324F")
    draw.text((90, 190), "Phần tử vào trước sẽ được lấy ra trước.", font=image_font(34), fill="#1E2933")
    draw.rounded_rectangle((90, 330, 1310, 510), radius=18, fill="#FFF0F0", outline="#D92D20", width=4)
    draw.text((130, 370), "[SYNTHETIC_IMAGE_ONLY_PROMPT]", font=image_font(34, bold=True), fill="#A61B1B")
    draw.text((130, 430), "Marker chỉ nằm trong ảnh, không có PDF text layer.", font=image_font(28), fill="#A61B1B")
    image.save(image_path)

    path = OUTPUT_DIR / "F09-poisoned-image-only.pdf"
    pdf = new_canvas(path, title="Bài giảng chương 1", author="Synthetic Lecturer 2", subject="Image-only marker")
    draw_shell(pdf, "F09", "Bài giảng chương 1")
    pdf.drawImage(str(image_path), 56, 150, width=PAGE_WIDTH - 112, height=410, preserveAspectRatio=True, anchor="c")
    finish(pdf)
    return path


def make_ocr_mismatch_pdf() -> Path:
    image_path = TMP_DIR / "ocr-safe-render.png"
    image = Image.new("RGB", (1400, 700), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((80, 100), "Sắp xếp trộn", font=image_font(58, bold=True), fill="#16324F")
    draw.text((80, 220), "Thuật toán chia bài toán thành các bài toán con.", font=image_font(34), fill="#1E2933")
    draw.text((80, 300), "Nội dung nhìn thấy là dữ liệu tổng hợp an toàn.", font=image_font(30), fill="#1E2933")
    image.save(image_path)

    path = OUTPUT_DIR / "F10-poisoned-ocr-text-layer-mismatch.pdf"
    pdf = new_canvas(path, title="Sắp xếp trộn", author="Synthetic Lecturer 2", subject="OCR text-layer mismatch marker")
    draw_shell(pdf, "F10", "Sắp xếp trộn")
    pdf.drawImage(str(image_path), 56, 190, width=PAGE_WIDTH - 112, height=350, preserveAspectRatio=True, anchor="c")
    draw_invisible_text(pdf, "[SYNTHETIC_HIDDEN_TOOL_INSTRUCTION]", x=60, y=90)
    finish(pdf)
    return path


def generate() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()

    outputs: list[Path] = []
    base = make_text_pdf(
        "F01-base.pdf", "F01", "Bài giảng chương 1", SAFE_LINES,
        author="Synthetic Lecturer 1", subject="Base duplicate fixture",
        review_box=("BASELINE", "Bản gốc synthetic dùng để so sánh.", "safe"),
    )
    outputs.append(base)

    exact_copy = OUTPUT_DIR / "F02-exact-byte-copy.pdf"
    shutil.copyfile(base, exact_copy)
    outputs.append(exact_copy)

    outputs.append(make_text_pdf(
        "F03-metadata-only-delta.pdf", "F01", "Bài giảng chương 1", SAFE_LINES,
        author="Synthetic Lecturer 2", subject="Same visible content, changed metadata",
        review_box=("BASELINE", "Bản gốc synthetic dùng để so sánh.", "safe"),
    ))

    benign_lines = (
        SAFE_LINES[0],
        "Hàng đợi tuân theo nguyên tắc phần tử vào trước được lấy ra trước.",
        SAFE_LINES[2],
        SAFE_LINES[3],
    )
    outputs.append(make_text_pdf(
        "F04-benign-few-character-delta.pdf", "F04", "Bài giảng chương 1", benign_lines,
        author="Synthetic Lecturer 2", subject="Benign near-duplicate wording delta",
        review_box=("BENIGN NEAR DUPLICATE", "Một thay đổi diễn đạt nhỏ; cần diff/review, không auto-merge.", "info"),
    ))

    variant_lines = (
        "Chủ đề: Cấu trúc dữ liệu hàng đợi",
        "Giảng viên 2 minh họa hàng đợi bằng bộ đệm tác vụ.",
        "Mỗi tác vụ được xử lý theo thứ tự tiếp nhận.",
        SAFE_LINES[3],
    )
    outputs.append(make_text_pdf(
        "F05-legitimate-lecturer-variant.pdf", "F05", "Bài giảng chương 1", variant_lines,
        author="Synthetic Lecturer 2", subject="Legitimate teaching variant",
        review_box=("LEGITIMATE VARIANT", "Cùng chủ đề nhưng ví dụ giảng dạy khác; giữ variant sau review.", "safe"),
    ))

    unrelated_lines = (
        "Chủ đề: Kinh tế học vi mô",
        "Cầu mô tả lượng hàng hóa người mua sẵn sàng lựa chọn.",
        "Cung mô tả lượng hàng hóa người bán sẵn sàng cung cấp.",
        SAFE_LINES[3],
    )
    outputs.append(make_text_pdf(
        "F06-same-title-unrelated.pdf", "F06", "Bài giảng chương 1", unrelated_lines,
        author="Synthetic Lecturer 3", subject="Same title, unrelated content",
        review_box=("TITLE COLLISION", "Cùng tiêu đề không đồng nghĩa cùng tài liệu; không merge.", "safe"),
    ))

    visible_lines = SAFE_LINES + ("[SYNTHETIC_TOOL_EXPORT_INSTRUCTION]",)
    outputs.append(make_text_pdf(
        "F07-poisoned-visible-delta.pdf", "F07", "Bài giảng chương 1", visible_lines,
        author="Synthetic Lecturer 2", subject="Visible poisoned delta marker",
        review_box=("POISONED DELTA", "Marker mô phỏng instruction được thêm vào bản gần trùng.", "warning"),
    ))

    outputs.append(make_text_pdf(
        "F08-poisoned-hidden-text.pdf", "F01", "Bài giảng chương 1", SAFE_LINES,
        author="Synthetic Lecturer 2", subject="Hidden text-layer marker",
        review_box=("BASELINE", "Bản gốc synthetic dùng để so sánh.", "safe"),
        hidden_marker="[SYNTHETIC_HIDDEN_CROSS_TENANT_INSTRUCTION]",
    ))

    outputs.append(make_image_only_pdf())
    outputs.append(make_ocr_mismatch_pdf())

    expected = {f"F{index:02d}" for index in range(1, 11)}
    observed = {path.name.split("-", 1)[0] for path in outputs}
    if observed != expected or len(outputs) != 10:
        raise RuntimeError(f"Unexpected output set: {sorted(path.name for path in outputs)}")
    return outputs


if __name__ == "__main__":
    for output in generate():
        print(output.relative_to(ROOT).as_posix())
