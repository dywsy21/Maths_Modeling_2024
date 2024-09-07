import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

def main(reduction_factor, index):
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')

    seasons = ['第一季','第二季']
    years = list(range(2024, 2031))
    region_areas = dict(zip(full_table['种植地块'],full_table['种植面积/亩']))
    region_to_type = dict(zip(full_table['种植地块'],full_table['地块类型']))

    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    # Create decision variables: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season] and the decision to plant or not
    planting_area = LpVariable.dicts("planting_area", ((crop, region, year, season) for crop in full_table['作物名称'].unique() for region in full_table['种植地块'].unique() for year in years for season in seasons), lowBound=0, cat='Continuous')
    planting_decision = LpVariable.dicts("planting_decision", ((crop, region, year, season) for crop in full_table['作物名称'].unique() for region in full_table['种植地块'].unique() for year in years for season in seasons), cat='Binary')

    # 加十三个约束条件：
    # 1. 平旱地、梯田和山坡地每年适宜单季种植粮食类作物（水稻除外）。 [已被12包含]
    # Already included in 12


    # 2. 水浇地每年可以单季种植水稻或[两季种植蔬菜作物]。 [已被12包含]
    # Already included in 12


    # 3. 若在某块水浇地种植两季蔬菜，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外）；第二季只能种植大白菜、白萝卜和红萝卜中的一种（便于管理）。
    # second_season_allowed_crops = ['大白菜', '白萝卜', '红萝卜']

    # for region in full_table['种植地块'].unique():
    #     for year in years:
    #         if region == '水浇地':
    #             second_season_constraint = lpSum(planting_decision[(crop, region, year, '第二季')] for crop in second_season_allowed_crops)
    #             linear_model += (second_season_constraint <= 1)

    # 4. 根据季节性要求，大白菜、白萝卜和红萝卜只能在水浇地的第二季种植。
    for year in years:
        for i, row in full_table.iterrows():
            if row['作物名称'] in ['大白菜', '白萝卜', '红萝卜'] and row['地块类型'] == '水浇地':
                linear_model += planting_decision[row['作物名称'], row['种植地块'], year, '第一季'] == 0
                

    # 5. 普通大棚每年种植两季作物，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外），第二季只能种植食用菌。[已被12包含]
    # Already included in 12

    # 6. 因食用菌类适应在较低且适宜的温度和湿度环境中生长，所以只能在秋冬季的普通大棚里种植。 [已被12包含]
    # Already included in 12

    # 7. 智慧大棚每年都可种植两季蔬菜（大白菜、白萝卜和红萝卜除外）。 [已被12包含]
    # Already included in 12


    # 8. 从 2023 年开始要求每个地块（含大棚）的所有土地三年内至少种植一次豆类作物。
    bean_crops = ['黄豆', '黑豆', '红豆', '绿豆', '爬豆', '豇豆', '刀豆', '芸豆']
    for region in full_table['种植地块'].unique():
        for y_begin in range(2024, 2029):
            linear_model += lpSum(planting_decision[crop, region, year, season] for crop in bean_crops 
                                  for year in range(y_begin, y_begin+3) for season in seasons) >= 1

    # 9. 每种作物每季的种植地不能太分散。我们限制最大种植地块数为 5。
    # Ensure planting_decision is used in constraints
    for crop in full_table['作物名称'].unique():
        for season in seasons:
            linear_model += lpSum(planting_decision[crop, region, year, season] for region in full_table['种植地块'].unique() for year in years) <= 5



    # 10. 每种作物在单个地块（含大棚）种植的面积不宜太小。我们限制最小种植面积为 30%。
    for crop in full_table['作物名称'].unique():
        for region in full_table['种植地块']:
            for year in years:
                for season in seasons:
                    linear_model += (region_areas[region] * planting_decision[crop, region, year, season] >= planting_area[crop, region, year, season] >= 0.3 * region_areas[region] * planting_decision[crop, region, year, season])
        

    # 11. 不能超出地块面积
    for region in full_table['种植地块'].unique():
        for year in years:
            for season in seasons:
                linear_model += lpSum(planting_area[crop, region, year, season] for crop in full_table['作物名称'].unique()) <= region_areas[region]


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
                seasons = land_season[1].split(' ')
                land_seasons_dict[land] = seasons
            else:
                land_seasons_dict[land] = ['单季']
        crop_to_condition[row['作物名称']] = land_seasons_dict
    # print(crop_to_condition)

    for crop in full_table['作物名称'].unique():
        for region in full_table['种植地块'].unique():
            for year in years:
                for season in seasons:
                    if region_to_type[region] in crop_to_condition[crop]:
                        # print(season not in crop_to_condition[crop][region_to_type[region]], end=' ')
                        if crop_to_condition[crop][region_to_type[region]] == ['单季']:
                            # print('2！', end=' ')
                            linear_model += (planting_decision[(crop, region, year, '第一季')] + planting_area[(crop, region, year, '第二季')] <= 1)
                        elif season not in crop_to_condition[crop][region_to_type[region]]:
                            # print('1！', end=' ')
                            linear_model += planting_decision[(crop, region, year, season)] == 0
                        
    
    # 13: 每种作物在同一地块（含大棚）都不能连续重茬种植，否则会减产
    for crop in full_table['作物名称'].unique():
        for region in full_table['种植地块'].unique():
            for year in years:
                # 同一年的第一季和第二季
                linear_model += (planting_decision[crop, region, year, '第一季'] + planting_decision[crop, region, year, '第二季'] <= 1)
                # 上一年第二季和下一年第一季
                if year < 2030:
                    linear_model += (planting_decision[crop, region, year, '第二季'] + planting_decision[crop, region, year+1, '第一季'] <= 1)



    # 计算每种作物的预期销售量，为了目标函数服务
    crop_to_expected_sales = {} # 斤
    for i, row in full_table.iterrows():
        if row['作物名称'] not in crop_to_expected_sales.keys():
            crop_to_expected_sales[row['作物名称']] = 0
        crop_to_expected_sales[row['作物名称']] += row['预期销售量/斤']
    # print(crop_to_expected_sales)

    # 创建两个dict，分别存储每种作物的种植成本和价格，为了目标函数服务
    crop_to_cost = dict(zip(full_table['作物名称'], full_table['种植成本/(元/亩)']))
    crop_to_price = dict(zip(full_table['作物名称'], full_table['平均价格/元']))
    # print(crop_to_cost, '\n\n\n\n', crop_to_price)

    def get_yield(crop, region): # 斤/亩
        for i, row in full_table.iterrows():
            if row['作物名称'] == crop and row['种植地块'] == region:
                return row['亩产量/斤']
        return 0
    
    def get_total_planting_area(crop, year, season):
        return lpSum(planting_area[crop, region, year, season] for region in full_table['种植地块'].unique())

    def my_max(a, b):
        return a if a >= b else b 
    
    def get_profit(crop, year, season):
        if get_total_planting_area(crop, year, season) >= crop_to_expected_sales[crop]:
            return my_max(0, crop_to_price[crop] * lpSum(get_yield(crop, region) for region in full_table['种植地块'].unique()) * (1 - reduction_factor) - crop_to_cost[crop]) * (get_total_planting_area(crop, year, season) - crop_to_expected_sales[crop]) + crop_to_expected_sales[crop] * crop_to_price[crop] - crop_to_cost[crop] * get_total_planting_area(crop, year, season)
        else:
            return (crop_to_price[crop] * lpSum(get_yield(crop, region) for region in full_table['种植地块'].unique()) - crop_to_cost[crop]) * get_total_planting_area(crop, year, season)

    # 目标函数, 超出预期销售量的部分，价格乘以 reduction_factor
    linear_model += lpSum(get_profit(crop, year, season)
                            for crop in full_table['作物名称'].unique()
                            for year in years 
                            for season in seasons)
    
    print(linear_model.constraints.items())
    linear_model.solve()

    for k in years:
        yearly_obj_value = lpSum((crop_to_price[j] * get_yield(j, i) - crop_to_cost[j]) * planting_area[j, i, k, t].varValue
                                for i in full_table['种植地块'].unique() for j in full_table['作物名称'].unique() for t in seasons
                                if planting_area[j, i, k, t].varValue > 0)  # 只计算种植面积大于 0 的决策变量
        print(f"Year {k} 目标函数值: {yearly_obj_value}")

    # Check if all planting_decision variables are binary (0 or 1)
    for var in planting_decision.values():
        if var.varValue not in [0, 1]:
            print(f"Variable {var.name} has a non-binary value: {var.varValue}")
    main(1, 1)
    # main(0.5, 2)
