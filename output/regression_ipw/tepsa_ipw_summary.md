# TESSA-PSA binary IPW (Hajek) + overlap

- **Input**: `data\tessa_psa\obs_macro_preview.csv`
- **run_id**: `(none)`
- **Outcome**: `quality_score`
- **Treatment**: `policy_id == 'pl_deepseek_pro'` (else 0)
- **Propensity**: logit `T ~ C(difficulty_label) + C(risk_class) + C(tepsa_sector)`
- **p clipping**: [0.05, 0.95]
- **N**: 1239 (after Z completeness + min cell ≥5 per Z level)

## Overlap (fitted p = P(T=1|Z))

- Treated n = 298, control n = 941
- p among treated — min/median/max: `0.2043` / `0.2491` / `0.2697`
- p among control — min/median/max: `0.2043` / `0.2491` / `0.2697`

## Hajek ATE (population mean difference, IPW)

- E[Y|T=1] ≈ `7.729635`
- E[Y|T=0] ≈ `6.549266`
- **ATE** ≈ `1.180370`

*解释*：在可交换性/无未测混杂等假设下对 ATE 的加权估计；本数据未必满足，故作**敏感性/对照**而非主因果结论。

```
                           Logit Regression Results                           
==============================================================================
Dep. Variable:                      T   No. Observations:                 1239
Model:                          Logit   Df Residuals:                     1230
Method:                           MLE   Df Model:                            8
Date:                Mon, 04 May 2026   Pseudo R-squ.:                0.003062
Time:                        15:44:58   Log-Likelihood:                -681.43
converged:                       True   LL-Null:                       -683.52
Covariance Type:            nonrobust   LLR p-value:                    0.8400
=========================================================================================================
                                            coef    std err          z      P>|z|      [0.025      0.975]
---------------------------------------------------------------------------------------------------------
Intercept                                -0.9940   2.34e+06  -4.25e-07      1.000   -4.59e+06    4.59e+06
C(difficulty_label)[T.hard]               0.0593      0.409      0.145      0.885      -0.743       0.862
C(difficulty_label)[T.medium]             0.0901      0.246      0.366      0.714      -0.392       0.572
C(risk_class)[T.low]                     -0.1659   2.34e+06  -7.09e-08      1.000   -4.59e+06    4.59e+06
C(risk_class)[T.medium]                   0.0007      0.394      0.002      0.998      -0.772       0.774
C(tepsa_sector)[T.education]              0.0736      0.255      0.289      0.773      -0.426       0.573
C(tepsa_sector)[T.enterprise_support]    -0.2001   2.34e+06  -8.55e-08      1.000   -4.59e+06    4.59e+06
C(tepsa_sector)[T.manufacturing]         -0.1723   2.34e+06  -7.37e-08      1.000   -4.59e+06    4.59e+06
C(tepsa_sector)[T.public_service]        -0.4556   2.34e+06  -1.95e-07      1.000   -4.59e+06    4.59e+06
=========================================================================================================
```
