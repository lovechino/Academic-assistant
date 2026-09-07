"""Generate E0.9 query/equivalent/conflicting-review-required PDF triplets."""
from __future__ import annotations

from pathlib import Path
import textwrap

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "output" / "pdf" / "academic-assistant-equivalence-triplets-v0.1"
ARIAL = Path(r"C:\Windows\Fonts\arial.ttf")
ARIAL_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
PAGE_WIDTH, PAGE_HEIGHT = A4


TRIPLETS: tuple[dict[str, object], ...] = (
    {
        "triplet_id": "TRI-001",
        "category": "algorithm_mechanism",
        "layout_family": "lecture_card",
        "topic": "Duyệt đồ thị theo chiều rộng",
        "filenames": {
            "query": "E901-graph-traversal-note.pdf",
            "equivalent": "E902-graph-traversal-paraphrase.pdf",
            "conflict": "E903-graph-traversal-mechanism-conflict.pdf",
        },
        "query": (
            "BFS khám phá các đỉnh theo từng lớp từ đỉnh bắt đầu.",
            "Thuật toán dùng hàng đợi để quản lý các đỉnh đang chờ.",
            "Mỗi đỉnh được đánh dấu trước khi đưa vào hàng đợi.",
            "Với danh sách kề, chi phí là O(V + E).",
        ),
        "equivalent": (
            "Duyệt theo chiều rộng mở rộng lần lượt từng mức của đồ thị.",
            "Các đỉnh chưa xử lý được lưu trong một cấu trúc FIFO.",
            "Đánh dấu khi tiếp nhận giúp tránh đưa một đỉnh vào nhiều lần.",
            "Biểu diễn danh sách kề cho độ phức tạp O(V + E).",
        ),
        "conflict": (
            "BFS khám phá các đỉnh theo từng lớp từ đỉnh bắt đầu.",
            "Thuật toán dùng ngăn xếp để quản lý các đỉnh đang chờ.",
            "Mỗi đỉnh được đánh dấu trước khi đưa vào ngăn xếp.",
            "Với danh sách kề, chi phí là O(V + E).",
        ),
    },
    {
        "triplet_id": "TRI-002",
        "category": "definition_constraint",
        "layout_family": "lecture_card",
        "topic": "Cây tìm kiếm nhị phân",
        "filenames": {
            "query": "E904-binary-search-tree-note.pdf",
            "equivalent": "E905-binary-search-tree-paraphrase.pdf",
            "conflict": "E906-binary-search-tree-order-conflict.pdf",
        },
        "query": (
            "Mỗi nút của cây lưu một khóa dùng để so sánh.",
            "Mọi khóa ở cây con trái nhỏ hơn khóa của nút.",
            "Mọi khóa ở cây con phải lớn hơn khóa của nút.",
            "Tính có thứ tự hỗ trợ tìm kiếm theo đường đi trên cây.",
        ),
        "equivalent": (
            "Cây tìm kiếm nhị phân tổ chức các khóa quanh từng nút gốc.",
            "Nhánh trái chỉ chứa giá trị bé hơn giá trị đang xét.",
            "Nhánh phải chỉ chứa giá trị lớn hơn giá trị đang xét.",
            "Quy tắc sắp thứ tự cho phép loại dần nhánh khi tìm kiếm.",
        ),
        "conflict": (
            "Mỗi nút của cây lưu một khóa dùng để so sánh.",
            "Mọi khóa ở cây con trái lớn hơn khóa của nút.",
            "Mọi khóa ở cây con phải nhỏ hơn khóa của nút.",
            "Tính có thứ tự hỗ trợ tìm kiếm theo đường đi trên cây.",
        ),
    },
    {
        "triplet_id": "TRI-003",
        "category": "quantitative_claim",
        "layout_family": "lecture_card",
        "topic": "Tìm kiếm nhị phân",
        "filenames": {
            "query": "E907-binary-search-complexity.pdf",
            "equivalent": "E908-binary-search-complexity-paraphrase.pdf",
            "conflict": "E909-binary-search-complexity-conflict.pdf",
        },
        "query": (
            "Tìm kiếm nhị phân yêu cầu dãy đã được sắp xếp.",
            "Mỗi bước loại bỏ một nửa khoảng tìm kiếm còn lại.",
            "Số phép so sánh tăng theo O(log n).",
            "Nếu dữ liệu chưa sắp xếp thì điều kiện áp dụng không còn đúng.",
        ),
        "equivalent": (
            "Thuật toán tìm kiếm nhị phân làm việc trên dữ liệu có thứ tự.",
            "Sau một lần so sánh, không gian ứng viên giảm còn khoảng một nửa.",
            "Vì vậy thời gian tìm kiếm có bậc logarit theo kích thước dãy.",
            "Cần kiểm tra tiền điều kiện sắp xếp trước khi sử dụng.",
        ),
        "conflict": (
            "Tìm kiếm nhị phân yêu cầu dãy đã được sắp xếp.",
            "Mỗi bước loại bỏ một nửa khoảng tìm kiếm còn lại.",
            "Số phép so sánh tăng theo O(n bình phương).",
            "Nếu dữ liệu chưa sắp xếp thì điều kiện áp dụng không còn đúng.",
        ),
    },
    {
        "triplet_id": "TRI-004",
        "category": "transaction_semantics",
        "layout_family": "lecture_card",
        "topic": "Tính nguyên tử của giao dịch",
        "filenames": {
            "query": "E910-transaction-atomicity.pdf",
            "equivalent": "E911-transaction-atomicity-paraphrase.pdf",
            "conflict": "E912-transaction-atomicity-conflict.pdf",
        },
        "query": (
            "Tính nguyên tử coi một giao dịch là một đơn vị không thể chia nhỏ.",
            "Hoặc toàn bộ thao tác được commit, hoặc tất cả bị rollback.",
            "Trạng thái dở dang không được công bố như kết quả thành công.",
            "Cơ chế phục hồi hỗ trợ duy trì thuộc tính này khi có lỗi.",
        ),
        "equivalent": (
            "Atomicity yêu cầu các bước trong giao dịch cùng thành công hoặc cùng hủy.",
            "Hệ thống không giữ một phần cập nhật nếu giao dịch thất bại.",
            "Chỉ trạng thái hoàn chỉnh mới được xác nhận cho bên sử dụng.",
            "Nhật ký phục hồi giúp đưa dữ liệu về trạng thái phù hợp.",
        ),
        "conflict": (
            "Tính nguyên tử coi một giao dịch là một đơn vị không thể chia nhỏ.",
            "Một phần thao tác có thể commit dù các bước còn lại bị rollback.",
            "Trạng thái dở dang được công bố như kết quả thành công.",
            "Cơ chế phục hồi hỗ trợ duy trì thuộc tính này khi có lỗi.",
        ),
    },
    {
        "triplet_id": "TRI-005",
        "category": "definition_constraint",
        "layout_family": "module_note",
        "topic": "Dạng chuẩn thứ ba",
        "filenames": {
            "query": "E913-third-normal-form.pdf",
            "equivalent": "E914-third-normal-form-paraphrase.pdf",
            "conflict": "E915-third-normal-form-conflict.pdf",
        },
        "query": (
            "Quan hệ ở dạng chuẩn ba trước hết phải đạt dạng chuẩn hai.",
            "Thuộc tính không khóa không phụ thuộc bắc cầu vào khóa.",
            "Tách quan hệ có thể giảm bất thường khi cập nhật dữ liệu.",
            "Phép tách vẫn cần xem xét bảo toàn phụ thuộc và kết nối không mất mát.",
        ),
        "equivalent": (
            "Chuẩn hóa đến 3NF bắt đầu từ một quan hệ đã thỏa 2NF.",
            "Không để thuộc tính thường phụ thuộc gián tiếp qua thuộc tính thường khác.",
            "Mục tiêu là hạn chế lỗi chèn, sửa và xóa dữ liệu.",
            "Thiết kế sau tách phải tiếp tục kiểm tra dependency và lossless join.",
        ),
        "conflict": (
            "Quan hệ ở dạng chuẩn ba trước hết phải đạt dạng chuẩn hai.",
            "Thuộc tính không khóa được phép phụ thuộc bắc cầu vào khóa.",
            "Tách quan hệ có thể giảm bất thường khi cập nhật dữ liệu.",
            "Phép tách vẫn cần xem xét bảo toàn phụ thuộc và kết nối không mất mát.",
        ),
    },
    {
        "triplet_id": "TRI-006",
        "category": "algorithm_mechanism",
        "layout_family": "module_note",
        "topic": "Điều phối Round Robin",
        "filenames": {
            "query": "E916-round-robin-scheduling.pdf",
            "equivalent": "E917-round-robin-scheduling-paraphrase.pdf",
            "conflict": "E918-round-robin-scheduling-conflict.pdf",
        },
        "query": (
            "Round Robin phân phối CPU theo một quantum thời gian cố định.",
            "Tiến trình hết quantum được đưa về cuối hàng đợi sẵn sàng.",
            "Cơ chế có ngắt giúp các tiến trình luân phiên sử dụng CPU.",
            "Quantum quá nhỏ làm tăng chi phí chuyển ngữ cảnh.",
        ),
        "equivalent": (
            "Bộ lập lịch vòng tròn cấp cho mỗi tiến trình một lát thời gian.",
            "Tác vụ chưa xong quay lại cuối cấu trúc FIFO để chờ lượt mới.",
            "Đây là phương pháp preemptive nhằm chia sẻ bộ xử lý.",
            "Lát thời gian ngắn có thể tạo nhiều lần context switch.",
        ),
        "conflict": (
            "Round Robin phân phối CPU mà không dùng quantum thời gian.",
            "Tiến trình chạy liên tục đến khi hoàn tất và không quay lại hàng đợi.",
            "Cơ chế không ngắt khiến một tiến trình giữ CPU đến khi kết thúc.",
            "Quantum quá nhỏ làm tăng chi phí chuyển ngữ cảnh.",
        ),
    },
    {
        "triplet_id": "TRI-007",
        "category": "protocol_semantics",
        "layout_family": "module_note",
        "topic": "Truyền dữ liệu với TCP",
        "filenames": {
            "query": "E919-tcp-delivery-semantics.pdf",
            "equivalent": "E920-tcp-delivery-semantics-paraphrase.pdf",
            "conflict": "E921-tcp-delivery-semantics-conflict.pdf",
        },
        "query": (
            "TCP thiết lập kết nối trước khi trao đổi dữ liệu ứng dụng.",
            "Số thứ tự và xác nhận hỗ trợ truyền tin cậy theo đúng thứ tự.",
            "Phân đoạn bị mất có thể được truyền lại.",
            "Kiểm soát luồng hạn chế bên gửi làm tràn bộ đệm bên nhận.",
        ),
        "equivalent": (
            "Giao thức TCP duy trì trạng thái kết nối giữa hai đầu cuối.",
            "Sequence number và ACK giúp tái lập dòng byte có thứ tự.",
            "Dữ liệu không được xác nhận sẽ được gửi lại theo cơ chế phục hồi.",
            "Cửa sổ nhận điều tiết lượng dữ liệu đang truyền.",
        ),
        "conflict": (
            "TCP thiết lập kết nối trước khi trao đổi dữ liệu ứng dụng.",
            "TCP không bảo đảm truyền tin cậy hoặc đúng thứ tự.",
            "Phân đoạn bị mất không bao giờ được truyền lại.",
            "Kiểm soát luồng hạn chế bên gửi làm tràn bộ đệm bên nhận.",
        ),
    },
    {
        "triplet_id": "TRI-008",
        "category": "statistical_interpretation",
        "layout_family": "module_note",
        "topic": "Trung vị và giá trị ngoại lai",
        "filenames": {
            "query": "E922-median-outliers.pdf",
            "equivalent": "E923-median-outliers-paraphrase.pdf",
            "conflict": "E924-median-outliers-conflict.pdf",
        },
        "query": (
            "Trung vị là giá trị nằm giữa khi dữ liệu đã được sắp thứ tự.",
            "Một giá trị ngoại lai rất lớn thường ít làm thay đổi trung vị.",
            "Vì vậy trung vị hữu ích cho phân phối lệch.",
            "Cần báo rõ cách xử lý khi số quan sát là chẵn.",
        ),
        "equivalent": (
            "Median chia dãy đã sắp xếp thành hai nửa về số quan sát.",
            "Các điểm cực đoan tác động đến median ít hơn so với mean.",
            "Thước đo này phù hợp khi dữ liệu có đuôi dài hoặc bị lệch.",
            "Với cỡ mẫu chẵn, quy tắc lấy hai vị trí giữa phải được nêu rõ.",
        ),
        "conflict": (
            "Trung vị là giá trị nằm giữa khi dữ liệu đã được sắp thứ tự.",
            "Một giá trị ngoại lai rất lớn luôn làm trung vị tăng tương ứng.",
            "Vì vậy trung vị không thể dùng cho phân phối lệch.",
            "Cần báo rõ cách xử lý khi số quan sát là chẵn.",
        ),
    },
    {
        "triplet_id": "TRI-009",
        "category": "quantitative_claim",
        "layout_family": "worked_example",
        "topic": "Đạo hàm của hàm lượng giác",
        "filenames": {
            "query": "E925-sine-derivative.pdf",
            "equivalent": "E926-sine-derivative-paraphrase.pdf",
            "conflict": "E927-sine-derivative-conflict.pdf",
        },
        "query": (
            "Xét hàm số f(x) = sin(x).",
            "Đạo hàm của hàm số là f'(x) = cos(x).",
            "Tại x = 0, giá trị đạo hàm bằng 1.",
            "Kết quả có thể kiểm tra từ giới hạn của thương sai phân.",
        ),
        "equivalent": (
            "Với y bằng sin của x, tốc độ thay đổi là cos của x.",
            "Công thức đạo hàm viết thành dy/dx = cos(x).",
            "Thay x bằng 0 cho hệ số góc tiếp tuyến bằng một.",
            "Có thể chứng minh công thức bằng định nghĩa giới hạn.",
        ),
        "conflict": (
            "Xét hàm số f(x) = sin(x).",
            "Đạo hàm của hàm số là f'(x) = -cos(x).",
            "Tại x = 0, giá trị đạo hàm bằng -1.",
            "Kết quả có thể kiểm tra từ giới hạn của thương sai phân.",
        ),
    },
    {
        "triplet_id": "TRI-010",
        "category": "metric_definition",
        "layout_family": "worked_example",
        "topic": "Precision trong bài toán phân loại",
        "filenames": {
            "query": "E928-classification-precision.pdf",
            "equivalent": "E929-classification-precision-paraphrase.pdf",
            "conflict": "E930-classification-precision-conflict.pdf",
        },
        "query": (
            "Precision đánh giá độ đúng của các dự đoán dương.",
            "Tử số là true positive.",
            "Mẫu số là true positive cộng false positive.",
            "Metric này không thay thế recall khi false negative quan trọng.",
        ),
        "equivalent": (
            "Độ chính xác dương cho biết bao nhiêu dự đoán positive là đúng.",
            "Số mẫu dương dự đoán đúng nằm ở tử số.",
            "Mọi mẫu được dự đoán dương tạo thành mẫu số.",
            "Cần xem thêm recall nếu bỏ sót dương tính gây hậu quả.",
        ),
        "conflict": (
            "Precision đánh giá độ đúng của các dự đoán dương.",
            "Tử số là true positive.",
            "Mẫu số là true positive cộng false negative.",
            "Metric này hoàn toàn thay thế recall khi false negative quan trọng.",
        ),
    },
    {
        "triplet_id": "TRI-011",
        "category": "operator_semantics",
        "layout_family": "worked_example",
        "topic": "So sánh và gán trong chương trình",
        "filenames": {
            "query": "E931-comparison-assignment.pdf",
            "equivalent": "E932-comparison-assignment-paraphrase.pdf",
            "conflict": "E933-comparison-assignment-conflict.pdf",
        },
        "query": (
            "Phép gán cập nhật biến bằng một giá trị mới.",
            "Phép so sánh bằng tạo ra kết quả đúng hoặc sai.",
            "Hai phép toán có vai trò khác nhau trong biểu thức điều kiện.",
            "Cần theo cú pháp của ngôn ngữ đang sử dụng.",
        ),
        "equivalent": (
            "Assignment thay đổi trạng thái được lưu trong biến.",
            "Equality comparison chỉ kiểm tra hai toán hạng có bằng nhau không.",
            "Điều kiện rẽ nhánh cần một biểu thức cho giá trị logic.",
            "Ký hiệu cụ thể phụ thuộc vào từng ngôn ngữ lập trình.",
        ),
        "conflict": (
            "Phép gán chỉ tạo ra kết quả đúng hoặc sai và không đổi biến.",
            "Phép so sánh bằng cập nhật biến bằng một giá trị mới.",
            "Hai phép toán có cùng vai trò trong biểu thức điều kiện.",
            "Cần theo cú pháp của ngôn ngữ đang sử dụng.",
        ),
    },
    {
        "triplet_id": "TRI-012",
        "category": "authorization_policy",
        "layout_family": "worked_example",
        "topic": "Cách ly dữ liệu giữa các tenant",
        "filenames": {
            "query": "E934-tenant-isolation-policy.pdf",
            "equivalent": "E935-tenant-isolation-policy-paraphrase.pdf",
            "conflict": "E936-tenant-isolation-policy-conflict.pdf",
        },
        "query": (
            "Mọi truy vấn tài liệu phải mang tenant context đã xác thực.",
            "Prefilter quyền được áp dụng trước khi semantic retrieval.",
            "Agent không được mở rộng scope vượt quá capability đã cấp.",
            "Khi thiếu bằng chứng quyền truy cập, hệ thống từ chối mặc định.",
        ),
        "equivalent": (
            "Danh tính workload phải gắn với phạm vi tổ chức được xác minh.",
            "Tài liệu ngoài quyền bị loại trước bước tìm kiếm theo ngữ nghĩa.",
            "Công cụ của agent chỉ hoạt động trong capability envelope.",
            "Trạng thái quyền không rõ ràng dẫn đến quyết định deny.",
        ),
        "conflict": (
            "Truy vấn tài liệu không cần tenant context đã xác thực.",
            "Semantic retrieval chạy trước rồi mới kiểm tra quyền ở đầu ra.",
            "Agent được mở rộng scope nếu tài liệu có score tương tự cao.",
            "Khi thiếu bằng chứng quyền truy cập, hệ thống cho phép mặc định.",
        ),
    },
)


PALETTES = {
    "lecture_card": ("#173B57", "#E8F2F7", "#0F6B78"),
    "module_note": ("#3C2F63", "#F0ECF8", "#6C4DB3"),
    "worked_example": ("#5A351F", "#FBF1E8", "#B35C24"),
}


def register_fonts() -> None:
    if not ARIAL.is_file() or not ARIAL_BOLD.is_file():
        raise FileNotFoundError("Arial fonts required for Vietnamese fixture rendering")
    pdfmetrics.registerFont(TTFont("E09Arial", str(ARIAL)))
    pdfmetrics.registerFont(TTFont("E09ArialBold", str(ARIAL_BOLD)))


def draw_wrapped(pdf: canvas.Canvas, text: str, x: float, y: float, *, width: int = 74) -> float:
    for line in textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False):
        pdf.drawString(x, y, line)
        y -= 18
    return y


def make_pdf(filename: str, topic: str, lines: tuple[str, ...], layout_family: str) -> Path:
    dark, pale, accent = (HexColor(value) for value in PALETTES[layout_family])
    path = OUTPUT_DIR / filename
    pdf = canvas.Canvas(str(path), pagesize=A4, invariant=1, pageCompression=1)
    pdf.setTitle(topic)
    pdf.setAuthor("Synthetic Academic Evaluation")
    pdf.setSubject("E0.9 semantic equivalence diagnostic")
    pdf.setCreator("Academic Assistant E0.9 independent triplet generator")

    pdf.setFillColor(HexColor("#F8FAFC"))
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    pdf.setFillColor(dark)
    pdf.rect(0, PAGE_HEIGHT - 104, PAGE_WIDTH, 104, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("E09ArialBold", 19)
    pdf.drawString(44, PAGE_HEIGHT - 56, topic)
    pdf.setFont("E09Arial", 9)
    pdf.drawString(44, PAGE_HEIGHT - 82, "Ghi chú học thuật synthetic - chỉ dùng trong quarantine evaluation")

    pdf.setFillColor(pale)
    pdf.roundRect(44, PAGE_HEIGHT - 166, PAGE_WIDTH - 88, 34, 7, fill=1, stroke=0)
    pdf.setFillColor(accent)
    pdf.setFont("E09ArialBold", 9)
    pdf.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 153, "E0.9 SYNTHETIC CONTENT - KHÔNG PHẢI GIÁO TRÌNH THẬT")

    pdf.setFillColor(dark)
    pdf.setFont("E09ArialBold", 13)
    section_name = {
        "lecture_card": "Khái niệm trọng tâm",
        "module_note": "Nội dung mô-đun",
        "worked_example": "Phân tích ví dụ",
    }[layout_family]
    pdf.drawString(56, PAGE_HEIGHT - 220, section_name)

    y = PAGE_HEIGHT - 262
    for index, line in enumerate(lines, start=1):
        pdf.setFillColor(accent)
        pdf.circle(64, y + 4, 9, fill=1, stroke=0)
        pdf.setFillColor(white)
        pdf.setFont("E09ArialBold", 8)
        pdf.drawCentredString(64, y + 1, str(index))
        pdf.setFillColor(HexColor("#1E2933"))
        pdf.setFont("E09Arial", 10.5)
        y = draw_wrapped(pdf, line, 84, y, width=70) - 20

    pdf.setStrokeColor(HexColor("#CBD5E1"))
    pdf.line(44, 68, PAGE_WIDTH - 44, 68)
    pdf.setFillColor(HexColor("#64748B"))
    pdf.setFont("E09Arial", 8)
    pdf.drawString(44, 50, "No serving index. No auto-merge. Review academic claims independently.")
    pdf.drawRightString(PAGE_WIDTH - 44, 50, "Trang 1/1")
    pdf.showPage()
    pdf.save()
    return path


def generate() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    outputs: list[Path] = []
    for triplet in TRIPLETS:
        filenames = triplet["filenames"]
        for role in ("query", "equivalent", "conflict"):
            outputs.append(make_pdf(
                str(filenames[role]),
                str(triplet["topic"]),
                tuple(triplet[role]),
                str(triplet["layout_family"]),
            ))
    expected = {str(name) for triplet in TRIPLETS for name in triplet["filenames"].values()}
    observed = {path.name for path in outputs}
    if observed != expected or len(outputs) != 36:
        raise RuntimeError(f"Unexpected E0.9 output set: {sorted(observed)}")
    return outputs


if __name__ == "__main__":
    for output in generate():
        print(output.relative_to(ROOT).as_posix())
