import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base_path = ROOT / "results" / "opencode"
md_path = base_path / "本科毕业论文-终稿.md"
tmp_md_path = base_path / "_tmp_no_manual_toc.md"
tex_body_path = base_path / "overleaf_xelatex_code.txt"


def strip_manual_toc(text: str) -> str:
    start = "\n目录\n"
    marker = "\n第1章 绪论\n"
    if start in text and marker in text:
        i = text.index(start)
        j = text.index(marker)
        return text[:i] + "\n" + text[j + 1 :]
    return text


def convert_md_to_latex(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "pandoc",
            str(src),
            "--from",
            "gfm+implicit_figures",
            "--to",
            "latex",
            "-o",
            str(dst),
        ],
        check=True,
    )


def transform_latex_body(text: str) -> str:
    lines = text.splitlines()
    out = []

    title = "多提案 MCMC 算法在 Black-Scholes 期权定价中的效率研究"
    inserted_toc = False
    inserted_roman = False

    for line in lines:
        if "\\includegraphics[" in line and "alt={" in line:
            line = re.sub(r",\s*alt=\{[^}]*\}", "", line)

        s = line.strip()

        if s == title:
            continue

        if s == "封面":
            out.append(r"\clearpage")
            out.append(r"\section*{封面}")
            out.append(r"\thispagestyle{empty}")
            continue

        if s == "原创性声明和版权使用授权书":
            out.append(r"\clearpage")
            out.append(r"\section*{原创性声明和版权使用授权书}")
            out.append(r"\thispagestyle{empty}")
            continue

        if s == "中文摘要":
            if not inserted_roman:
                out.append(r"\clearpage")
                out.append(r"\pagenumbering{Roman}")
                inserted_roman = True
            out.append(r"\section*{中文摘要}")
            out.append(r"\addcontentsline{toc}{section}{中文摘要}")
            continue

        if s == "Abstract":
            out.append(r"\section*{Abstract}")
            out.append(r"\addcontentsline{toc}{section}{Abstract}")
            continue

        m_ch = re.match(r"^第([0-9]+)章\s+(.+)$", s)
        if m_ch:
            if not inserted_toc and m_ch.group(1) == "1":
                out.append(r"\clearpage")
                out.append(r"\tableofcontents")
                out.append(r"\clearpage")
                out.append(r"\pagenumbering{arabic}")
                inserted_toc = True
            out.append(rf"\section{{第{m_ch.group(1)}章 {m_ch.group(2)}}}")
            continue

        m_sec = re.match(r"^([0-9]+\.[0-9]+)\s+(.+)$", s)
        if m_sec:
            out.append(rf"\subsection{{{m_sec.group(1)} {m_sec.group(2)}}}")
            continue

        if s == "参考文献":
            out.append(r"\section{参考文献}")
            continue

        if s == "附录":
            out.append(r"\section{附录}")
            continue

        m_app = re.match(r"^附录([A-Z])\s+(.+)$", s)
        if m_app:
            out.append(rf"\subsection{{附录{m_app.group(1)} {m_app.group(2)}}}")
            continue

        out.append(line)

    return "\n".join(out) + "\n"


def main() -> None:
    raw = md_path.read_text(encoding="utf-8")
    cleaned = strip_manual_toc(raw)
    tmp_md_path.write_text(cleaned, encoding="utf-8")

    convert_md_to_latex(tmp_md_path, tex_body_path)

    body = tex_body_path.read_text(encoding="utf-8")
    body = transform_latex_body(body)
    tex_body_path.write_text(body, encoding="utf-8")


if __name__ == "__main__":
    main()
