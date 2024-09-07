import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

def main():
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')

    seasons = ['第一季','第二季']
    years = list(range(2024, 2031))
    region_areas = dict(zip(full_table['种植地块'],full_table['种植面积/亩']))

    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    # Create a sole decision variable: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season]
    x = LpVariable.dicts("planting_area", ((crop, region, year, season) for crop in full_table['作物名称'] for region in full_table['种植地块'].unique() for year in years for season in full_table['种植季次'].unique()), lowBound=0, cat='Continuous')

    # 加十二个约束条件：
    # 1. 平旱地、梯田和山坡地每年适宜单季种植粮食类作物（水稻除外）。 [已被12包含]
    # Already included in 12


    # 2. 水浇地每年可以单季种植水稻或[两季种植蔬菜作物]。 [已被12包含]
    # Already included in 12
    # for region in full_table['种植地块'].unique():
    #     for year in years:
    #         linear_model += not (x['水稻', region, year, '第一季'] and x['水稻', region, year, '第二季'])


    # 3. 若在某块水浇地种植两季蔬菜，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外）；第二季只能种植大白菜、白萝卜和红萝卜中的一种（便于管理）。
    for region in full_table['种植地块'].unique():
        for year in years:
            linear_model += lpSum(x[crop, region, year, '第一季'] for crop in full_table['作物名称'].unique() if crop not in ['大白菜', '白萝卜', '红萝卜']) <= 1
            linear_model += lpSum(x[crop, region, year, '第二季'] for crop in full_table['作物名称'].unique() if crop in ['大白菜', '白萝卜', '红萝卜']) <= 1
            linear_model += lpSum(x[crop, region, year, '第二季'] for crop in full_table['作物名称'].unique() if crop not in ['大白菜', '白萝卜', '红萝卜']) == 0
            

    # 4. 根据季节性要求，大白菜、白萝卜和红萝卜只能在水浇地的第二季种植。
    for year in years:
        for i, row in full_table.iterrows():
            if row['作物名称'] in ['大白菜', '白萝卜', '红萝卜'] and row['地块类型'] == '水浇地':
                linear_model += x[row['作物名称'], row['种植地块'], year, '第一季'] == 0
                

    # 5. 普通大棚每年种植两季作物，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外），第二季只能种植食用菌。[已被12包含]
    # Already included in 12

    # 6. 因食用菌类适应在较低且适宜的温度和湿度环境中生长，所以只能在秋冬季的普通大棚里种植。 [已被12包含]
    # Already included in 12

    # 7. 智慧大棚每年都可种植两季蔬菜（大白菜、白萝卜和红萝卜除外）。 [已被12包含]
    # Already included in 12


    # 8. 从 2023 年开始要求每个地块（含大棚）的所有土地三年内至少种植一次豆类作物。
    bean_crops = ['黄豆', '黑豆', '红豆', '绿豆', '爬豆', '豇豆', '刀豆', '芸豆']
    for region in full_table['种植地块']:
        for y_begin in range(2024, 2029):
            linear_model += lpSum(x[crop, region, year, season] for crop in bean_crops 
                                  for year in range(y_begin, y_begin+3) for season in seasons) > 0

    # 9. 每种作物每季的种植地不能太分散。我们限制最大种植地块数为 5。
    small_value = 0
    for crop in full_table['作物名称'].unique():
        for season in full_table['种植季次'].unique():
            model += (lpSum((x[crop, region, year, season] > small_value) for region in full_table['种植地块'].unique() for year in years) <= 5, f"{crop}_{season}_地块数限制")



    # 10. 每种作物在单个地块（含大棚）种植的面积不宜太小。我们限制最小种植面积为 30%。
    for crop in full_table['作物名称'].unique():
        for region in full_table['种植地块']:
            for year in years:
                for season in seasons:
                    linear_model += (x[crop, region, year, season] >= 0.3*region_areas[region])
        

    # 11. 不能超出地块面积
    # TODO: need to be revised: sum of crops
    for region in full_table['种植地块'].unique():
        for year in years:
            for season in seasons:
                linear_model += lpSum(x[crop, region, year, season] for crop in full_table['作物名称'].unique()) <= region_areas[region]


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

    for crop in full_table['作物名称']:
        for region in full_table['种植地块'].unique():
            for year in years:
                for season in full_table['种植季次'].unique():
                    if region in crop_to_condition[crop]:
                        if season not in crop_to_condition[crop][region]:
                            linear_model += x[(crop, region, year, season)] == 0
                        elif crop_to_condition[crop][region] == ['单季']:
                            linear_model += not (x[(crop, region, year, '第一季')] and x[(crop, region, year, '第二季')])


if __name__ == '__main__':
    main()