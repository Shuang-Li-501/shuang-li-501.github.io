# ================================================================
# Bayesian Analysis of Student Performance
# Author: Shuang Li
# ================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import invgamma, norm

# ------------------------------------------------
# 1. Load Data
# ------------------------------------------------
df = pd.read_csv("StudentsPerformance.csv")

# Normalize column names
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
df.rename(columns={
    "math_score": "math",
    "reading_score": "reading",
    "writing_score": "writing",
    "parental_level_of_education": "parent_ed",
    "test_preparation_course": "test_prep"
}, inplace=True)

# ------------------------------------------------
# 2. Define Bayesian Posterior Functions
# ------------------------------------------------

def posterior_params(y, mu0=50, kappa0=0.001, alpha0=0.001, beta0=0.001):
    """Return posterior parameters for Normal-Inverse-Gamma conjugate prior."""
    n = len(y)
    ybar = np.mean(y)
    s2 = np.var(y, ddof=1)
    kappa_n = kappa0 + n
    mu_n = (kappa0 * mu0 + n * ybar) / kappa_n
    alpha_n = alpha0 + n / 2
    beta_n = beta0 + 0.5 * ((n - 1) * s2 + (kappa0 * n / kappa_n) * (ybar - mu0) ** 2)
    return mu_n, kappa_n, alpha_n, beta_n


def sample_posterior_mean(y, draws=10000, seed=42):
    """Draw posterior samples for group mean."""
    np.random.seed(seed)
    mu_n, kappa_n, alpha_n, beta_n = posterior_params(y)
    sigma2 = invgamma.rvs(alpha_n, scale=beta_n, size=draws)
    mu = norm.rvs(mu_n, np.sqrt(sigma2 / kappa_n))
    return mu


def compare_groups(df, group_col, subject, group_a, group_b, draws=10000):
    """Compare posterior mean difference between two groups."""
    yA = df.loc[df[group_col] == group_a, subject].dropna().values
    yB = df.loc[df[group_col] == group_b, subject].dropna().values
    muA = sample_posterior_mean(yA, draws=draws)
    muB = sample_posterior_mean(yB, draws=draws)
    diff = muA - muB
    return {
        "Comparison": f"{group_a} vs {group_b}",
        "Subject": subject,
        "Mean_Diff": diff.mean(),
        "CrI_Low": np.percentile(diff, 2.5),
        "CrI_High": np.percentile(diff, 97.5),
        "P(diff>0)": np.mean(diff > 0)
    }

# ------------------------------------------------
# 3. Define All Comparisons
# ------------------------------------------------

comparisons = [
    ("test_prep", "math", "completed", "none"),
    ("test_prep", "reading", "completed", "none"),
    ("test_prep", "writing", "completed", "none"),
    ("gender", "math", "female", "male"),
    ("gender", "reading", "female", "male"),
    ("gender", "writing", "female", "male"),
    ("lunch", "math", "standard", "free/reduced"),
    ("lunch", "reading", "standard", "free/reduced"),
    ("lunch", "writing", "standard", "free/reduced"),
    ("parent_ed", "math", "bachelor's degree", "some high school"),
    ("parent_ed", "reading", "bachelor's degree", "some high school"),
    ("parent_ed", "writing", "bachelor's degree", "some high school")
]

# ------------------------------------------------
# 4. Run Bayesian Comparisons
# ------------------------------------------------

results = []
for col, subj, a, b in comparisons:
    try:
        res = compare_groups(df, col, subj, a, b)
        results.append(res)
    except Exception as e:
        print(f"Skipped {col}-{subj}: {e}")

res_df = pd.DataFrame(results)
res_df.to_csv("bayesian_summary_results.csv", index=False)
print("\nSummary of Bayesian Comparisons:\n")
print(res_df.round(3))

# ------------------------------------------------
# 5. Create Forest Plots
# ------------------------------------------------

def forest_plot(subject):
    """Create a forest plot for a given subject."""
    data_sub = res_df[res_df["Subject"] == subject]
    fig, ax = plt.subplots(figsize=(7, 4))
    y_pos = np.arange(len(data_sub))
    ax.errorbar(
        data_sub["Mean_Diff"], y_pos,
        xerr=[data_sub["Mean_Diff"] - data_sub["CrI_Low"], data_sub["CrI_High"] - data_sub["Mean_Diff"]],
        fmt='o', color='black', ecolor='gray', elinewidth=2, capsize=4
    )
    ax.axvline(x=0, color='red', linestyle='--')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(data_sub["Comparison"])
    ax.set_xlabel("Posterior Mean Difference (A - B)")
    ax.set_title(f"{subject.title()} - Posterior Mean Differences (95% CrI)")
    plt.tight_layout()
    fig.savefig(f"forest_{subject}.png", dpi=300)
    plt.close(fig)

for subj in ["math", "reading", "writing"]:
    forest_plot(subj)

print("\nForest plots saved: forest_math.png, forest_reading.png, forest_writing.png")
print("Results saved to bayesian_summary_results.csv")

# ------------------------------------------------
# End of Script
# ------------------------------------------------
