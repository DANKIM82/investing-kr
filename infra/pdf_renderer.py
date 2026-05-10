#!/usr/bin/env python3
"""
pdf_renderer.py - HTML/Markdown -> PDF 변환

WeasyPrint 또는 reportlab fallback 사용.

CLI:
    python infra/pdf_renderer.py --input report.html --output report.pdf
    python infra/pdf_renderer.py --markdown report.md --output report.pdf
"""

import argparse
import json
import os
import sys


HTML_WRAPPER = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: 'Noto Sans CJK KR', 'Malgun Gothic', sans-serif; line-height: 1.6; color: #1a1a1a; }}
  h1 {{ font-size: 24pt; border-bottom: 2px solid #1a1a1a; padding-bottom: 6pt; }}
  h2 {{ font-size: 16pt; margin-top: 16pt; }}
  h3 {{ font-size: 13pt; color: #333; }}
  table {{ width: 100%; border-collapse: collapse; margin: 10pt 0; font-size: 10pt; }}
  th, td {{ padding: 6pt; border: 1px solid #ccc; }}
  th {{ background: #f5f5f5; font-weight: bold; }}
  td:first-child {{ text-align: left; }}
  td:not(:first-child) {{ text-align: right; }}
  a {{ color: #0066cc; text-decoration: none; }}
  .footer {{ margin-top: 20pt; padding-top: 10pt; border-top: 1pt solid #ccc; font-size: 9pt; color: #666; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def markdown_to_html(md_text):
    try:
        import markdown
        return markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    except ImportError:
        return f"<pre>{md_text}</pre>"


def render_pdf(html_content, output_path, title="Report"):
    full_html = HTML_WRAPPER.format(title=title, body=html_content)
    
    # WeasyPrint 시도
    try:
        from weasyprint import HTML
        HTML(string=full_html).write_pdf(output_path)
        return True
    except ImportError:
        print("[warn] WeasyPrint 미설치. pip install weasyprint 권장.", file=sys.stderr)
    except Exception as e:
        print(f"[warn] WeasyPrint 실패: {e}", file=sys.stderr)
    
    # Fallback: HTML 그대로 저장
    fallback_path = output_path.replace(".pdf", ".html")
    with open(fallback_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[info] PDF 생성 실패, HTML로 저장: {fallback_path}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="HTML 파일")
    parser.add_argument("--markdown", help="Markdown 파일")
    parser.add_argument("--output", required=True, help="출력 PDF 경로")
    parser.add_argument("--title", default="Report")
    args = parser.parse_args()
    
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            content = f.read()
        if "<html" not in content.lower():
            content = f"<div>{content}</div>"
    elif args.markdown:
        with open(args.markdown, encoding="utf-8") as f:
            md = f.read()
        content = markdown_to_html(md)
    else:
        print("--input 또는 --markdown 필요", file=sys.stderr)
        sys.exit(1)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    success = render_pdf(content, args.output, args.title)
    
    print(json.dumps({"output": args.output, "success": success}, ensure_ascii=False))


if __name__ == "__main__":
    main()
