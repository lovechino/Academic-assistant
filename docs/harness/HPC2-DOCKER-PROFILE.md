# HPC-2: Docker synthetic profile v0.1

Ngày: 2026-09-08. Trạng thái: **draft for review, execution NOT RUN**.
Đây là specialization của [boundary contract](HPC2-BOUNDARY-CONTRACT.md),
không phải launcher, Dockerfile, Compose, quyền provisioning hoặc product GO.

## 1. Mục tiêu và bằng chứng hiện có

Đề xuất `hpc2_docker_synthetic_v0.1`: một producer deterministic nhận packet
synthetic và trả proposal; không model, PDF, network, repo write hoặc applier.
Worker rồi executor nếu được cấp scope riêng; không chạy đồng thời.

Khảo sát read-only trước task này, không phải phép đo mới của profile:

| Quan sát | Giới hạn diễn giải |
|---|---|
| Windows 11 Home, RAM khoảng 7.7 GiB; không tìm thấy Docker CLI trên Windows PATH | Không chứng minh Docker chưa cài; không dùng giới hạn Windows Sandbox để phủ định Docker WSL |
| Ubuntu 24.04.4 LTS trên WSL2; CLI 29.1.3; socket local truy vấn được Engine 29.6.1 | systemd service/socket inactive không nghĩa daemon tắt; không start daemon thứ hai |
| Socket root:docker; user Ubuntu thuộc docker; security options báo builtin seccomp | Không xác nhận rootless, AppArmor hoặc SELinux; user Ubuntu không là worker bị hạn quyền |
| Engine module version có hậu tố `+dirty`; containerd 2.3.3, runc 1.5.1 | Nguồn build/version khác CLI cần xác minh; không tự suy compromise hoặc tính an toàn |
| Docker cgroupfs/v1; cảnh báo thiếu blkio throttle bps/iops và v1 deprecated | Chưa chứng minh memory/swap/CPU/PID limits thực thi; không tự nâng cấp/restart |
| Hai container đang chạy, chưa inspect nội dung/env/log của chúng | Shared daemon/workload risk; không coi host là máy thử nghiệm trống |
| WSL tổng RAM khoảng 3.74 GiB, available 2574 MiB lúc khảo sát | Không phải headroom hiện tại hoặc reservation |
| ext4 virtual disk báo khoảng 911 GiB available; Windows C/E free 37.2/106.3 GiB lúc khảo sát | Virtual capacity không là physical free; vị trí backing disk/headroom hiện tại chưa chốt |

Không có container mới được create/start trong task này. Các con số trên là
transcript evidence lịch sử, chưa có protected observer receipt tái lập độc lập.

## 2. Trust boundary và quyền

Controller/operator ở ngoài container giữ quyền Docker, task/grant/base digest,
checker release và evidence. Worker chỉ là process bên trong container; không
được chuyển full shell Windows/Ubuntu hay Docker API tool cho worker.
Agent coding hiện tại có shell host: profile này **không cách ly agent hiện tại**.
Phải có broker/launcher do trusted actor kiểm soát trước tích hợp agent thật.

Docker group có quyền mức root theo [Docker post-install](https://docs.docker.com/engine/install/linux-postinstall/).
Container không là VM độc lập; shared kernel/rootful daemon vẫn là residual risk.
Tên/label container hỗ trợ tracking, không là security boundary giữa users.

| Bề mặt | Giá trị đề xuất; preflight phải kiểm effective config |
|---|---|
| Identity | Numeric UID/GID 65532:65532; không supplementary groups, sudo, credentials |
| Privilege | Drop ALL capabilities; no-new-privileges=true; không privileged/devices; builtin seccomp, không unconfined |
| Namespaces | Không host PID/IPC/network/cgroup namespace; private IPC; giữ masked/read-only system paths |
| Filesystem | Read-only rootfs; không host bind, named/anonymous volume, Docker socket hoặc device passthrough |
| Host data | Không repo, .git, home, SSH agent, `/mnt/c`, `/mnt/e`, `/mnt/wsl`, credential/config mount |
| Network | network=none, không publish ports/host gateway/proxy/attach network; không host service bridge |
| Image | Pin digest + platform + local image identity; reviewed provenance, explicit entrypoint/args/env allowlist; không secret baked in |
| Hidden defaults | Reject image VOLUME; disable healthcheck/restart; inspect declared ENV/entrypoint and effective mounts; không thừa hưởng shell/proxy config |

Flags là yêu cầu thiết kế, chưa chứng minh hỗ trợ trên engine đang có. Tham chiếu
[run security options](https://docs.docker.com/reference/cli/docker/container/run/),
[seccomp](https://docs.docker.com/engine/security/seccomp/) và
[network none](https://docs.docker.com/engine/network/drivers/none/): none vẫn có
loopback. Không dùng một probe Internet thất bại để kết luận mọi egress đã chặn.

## 3. Kênh dữ liệu và evidence

1. Trusted controller giữ packet gốc/classification/hash; gửi tối đa 4 MiB qua
   stdin, đóng input khi hết. Không mount packet hay cho worker đọc host path.
   Worker có thể đổi bản trong RAM của mình; bản đó không thay authority bên ngoài.
2. Non-TTY stdout chỉ một proposal JSON tối đa 1 MiB; stderr chỉ diagnostics tối đa
   256 KiB. Collector enforce trong lúc đọc, tổng tối đa 1.25 MiB; không capture
   toàn bộ rồi mới cắt. Framing/parser không allocate theo độ dài untrusted vô hạn.
3. Collector attach trước start; mất stream, EOF bất thường, overflow hoặc timeout
   là failed/incomplete, không PASS. Không tự retry. Cơ chế attach và backpressure
   trên engine này phải có bounded positive/negative control trước dùng thật.
4. Đề xuất logging driver `none` để không ghi proposal/log flood vào daemon log.
   [Docker logging](https://docs.docker.com/engine/logging/configure/) xác nhận
   `docker logs` không trả output với driver này: không coi nó là kênh recovery.
   Live collector chưa implement/verify; thiếu collector thì chặn launch.
5. Controller bind bytes vào exact container ID/job/generation/attempt/fence,
   packet/base/checker/profile digests; không tin identity hoặc PASS trong JSON.
   Validate proposal ngoài container, chỉ sealed in-memory candidate ở slice này.
   Không docker-cp, tar extraction, shell command hoặc host destination từ output.
6. Evidence là bounded plain text/metadata; escape ANSI/HTML, không auto-fetch URL,
   không đưa raw secrets/source vào SQLite/log. Retention/ACL/owner của protected
   receipt còn pending; SQLite journal hiện tại không là trusted authority store.

## 4. Budget nhỏ cho synthetic smoke

Các giá trị sau là **proposed caps**, không benchmark hoặc cấu hình đã áp dụng;
thắt chặt, không thay upper bounds của contract cho profile tương lai.

| Resource | Cap đề xuất |
|---|---|
| Concurrency/retry | Một container active trên profile; zero queued jobs; restart=no, zero automatic retry |
| CPU / RAM / swap | 0.5 CPU; memory 512 MiB; memory-swap 512 MiB, không extra swap |
| Processes | pids-limit 32, bao gồm children/threads theo runtime accounting |
| Writable workspace | tmpfs 32 MiB, mode 0700, UID/GID worker, noexec/nosuid/nodev; inode cap 1024 nếu hỗ trợ |
| Other writable mounts | Private /dev/shm 8 MiB; inventory tất cả runtime-injected mounts, không thêm tmpfs ngầm |
| Deadline | 60s tổng từ admission gồm setup/capture/validation/teardown; mỗi command tối đa 30s; kill grace tối đa 5s nằm trong tổng |
| Controller | Packet/proposal/log byte caps §3; bounded buffers, parser tối đa 10s; aggregate process/RAM/API deadline enforcement chưa implement |

[Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)
quy định memory-swap bằng memory để không thêm swap; phải kiểm kernel/cgroup hỗ trợ,
không suy từ `free` bên trong container. [Tmpfs](https://docs.docker.com/engine/storage/tmpfs/)
có thể xuống swap; noexec không chặn interpreter đọc script (giới hạn thiết kế).
Không tự bỏ flag khi unsupported hoặc bật privileged để chữa mount failure.

Cgroup v1/thiếu blkio nghĩa chưa hứa được quota I/O throughput. Read-only root và
bounded tmpfs giảm writes nhưng không cap mọi daemon metadata/host overhead.
Chỉ admission khi operator đã chốt headroom và observer; không dùng số RAM/free
disk lịch sử để cho chạy. Harmless smoke trước; resource adversarial probes chỉ
sau xác minh effective caps và scope riêng. Không fork bomb trên shared host.

## 5. Lifecycle, cancellation và bảo vệ workload cũ

Controller giữ lock một active attempt và exact ID receipt từ create; inspect
effective config trước start. Label/name không đủ để nhận ownership. Không auto-remove
trước khi thu termination evidence. Không dùng name glob hoặc enumerate-all để xóa.

Cancel/deadline fence attempt trước nhận kết quả; late output ghi rejected, không
resurrect/accept. Kết quả chỉ ứng viên, không có repo apply/approval ở HPC-2.
Stop/kill chỉ exact container mới do controller tạo; wait/inspect trạng thái kết thúc
trước cleanup exact ID. Kill CLI không chứng minh container/children đã dừng.
Nếu API hang hoặc termination không rõ: blocked, giữ incident metadata và báo
operator; không báo clean success hoặc restart daemon để xử lý.

Không prune, compose down, stop container cũ, restart Docker/WSL, nâng cấp engine,
đổi daemon config, networks hay volumes dùng chung. Host/kernel compromise hoặc
daemon-wide exhaustion vẫn có thể ảnh hưởng hai workloads: profile không bảo đảm
zero impact. Nếu cần thử hostile escape/flood, chọn môi trường dedicated qua quyết
định riêng, không mở rộng smoke này.

## 6. Gates và test disposition

| Gate | Bằng chứng còn thiếu / checkpoint |
|---|---|
| HB-D01 | Review shared-host risk; engine/build provenance và pinned image/local inventory; trước create/pull/build |
| HB-D02 | Trusted launcher/collector/checker owner ngoài worker; bounded stream positive/negative controls; trước integration |
| HB-D03 | Exact harmless fixtures, headroom, effective cgroup limits, total controller budgets; trước smoke |
| HB-D04 | Independent access/network/process observations, calibration, protected evidence ACL/retention; trước enforcement claim |
| HB-D05 | Authenticated acceptance/replay/crash/restore là HPC-3/4, không implement ở slice này |

Tất cả HB-01..08: **NOT RUN (0 executed/8 groups; pass rate N/A)**.
[Test map §7](PATCH-ONLY-TEST-MAP.md) nối controls với counterexamples; Docker
config inspection và parser tests không thay host probes. Không lựa image theo tag
mutable, suy gold/security từ synthetic PASS, hoặc tự cấp ASTRA/product GO.

Bước tiếp theo: review profile rồi read-only preflight image inventory/provenance
và capability gaps; không inspect secrets/workload business data. Khi có exact
image/fixture/observer và quyền thực thi rõ ràng mới lập task smoke riêng. Generic
“tiếp tục” không tự pull/build/create/start. Chưa có môi trường được nghiệm thu.
