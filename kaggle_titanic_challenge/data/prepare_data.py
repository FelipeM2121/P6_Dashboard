import seaborn as sns

df = sns.load_dataset("titanic")
# Drop redundant/duplicate columns kept by seaborn alongside the original Kaggle fields
df = df.drop(columns=["alive", "class", "who", "adult_male", "embark_town"])
df.to_csv("train.csv", index=False)
print(df.shape)
