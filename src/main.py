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
        crop_type = row['作物类型']
        suitable_land = row['种植耕地'].split('\n')
        for year in years:
            for land in land_types:
                if land not in suitable_land:
                    model += planting_area[crop_name][land][year] == 0
                # Constraint for single-season grain crops (excluding rice) on specific land types, (1)
                if crop_type == '粮食' and crop_name != '水稻' and land in ['平旱地', '梯田', '山坡地']:
                    model += lpSum(planting_area[crop_name][land][year] for crop_name in crops if crop_type == '粮食' and crop_name != '水稻') <= 1
                # Constraint for irrigated land: either single-season rice or two-season vegetables, (2) and (3)
                if land == '水浇地':
                    rice_area = planting_area['水稻'][land][year]
                    vegetable_area = lpSum(planting_area[crop][land][year] for crop in crops if crop_type == '蔬菜')
                    model += (rice_area == 0) | (vegetable_area == 0)

                    # Constraint for cabbage, white radish, and red radish only in the second season, (4)
                    for crop in ['大白菜', '白萝卜', '红萝卜']:
                        model += planting_area[crop][land][year] == 0  # First season
                        model += planting_area[crop][land][year + 1] >= 0  # Second season

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
