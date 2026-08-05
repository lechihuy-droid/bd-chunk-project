# Agent skill tool

## Nguồn sự thật duy nhất

`services/skill_library.py` là index skill duy nhất có thẩm quyền. Nó quét các
nguồn đã cấu hình, hỗ trợ cả thư mục `SKILL.md` và file `.md` độc lập; đồng thời
là nguồn dùng để xác thực `agent.skills` và nạp nội dung skill cho chat, workflow
run.

`services/runtime_skills.py` không quét filesystem. Nó là lớp đọc qua
`skill_library`, chỉ chuyển dữ liệu sang contract cũ của `/api/skills`,
`/api/skills/{id}`, và `/api/skills/{id}/usage`: `id` slug, `title`,
`description`, `path`, `read_only`, và `body` khi xem chi tiết. Vì vậy UI/runtime
cũ giữ được response shape, còn discovery chỉ còn một nơi.
