import pandas as pd
from pulp import *

def main(reduction_factor, index):
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

    # Create decision variables: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season] and the decision to plant or not
    planting_area = LpVariable.dicts("planting_area", [(crop, region, year, season) for crop in crops for region in regions for year in years for season in seasons], lowBound=0, cat='Continuous')
    planting_decision = LpVariable.dicts("planting_decision", [(crop, region, year, season) for crop in crops for region in regions for year in years for season in seasons], cat='Binary')

    # 计算每种作物的预期销售量，为了目标函数服务
    def get_expected_sales(crop, season):
        # need to sum over all regions
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
    
    def get_total_yield(crop, year):
        return sum(planting_area[(crop, region, year, season)] * get_yield_per_acre(crop, region) for region in regions for season in seasons)
    
    def get_profit(crop, year):
        if get_total_yield(crop, year) <= get_expected_sales(crop, '第一季') + get_expected_sales(crop, '第二季'):
            print(0,end='')
            return lpSum(planting_area[(crop, region, year, season)]
                         * (get_yield_per_acre(crop, region) * get_price(crop, season) - get_cost(crop, region))
                        for region in regions for season in seasons
                    )
        else:
            print(1,end='')
            return lpSum((planting_area[(crop, region, year, season)] * get_yield_per_acre(crop, region) - get_expected_sales(crop, season) - get_cost(crop, region))
                         * get_price(crop, season) * (1 - reduction_factor) 
                         for region in regions for season in seasons) \
                    + lpSum(get_expected_sales(crop, season) * get_price(crop, season) for season in seasons)

    # 目标函数, 超出预期销售量的部分，价格乘以 reduction_factor
    linear_model += lpSum(get_profit(crop, year) for crop in crops for year in years)

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
    print(crop_to_condition)

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

    # # test constraint: all crops's area <= 1
    # for crop in crops:
    #     for region in regions:
    #         for year in years:
    #             for season in seasons:
    #                 linear_model += planting_area[crop, region, year, season] <= 1





    # # Define the target function: Maximize profit excluding dormant sales
    # linear_model += lpSum(
    #     get_price(crop, season) * get_yield_per_acre(crop, region) * planting_area[crop, region, year, season] - planting_area[crop, region, year, season] * get_cost(crop, region)
    #     for crop in crops for region in regions for year in years for season in seasons
    # )
    
    linear_model.writeLP("model.lp")
    linear_model.solve(PULP_CBC_CMD(msg=1, timeLimit=150))


    # for var in planting_decision.values():
    #     if var.varValue not in [0, 1]:
    #         print(f"Variable {var.name} has a non-binary value: {var.varValue}")

# Calculate target function values for each year
    for k in years:
        yearly_obj_value = lpSum(
            (get_price(crop, season) * get_yield_per_acre(crop, region) - get_cost(crop, region)) * planting_area[crop, region, k, season].varValue
            for crop in crops for region in regions for season in seasons
            if planting_area[crop, region, k, season].varValue > 0  # Only consider variables with planting area greater than 0
        )
        print(f"Year {k} objective function value: {yearly_obj_value}")

    # Output results
    results = {year: {crop: {region: {season: planting_area[(crop, region, year, season)].varValue for season in seasons} for region in regions} for crop in crops} for year in years}

    # 作物名称 地块编号 种植季节 种植数量 年份 五列数据
    output = []
    for year in years:
        for crop in crops:
            for region in regions:
                for season in seasons:
                    output.append([crop, region, season,year ,planting_area[(crop, region, year, season)].varValue])

    output_df = pd.DataFrame(output, columns=['作物名称', '地块编号', '种植季节','年份', '种植数量'])
    output_df.to_excel('result_1_' + str(index) + '.xlsx', index=False)


if __name__ == "__main__":
    main(1, 1)
    main(0.5, 2)
