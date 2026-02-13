import pandas as pd
from io import StringIO
from openpyxl.workbook import Workbook

# Paste your full CSV text here
csv_text = """"""
df = pd.read_csv(StringIO(csv_text))

# Quick inspection
print(df.shape)               # → (105, 6)
print(df['Part_Type'].value_counts())  # count by type
print(df['Date'].value_counts())       # group by date

# Optional: save to Excel
df.to_excel('rma_swaps_1.xlsx', index=False, engine='openpyxl')