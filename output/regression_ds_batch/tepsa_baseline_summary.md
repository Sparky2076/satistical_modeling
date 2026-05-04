# TESSA-PSA baseline regressions

- **Input**: `data\tessa_psa\obs_macro_preview.csv`
- **Rows used (after filter)**: 600
- **run_id filter**: `ds_batch`
- **min_cell** (drop sparse FE levels): 5
- **SE**: HC1 robust

## M1 `log_cost ~ log_tokens + C(policy_id)`

- N = 600, R² = 0.9997

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               log_cost   R-squared:                       1.000
Model:                            OLS   Adj. R-squared:                  1.000
Method:                 Least Squares   F-statistic:                 8.032e+05
Date:                Mon, 04 May 2026   Prob (F-statistic):               0.00
Time:                        12:19:37   Log-Likelihood:                 1198.4
No. Observations:                 600   AIC:                            -2391.
Df Residuals:                     597   BIC:                            -2378.
Df Model:                           2                                         
Covariance Type:                  HC1                                         
===================================================================================================
                                      coef    std err          z      P>|z|      [0.025      0.975]
---------------------------------------------------------------------------------------------------
Intercept                         -15.8882      0.023   -698.599      0.000     -15.933     -15.844
C(policy_id)[T.pl_deepseek_pro]     2.4980      0.003    830.304      0.000       2.492       2.504
log_tokens                          1.1095      0.004    315.345      0.000       1.103       1.116
==============================================================================
Omnibus:                      220.997   Durbin-Watson:                   1.688
Prob(Omnibus):                  0.000   Jarque-Bera (JB):             1128.779
Skew:                          -1.569   Prob(JB):                    7.74e-246
Kurtosis:                       8.942   Cond. No.                         77.3
==============================================================================

Notes:
[1] Standard Errors are heteroscedasticity robust (HC1)
```

## M2 `quality_score ~ log_tokens + C(tepsa_sector)`

- N = 588, R² = 0.6376

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:          quality_score   R-squared:                       0.638
Model:                            OLS   Adj. R-squared:                  0.635
Method:                 Least Squares   F-statistic:                     196.7
Date:                Mon, 04 May 2026   Prob (F-statistic):          1.72e-122
Time:                        12:19:37   Log-Likelihood:                -990.80
No. Observations:                 588   AIC:                             1994.
Df Residuals:                     582   BIC:                             2020.
Df Model:                           5                                         
Covariance Type:                  HC1                                         
=========================================================================================================
                                            coef    std err          z      P>|z|      [0.025      0.975]
---------------------------------------------------------------------------------------------------------
Intercept                                -3.0132      0.689     -4.372      0.000      -4.364      -1.662
C(tepsa_sector)[T.education]             -1.3921      0.261     -5.328      0.000      -1.904      -0.880
C(tepsa_sector)[T.enterprise_support]     0.7922      0.236      3.364      0.001       0.331       1.254
C(tepsa_sector)[T.manufacturing]          1.0155      0.248      4.100      0.000       0.530       1.501
C(tepsa_sector)[T.public_service]         0.9822      0.243      4.043      0.000       0.506       1.458
log_tokens                                1.5555      0.105     14.804      0.000       1.350       1.761
==============================================================================
Omnibus:                       99.556   Durbin-Watson:                   1.135
Prob(Omnibus):                  0.000   Jarque-Bera (JB):              340.734
Skew:                          -0.766   Prob(JB):                     1.02e-74
Kurtosis:                       6.400   Cond. No.                         74.3
==============================================================================

Notes:
[1] Standard Errors are heteroscedasticity robust (HC1)
```

## M3 value_score ~ log_tokens + C(policy_id)

Skipped: insufficient non-missing value_score or fewer than 2 policies.