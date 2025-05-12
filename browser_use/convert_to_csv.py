import pandas as pd
import json
from pathlib import Path
import re
from datetime import datetime

def transform_columns(row):
    """
    Function to transform the columns of the DataFrame.
    """
    # Remove leading and trailing whitespace from all string columns

    for col in row.index:
        if isinstance(row[col], str):
            row[col] = row[col].strip()

    row["descrizione"] = re.sub(r'\s+', ' ', row["descrizione"])
    row["titolo"] = re.sub(r'\s+', ' ', row["titolo"])
    for col in ["prezzo", "superficie", "locali", "bagni", "piano"]:
        try:
            value = re.search(r'([\d\.]+)', row[col]).group(0)
            value = value.replace('.', '')
            row[col] = int(value)
        except AttributeError:
            # Handle the case where the regex does not find a match
            pass

    return row

data = json.loads(
    Path("final_result.json").read_text(encoding="utf-8")
)

df = pd.DataFrame(data['immobili'])
df.reset_index(drop=True, inplace=True)

df = df.apply(
    lambda row: transform_columns(row),
    axis=1,
    result_type='expand'
)


print(df.columns)
print(len(df))

print(df.head())

df.to_csv(f"immobili_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)