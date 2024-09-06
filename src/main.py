import pandas as pd
import csv
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

def optimize_planting_strategy():
    # Define the problem
    model = LpProblem(name="planting-strategy", sense=LpMaximize)

    # Load crop and land data from CSV files
    crops_data = pd.read_csv('附件/附件(csv)/附件1_乡村种植的农作物.csv')
    land_data = pd.read_csv('附件/附件(csv)/附件1_乡村的现有耕地.csv')

    # Extract crops and land types
    crops = crops_data['作物名称'].unique()
    land_types = land_data['地块类型'].unique()
    years = range(2024, 2031)

    # Define decision variables
    planting_area = LpVariable.dicts("planting_area", (crops, land_types, years), lowBound=0)

    # Add constraints based on land availability
    for index, row in land_data.iterrows():
        land_type = row['地块类型']
        land_area = row['地块面积/亩']
        for year in years:
            model += lpSum(planting_area[crop][land_type][year] for crop in crops) <= land_area

    # Add crop-specific constraints
    for index, row in crops_data.iterrows():
        crop_name = row['作物名称']
        suitable_land = row['种植耕地'].split('\n')
        for year in years:
            for land in land_types:
                if land not in suitable_land:
                    model += planting_area[crop_name][land][year] == 0

    # Objective function (maximize profit)
    model += lpSum(planting_area[crop][land][year] * 100 for crop in crops for land in land_types for year in years)  # Example

    # Solve the problem
    model.solve()

    # Output results
    results = {year: {crop: {land: planting_area[crop][land][year].value() for land in land_types} for crop in crops} for year in years}
    df = pd.DataFrame(results)
    df.to_excel("result1_1.xlsx")

if __name__ == "__main__":
    optimize_planting_strategy()