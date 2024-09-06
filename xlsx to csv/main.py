# transform the data from .xlsx files to .csv files

import pandas as pd
import os

# the core tramformation function
def transform(file_name):
    # read all the pages in the excel file
    data = pd.ExcelFile(file_name)
    for sheet_name in data.sheet_names:
        data = pd.read_excel(file_name, sheet_name = sheet_name)
        data.to_csv(file_name[:-5] + '_' + sheet_name + '.csv', index = False, encoding='utf-8')

if __name__ == "__main__":
    for file in os.listdir("xlsx_files"):
        if file.endswith(".csv"):
            os.remove("xlsx_files/" + file)

    for excel_file in os.listdir("xlsx_files"):
        if excel_file.endswith(".xlsx"):
            transform("xlsx_files/" + excel_file)
            print(f"{excel_file} has been transformed to csv file")
    