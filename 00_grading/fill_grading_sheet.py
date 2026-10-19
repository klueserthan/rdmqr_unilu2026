"""Render a filled presentation grading sheet from an evaluation YAML file.

    python3 00_grading/fill_grading_sheet.py 00_grading/presentations/session04/session04.yml
    python3 00_grading/fill_grading_sheet.py --blank 00_grading/presentations/session04/session04.yml
    python3 00_grading/fill_grading_sheet.py --check

Everything on the sheet comes from the YAML (session, date, presenters, paper,
scores, comments). --blank fills in only the header and writes
sessionNN_handwritten.pdf, the copy to annotate by hand during the talk.
The blank template presentation_grading_sheet.qmd stays the single source of
the layout.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "presentation_grading_sheet.qmd"
CRITERIA = ["clarity", "understanding", "critique", "reasoning", "feasibility", "discussion"]
# Lower bound of each points band -> grade, copied from the sheet's table.
GRADE_TABLE = [(29, "6.0"), (25, "5.5"), (21, "5.0"), (17, "4.5"), (15, "4.0"),
               (12, "3.5"), (9, "3.0"), (7, "2.5"), (4, "2.0"), (2, "1.5"), (0, "1.0")]


def grade(points):
    return next(g for lo, g in GRADE_TABLE if points >= lo)


def tex(s):
    out = str(s).replace("\\", r"\textbackslash{}")
    for c in "&%$#_{}":
        out = out.replace(c, "\\" + c)
    out = out.replace("~", r"\textasciitilde{}").replace("^", r"\textasciicircum{}")
    return re.sub(r'"([^"]*)"', r"``\1''", out)  # straight quotes -> typographic


def sub(text, old, new, count=1):
    assert text.count(old) == count, f"template changed: expected {count}x {old!r}"
    return text.replace(old, new)


def header(ev):
    missing = [k for k in ("session", "date", "presenters", "paper") if not ev.get(k)]
    assert not missing, f"YAML is missing: {missing}"
    presenters, paper, date = ev["presenters"], ev["paper"], ev["date"]
    if isinstance(presenters, str):
        presenters = [presenters]
    t = TEMPLATE.read_text()
    t = sub(t, r"Session: \rule{1.8cm}{0.4pt}", rf"Session: \textbf{{{ev['session']}}}")
    t = sub(t, r"Date: \rule{2.6cm}{0.4pt}", rf"Date: \textbf{{{tex(date)}}}")
    t = sub(t, r"Presenter(s): \rule{15cm}{0.4pt}", rf"Presenter(s): \textbf{{{tex(', '.join(presenters))}}}")
    t = sub(t, r"Paper: \rule{25.2cm}{0.4pt}", rf"Paper: \textbf{{{tex(paper)}}}")
    return t


def fill(ev):
    missing = [k for k in ("scores", "comments") if not ev.get(k)]
    assert not missing, f"YAML is missing: {missing}"
    t = header(ev)

    scores = ev["scores"]
    assert set(scores) == set(CRITERIA), f"scores need exactly: {CRITERIA}"
    assert all(isinstance(scores[c], int) and 0 <= scores[c] <= 5 for c in CRITERIA), "scores must be integers 0-5"
    total = sum(scores.values())

    cell = r" & \\[1.2em]"
    assert t.count(cell) == len(CRITERIA), "template changed: score cells"
    for c in CRITERIA:  # rows appear in CRITERIA order
        t = t.replace(cell, rf" & \textbf{{\large {scores[c]}}}\\[1.2em]", 1)
    t = sub(t, r"\rule{1.5cm}{0.4pt} / 30", rf"\textbf{{{total}}} / 30")
    t = sub(t, r"\textbf{Grade:} \rule{1.5cm}{0.4pt}", rf"\textbf{{Grade:}} \textbf{{{grade(total)}}}")
    comments = "\n\n".join(tex(p.strip()) for p in ev["comments"].strip().split("\n\n"))
    t = sub(t, "\\noindent\\rule{\\linewidth}{0.4pt}\\\\[14pt]\n\\noindent\\rule{\\linewidth}{0.4pt}", comments)
    return t, total


def render(qmd, out):
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "sheet.qmd"
        src.write_text(qmd)
        subprocess.run(["quarto", "render", str(src), "--to", "pdf", "-M", "pdf-engine:xelatex"], check=True, cwd=d)
        shutil.copy(Path(d) / "sheet.pdf", out)


def main(path, blank=False):
    path = Path(path)
    ev = yaml.safe_load(path.read_text())
    if blank:
        out = path.parent / f"{path.stem}_handwritten.pdf"
        assert not out.exists(), f"{out} exists; delete it first if you really want a fresh blank copy"
        render(header(ev), out)
        print(out)
        return
    qmd, total = fill(ev)
    out = path.parent / f"{path.stem}_grading_sheet.pdf"
    render(qmd, out)
    print(f"{out}  ({total}/30, grade {grade(total)})")


def check():
    assert [grade(p) for p in (30, 29, 28, 25, 24, 21, 20, 17, 16, 15, 14, 12, 11, 9, 8, 7, 6, 4, 3, 2, 1, 0)] == \
        ["6.0", "6.0", "5.5", "5.5", "5.0", "5.0", "4.5", "4.5", "4.0", "4.0", "3.5", "3.5",
         "3.0", "3.0", "2.5", "2.5", "2.0", "2.0", "1.5", "1.5", "1.0", "1.0"]
    assert tex('A & B 50% #1 "x"') == r"A \& B 50\% \#1 ``x''"
    print("ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--check"]:
        check()
    elif args[:1] == ["--blank"]:
        main(args[1], blank=True)
    else:
        main(args[0])
