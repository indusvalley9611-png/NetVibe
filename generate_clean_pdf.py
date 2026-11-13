"""
Generate a Clean, Simple, and Professional Academic PDF Report
Format: IEEE / Standard College Lab Submission Style
"""

import os
import subprocess
import markdown_it

def build_clean_pdf():
    report_md_path = os.path.join(os.path.dirname(__file__), 'REPORT.md')
    output_pdf_path = os.path.join(os.path.dirname(__file__), 'NetVibe_Project_Report.pdf')
    report_html_path = os.path.join(os.path.dirname(__file__), 'report_clean.html')

    with open(report_md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Convert Markdown to HTML
    md = markdown_it.MarkdownIt("commonmark", {"breaks": True, "html": True})
    content_html = md.render(md_text)

    # Clean, professional, academic styling
    styled_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Project Report - NetVibe LAN Chat</title>
<style>
  @page {{
    size: A4;
    margin: 22mm 20mm 22mm 20mm;
    @bottom-right {{
      content: counter(page);
      font-size: 9pt;
      color: #666;
    }}
  }}

  body {{
    font-family: 'Times New Roman', Times, Georgia, serif;
    color: #111111;
    line-height: 1.5;
    font-size: 11pt;
  }}

  /* Professional Header */
  .report-header {{
    text-align: center;
    border-bottom: 2px solid #222222;
    padding-bottom: 16px;
    margin-bottom: 24px;
  }}

  .institution {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #444444;
    margin-bottom: 6px;
  }}

  .title {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 18pt;
    font-weight: 700;
    color: #000000;
    margin: 10px 0;
    line-height: 1.3;
  }}

  .subtitle {{
    font-size: 11pt;
    color: #555555;
    margin-bottom: 14px;
    font-style: italic;
  }}

  .author-box {{
    display: flex;
    justify-content: space-around;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9.5pt;
    color: #333333;
    border-top: 1px solid #e0e0e0;
    padding-top: 10px;
    margin-top: 10px;
  }}

  /* Headings */
  h1 {{
    display: none; /* Hide the markdown h1 since we have custom header */
  }}

  h2 {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 12.5pt;
    font-weight: 700;
    color: #002b49;
    border-bottom: 1px solid #cccccc;
    padding-bottom: 4px;
    margin-top: 24px;
    margin-bottom: 10px;
    page-break-after: avoid;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  h3 {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    font-weight: 700;
    color: #222222;
    margin-top: 16px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}

  p {{
    text-align: justify;
    margin-bottom: 10px;
  }}

  ul, ol {{
    padding-left: 22px;
    margin-bottom: 10px;
  }}

  li {{
    margin-bottom: 3px;
  }}

  /* Professional Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 9pt;
    page-break-inside: avoid;
    font-family: Arial, Helvetica, sans-serif;
  }}

  th, td {{
    border: 1px solid #999999;
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
  }}

  th {{
    background-color: #f0f4f8;
    color: #000000;
    font-weight: 700;
  }}

  tr:nth-child(even) {{
    background-color: #fafafa;
  }}

  /* Code & Syntax */
  pre {{
    background-color: #f7f7f7;
    border: 1px solid #dddddd;
    border-radius: 4px;
    padding: 10px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8.5pt;
    overflow-x: auto;
    page-break-inside: avoid;
    white-space: pre-wrap;
    word-break: break-all;
    line-height: 1.4;
  }}

  code {{
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    background-color: #f2f2f2;
    padding: 1px 3px;
    border-radius: 3px;
    color: #111111;
  }}

  pre code {{
    background: none;
    padding: 0;
  }}

  blockquote {{
    border-left: 3px solid #002b49;
    margin: 12px 0;
    padding: 6px 12px;
    background-color: #f8f9fa;
    color: #333333;
    font-style: italic;
  }}

  hr {{
    border: none;
    border-top: 1px solid #dddddd;
    margin: 16px 0;
  }}
</style>
</head>
<body>

<div class="report-header">
  <div class="institution">Computer Networks Laboratory &bull; Mini-Project (CA-4)</div>
  <div class="title">LAN-Based Real-Time Chat Application Using Python Socket Programming</div>
  <div class="subtitle">Demonstrating Berkeley Sockets, TCP/IP Protocol, Multithreading, and Local Area Network Communication</div>
  <div class="author-box">
    <span><strong>Author:</strong> GOKUL P</span>
    <span><strong>Course:</strong> CS-3104 / CN-LAB</span>
    <span><strong>Academic Session:</strong> 2026&ndash;2027</span>
    <span><strong>Marks:</strong> 20 Marks</span>
  </div>
</div>

{content_html}

</body>
</html>
"""

    with open(report_html_path, 'w', encoding='utf-8') as f:
        f.write(styled_html)

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

    subprocess.run(cmd, check=True)
    size_kb = os.path.getsize(output_pdf_path) / 1024
    print(f"[✓] Professional clean PDF generated successfully: {output_pdf_path} ({size_kb:.1f} KB)")

if __name__ == '__main__':
    build_clean_pdf()
