import pandas as pd
from lib import *   # Import your custom library
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

# Load crop and land data from CSV files using a function from lib
crops_data, land_data, data_2023, planting_data_2023 = lib.load_data()

# Extract crops and land types
crops = crops_data['作物名称'].unique()
land_types = land_data['地块类型'].unique()
years = range(2024, 2031)

# Define decision variables
seasons = ["第一季", "第二季"]
planting_area = LpVariable.dicts("planting_area", (crops, land_types, years, seasons), lowBound=0)

# Create the optimization model
def optimize_planting_strategy():
    # Define the problem
    model = LpProblem(name="planting-strategy", sense=LpMaximize)

    # Calculate expected sales volume using lib's function
    expected_sales_volume = lib.calculate_expected_sales_volume(planting_data_2023, data_2023)

    # Add land area constraints using lib's helper function
    for land_type, land_area in lib.get_land_area(land_data):
        for year in years:
            for season in seasons:
                model += lpSum(planting_area[crop][land_type][year][season] for crop in crops) <= land_area

    # Add crop-specific constraints
    for crop_name, crop_type, land_seasons_dict in lib.get_crop_constraints(crops_data):
        for year in years:
            for land in land_types:
                if land in land_seasons_dict:
                    seasons = land_seasons_dict[land]
                else:
                    seasons = ["第一季", "第二季"]

                # Constraint for single-season grain crops (excluding rice)
                if crop_type == '粮食' and crop_name != '水稻' and land in ['平旱地', '梯田', '山坡地']:
                    for season in seasons:
                        model += lpSum(planting_area[crop_name][land][year][season] for crop_name in crops if crop_type == '粮食' and crop_name != '水稻') <= 1

                # Irrigated land constraint (rice vs vegetables)
                if land == '水浇地':
                    rice_area = planting_area['水稻'][land][year]["第一季"]
                    vegetable_area = lpSum(planting_area[crop][land][year][season] for crop in crops if crop_type == '蔬菜' for season in seasons)
                    model += (rice_area == 0) | (vegetable_area == 0)

                    # Special season constraint for specific crops
                    for crop in ['大白菜', '白萝卜', '红萝卜']:
                        model += planting_area[crop][land][year]["第一季"] == 0  # First season
                        model += planting_area[crop][land][year]["第二季"] >= 0  # Second season

    # Greenhouse constraints
    for land in land_types:
        if land == '普通大棚':
            for year in years:
                first_season_vegetables = lpSum(planting_area[crop][land][year]["第一季"] for crop in crops if crop not in ['大白菜', '白萝卜', '红萝卜'] and '蔬菜' in crop)
                model += first_season_vegetables >= 0
                second_season_mushrooms = lpSum(planting_area[crop][land][year]["第二季"] for crop in crops if '食用菌' in crop)
                model += second_season_mushrooms >= 0
                model += lpSum(planting_area[crop][land][year]["第一季"] for crop in crops if '食用菌' in crop) == 0

        elif land == '智慧大棚':
            for year in years:
                for season in ["第一季", "第二季"]:
                    model += lpSum(planting_area[crop][land][year][season] for crop in crops if crop not in ['大白菜', '白萝卜', '红萝卜'] and '蔬菜' in str(crop)) >= 0

    return model, expected_sales_volume

# Main function to run the optimization
if __name__ == "__main__":
    model, expected_sales_volume = optimize_planting_strategy()
    model.solve()
    lib.output_results(model, expected_sales_volume)  # Use lib to output the results
