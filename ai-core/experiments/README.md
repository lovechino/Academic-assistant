# AI experiments

Các khảo sát offline trước production. Runtime trong `src/` không import từ đây.

Review repair 2026-09-06: [context-integrity-v0.1](context-integrity-v0.1/README.md) sửa mất sub/sup trong model-text projection và atomic required-dependency packing bằng profile riêng. 23 synthetic regression methods; R2–R4 scripts/artifacts lịch sử giữ nguyên. Không tiếp tục dùng legacy stripping làm model evidence hoặc coi resolver-only 6/6 là post-pack completeness.

Hiện có [PDF pilot](pdf-pilot/README.md): hai helper được chuyển từ thư mục `research/pdf-pilot/` cũ, thuật toán giữ nguyên. Data/annotations/results vẫn ở `data/` tại root.

Bổ sung [evidence mapping audit](evidence-mapping/README.md): kiểm tra hash/offset của 22 spans và AND/OR của nhóm bằng chứng; không chạy model/retrieval, không tái ghi dữ liệu.

Đã chạy [workflow tabletop](workflow-tabletop/README.md): 11 tình huống synthetic về packing/citation/revoke/cache, 9 guard mutations và trace từng bước; không kiểm thử runtime sản phẩm.

Đã có [evidence contract checks](evidence-contract/README.md): năm ví dụ chọn bằng tay từ nguồn thật, kiểm tra provenance/lineage, packet và evaluator separation; chưa chạy parser/chunker/retriever.

Vòng tiếp theo đã chạy [HTML source structure](html-structure/README.md) trên 16 module CTDL: cây thẻ/vị trí nguồn, section, bảng, ảnh, inline sub/sup và ánh xạ 22 locator silver. Chỉ kiểm tra bảo toàn/truy vết; chưa gom code, hiểu hình, chunk/index hoặc chạy model. Builder và auditor read-only, không tự ghi đè snapshot.

Mỗi experiment về sau cần có câu hỏi, snapshot, config/version, metric, limitation và nơi ghi output. Không chạy thí nghiệm theo test kín hoặc ngầm đưa nguồn cách ly lên dịch vụ bên ngoài.

Bổ sung [context review audit](context-review/README.md): kiểm tra annotations của 30 probe / 31 biến thể, 29 nhóm nguồn và 7 dependency candidates; 12 mutation tests cho validator. Chưa chạy chunker/retriever/generator hoặc đo semantic accuracy.

Đã chạy [source-preserving serialization](source-serialization/README.md) trên 29 nhóm/188 roots: typed events + aligned review view, giữ sub/sup, ranh giới p, cells và image refs; 12 synthetic tests/14 mutations. Đây là R0 kỹ thuật, không phải chunker hoặc model-ready context.

Đã chạy [chunking R1 boundary-only](chunking-r1/README.md): BGE-M3 tokenizer đã pin, cap 512/overlap 0, fixed và structure-aware nhìn cùng 4 module. Structure không cắt atom nhưng tạo nhiều chunks hơn và chưa giải quyết code/dependency; chưa retrieval/model.

Đã chạy [retrieval R4 diagnostics](retrieval-r4/README.md): frozen F32/int8 stability probe, comparison branch coverage gate và source-only code-prologue expansion. F32 ổn định theo batch trên probe; int8 có 19 đảo cặp. X3 cứu 6/6 text dependencies nhưng match rộng và visual path vẫn chưa hỗ trợ; chưa generation/agent benchmark.

Đã bổ sung [synthetic security PDF fixtures và duplicate candidate diagnostics](security-fixtures/README.md) cho upload quarantine, exact/near duplicate, visible/hidden/image/OCR markers, BGE-M3 local, E0.8 hard-negative routing và E0.9 equivalence/conflict triplets. Đây là offline evaluation helper; output local không vào content DB/serving index.
