
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

for file in sorted(DATA_DIR.glob("*.csv")):
    print("\n" + "=" * 60)
    print("DATASET:", file.name)
    print("=" * 60)

    try:
        df = pd.read_csv(file)

        print(f"Number of rows: {df.shape[0]}")
        print(f"Number of columns: {df.shape[1]}")

        print("\nColumn names:")
        for column in df.columns:
            print("-", column)

        print("\nFirst 3 rows:")
        print(df.head(3).to_string(index=False))

        print("\nTotal missing values:", int(df.isna().sum().sum()))

    except Exception as error:
        print("ERROR:", error)

print("\nDataset inspection finished.")

