import pandas as pd
import numpy as np

# -----------------------------
# 1. OD-level undersampling
# -----------------------------
def undersample_by_od(df, od_cols=("Origin", "Destination"), cap=None, cap_pct=0.8, random_state=42):
    """
    Perform undersampling based on Origin–Destination pairs.

    Parameters:
        df (pd.DataFrame) : Input dataframe
        od_cols (tuple)   : Columns used as grouping key (Origin, Destination)
        cap (int)         : Max samples per OD (if None, computed from percentile)
        cap_pct (float)   : Percentile (0-1). Eg: 0.8 = 80th percentile of OD sizes
        random_state (int): Random seed for reproducibility
    
    Returns:
        pd.DataFrame : Undersampled dataframe
    """
    df = df.copy()
    
    # If cap not given, calculate from percentile of OD sizes
    if cap is None:
        counts = df.groupby(list(od_cols)).size()
        cap = int(np.percentile(counts.values, cap_pct*100))
        cap = max(cap, 1)

    # Apply undersampling per OD group
    sampled = (
        df.groupby(list(od_cols), group_keys=False)
          .apply(lambda g: g.sample(n=min(len(g), cap), random_state=random_state))
    )
    return sampled


# -----------------------------
# 2. OD + LeadDays bucket undersampling
# -----------------------------
def undersample_by_od_leadbin(df, 
                              od_cols=("Origin", "Destination"), 
                              lead_col="LeadDays",
                              binning="fixed",   # "fixed" or "quantile"
                              q=3,
                              cap=None, 
                              cap_pct=0.8, 
                              random_state=42):
    """
    Perform undersampling based on OD + LeadDays buckets.
    
    Buckets:
        - "fixed": Short (0–7), Medium (8–30), Long (>30)
        - "quantile": q equal-frequency bins
    """
    df = df.copy()

    # Step 1: Create LeadDays bins
    if binning == "quantile":
        df["LeadBin"] = pd.qcut(df[lead_col], q=q, labels=[f"Q{i+1}" for i in range(q)], duplicates="drop")
    else:  # fixed buckets
        max_ld = int(df[lead_col].max())
        bins = [0, 7, 30, max_ld]
        labels = ["Short", "Medium", "Long"]
        df["LeadBin"] = pd.cut(df[lead_col], bins=bins, labels=labels, include_lowest=True, right=True)

    # Step 2: Find cap
    group_cols = list(od_cols) + ["LeadBin"]
    if cap is None:
        counts = df.groupby(group_cols).size()
        cap = int(np.percentile(counts.values, cap_pct*100))
        cap = max(cap, 1)

    # Step 3: Apply undersampling
    sampled = (
        df.groupby(group_cols, group_keys=False)
          .apply(lambda g: g.sample(n=min(len(g), cap), random_state=random_state))
    )
    return sampled
