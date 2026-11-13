"""
Generate Publication-Quality PDF from REPORT.md using Headless Chrome
"""

import os
import subprocess
import markdown_it

def build_pdf():
    report_md_path = os.path.join(os.path.dirname(__file__), 'REPORT.md')
    report_html_path = os.path.join(os.path.dirname(__file__), 'report_print.html')
    output_pdf_path = os.path.join(os.path.dirname(__file__), 'NetVibe_Project_Report.pdf')

    with open(report_md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    md = markdown_it.MarkdownIt("commonmark", {"breaks": True, "html": True})
    content_html = md.render(md_text)

    # Wrap in academic print CSS stylesheet
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>NetVibe - Project Report</title>
<style>
  @page {{
    size: A4;
    margin: 20mm 18mm 20mm 18mm;
  }}

  body {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1f2937;
    line-height: 1.6;
    font-size: 11pt;
  }}

  h1 {{
    font-size: 20pt;
    font-weight: 700;
    color: #111827;
    border-bottom: 2px solid #4f46e5;
    padding-bottom: 8px;
    margin-top: 0;
    margin-bottom: 12px;
  }}

  h2 {{
    font-size: 14pt;
    font-weight: 700;
    color: #1e1b4b;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 12px;
    page-break-after: avoid;
  }}

  h3 {{
    font-size: 12pt;
    font-weight: 600;
    color: #3730a3;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }}

  p, li {{
    color: #374151;
    text-align: justify;
  }}

  ul, ol {{
    padding-left: 24px;
    margin-bottom: 12px;
  }}

  li {{
    margin-bottom: 4px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}

  th, td {{
    border: 1px solid #d1d5db;
    padding: 8px 10px;
    text-align: left;
  }}

  th {{
    background-color: #f3f4f6;
    font-weight: 600;
    color: #111827;
  }}

  tr:nth-child(even) {{
    background-color: #f9fafb;
  }}

  pre {{
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    overflow-x: auto;
    page-break-inside: avoid;
    white-space: pre-wrap;
    word-break: break-all;
  }}

  code {{
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9.5pt;
    background-color: #f1f5f9;
    padding: 2px 4px;
    border-radius: 4px;
    color: #0f172a;
  }}

  pre code {{
    background: none;
    padding: 0;
  }}

  blockquote {{
    border-left: 4px solid #6366f1;
    margin: 14px 0;
    padding: 8px 16px;
    background-color: #f5f3ff;
    color: #4338ca;
  }}

  hr {{
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 20px 0;
  }}

  .page-break {{
    page-break-before: always;
  }}
</style>
</head>
<body>
{content_html}
</body>
</html>
"""

    with open(report_html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"[✓] Formatted HTML report generated: {report_html_path}")

    # Use Chrome to render PDF
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={output_pdf_path}",
        report_html_path
    ]

    print("[*] Rendering PDF with Chrome print engine...")
    subprocess.run(cmd, check=True)

    if os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0:
        size_kb = os.path.getsize(output_pdf_path) / 1024
        print(f"[✓] SUCCESS! PDF successfully created: {output_pdf_path} ({size_kb:.1f} KB)")
    else:
        print("[!] PDF generation failed.")

if __name__ == '__main__':
    build_pdf()
