# HARNESS-DOCKER-01 handoff

Ngày: 2026-09-08. Status: draft_complete, verified_local (mechanical), needs_review.

## Scope và ownership

User giao tiếp tục profile Docker sau khảo sát Ubuntu. Card
[HARNESS-DOCKER-01](tasks/HARNESS-DOCKER-01.json) được check-task và begin trước
editing; run `harness-docker-01-r1`, baseline 244 Git-visible files, không rebaseline.
Reuse boundary contract/test map/README; new canonical profile
[HPC2-DOCKER-PROFILE.md](HPC2-DOCKER-PROFILE.md), không module/runtime cạnh tranh.
Năm output docs đúng card; card được tạo trước baseline, vẫn thuộc nội dung review.

## Kết quả

- Profile draft: non-root, no host mounts/socket, network none, bounded stdin/stdout/stderr.
- Image defaults/provenance, cgroup v1, daemon logs, shared-workload safety,
  cancellation/exact-ID cleanup và trusted collector được ghi thành blocking gates.
- Historical Docker survey được tách khỏi current verification; systemd inactive
  không bị hiểu nhầm daemon unavailable; virtual disk không là physical headroom.
- Contract/test map/README liên kết profile; không biến proposed controls thành implemented enforcement.

## Verification

`harness_journal.py capture --run harness-docker-01-r1 --event docker-profile-verify-01
--phase verify --require-local-data`: passed, 120 harness test methods; structure
886/886 checks, 56 Python syntax files, 17 PDF source hashes, 0 failures/skips.
Scope check: đúng năm outputs; `git diff --check`: exit 0. Các thay đổi cũ ngoài
scope được giữ nguyên. Đây là mechanical verification, không host acceptance.

Capture finished `2026-09-08T03:55:53.247013+00:00`; baseline SHA-256
`dd617ae4fcbc76ddc088b1f5274e58327f2460866cfb9e25789973ebbc95e53d`.
Observed tree `018d706134d03a090f5417ceea411fa49255a36141b9f48579a36e75181a5245`
là trước cập nhật evidence vào handoff này, không hash bản cuối. Sau cập nhật chạy
lại scope/structure/diff; không sửa code/tests hoặc tạo baseline mới.
Resume check trước outputs báo missing profile là expected, không là test PASS.
Không rerun historical artifact generators. Web research dùng official Docker docs
được link ngay trong profile; không thực thi snippet từ web.

## NOT RUN, residuals và bước tiếp

HB-01..08 NOT RUN; không chạy worker/executor/model/PDF, Docker create/start/pull/build,
không đổi WSL/daemon, không đụng hai workloads cũ. Không applier/broker hoặc protected
receipt store được thêm. Không claim 100% adherence hoặc security acceptance.

Review profile → read-only image/provenance/capability preflight → exact bounded
smoke task khi đủ authority, fixtures và observer. Shared kernel/rootful daemon,
collector resource cap và supply-chain evidence vẫn pending. HPC-3/4 recovery và
authenticated approval không được mở khóa bởi tài liệu này. Giữ option 2/manual
Academic, WP-04/ASTRA review và explicit product GO pending; plan/state không sửa.
