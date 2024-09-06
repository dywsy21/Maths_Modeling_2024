import pandas as pd
import csv
from pulp import LpMaximize, LpProblem, LpVariable, lpSum
from lib import *

def main(reduction_factor=0, index=1):
    # Define the problem
    model, expected_sales_volume = optimize_planting_strategy()
    # Revise the objective function using data from 附件2_2023年统计的相关数据.csv
    # Load the 2023 dat
    data_2023 = pd.read_csv('附件/附件(csv)/附件2_2023年统计的相关数据.csv', encoding='utf-8-sig')

    # Helper function to convert price range to average price
    def get_average_price(price_range):
        if '-' in price_range:
            low, high = map(float, price_range.split('-'))
            return (low + high) / 2
        return float(price_range)

    model += lpSum(
        planting_area[crop][land][year][season] * data_2023.loc[data_2023['作物名称'] == crop, '亩产量/斤'].values[0] * get_average_price(data_2023.loc[data_2023['作物名称'] == crop, '销售单价/(元/斤)'].values[0]) -
        planting_area[crop][land][year][season] * data_2023.loc[data_2023['作物名称'] == crop, '种植成本/(元/亩)'].values[0] +
        reduction_factor * (
            planting_area[crop][land][year][season] * data_2023.loc[data_2023['作物名称'] == crop, '亩产量/斤'].values[0] - expected_sales_volume[crop]
        ) * get_average_price(data_2023.loc[data_2023['作物名称'] == crop, '销售单价/(元/斤)'].values[0])
        for crop in crops for land in land_types for year in years for season in seasons
    )

    model.solve()

    # Output results
    results = {year: {crop: {land: planting_area[crop][land][year] for land in land_types} for crop in crops} for year in years}
    df = pd.DataFrame(results)
    df.to_excel("result1_" + str(index) + ".xlsx")

if __name__ == "__main__":
    # question 1(1)
    main(0, 1)
    # question 1(2)
    main(0.5, 2)
