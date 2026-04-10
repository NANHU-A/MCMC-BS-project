import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path

def pdf_to_markdown(pdf_path: str, output_md: str = None):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"文件不存在: {pdf_path}")
        return

    md_content = []
    md_content.append(f"# {pdf_path.stem}\n\n")

    # 方案A：pdfplumber（推荐，提取表格和文本最准）
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                md_content.append(f"## Page {i}\n\n{text}\n\n")

    # 方案B：PyMuPDF 备用（保留更多布局）
    # doc = fitz.open(pdf_path)
    # for i, page in enumerate(doc, 1):
    #     text = page.get_text("text")
    #     md_content.append(f"## Page {i}\n\n{text}\n\n")

    output_md = output_md or pdf_path.with_suffix(".md")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("".join(md_content))
    print(f"✅ 转换完成 → {output_md}")

# 使用示例（把路径改成你实际的 PDF 文件路径）
pdf_to_markdown("C:\\Users\\16376\\Desktop\\毕业论文\\开题\\文件2-武汉大学本科生毕业论文（设计）书写印制规范（2024版）.pdf")
pdf_to_markdown("C:\\Users\\16376\\Desktop\\毕业论文\\开题\\文件3-武汉大学本科生毕业论文（设计）参考模板（2024版）.pdf")
