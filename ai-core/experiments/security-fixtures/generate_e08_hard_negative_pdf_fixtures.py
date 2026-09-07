"""Generate E0.8 hard-negative PDFs for duplicate candidate evaluation."""
from __future__ import annotations

from pathlib import Path

from generate_duplicate_pdf_fixtures import OUTPUT_DIR, ROOT, register_fonts
from generate_remaining_pair_pdf_fixtures import make_pdf


HARD_NEGATIVES: tuple[dict[str, object], ...] = (
    {
        "filename": "H01-boilerplate-algorithms.pdf",
        "fixture_id": "H01",
        "category": "shared_boilerplate",
        "target_family": "data_structures",
        "title": "Đề cương môn học",
        "heading": "Thông tin chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Nội dung cốt lõi: thiết kế và phân tích thuật toán."),
    },
    {
        "filename": "H02-boilerplate-software-engineering.pdf",
        "fixture_id": "H02",
        "category": "shared_boilerplate",
        "target_family": "data_structures",
        "title": "Đề cương môn học",
        "heading": "Thông tin chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Nội dung cốt lõi: quy trình phát triển phần mềm."),
    },
    {
        "filename": "H03-boilerplate-computer-networks.pdf",
        "fixture_id": "H03",
        "category": "shared_boilerplate",
        "target_family": "computer_networks",
        "title": "Đề cương môn học",
        "heading": "Thông tin chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Nội dung cốt lõi: mạng máy tính và giao thức."),
    },
    {
        "filename": "H04-boilerplate-operating-systems.pdf",
        "fixture_id": "H04",
        "category": "shared_boilerplate",
        "target_family": "operating_systems",
        "title": "Đề cương môn học",
        "heading": "Thông tin chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Nội dung cốt lõi: hệ điều hành và quản lý tiến trình."),
    },
    {
        "filename": "H05-boilerplate-artificial-intelligence.pdf",
        "fixture_id": "H05",
        "category": "shared_boilerplate",
        "target_family": "artificial_intelligence",
        "title": "Đề cương môn học",
        "heading": "Thông tin chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Nội dung cốt lõi: trí tuệ nhân tạo và tìm kiếm."),
    },
    {
        "filename": "H06-boilerplate-calculus.pdf",
        "fixture_id": "H06",
        "category": "shared_boilerplate",
        "target_family": "mathematics",
        "title": "Đề cương môn học",
        "heading": "Thông tin chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Nội dung cốt lõi: giới hạn, đạo hàm và tích phân."),
    },
    {
        "filename": "H07-same-title-electromagnetism.pdf",
        "fixture_id": "H07",
        "category": "same_title_different_content",
        "target_family": "physics",
        "title": "Bài giảng chương 1",
        "heading": "Điện trường",
        "lines": ("Điện trường mô tả tương tác giữa các điện tích.", "Ví dụ này không liên quan đến cấu trúc dữ liệu."),
    },
    {
        "filename": "H08-same-title-microeconomics.pdf",
        "fixture_id": "H08",
        "category": "same_title_different_content",
        "target_family": "economics",
        "title": "Bài giảng chương 1",
        "heading": "Cung và cầu",
        "lines": ("Giá cân bằng xuất hiện tại giao điểm cung và cầu.", "Ví dụ này không mô tả hàng đợi máy tính."),
    },
    {
        "filename": "H09-same-title-business-law.pdf",
        "fixture_id": "H09",
        "category": "same_title_different_content",
        "target_family": "law",
        "title": "Bài giảng chương 1",
        "heading": "Pháp luật kinh doanh",
        "lines": ("Chủ thể kinh doanh có quyền và nghĩa vụ theo quy định.", "Tình huống minh họa hoàn toàn synthetic."),
    },
    {
        "filename": "H10-same-title-marketing.pdf",
        "fixture_id": "H10",
        "category": "same_title_different_content",
        "target_family": "marketing",
        "title": "Bài giảng chương 1",
        "heading": "Hành vi khách hàng",
        "lines": ("Nhu cầu và nhận thức ảnh hưởng quyết định mua.", "Nội dung không phải thuật toán máy tính."),
    },
    {
        "filename": "H11-same-title-statistics.pdf",
        "fixture_id": "H11",
        "category": "same_title_different_content",
        "target_family": "statistics",
        "title": "Bài giảng chương 1",
        "heading": "Thống kê mô tả",
        "lines": ("Trung bình và trung vị mô tả xu hướng trung tâm.", "Dữ liệu ví dụ chỉ phục vụ fixture synthetic."),
    },
    {
        "filename": "H12-same-title-organic-chemistry.pdf",
        "fixture_id": "H12",
        "category": "same_title_different_content",
        "target_family": "chemistry",
        "title": "Bài giảng chương 1",
        "heading": "Liên kết hóa học",
        "lines": ("Liên kết cộng hóa trị hình thành do dùng chung electron.", "Nội dung không liên quan đến hàng đợi."),
    },
    {
        "filename": "H13-lexical-queue-operating-system.pdf",
        "fixture_id": "H13",
        "category": "cross_course_lexical_overlap",
        "target_family": "queue",
        "title": "Điều phối tiến trình",
        "heading": "Hàng đợi sẵn sàng",
        "lines": ("Hệ điều hành đặt tiến trình vào hàng đợi sẵn sàng.", "Bộ lập lịch chọn tác vụ theo chính sách điều phối."),
    },
    {
        "filename": "H14-lexical-tree-decision-model.pdf",
        "fixture_id": "H14",
        "category": "cross_course_lexical_overlap",
        "target_family": "tree",
        "title": "Mô hình cây quyết định",
        "heading": "Phân loại dữ liệu",
        "lines": ("Cây quyết định chia dữ liệu theo thuộc tính.", "Nút lá biểu diễn dự đoán của mô hình."),
    },
    {
        "filename": "H15-lexical-index-database.pdf",
        "fixture_id": "H15",
        "category": "cross_course_lexical_overlap",
        "target_family": "index",
        "title": "Chỉ mục cơ sở dữ liệu",
        "heading": "Tăng tốc truy vấn",
        "lines": ("Chỉ mục hỗ trợ tìm bản ghi mà không quét toàn bảng.", "B-tree thường được dùng để tổ chức khóa."),
    },
    {
        "filename": "H16-lexical-heap-memory.pdf",
        "fixture_id": "H16",
        "category": "cross_course_lexical_overlap",
        "target_family": "heap",
        "title": "Bộ nhớ heap",
        "heading": "Cấp phát động",
        "lines": ("Vùng heap lưu đối tượng được cấp phát khi chạy.", "Khái niệm này khác hàng đợi ưu tiên heap."),
    },
    {
        "filename": "H17-lexical-graph-business-chart.pdf",
        "fixture_id": "H17",
        "category": "cross_course_lexical_overlap",
        "target_family": "graph",
        "title": "Biểu đồ kinh doanh",
        "heading": "Trình bày dữ liệu",
        "lines": ("Biểu đồ đường mô tả doanh thu theo thời gian.", "Đây không phải đồ thị đỉnh và cạnh."),
    },
    {
        "filename": "H18-lexical-complexity-project.pdf",
        "fixture_id": "H18",
        "category": "cross_course_lexical_overlap",
        "target_family": "complexity",
        "title": "Độ phức tạp dự án",
        "heading": "Quản lý phạm vi",
        "lines": ("Độ phức tạp dự án tăng khi nhiều bên tham gia.", "Khái niệm này không phải độ phức tạp thuật toán."),
    },
    {
        "filename": "H19-short-template-attendance.pdf",
        "fixture_id": "H19",
        "category": "template_dominated_short",
        "target_family": "course_policy",
        "title": "Thông tin học phần",
        "heading": "Quy định chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Sinh viên theo dõi lịch học và điểm danh."),
    },
    {
        "filename": "H20-short-template-laboratory.pdf",
        "fixture_id": "H20",
        "category": "template_dominated_short",
        "target_family": "course_policy",
        "title": "Thông tin học phần",
        "heading": "Quy định chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Sinh viên hoàn thành bài thực hành tại phòng máy."),
    },
    {
        "filename": "H21-short-template-presentation.pdf",
        "fixture_id": "H21",
        "category": "template_dominated_short",
        "target_family": "course_policy",
        "title": "Thông tin học phần",
        "heading": "Quy định chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Sinh viên trình bày kết quả theo nhóm."),
    },
    {
        "filename": "H22-short-template-midterm.pdf",
        "fixture_id": "H22",
        "category": "template_dominated_short",
        "target_family": "course_policy",
        "title": "Thông tin học phần",
        "heading": "Quy định chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Bài kiểm tra giữa kỳ dùng câu hỏi tự luận."),
    },
    {
        "filename": "H23-short-template-project.pdf",
        "fixture_id": "H23",
        "category": "template_dominated_short",
        "target_family": "course_policy",
        "title": "Thông tin học phần",
        "heading": "Quy định chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Đồ án cuối kỳ sử dụng dữ liệu synthetic."),
    },
    {
        "filename": "H24-short-template-reading.pdf",
        "fixture_id": "H24",
        "category": "template_dominated_short",
        "target_family": "course_policy",
        "title": "Thông tin học phần",
        "heading": "Quy định chung",
        "lines": ("Mục tiêu môn học. Quy định đánh giá.", "Danh mục đọc được công bố theo từng tuần."),
    },
)


def generate() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    outputs: list[Path] = []
    for item in HARD_NEGATIVES:
        outputs.append(make_pdf(
            str(item["filename"]),
            str(item["fixture_id"]),
            str(item["title"]),
            ((str(item["heading"]), tuple(item["lines"])),),
            author="Synthetic Lecturer",
            subject=f"E0.8 {item['category']} fixture",
        ))
    expected = {f"H{index:02d}" for index in range(1, 25)}
    observed = {path.name.split("-", 1)[0] for path in outputs}
    if observed != expected or len(outputs) != 24:
        raise RuntimeError(f"Unexpected E0.8 output set: {sorted(path.name for path in outputs)}")
    return outputs


if __name__ == "__main__":
    for output in generate():
        print(output.relative_to(ROOT).as_posix())
