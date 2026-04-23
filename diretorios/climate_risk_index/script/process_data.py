import pandas as pd

# File paths
input_file = r'C:\Users\rebecca-lara\Documents\Projetos\diretorios\climate_risk_index\data\raw_data\CELESC\Municipio-Mensal-3T-2025 (1).xlsx'
output_file = r'C:\Users\rebecca-lara\Documents\Projetos\diretorios\climate_risk_index\data\processed_data\processed_consumo_industrial.xlsx'

# Read the Excel file, only the "Consumo MWh" sheet
df = pd.read_excel(input_file, sheet_name='Consumo MWh')

# Convert Excel column letters to 0-based pandas indices
def excel_col_to_index(col):
    n = 0
    for c in col:
        n = n * 26 + (ord(c.upper()) - ord('A') + 1)
    return n - 1

# Columns to keep: A, F, H, and NE..NP
cols_to_keep = [excel_col_to_index('A'), excel_col_to_index('F'), excel_col_to_index('H')] + list(range(excel_col_to_index('NE'), excel_col_to_index('NP') + 1))
df = df.iloc[:, cols_to_keep]

# Filter rows where column H (index 2) is 'Industrial'
df = df[df.iloc[:, 2] == 'Industrial']

# Sum columns NE to NP and add as new column 'NQ'
sum_cols = df.iloc[:, 3:].sum(axis=1)
df['NQ'] = sum_cols

# Group by column F (index 1, 'Município') and sum 'NQ'
grouped = df.groupby(df.iloc[:, 1])['NQ'].sum().reset_index()

# Rename columns for clarity
grouped.columns = ['Município', 'Total_Consumo_Industrial']

# Save the processed data to Excel
grouped.to_excel(output_file, index=False)

print("Processing complete. File saved to:", output_file)