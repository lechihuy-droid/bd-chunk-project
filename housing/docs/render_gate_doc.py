"""Render the planning documents only; never reads listing or buyer data."""
from pathlib import Path
from markdown_it import MarkdownIt

root = Path(__file__).resolve().parent
md = MarkdownIt('commonmark', {'html': False}).enable('table')
spec = (root/'standards/HOUSING-GATES-v1.0.md').read_text(encoding='utf-8')
plan = (root/'plans/2026-11-03-v2-gate-execution-plan.md').read_text(encoding='utf-8')
body = md.render(spec) + '<hr><section id="plan">' + md.render(plan) + '</section>'
page = '''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chuẩn 5 gate và kế hoạch v2</title><link rel="stylesheet" href="gate-doc.css"></head>
<body><nav><strong>Tài liệu thiết kế — chưa chạy gate trên v2</strong><br>
<a href="#plan">Đến kế hoạch và phân vai</a></nav>
<p>Flow: G1 phạm vi → G2 khả thi → G3 nền tảng → G4 ưu tiên → G5 giao dịch.
Thiếu bằng chứng đi vào nhánh nghiên cứu, không tự vượt gate.</p>''' + body + '</body></html>'
(root/'standards/HOUSING-GATES-v1.0.html').write_text(page, encoding='utf-8')
print('Rendered', len(page.encode('utf-8')), 'bytes')
