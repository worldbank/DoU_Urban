import os
import pandas as pd

def combine_and_summarize_data(years):
    homedir = os.getcwd()

    combined_adm0 = pd.DataFrame()
    combined_adm1 = pd.DataFrame()
    combined_adm2 = pd.DataFrame()
    combined_adm3 = pd.DataFrame()

    for year in years:
        outdir = os.path.join(homedir, "Input") #this is the directory code
        outdir2 = os.path.join(homedir, "Output") #this is the second directory code

        input_dir = os.path.join(outdir, year)
        output_dir = os.path.join(outdir2, year)

        all_files = os.listdir(output_dir)

        for file in all_files:
            if os.path.isfile(os.path.join(output_dir, file)) and len(file) >= 4 and file[-4:] == ".csv":
                df = pd.read_csv(os.path.join(output_dir, file))
                df['year'] = year
                if 'PAK_adm0' in file:
                    combined_adm0 = pd.concat([combined_adm0, df], ignore_index=True)
                if 'PAK_adm1' in file:
                    combined_adm1 = pd.concat([combined_adm1, df], ignore_index=True)
                if 'PAK_adm2' in file:
                    combined_adm2 = pd.concat([combined_adm2, df], ignore_index=True)
                if 'PAK_adm3' in file:
                    combined_adm3 = pd.concat([combined_adm3, df], ignore_index=True)

        # Additional processing or modifications if needed...

    # Save to CSV in homedir without including the year in the filename
    combined_adm0.to_csv(os.path.join(outdir2, "PAK_ADM0.csv"), index=False)
    combined_adm1.to_csv(os.path.join(outdir2, "PAK_ADM1.csv"), index=False)
    combined_adm2.to_csv(os.path.join(outdir2, "PAK_ADM2.csv"), index=False)
    combined_adm3.to_csv(os.path.join(outdir2, "PAK_ADM3.csv"), index=False)

    # Save to Excel
    writer = pd.ExcelWriter(os.path.join(outdir2, 'PAK_TREND_GHSSMOD.xlsx'))
    for k in ["PAK_ADM0.csv", "PAK_ADM1.csv", "PAK_ADM2.csv", "PAK_ADM3.csv"]:
        df = pd.read_csv(os.path.join(outdir2, k))
        df['total'] = df[['sum_10', 'sum_11', 'sum_12', 'sum_13', 'sum_21', 'sum_22', 'sum_23', 'sum_30']].values.sum(axis=1)
        df['perc_10'] = (df['sum_10'] / df['total'])
        df['perc_11'] = (df['sum_11'] / df['total'])
        df['perc_12'] = (df['sum_12'] / df['total'])
        df['perc_13'] = (df['sum_13'] / df['total'])
        df['perc_21'] = (df['sum_21'] / df['total'])
        df['perc_22'] = (df['sum_22'] / df['total'])
        df['perc_23'] = (df['sum_23'] / df['total'])
        df['perc_30'] = (df['sum_30'] / df['total'])
        df['perc_total'] = df[['perc_10', 'perc_11', 'perc_12', 'perc_13', 'perc_21', 'perc_22', 'perc_23', 'perc_30']].values.sum(axis=1)
        df.iloc[:, 2:].to_csv(os.path.join(outdir2, k), index=False)
        df.to_excel(writer, sheet_name=k, index=False)
    writer.close()

# Usage
years_to_process = ["1975", "1980", "1985", "1990", "1995", "2000","2005","2010","2015","2020", "2025", "2030"]
combine_and_summarize_data(years_to_process)


