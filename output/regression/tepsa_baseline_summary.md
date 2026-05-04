# TESSA-PSA baseline regressions

- **Input**: `data\tessa_psa\obs_macro_preview.csv`
- **Rows used (after filter)**: 1268
- **run_id filter**: `(none)`
- **min_cell** (drop sparse FE levels): 5
- **SE**: HC1 robust
- **M3** `value_score`: 若 CSV 中 `value_score` 为空，则按 `tepsa_main.compute_value_score_row` 与主表相同默认参数重算为 `value_score_calc`。

## M1 `log_cost ~ log_tokens + C(policy_id)`

- N = 1267, R² = 0.9996

- **定位（价目—日志核对 / accounting check）**：不把本式当作因果识别或「政策解释力」；高 R² 反映 `cost_usd` 与公开价目×token 的**记账一致性**。

- **核对指标**（补充 R²，便于答辩「过拟合了吗」）：

  - log 残差 RMSE = `0.030023`；MAE = `0.021240`；|残差|中位数 = `0.016098`

  - 美元成本相对误差：均值 `0.0214`，中位数 `0.0160`（由 log 空间拟合反推 `cost`）

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               log_cost   R-squared:                       1.000
Model:                            OLS   Adj. R-squared:                  1.000
Method:                 Least Squares   F-statistic:                 5.396e+05
Date:                Mon, 04 May 2026   Prob (F-statistic):               0.00
Time:                        14:33:59   Log-Likelihood:                 2644.0
No. Observations:                1267   AIC:                            -5274.
Df Residuals:                    1260   BIC:                            -5238.
Df Model:                           6                                         
Covariance Type:                  HC1                                         
====================================================================================================
                                       coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------------------
Intercept                          -15.8442      0.018   -876.433      0.000     -15.880     -15.809
C(policy_id)[T.pl_deepseek_pro]      2.5028      0.003    883.397      0.000       2.497       2.508
C(policy_id)[T.pl_glm_47]            2.0207      0.004    543.124      0.000       2.013       2.028
C(policy_id)[T.pl_glm_47_flashx]     0.3085      0.003     93.900      0.000       0.302       0.315
C(policy_id)[T.pl_spark_max]        -0.0126      0.003     -4.727      0.000      -0.018      -0.007
C(policy_id)[T.pl_spark_ultra]       1.7624      0.003    560.928      0.000       1.756       1.769
log_tokens                           1.1024      0.003    397.201      0.000       1.097       1.108
==============================================================================
Omnibus:                      578.251   Durbin-Watson:                   1.421
Prob(Omnibus):                  0.000   Jarque-Bera (JB):             4492.272
Skew:                          -1.947   Prob(JB):                         0.00
Kurtosis:                      11.362   Cond. No.                         91.7
==============================================================================

Notes:
[1] Standard Errors are heteroscedasticity robust (HC1)
```

## M2 `quality_score ~ log_tokens + C(tepsa_sector)`

- N = 1239, R² = 0.4576

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:          quality_score   R-squared:                       0.458
Model:                            OLS   Adj. R-squared:                  0.455
Method:                 Least Squares   F-statistic:                     185.0
Date:                Mon, 04 May 2026   Prob (F-statistic):          4.26e-147
Time:                        14:33:59   Log-Likelihood:                -2503.6
No. Observations:                1239   AIC:                             5019.
Df Residuals:                    1233   BIC:                             5050.
Df Model:                           5                                         
Covariance Type:                  HC1                                         
=========================================================================================================
                                            coef    std err          z      P>|z|      [0.025      0.975]
---------------------------------------------------------------------------------------------------------
Intercept                                 0.4200      0.748      0.561      0.575      -1.047       1.887
C(tepsa_sector)[T.education]             -1.3623      0.262     -5.203      0.000      -1.875      -0.849
C(tepsa_sector)[T.enterprise_support]     1.9056      0.234      8.142      0.000       1.447       2.364
C(tepsa_sector)[T.manufacturing]          1.6830      0.252      6.677      0.000       1.189       2.177
C(tepsa_sector)[T.public_service]         1.8119      0.243      7.445      0.000       1.335       2.289
log_tokens                                0.8590      0.117      7.340      0.000       0.630       1.088
==============================================================================
Omnibus:                      119.918   Durbin-Watson:                   0.987
Prob(Omnibus):                  0.000   Jarque-Bera (JB):              171.081
Skew:                          -0.737   Prob(JB):                     7.08e-38
Kurtosis:                       4.068   Cond. No.                         84.0
==============================================================================

Notes:
[1] Standard Errors are heteroscedasticity robust (HC1)
```

## M3 `value_score ~ log_tokens + C(policy_id)`

- N = 1239, R² = 0.5162

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:        value_score_reg   R-squared:                       0.516
Model:                            OLS   Adj. R-squared:                  0.514
Method:                 Least Squares   F-statistic:                     903.8
Date:                Mon, 04 May 2026   Prob (F-statistic):               0.00
Time:                        14:33:59   Log-Likelihood:                -4035.6
No. Observations:                1239   AIC:                             8085.
Df Residuals:                    1232   BIC:                             8121.
Df Model:                           6                                         
Covariance Type:                  HC1                                         
====================================================================================================
                                       coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------------------
Intercept                          -16.4929      2.472     -6.672      0.000     -21.338     -11.648
C(policy_id)[T.pl_deepseek_pro]     -1.1727      0.372     -3.151      0.002      -1.902      -0.443
C(policy_id)[T.pl_glm_47]           14.8525      0.603     24.651      0.000      13.672      16.033
C(policy_id)[T.pl_glm_47_flashx]    14.3527      0.639     22.447      0.000      13.099      15.606
C(policy_id)[T.pl_spark_max]         9.7071      0.632     15.355      0.000       8.468      10.946
C(policy_id)[T.pl_spark_ultra]      12.5674      0.612     20.530      0.000      11.368      13.767
log_tokens                           2.1133      0.405      5.214      0.000       1.319       2.908
==============================================================================
Omnibus:                       64.111   Durbin-Watson:                   0.325
Prob(Omnibus):                  0.000   Jarque-Bera (JB):              106.742
Skew:                          -0.405   Prob(JB):                     6.63e-24
Kurtosis:                       4.188   Cond. No.                         92.1
==============================================================================

Notes:
[1] Standard Errors are heteroscedasticity robust (HC1)
```
