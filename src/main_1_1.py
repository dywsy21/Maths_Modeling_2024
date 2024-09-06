import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

def main():
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')
    years = list(range(2024, 2031))

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
                land_seasons_dict[land] = ["第一季", "第二季"]
        crop_to_condition[row['作物名称']] = land_seasons_dict
        

        
    
    # create dict of land areas
    region_areas = dict(zip(full_table['种植地块'],full_table['种植面积/亩']))

    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    # Create a sole decision variable: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season]
    x = LpVariable.dicts("planting_area", ((crop, region, year, season) for crop in full_table['作物名称'] for region in full_table['种植地块'].unique() for year in years for season in full_table['种植季次'].unique()), lowBound=0, cat='Continuous')

    # 加十个约束条件：
    # 1. 平旱地、梯田和山坡地每年适宜单季种植粮食类作物（水稻除外）。


    # 2. 水浇地每年可以单季种植水稻或两季种植蔬菜作物。


    # 3. 若在某块水浇地种植两季蔬菜，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外）；第二季只能种植大白菜、白萝卜和红萝卜中的一种（便于管理）。


    # 4. 根据季节性要求，大白菜、白萝卜和红萝卜只能在水浇地的第二季种植。


    # 5. 普通大棚每年种植两季作物，第一季可种植多种蔬菜（大白菜、白萝卜和红萝卜除外），第二季只能种植食用菌。


    # 6. 因食用菌类适应在较低且适宜的温度和湿度环境中生长，所以只能在秋冬季的普通大棚里种植。


    # 7. 智慧大棚每年都可种植两季蔬菜（大白菜、白萝卜和红萝卜除外）。


    # 8. 从 2023 年开始要求每个地块（含大棚）的所有土地三年内至少种植一次豆类作物。


    # 9. 每种作物每季的种植地不能太分散。


    # 10. 每种作物在单个地块（含大棚）种植的面积不宜太小。

    # 11. 不能超出地块面积
    for i in full_table['种植地块']:




if __name__ == '__main__':
    main()