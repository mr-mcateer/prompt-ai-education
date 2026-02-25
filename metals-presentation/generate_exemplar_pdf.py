#!/usr/bin/env python3
"""
Generate a polished, print-ready HTML of the complete exemplar portfolio.
Saves HTML to Downloads and opens in browser for Print > Save as PDF.

Usage:
    python3 generate_exemplar_pdf.py
"""

import sys
import os
import subprocess

# Add parent dir for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Import page generators from the main script
import importlib.util
exec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canvas_exemplar_portfolio.py")
spec = importlib.util.spec_from_file_location("exemplar", exec_path)
mod = importlib.util.module_from_spec(spec)

# Patch sys.argv to prevent argparse from running
_orig_argv = sys.argv
sys.argv = [exec_path, "--dry-run"]
spec.loader.exec_module(mod)
sys.argv = _orig_argv

VehicleProfile = mod.VehicleProfile
PAGE_REGISTRY = mod.PAGE_REGISTRY


def build_full_html():
    """Build complete HTML document with all 16 pages, styled for print."""
    v = VehicleProfile()
    pages_html = []

    for num in sorted(PAGE_REGISTRY.keys()):
        gen_fn, asgn_name = PAGE_REGISTRY[num]
        title, body = gen_fn(v)
        pages_html.append(f"""
<div class="portfolio-page">
  <div class="page-header">
    <span class="page-label">Page {num} of 16</span>
    <span class="assignment-label">{asgn_name}</span>
  </div>
  {body}
</div>
""")

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Mr. McAteer's Prius Decision</title>
<style>
  @media print {{
    @page {{
      size: letter;
      margin: 0.6in 0.6in 0.75in 0.6in;
    }}
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}

  * {{ box-sizing: border-box; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #2c3e50;
    margin: 0;
    padding: 0;
    background: white;
  }}

  /* ===================== TITLE PAGE ===================== */
  .title-page {{
    page-break-after: always;
    text-align: center;
    padding-top: 2.2in;
    min-height: 9in;
  }}
  .title-page h1 {{
    font-size: 28pt;
    color: #1a5276;
    margin: 0 0 6px 0;
    font-weight: 700;
    letter-spacing: -0.5px;
    border-bottom: none;
  }}
  .title-page .subtitle {{
    font-size: 15pt;
    color: #2980b9;
    margin-bottom: 28px;
    font-weight: 400;
  }}
  .title-page .divider {{
    width: 240px;
    height: 3px;
    background: linear-gradient(to right, #2980b9, #1a5276);
    margin: 24px auto;
  }}
  .title-page .vehicle-info {{
    font-size: 11.5pt;
    color: #555;
    margin: 4px 0;
  }}
  .title-page .author {{
    font-size: 13pt;
    color: #2c3e50;
    margin-top: 48px;
    font-weight: 600;
  }}
  .title-page .course {{
    font-size: 10.5pt;
    color: #666;
    margin-top: 3px;
  }}
  .title-page .date {{
    font-size: 10.5pt;
    color: #888;
    margin-top: 20px;
  }}

  /* ================ TABLE OF CONTENTS ================ */
  .toc-page {{
    page-break-after: always;
    max-width: 650px;
    margin: 0 auto;
    padding-top: 20px;
  }}
  .toc-page h2 {{
    font-size: 17pt;
    color: #1a5276;
    border-bottom: 2px solid #2980b9;
    padding-bottom: 5px;
    margin-bottom: 14px;
    background: none !important;
    border-left: none !important;
  }}
  .toc-table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .toc-table td {{
    padding: 6px 5px;
    border-bottom: 1px dotted #ccc;
    font-size: 10pt;
    vertical-align: middle;
  }}
  .toc-table .toc-num {{
    width: 28px;
    color: #2980b9;
    font-weight: 700;
    text-align: center;
  }}
  .toc-table .toc-pts {{
    width: 55px;
    text-align: right;
    color: #888;
    font-size: 9pt;
  }}
  .toc-table tr.toc-total td {{
    border-top: 2px solid #1a5276;
    border-bottom: none;
    font-weight: bold;
    padding-top: 10px;
    color: #1a5276;
  }}

  /* ================ PORTFOLIO PAGES ================ */
  .portfolio-page {{
    page-break-before: always;
    max-width: 750px;
    margin: 0 auto;
    padding: 0 10px;
  }}
  .page-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    padding-bottom: 2px;
    border-bottom: 1px solid #eee;
  }}
  .page-label {{
    font-size: 7.5pt;
    color: #999;
    font-weight: 600;
  }}
  .assignment-label {{
    font-size: 7.5pt;
    color: #999;
    font-style: italic;
  }}

  /* ========== Override inline Canvas HTML styles ========== */
  .portfolio-page div[style] {{
    max-width: 100% !important;
    margin: 0 !important;
  }}
  .portfolio-page h1 {{
    font-size: 15pt !important;
    color: #1a5276 !important;
    margin: 0 0 6px 0 !important;
    padding: 6px 0 !important;
    border-bottom: 2px solid #2980b9 !important;
  }}
  .portfolio-page h2 {{
    font-size: 12pt !important;
    color: #1a5276 !important;
    margin: 12px 0 5px 0 !important;
    padding: 4px 8px !important;
    background: #eaf2f8 !important;
    border-left: 3px solid #2980b9 !important;
  }}
  .portfolio-page table {{
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 6px 0 !important;
    font-size: 8.5pt !important;
  }}
  .portfolio-page th {{
    background: #1a5276 !important;
    color: white !important;
    padding: 4px 6px !important;
    font-size: 8pt !important;
    text-align: left !important;
  }}
  .portfolio-page td {{
    padding: 3px 6px !important;
    border-bottom: 1px solid #dee2e6 !important;
    font-size: 8.5pt !important;
    vertical-align: top !important;
  }}
  .portfolio-page tr:nth-child(even) td {{
    background: #f8f9fa !important;
  }}
  .portfolio-page p {{
    margin: 5px 0 !important;
    font-size: 9.5pt !important;
  }}
  .portfolio-page ul, .portfolio-page ol {{
    margin: 3px 0 !important;
    padding-left: 18px !important;
  }}
  .portfolio-page li {{
    margin: 2px 0 !important;
    font-size: 9pt !important;
  }}
  .portfolio-page em {{
    font-size: 8.5pt !important;
    color: #666 !important;
  }}
  .portfolio-page a {{
    color: #2980b9 !important;
    text-decoration: none !important;
  }}
  .portfolio-page caption {{
    font-size: 8pt !important;
    color: #666 !important;
    font-style: italic !important;
    text-align: left !important;
    margin-bottom: 2px !important;
  }}

  /* Avoid breaking inside tables */
  table, tr {{ page-break-inside: avoid; }}
</style>
</head>
<body>

<!-- Title Page -->
<div class="title-page">
  <h1>Mr. McAteer's Prius Decision</h1>
  <div class="subtitle">What Nobody Teaches You About Owning a Car</div>
  <div class="divider"></div>
  <div class="vehicle-info">2015 Toyota Prius Two -- White</div>
  <div class="vehicle-info">80,000 miles -- $12,000 Purchase</div>
  <div class="vehicle-info">Corvallis, Oregon</div>
  <div class="author">Andrew McAteer</div>
  <div class="course">Engines &amp; Fabrication -- Crescent Valley High School</div>
  <div class="course">Bend-La Pine Schools (CSD 509J)</div>
  <div class="date">Exemplar Portfolio -- February 2026</div>
</div>

<!-- Table of Contents -->
<div class="toc-page">
  <h2>Portfolio Contents</h2>
  <table class="toc-table">
    <tr><td class="toc-num">01</td><td>Your First Car Is Probably a Bad Deal</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">02</td><td>Everything on the Sticker They Hope You Won't Read</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">03</td><td>The Most Expensive Room in the Dealership</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">04</td><td>Insurance: You're Required to Buy It, You Should Understand It</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">05</td><td>The Car Payment Is the Smallest Part</td><td class="toc-pts">25 pts</td></tr>
    <tr><td class="toc-num">06</td><td>Four Patches of Rubber Between You and the Road</td><td class="toc-pts">15 pts</td></tr>
    <tr><td class="toc-num">07</td><td>The 3,000-Mile Myth</td><td class="toc-pts">15 pts</td></tr>
    <tr><td class="toc-num">08</td><td>Trust, But Verify</td><td class="toc-pts">15 pts</td></tr>
    <tr><td class="toc-num">09</td><td>What the Seller Won't Tell You</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">10</td><td>Stranded Is a Plan You Didn't Make</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">11</td><td>Free Repairs You Didn't Know You Had</td><td class="toc-pts">15 pts</td></tr>
    <tr><td class="toc-num">12</td><td>The Word 'No' Is Worth Thousands</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">13</td><td>Every Mile Is on Your Record</td><td class="toc-pts">15 pts</td></tr>
    <tr><td class="toc-num">14</td><td>The Breakeven Point</td><td class="toc-pts">20 pts</td></tr>
    <tr><td class="toc-num">15</td><td>The Drivetrain Is Changing</td><td class="toc-pts">25 pts</td></tr>
    <tr><td class="toc-num">16</td><td>Your Owner's Manual for Owning a Car (Capstone)</td><td class="toc-pts">50 pts</td></tr>
    <tr class="toc-total"><td></td><td>Total Portfolio Points</td><td class="toc-pts" style="font-weight: bold; color: #1a5276;">315 pts</td></tr>
  </table>
</div>

<!-- Portfolio Pages -->
{"".join(pages_html)}

</body>
</html>"""
    return full_html


def main():
    html_path = os.path.expanduser("~/Downloads/Mr_McAteers_Prius_Decision.html")

    print("Generating exemplar portfolio HTML...")
    html_content = build_full_html()
    print(f"  HTML: {len(html_content):,} characters")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  Saved: {html_path}")

    # Open in default browser
    subprocess.run(["open", html_path])
    print("  Opened in browser. Use Cmd+P > Save as PDF to save as:")
    print(f"    ~/Downloads/Mr_McAteers_Prius_Decision.pdf")
    print("Done.")


if __name__ == "__main__":
    main()
