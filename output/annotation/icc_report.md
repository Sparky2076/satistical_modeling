# Annotation inter-rater report

- **Input**: `data\tessa_psa\human_labels.csv`
- **Rows**: 1417
- **Unique keys** `(task_id, policy_id, run_id)`: 1417
- **Keys with ≥2 rows or ≥2 distinct annotator_id**: 0

## Result

**ICC not computed**: no duplicate keys with multiple raters. To report ICC in the paper,
pilot a subset with **two human annotators** per `(task_id, policy_id, run_id)` (wide table
or two rows per key), then use `pingouin.intraclass_corr` or Stata/R. Optional deps:
`requirements-annotation.txt`.
