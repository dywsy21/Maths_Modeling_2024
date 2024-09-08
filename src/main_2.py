import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary
import numpy as np
from main_1 import *
import random

def main(reduction_factor):
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')
    file1 = pd.read_csv('附件\\附件(csv)\\附件1_乡村的现有耕地.csv')
    
    # 将full_table中的单季改为第一季
    full_table['种植季次'] = full_table['种植季次'].apply(lambda x: '第一季' if x == '单季' else x)

    seasons = ['第一季','第二季']
    years = list(range(2024, 2031))
    regions = full_table['种植地块'].unique()
    crops = full_table['作物名称'].unique()

    region_areas = dict(zip(file1['地块名称'], file1['地块面积/亩']))
    
    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    region_to_type = dict(zip(full_table['种植地块'],full_table['地块类型']))
    crop_to_type = dict(zip(file2['作物名称'],file2['作物类型']))

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
            sales_rate[row['作物名称']] = lambda: np.random.uniform(1.05, 1.10)
        else:
            sales_rate[row['作物名称']] = lambda: np.random.uniform(0.95, 1.05) #! TODO: potential misunderstanding

    

    price_rate = {}
    for index, row in file2.iterrows():
        if row['作物名称'] == '羊肚菌':
            price_rate[row['作物名称']] = lambda: 0.95
        elif row['作物类型'] == '粮食' or row['作物类型'] == '粮食（豆类）':
            price_rate[row['作物名称']] = lambda: 1.00
        elif row['作物类型'] == '蔬菜' or row['作物类型'] == '蔬菜（豆类）':
            price_rate[row['作物名称']] = lambda: 1.05
        else:# 食用菌 except 羊肚菌
            price_rate[row['作物名称']] = lambda: np.random.uniform(0.95, 0.99)
    
    yield_rate = lambda: np.random.uniform(0.9, 1.1)

    cost_rate = 1.05

    # reduction of production considering risk
    bean_dis_rate = 0.0325 # 粮食（豆类）
    grain_dis_rate = 0.03
    veg_dis_rate = 0.1
    fungi_dis_rate = 0.2
    # risk_list = []
    # for j in range(4):
    #     temp = []
    #     for i in years:
    #         temp.append(random.random())
    #     risk_list.append(temp)

    def risk(crop, year): # 蒙特卡洛算法实现
        if crop_to_type[crop] == '粮食（豆类）':
            return 0 if random.random() < bean_dis_rate else 1
        elif crop_to_type[crop] == '粮食':
            return 0 if random.random() < grain_dis_rate else 1
        elif crop_to_type[crop] == '蔬菜' or crop_to_type[crop] == '蔬菜（豆类）':
            return 0 if random.random() < veg_dis_rate else 1
        else:
            return 0 if random.random() < fungi_dis_rate else 1


    # use data for 2024 and change rate to form a list of data for 2024-2030
    def get_expected_sales_list(crop, season):# get_expected_sales(crop, season)[year-2024]
        ret_sales = []
        ret_sales.append(get_expected_sales(crop, season))
        for i in years[1:]:
            ret_sales.append(ret_sales[-1]*sales_rate[crop]())
        return ret_sales
    
    def get_yield_per_acre_list(crop, region):
        ret_yield = []
        ret_yield.append(get_yield_per_acre(crop, region))
        for i in years[1:]:
            ret_yield.append(ret_yield[-1]*yield_rate())
        return ret_yield
    
    def get_price_list(crop, season):
        ret_price = []
        ret_price.append(get_price(crop, season))
        for i in years[1:]:
            ret_price.append(ret_price[-1]*price_rate[crop]())
        return ret_price
    
    def get_cost_list(crop, region):
        ret_cost = []
        ret_cost.append(get_cost(crop, region))
        for i in years[1:]:
            ret_cost.append(ret_cost[-1]*cost_rate)
        return ret_cost
    
    def get_total_yield(crop, year):
        return lpSum(planting_area[(crop, region, year, season)] * get_yield_per_acre_list(crop, region)[year-2024] for region in regions for season in seasons)
    
    def get_seasonly_yield(crop, year, season):
        return lpSum(planting_area[(crop, region, year, season)] * get_yield_per_acre_list(crop, region)[year-2024] for region in regions)
    
    # object function
    def get_profit(crop, year):
        _risk = risk(crop, year)
        if get_total_yield(crop, year) * _risk <= get_expected_sales_list(crop, '第一季')[year-2024] + get_expected_sales_list(crop, '第二季')[year-2024]:
            return lpSum(planting_area[(crop, region, year, season)]
                         * (get_yield_per_acre_list(crop, region)[year-2024] * get_price_list(crop, season)[year-2024] * _risk - get_cost_list(crop, region)[year-2024])
                        for region in regions for season in seasons
                    )
        else:
            return lpSum((planting_area[(crop, region, year, season)] * get_yield_per_acre_list(crop, region)[year-2024] - get_expected_sales_list(crop, season)[year-2024] - get_cost_list(crop, region)[year-2024])
                         * get_price_list(crop, season)[year-2024] * (1 - reduction_factor) 
                         for region in regions for season in seasons) \
                    + lpSum(get_expected_sales_list(crop, season)[year-2024] * get_price_list(crop, season)[year-2024] for season in seasons)

    def get_profit_robust(crop, year): # 鲁棒优化
        # 确定价格、产量和销售量的不确定性波动
        delta_price = 0.05  # 假设价格最大波动范围为 ±5%
        delta_yield = 0.10  # 假设产量最大波动范围为 ±10%
        delta_sales = 0.10  # 假设销售量最大波动范围为 ±10%

        # 获取该作物的总产量，考虑不确定性
        total_yield_uncertain = lpSum(
            planting_area[(crop, region, year, season)] * (1 - delta_yield) * get_yield_per_acre_list(crop, region)[year - 2024]
            for region in regions for season in seasons
        )

        _risk = risk(crop, year)

        # 如果总产量小于或等于预期销售量（考虑销售量波动）
        if total_yield_uncertain * _risk <= (get_expected_sales_list(crop, '第一季')[year - 2024] * (1 - delta_sales) +
                                                        get_expected_sales_list(crop, '第二季')[year - 2024] * (1 - delta_sales)):
            # 正常利润计算
            return lpSum(
                planting_area[(crop, region, year, season)] *
                ((1 - delta_yield) * get_yield_per_acre_list(crop, region)[year - 2024] * 
                (1 - delta_price) * get_price_list(crop, season)[year - 2024] * _risk -
                get_cost_list(crop, region)[year - 2024])
                for region in regions for season in seasons
            )
        else:
            # 考虑到销售超过预期的情况
            return lpSum(
                (planting_area[(crop, region, year, season)] * (1 - delta_yield) * get_yield_per_acre_list(crop, region)[year - 2024] -
                get_expected_sales_list(crop, season)[year - 2024]) * (1 - delta_price) * get_price_list(crop, season)[year - 2024] *
                (1 - reduction_factor)
                for region in regions for season in seasons
            ) + lpSum(
                get_expected_sales_list(crop, season)[year - 2024] * (1 - delta_price) * get_price_list(crop, season)[year - 2024]
                for season in seasons
            )

    # linear_model += lpSum(get_profit_robust(crop, year) for crop in crops for year in years)

    total_profit = lpSum([])
    z_list = []

    for crop in crops:
        for year in years:
            _risk = risk(crop, year)
            # Define the auxiliary variables for profit in each case
            profit_less_or_equal = LpVariable(f"profit_less_or_equal_{crop}_{year}")
            profit_greater = LpVariable(f"profit_greater_{crop}_{year}")
            z = LpVariable(f"z_{crop}_{year}", cat='Binary')

            z_list.append(z)

            BigM1 = 3 * 1e6
            BigM2 = 1e8

            # Add constraints to handle the binary logic (Big-M method)
            linear_model += get_total_yield(crop, year) * _risk <= get_expected_sales_list(crop, '第一季')[year-2024] + get_expected_sales_list(crop, '第二季')[year-2024] + BigM1 * (1 - z)
            linear_model += get_total_yield(crop, year) * _risk >= get_expected_sales_list(crop, '第一季')[year-2024] + get_expected_sales_list(crop, '第二季')[year-2024] - BigM1 * z

            # Define the actual profit conditions in terms of these auxiliary variables
            # If z = 0, profit_less_or_equal should hold the value of the first branch
            # If z = 1, profit_greater should hold the value of the second branch

            # Constraint for profit in the "less or equal" case
            linear_model += profit_less_or_equal == lpSum(planting_area[(crop, region, year, season)]
                         * (get_yield_per_acre_list(crop, region)[year-2024] * get_price_list(crop, season)[year-2024] * _risk - get_cost_list(crop, region)[year-2024])
                        for region in regions for season in seasons
                    )

            # Constraint for profit in the "greater" case
            linear_model += profit_greater == lpSum((planting_area[(crop, region, year, season)] * get_yield_per_acre_list(crop, region)[year-2024] - get_expected_sales_list(crop, season)[year-2024] - get_cost_list(crop, region)[year-2024])
                         * get_price_list(crop, season)[year-2024] * (1 - reduction_factor) 
                         for region in regions for season in seasons) \
                    + lpSum(get_expected_sales_list(crop, season)[year-2024] * get_price_list(crop, season)[year-2024] for season in seasons)

            # The final profit is determined by z, so we define the overall profit
            profit = LpVariable(f"profit_{crop}_{year}")

            # Constrain the final profit to be one of the two cases
            # When z = 1, profit <= profit_less_or_equal, when z = 0, profit <= profit_greater
            linear_model += profit <= profit_less_or_equal + BigM2 * (1 - z)
            linear_model += profit <= profit_greater + BigM2 * z

            # Now, you can add the objective to maximize the profit
            total_profit += profit

    linear_model += total_profit
    # 加十三个约束条件：
    # 1. 平旱地、梯田和山坡地每年适宜单季种植粮食类作物（水稻除外）。 [已被12包含]
    # Already included in 12


    # 2. 水浇地每年可以单季种植水稻或[两季种植蔬菜作物]。 [已被12包含]
    # Already included in 12


    # 3. 若在某块水浇地种植两季蔬菜，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外）；第二季只能种植大白菜、白萝卜和红萝卜中的一种（便于管理）。
    second_season_allowed_crops = ['大白菜', '白萝卜', '红萝卜']

    for region in regions:
        for year in years:
            if region_areas[region] == '水浇地':
                second_season_constraint = lpSum(planting_decision[(crop, region, year, '第二季')] for crop in second_season_allowed_crops)
                linear_model += (second_season_constraint <= 1)

    # 4. 根据季节性要求，大白菜、白萝卜和红萝卜只能在水浇地的第二季种植。  [已被12包含]
    # Already included in 12
    # for year in years:
    #     for i, row in full_table.iterrows():
    #         if row['作物名称'] in ['大白菜', '白萝卜', '红萝卜'] and row['地块类型'] == '水浇地':
    #             linear_model += planting_decision[row['作物名称'], row['种植地块'], year, '第一季'] == 0            

    # 5. 普通大棚每年种植两季作物，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外），第二季只能种植食用菌。[已被12包含]
    # Already included in 12

    # 6. 因食用菌类适应在较低且适宜的温度和湿度环境中生长，所以只能在秋冬季的普通大棚里种植。 [已被12包含]
    # Already included in 12

    # 7. 智慧大棚每年都可种植两季蔬菜（大白菜、白萝卜和红萝卜除外）。 [已被12包含]
    # Already included in 12


    # 8. 从 2023 年开始要求每个地块（含大棚）的所有土地三年内至少种植一次豆类作物。
    bean_crops = ['黄豆', '黑豆', '红豆', '绿豆', '爬豆', '豇豆', '刀豆', '芸豆']
    for region in regions:
        for y_begin in range(2024, 2029):
            linear_model += lpSum(planting_decision[crop, region, year, season] for crop in bean_crops 
                                  for year in range(y_begin, y_begin + 3) for season in seasons) >= 1

    # 9. 每种作物每季的种植地不能太分散。我们限制最大种植地块数为 8。
    for year in years:
        for crop in crops:
            for season in seasons:
                linear_model += lpSum(planting_decision[crop, region, year, season] for region in regions) <= 8



    # 10. 每种作物在单个地块（含大棚）种植的面积不宜太小。我们限制最小种植面积为 30%。
    for crop in crops:
        for region in regions:
            for year in years:
                for season in seasons:
                    linear_model += planting_area[crop, region, year, season] >= 0.3 * region_areas[region] * planting_decision[crop, region, year, season]
                    linear_model += planting_area[crop, region, year, season] <= region_areas[region] * planting_decision[crop, region, year, season]

        

    # 11. 不能超出地块面积
    for region in regions:
        for year in years:
            for season in seasons:
                linear_model += lpSum(planting_area[crop, region, year, season] for crop in crops) <= region_areas[region]


    # 12. 每种作物须满足相应的种植条件
    crop_to_condition = {}
    for i, row in file2.iterrows():
        text: str = row['种植耕地']
        land_seasons = text.split(';')
        land_seasons_dict: dict = {}
        for land_season in land_seasons:
            land_season = land_season.split(':')
            land = land_season[0]
            if len(land_season) > 1:
                _seasons = land_season[1].split(' ')
                land_seasons_dict[land] = _seasons
            else:
                land_seasons_dict[land] = ['第一季']
        crop_to_condition[row['作物名称']] = land_seasons_dict
    # print(crop_to_condition)

    for crop in crops:
        for region in regions:
            for year in years:
                for season in seasons:
                    if region_to_type[region] in crop_to_condition[crop]:
                        if season not in crop_to_condition[crop][region_to_type[region]]:
                            linear_model += planting_decision[(crop, region, year, season)] == 0
                    else:
                        linear_model += planting_decision[(crop, region, year, season)] == 0
                        
    
    # 13: 每种作物在同一地块（含大棚）都不能连续重茬种植，否则会减产
    for crop in crops:
        for region in regions:
            for year in years:
                # 同一年的第一季和第二季
                linear_model += (planting_decision[crop, region, year, '第一季'] + planting_decision[crop, region, year, '第二季'] <= 1)
                # 上一年第二季和下一年第一季
                if year < 2030:
                    linear_model += (planting_decision[crop, region, year, '第二季'] + planting_decision[crop, region, year+1, '第一季'] <= 1)

    linear_model.writeLP("model2.lp") # ***edited
    linear_model.solve(PULP_CBC_CMD(msg=1, timeLimit=1000))


    # for var in planting_decision.values():
    #     if var.varValue not in [0, 1]:
    #         print(f"Variable {var.name} has a non-binary value: {var.varValue}")

# Calculate target function values for each year
    yearly_obj_values = []
    for k in years:
        yearly_obj_value = lpSum(
            (get_price_list(crop, season)[year-2024] * get_yield_per_acre_list(crop, region)[year-2024] - get_cost_list(crop, region)[year-2024]) * planting_area[crop, region, k, season].varValue
            for crop in crops for region in regions for season in seasons
            if planting_area[crop, region, k, season].varValue > 0  # Only consider variables with planting area greater than 0
        )
        yearly_obj_values.append(yearly_obj_value)
        print(f"Year {k} objective function value: {yearly_obj_value}")

    # 作物名称 地块编号 种植季节 种植数量 年份 五列数据
    output = []
    for year in years:
        for crop in crops:
            for region in regions:
                for season in seasons:
                    output.append([crop, region, season,year ,planting_area[(crop, region, year, season)].varValue])


    # output_df = pd.DataFrame(output, columns=['作物名称', '地块编号', '种植季节','年份', '种植数量'])
    # output_df.to_excel('result_2.xlsx', index=False)

    for z in z_list:
        print(z.varValue, end=' ')

    return output, yearly_obj_values

def merge(output1: list, output2: list):
    for i in range(len(output1)):
        output1[i][4] += output2[i][4]
    return output1

def merge_entire(output_list: list):
    output = output_list[0]
    for i in range(1, len(output_list)):
        output = merge(output, output_list[i])
    return output

def to_average(output: list, n: int):
    for i in range(len(output)):
        output[i][4] /= n
    return output

if __name__ == "__main__":
    output_list = []
    yearly_obj_values_list = []
    times = 10
    for i in range(times):
        output, yearly_obj_values = main(1)
        output_list.append(output)
        yearly_obj_values_list.append(yearly_obj_values)
        if i == 0:
            output_df = pd.DataFrame(output, columns=['作物名称', '地块编号', '种植季节','年份', '种植数量'])
            print("Saved result_2.xlsx!")
            output_df.to_excel('result_2.xlsx', index=False)

    for i in range(1, times):
        yearly_obj_values_list[0] = [yearly_obj_values_list[0][j] + yearly_obj_values_list[i][j] for j in range(len(yearly_obj_values_list[0]))]
    
    for i in range(len(yearly_obj_values_list[0])):
        yearly_obj_values_list[0][i] /= times
        print(f"Average Year {i+2024} objective function value: {yearly_obj_values_list[0][i]}")

    output = merge_entire(output_list)
    output = to_average(output, times)

    output_df = pd.DataFrame(output, columns=['作物名称', '地块编号', '种植季节','年份', '种植数量'])
    output_df.to_excel('result_2_average.xlsx', index=False)
