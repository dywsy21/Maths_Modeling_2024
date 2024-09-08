import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary
import numpy as np
from main_1_1 import *

def main(reduction_factor, index):
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')

    # 将full_table中的单季改为第一季
    full_table['种植季次'] = full_table['种植季次'].apply(lambda x: '第一季' if x == '单季' else x)

    seasons = ['第一季','第二季']
    years = list(range(2024, 2031))
    regions = full_table['种植地块'].unique()
    crops = full_table['作物名称'].unique()

    region_areas = {}
    for index, row in full_table.iterrows():
        if row['种植地块'] not in region_areas:
            region_areas[row['种植地块']] = row['种植面积/亩']
        else:
            region_areas[row['种植地块']] += row['种植面积/亩']
            
    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    region_to_type = dict(zip(full_table['种植地块'],full_table['地块类型']))

    # Create decision variables: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season] and the decision to plant or not
    planting_area = LpVariable.dicts("planting_area", [(crop, region, year, season) for crop in crops for region in regions for year in years for season in seasons], lowBound=0, cat='Continuous')
    planting_decision = LpVariable.dicts("planting_decision", [(crop, region, year, season) for crop in crops for region in regions for year in years for season in seasons], cat='Binary')

    # functions in main_1_1 (to get data for 2024)
    def get_expected_sales(crop, season):
        ret = 0
        for i, row in full_table.iterrows():
            if row['作物名称'] == crop and row['种植季次'] == season:
                ret += row['预期销售量/斤']
        return ret

    def get_yield_per_acre(crop, region): # 斤/亩
        for i, row in full_table.iterrows():
            if row['作物名称'] == crop and row['地块类型'] == region_to_type[region]:
                return row['亩产量/斤']
        return 0
    
    def get_price(crop, season):
        for i, row in full_table.iterrows():
            if row['作物名称'] == crop and row['种植季次'] == season:
                return row['平均价格/(元/斤)']
        return 0

    def get_cost(crop, region):
        for i, row in full_table.iterrows():
            if row['作物名称'] == crop and row['地块类型'] == region_to_type[region]:
                return row['种植成本/(元/亩)']
        return 0
    
    


    # change rate
    sales_rate = {}
    for index, row in file2.iterrows():
        if row['作物名称'] == '小麦' or row['作物名称'] == '玉米':
            sales_rate['作物名称'] = lambda: np.random.uniform(1.05, 1.10)
        else:
            sales_rate['作物名称'] = lambda: np.random.uniform(0.95, 1.05) #! TODO: potential misunderstanding

    price_rate = {}
    for index, row in file2.iterrows():
        if row['作物名称'] == '羊肚菌':
            price_rate[row['作物名称']] = 0.95
        elif row['作物类型'] == '粮食' or row['作物类型'] == '粮食（豆类）':
            price_rate[row['作物名称']] = 1.00
        elif row['作物类型'] == '蔬菜' or row['作物类型'] == '蔬菜（豆类）':
            price_rate[row['作物名称']] = 1.05
        else:# 食用菌 except 羊肚菌
            price_rate[row['作物名称']] = lambda: np.random.uniform(0.95, 0.99)
    
    yield_rate = lambda: np.random.uniform(0.9, 1.1)

    cost_rate = 1.05

    # use data for 2024 and change rate to form a list of data for 2024-2030
    def get_expected_sales_list(crop, season):# get_expected_sales(crop, season)[year-2024]
        ret_sales = []
        ret_sales[0] = get_expected_sales(crop, season)
        for i in years[1:]:
            ret_sales.append(ret_sales[-1]*sales_rate)
        return ret_sales
    
    def get_yield_per_acre_list(crop, region):
        ret_yield = []
        ret_yield[0] = get_yield_per_acre(crop, region)
        for i in years[1:]:
            ret_yield.append(ret_yield[-1]*yield_rate)
        return ret_yield
    
    def get_price_list(crop, season):
        ret_price = []
        ret_price[0] = get_price(crop, season)
        for i in years[1:]:
            ret_price.append(ret_price[-1]*price_rate)
        return ret_price
    
    def get_cost_list(crop, region):
        ret_cost = []
        ret_cost[0] = get_cost(crop, region)
        for i in years[1:]:
            ret_cost.append(ret_cost[-1]*cost_rate)
        return ret_cost
    
    def get_total_yield(crop, year):
        return lpSum(planting_area[(crop, region, year, season)] * get_yield_per_acre_list(crop, region)[year-2024] for region in regions for season in seasons)
    
    # object function
    def get_profit(crop, year):
        if get_total_yield(crop, year) <= get_expected_sales_list(crop, '第一季')[year-2024] + get_expected_sales_list(crop, '第二季')[year-2024]:
            return lpSum(planting_area[(crop, region, year, season)]
                         * (get_yield_per_acre_list(crop, region)[year-2024] * get_price_list(crop, season)[year-2024] - get_cost_list(crop, region)[year-2024])
                        for region in regions for season in seasons
                    )
        else:
            return lpSum((planting_area[(crop, region, year, season)] * get_yield_per_acre_list(crop, region)[year-2024] - get_expected_sales_list(crop, season)[year-2024] - get_cost_list(crop, region)[year-2024])
                         * get_price_list(crop, season)[year-2024] * (1 - reduction_factor) 
                         for region in regions for season in seasons) \
                    + lpSum(get_expected_sales_list(crop, season)[year-2024] * get_price_list(crop, season)[year-2024] for season in seasons)


