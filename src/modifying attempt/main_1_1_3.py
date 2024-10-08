import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

def main(reduction_factor, index):
    # full_table = pd.read_csv('src\\data\\full_table.csv')
    # file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')
    full_table = pd.read_csv('full_table.csv')
    file2 = pd.read_csv('附件1_乡村种植的农作物.csv')

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


    second_season_allowed_crops = ['大白菜', '白萝卜', '红萝卜']

    for region in regions:
        for year in years:
            if region_areas[region] == '水浇地':
                second_season_constraint = lpSum(planting_decision[(crop, region, year, '第二季')] for crop in second_season_allowed_crops)
                linear_model += (second_season_constraint <= 1)


    bean_crops = ['黄豆', '黑豆', '红豆', '绿豆', '爬豆', '豇豆', '刀豆', '芸豆']
    for region in regions:
        for y_begin in range(2024, 2029):
            linear_model += lpSum(planting_decision[crop, region, year, season] for crop in bean_crops 
                                  for year in range(y_begin, y_begin + 3) for season in seasons) >= 1

    # 9. 每种作物每季的种植地不能太分散。我们限制最大种植地块数为 5。
    for year in years:
        for crop in crops:
            for season in seasons:
                linear_model += lpSum(planting_decision[crop, region, year, season] for region in regions) <= 5



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
                seasons = land_season[1].split(' ')
                land_seasons_dict[land] = seasons
            else:
                land_seasons_dict[land] = ['第一季']
        crop_to_condition[row['作物名称']] = land_seasons_dict
    # print(crop_to_condition)

    for crop in crops:
        for region in regions:
            for year in years:
                for season in seasons:
                    if region_areas[region] in crop_to_condition[crop]:
                        # print(season not in crop_to_condition[crop][region_to_type[region]], end=' ')
                        # if crop_to_condition[crop][region_areas[region]] == ['单季']:
                        #     # print('2！', end=' ')
                        #     linear_model += planting_decision[(crop, region, year, '第二季')] == 0
                        if season not in crop_to_condition[crop][region_areas[region]]:
                            # print('1！', end=' ')
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
            if row['作物名称'] == crop and row['种植地块'] == region:
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
        return lpSum(planting_area[(crop, region, year, season)] * get_yield_per_acre(crop, region) for region in regions for season in seasons)
    
    def my_max(a, b):
        return a if a >= b else b
    
    def get_profit(crop, year):
        if get_total_yield(crop, year) <= get_expected_sales(crop, '第一季') + get_expected_sales(crop, '第二季'):
            return my_max(lpSum(planting_area[(crop, region, year, season)]
                         * (get_yield_per_acre(crop, region) * get_price(crop, season) - get_cost(crop, region))
                        for region in regions for season in seasons
                    ), 0)
        else:
            return my_max(lpSum((planting_area[(crop, region, year, season)] * get_yield_per_acre(crop, region) - get_expected_sales(crop, season))
                         * get_price(crop, season) * (1 - reduction_factor) 
                         for region in regions for season in seasons) \
                    + lpSum(get_expected_sales(crop, season) * get_price(crop, season) for season in seasons) \
                    - lpSum(planting_area[(crop, region, year, season)] * get_cost(crop, region) for region in regions for season in seasons), 0)

    # 目标函数, 超出预期销售量的部分，价格乘以 reduction_factor
    linear_model += lpSum(get_profit(crop, year) for crop in crops for year in years)

    # # Define the target function: Maximize profit excluding dormant sales
    # linear_model += lpSum(
    #     get_price(crop, season) * get_yield_per_acre(crop, region) * planting_area[crop, region, year, season] - planting_area[crop, region, year, season] * get_cost(crop, region)
    #     for crop in crops for region in regions for year in years for season in seasons
    # )
    
    linear_model.writeLP("model.lp")
    linear_model.solve()


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
    results = {year: {crop: {region: planting_area[(crop, region, year, season)].varValue for region in regions} for crop in crops} for year in years}
    df = pd.DataFrame(results)
    df.to_excel("result1_" + str(index) + "_3.xlsx")

if __name__ == "__main__":
    main(1, 1)
    main(0.5, 2)
