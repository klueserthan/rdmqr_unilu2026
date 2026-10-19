# Presentation grading

Each presentation has its own folder, `presentations/sessionNN/`, with three files:

- `sessionNN_handwritten.pdf`: the grading sheet with the header (session, date, presenters, paper) already filled in. Annotate it by hand on the iPad during the talk and save it in place.
- `sessionNN.yml`: header prefilled from `00_admin/presentation_schedule.csv` (check it), scores and comments left empty.
- `sessionNN_grading_sheet.pdf`: the sheet for the students, rendered from the YAML.

1. During the talk, annotate `sessionNN_handwritten.pdf`.
2. Afterwards, give Claude the scores and notes (typed, dictated, or just point to the annotated PDF).
3. Claude fills in the scores and polished, student-facing comments in `sessionNN.yml`, then runs:

   ```bash
   python3 00_grading/fill_grading_sheet.py 00_grading/presentations/sessionNN/sessionNN.yml
   ```

   This produces `sessionNN_grading_sheet.pdf` in the same folder. Everything on the sheet comes from the YAML; only the total and grade are computed, from the table on the sheet.
4. Check the PDF, then send it to the presenters. Pairs and groups get one sheet with the same grade.

A fresh blank copy (only if the handwritten one is missing; it refuses to overwrite an existing file):

```bash
python3 00_grading/fill_grading_sheet.py --blank 00_grading/presentations/sessionNN/sessionNN.yml
```

`presentations/` is git-ignored (this repo is a public fork); it is the archive of handwritten sheets, YAMLs and rendered PDFs.

```yaml
session: 4
date: "08.10.26"
presenters: [Name One, Name Two]
paper: "Author (Year), Short title"
scores: {clarity: 4, understanding: 5, critique: 3, reasoning: 4, feasibility: 3, discussion: 4}
comments: |
  First paragraph.

  Second paragraph.
```

Self-check of the grade table: `python3 00_grading/fill_grading_sheet.py --check`
