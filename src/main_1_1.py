import pandas as pd
import csv
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

def optimize_planting_strategy():
    # Define the problem
    model = LpProblem(name="planting-strategy", sense=LpMaximize)

    # Load crop and land data from CSV files
    crops_data = pd.read_csv('附件/附件(csv)/附件1_乡村种植的农作物.csv', encoding='utf-8-sig')
    land_data = pd.read_csv('附件/附件(csv)/附件1_乡村的现有耕地.csv', encoding='utf-8-sig')

    # Extract crops and land types
    crops = crops_data['作物名称'].unique()
    land_types = land_data['地块类型'].unique()
    years = range(2024, 2031)

    # Define decision variables
    seasons = ["第一季", "第二季"]
    planting_area = LpVariable.dicts("planting_area", (crops, land_types, years, seasons), lowBound=0)

    # Load the 2023 data
    data_2023 = pd.read_csv('附件/附件(csv)/附件2_2023年统计的相关数据.csv', encoding='utf-8-sig')
    
    # Debug: Print column names to verify
    # print("Columns in data_2023:", data_2023.columns)
    planting_data_2023 = pd.read_csv('附件/附件(csv)/附件2_2023年的农作物种植情况.csv', encoding='utf-8-sig')

    # Calculate expected sales volume for each crop
    expected_sales_volume = {}
    # Sum the planting areas for each crop
    total_planting_area = planting_data_2023.groupby('作物名称')['种植面积/亩'].sum()

    # print(total_planting_area)

    for crop_name, planting_area_2023 in total_planting_area.items():
        # print(data_2023.loc[data_2023['作物名称'] == crop_name, '亩产量/斤'].values)
        if not data_2023.loc[data_2023['作物名称'] == crop_name, '亩产量/斤'].empty:
            yield_per_mu = data_2023.loc[data_2023['作物名称'] == crop_name, '亩产量/斤'].values[0]
            expected_sales_volume[crop_name] = planting_area_2023 * yield_per_mu
        else:
            print(f"Warning: No yield data found for crop '{crop_name}'")
            expected_sales_volume[crop_name] = 0
    for index, row in land_data.iterrows():
        land_type = row['地块类型']
        land_area = row['地块面积/亩']
        for year in years:
            for season in seasons:
                model += lpSum(planting_area[crop][land_type][year][season] for crop in crops) <= land_area

    # Add crop-specific constraints
    for index, row in crops_data.iterrows():
        crop_name = row['作物名称']
        crop_type = row['作物类型']
        suitable_land = str(row['种植耕地']).split('\n') if isinstance(row['种植耕地'], str) else []
        print("suitable_land: ", suitable_land)
        for year in years:
            for land in land_types:
                if land not in suitable_land:
                    for season in seasons:
                        model += planting_area[crop_name][land][year][season] == 0
                # Constraint for single-season grain crops (excluding rice) on specific land types, (1)
                if crop_type == '粮食' and crop_name != '水稻' and land in ['平旱地', '梯田', '山坡地']:
                    for season in seasons:
                        model += lpSum(planting_area[crop_name][land][year][season] for crop_name in crops if crop_type == '粮食' and crop_name != '水稻') <= 1
                # Constraint for irrigated land: either single-season rice or two-season vegetables, (2) and (3)
                if land == '水浇地':
                    rice_area = planting_area['水稻'][land][year]["第一季"]
                    vegetable_area = lpSum(planting_area[crop][land][year][season] for crop in crops if crop_type == '蔬菜' for season in seasons)
                    model += (rice_area == 0) | (vegetable_area == 0)

                    # Constraint for cabbage, white radish, and red radish only in the second season, (4)
                    for crop in ['大白菜', '白萝卜', '红萝卜']:
                        model += planting_area[crop][land][year]["第一季"] == 0  # First season
                        model += planting_area[crop][land][year]["第二季"] >= 0  # Second season

    # Constraint for ordinary greenhouses: two seasons of crops
    for land in land_types:
        if land == '普通大棚':
            # constraint (5)
            for year in years:
                # First season: exclude cabbage, white radish, and red radish
                first_season_vegetables = lpSum(planting_area[crop][land][year]["第一季"] for crop in crops if crop not in ['大白菜', '白萝卜', '红萝卜'] and '蔬菜' in crop)
                model += first_season_vegetables >= 0

                # Second season: only mushrooms (constraint 6)
                second_season_mushrooms = lpSum(planting_area[crop][land][year]["第二季"] for crop in crops if '食用菌' in crop)
                model += second_season_mushrooms >= 0
                model += lpSum(planting_area[crop][land][year]["第一季"] for crop in crops if '食用菌' in crop) == 0  # Ensure no mushrooms in the first season

    # Constraint for smart greenhouses: two seasons of vegetables excluding cabbage, white radish, and red radish, (7)
    for land in land_types:
        if land == '智慧大棚':
            for year in years:
                for season in ["第一季", "第二季"]:  # Two seasons
                    model += lpSum(planting_area[crop][land][year][season] for crop in crops if crop not in ['大白菜', '白萝卜', '红萝卜'] and '蔬菜' in str(crop)) >= 0
    
    # Revise the objective function using data from 附件2_2023年统计的相关数据.csv
    # Load the 2023 data
    data_2023 = pd.read_csv('附件/附件(csv)/附件2_2023年统计的相关数据.csv', encoding='utf-8-sig')

    # Helper function to convert price range to average price
    def get_average_price(price_range):
        if '-' in price_range:
            low, high = map(float, price_range.split('-'))
            return (low + high) / 2
        return float(price_range)
    
    model += lpSum(
        planting_area[crop][land][year][season] * (
            get_average_price(data_2023.loc[data_2023['作物名称'] == crop, '销售单价/(元/斤)'].values[0]) *
            data_2023.loc[data_2023['作物名称'] == crop, '亩产量/斤'].values[0] -
            data_2023.loc[data_2023['作物名称'] == crop, '种植成本/(元/亩)'].values[0]
        )
        for crop in crops for land in land_types for year in years
    )

    model.solve()

    # Output results
    results = {year: {crop: {land: planting_area[crop][land][year].value() for land in land_types} for crop in crops} for year in years}
    df = pd.DataFrame(results)
    df.to_excel("result1_1.xlsx")

if __name__ == "__main__":
    optimize_planting_strategy()
