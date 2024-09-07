import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary
import numpy as np
from main_1_1 import *

def main(reduction_factor, index):
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')

    seasons = ['第一季','第二季']
    years = list(range(2024, 2031))
    region_areas = dict(zip(full_table['种植地块'],full_table['种植面积/亩']))
    region_to_type = dict(zip(full_table['种植地块'],full_table['地块类型']))

    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    # Create a sole decision variable: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season]
    planting_area = LpVariable.dicts("planting_area", ((crop, region, year, season) for crop in full_table['作物名称'].unique() for region in full_table['种植地块'].unique() for year in years for season in seasons), lowBound=0, cat='Continuous')

    # sales change rate
    sales_rate = {}
    for index, row in file2.iterrows():
        if row['作物名称'] == '小麦' or row['作物名称'] == '玉米':
            sales_rate['作物名称'] = lambda: np.random.uniform(1.05, 1.10)
        else:
            sales_rate['作物名称'] = lambda: np.random.uniform(0.95, 1.05) #! TODO: potential misunderstanding

    # price change rate
    crop_to_type = dict(zip(file2['作物名称'], file2['作物类型']))
        # mentioned types
        # '粮食': 1.00,
        # '粮食（豆类）': 1.00,
        # '蔬菜': 1.05,
        # '蔬菜（豆类）': 1.05,
        # '食用菌': lambda: np.random.uniform(0.95, 0.99)
        # 羊肚菌: 0.95 uncovered
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
    
    


