import pandas as pd

df = pd.read_csv("dataset.csv")  # hoặc format của dataset đó

# 1. Xem cấu trúc
print(df.head())
print(df.columns.tolist())
print(df.dtypes)

# 2. Class distribution
print(df["label"].value_counts())
print(df["label"].value_counts(normalize=True).round(3))

# 3. Kiểm tra null
print(df.isnull().sum())

# 4. Độ dài request
df["request_len"] = df["request"].str.len()
print(df.groupby("label")["request_len"].describe())

# 5. Kiểm tra duplicate
print(f"Total rows: {len(df)}")
print(f"Exact duplicates: {df.duplicated().sum()}")
print(f"Request duplicates: {df['request'].duplicated().sum()}")

# 6. Near-duplicate check (tìm request giống nhau khác label) — quan trọng!
dup_req = df[df["request"].duplicated(keep=False)]
dup_diff_label = dup_req.groupby("request")["label"].nunique()
hard_cases = dup_diff_label[dup_diff_label > 1]
print(f"Requests with multiple labels (hard cases): {len(hard_cases)}")
