import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

def optimize_planting_strategy_question2():
    # Define the problem
    model = LpProblem(name="planting-strategy-question2", sense=LpMaximize)

    # Load crop and land data from CSV files
    crops_data = pd.read_csv('附件/附件(csv)/附件1_乡村种植的农作物.csv', encoding='utf-8-sig')
    land_data = pd.read_csv('附件/附件(csv)/附件1_乡村的现有耕地.csv', encoding='utf-8-sig')
    data_2023 = pd.read_csv('附件/附件(csv)/附件2_2023年统计的相关数据.csv', encoding='utf-8-sig')

    # Extract crops and land types
    crops = crops_data['作物名称'].unique()
    land_types = land_data['地块类型'].unique()
    years = range(2024, 2031)
    seasons = ["第一季", "第二季"]

    # Define decision variables
    planting_area = LpVariable.dicts("planting_area", (crops, land_types, years, seasons), lowBound=0)

    # Helper function to get the dynamic price based on year and crop type
    def get_dynamic_price(crop_name, year):
        base_price = data_2023.loc[data_2023['作物名称'] == crop_name, '销售单价/(元/斤)'].values[0]
        if '粮食' in crop_name:
            return base_price  # 粮食类价格稳定
        elif '蔬菜' in crop_name:
            return base_price * (1 + 0.05 * (year - 2023))  # 蔬菜类每年增长5%
        elif '食用菌' in crop_name:
            if crop_name == '羊肚菌':
                return base_price * (1 - 0.05 * (year - 2023))  # 羊肚菌每年下降5%
            else:
                return base_price * (1 - np.random.uniform(0.01, 0.05) * (year - 2023))  # 其他食用菌下降1%-5%
    
    # Helper function to simulate the uncertain yield per acre
    def get_dynamic_yield(crop_name):
        base_yield = data_2023.loc[data_2023['作物名称'] == crop_name, '亩产量/斤'].values[0]
        return base_yield * np.random.uniform(0.9, 1.1)  # 亩产量每年波动±10%

    # Helper function to calculate expected sales volume growth
    def get_sales_volume_growth(crop_name, year):
        if crop_name in ['小麦', '玉米']:
            return 1 + np.random.uniform(0.05, 0.10) * (year - 2023)  # 小麦和玉米每年增长5%-10%
        else:
            return 1 + np.random.uniform(-0.05, 0.05)  # 其他作物±5%波动

    # Add constraints for each year and land type
    for index, row in land_data.iterrows():
        land_type = row['地块类型']
        land_area = row['地块面积/亩']
        for year in years:
            for season in seasons:
                model += lpSum(planting_area[crop][land_type][year][season] for crop in crops) <= land_area

    # Revised objective function with uncertainties and dynamic factors
    model += lpSum(
        planting_area[crop][land][year][season] * (
            get_dynamic_price(crop, year) * get_dynamic_yield(crop) * get_sales_volume_growth(crop, year)
            - data_2023.loc[data_2023['作物名称'] == crop, '种植成本/(元/亩)'].values[0] * (1 + 0.05 * (year - 2023))  # 每年成本增加5%
        )
        for crop in crops for land in land_types for year in years for season in seasons  # Make sure season is included
    )

    # Solve the model
    model.solve()

    # Output results
    results = {year: {crop: {land: {season: planting_area[crop][land][year][season].value() for season in seasons} for land in land_types} for crop in crops} for year in years}
    df = pd.DataFrame(results)
    df.to_excel("result2.xlsx")

if __name__ == "__main__":
    optimize_planting_strategy_question2()
