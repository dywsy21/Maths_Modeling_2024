import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

def main(reduction_factor, index):
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')

    # full_table = pd.read_csv('full_table.csv')
    # file2 = pd.read_csv('附件1_乡村种植的农作物.csv')

    # 将full_table中的单季改为第一季
    full_table['种植季次'] = full_table['种植季次'].apply(lambda x: '第一季' if x == '单季' else x)

    seasons = ['第一季', '第二季']
    years = list(range(2024, 2031))
    regions = full_table['种植地块'].unique()
    crops = full_table['作物名称'].unique()

    region_areas = {region: full_table.loc[full_table['种植地块'] == region, '种植面积/亩'].sum() for region in regions}
    region_to_type = dict(zip(full_table['种植地块'], full_table['地块类型']))

    # 初始化模型
    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)

    #planting area and binary planting decision
    planting_area = LpVariable.dicts("planting_area", [(crop, region, year, season) for crop in crops for region in regions for year in years for season in seasons], lowBound=0, cat='Continuous')
    planting_decision = LpVariable.dicts("planting_decision", [(crop, region, year, season) for crop in crops for region in regions for year in years for season in seasons], cat='Binary')

    # 休耕政策：用于土地休耕的新二元变量
    fallow_decision = LpVariable.dicts("fallow_decision", [(region, year, season) for region in regions for year in years for season in seasons], cat='Binary')

    # 约束条件

    # 放宽： 在第二季度种植
    for region in regions:
        for year in years:
            linear_model += lpSum(planting_decision[(crop, region, year, '第二季')] for crop in crops) <= 5

    # 作物轮作限制：惩罚连续几年重复种植同一作物
    for crop in crops:
        for region in regions:
            for year in years[:-1]:
                linear_model += planting_decision[(crop, region, year, '第一季')] + planting_decision[(crop, region, year + 1, '第一季')] <= 1

    # 休耕地限制：土地只能用于种植，不能休耕，不能同时用于种植和休耕。
    for region in regions:
        for year in years:
            for season in seasons:
                linear_model += lpSum(planting_decision[(crop, region, year, season)] for crop in crops) + fallow_decision[(region, year, season)] <= 1

    # 最小化种植面积的限制
    for crop in crops:
        for region in regions:
            for year in years:
                for season in seasons:
                    linear_model += planting_area[crop, region, year, season] >= 0.1 * region_areas[region] * planting_decision[crop, region, year, season]
                    linear_model += planting_area[crop, region, year, season] <= region_areas[region] * planting_decision[crop, region, year, season]

    # 总体的种植区域
    for region in regions:
        for year in years:
            for season in seasons:
                linear_model += lpSum(planting_area[crop, region, year, season] for crop in crops) <= region_areas[region]

    # 相对于销售预期而言生产过剩的惩罚
    def get_expected_sales(crop, season):
        ret = 0
        for i, row in full_table.iterrows():
            if row['作物名称'] == crop and row['种植季次'] == season:
                ret += row['预期销售量/斤']
        return ret

    def get_yield_per_acre(crop, region):
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

    # 带有过度生产惩罚和销售利润的目标函数
    def get_profit(crop, year):
        total_yield = get_total_yield(crop, year)
        expected_sales = get_expected_sales(crop, '第一季') + get_expected_sales(crop, '第二季')
        if total_yield <= expected_sales:
            return lpSum(planting_area[(crop, region, year, season)]
                         * (get_yield_per_acre(crop, region) * get_price(crop, season) - get_cost(crop, region))
                         for region in regions for season in seasons)
        else:
            return (lpSum(planting_area[(crop, region, year, season)] * get_yield_per_acre(crop, region) * get_price(crop, season)
                          - get_cost(crop, region) for region in regions for season in seasons)
                    - reduction_factor * (total_yield - expected_sales))

    # 最终目标函数（最大化利润并纳入休耕决策）
    linear_model += lpSum(get_profit(crop, year) for crop in crops for year in years) - lpSum(fallow_decision[(region, year, season)] * 100 for region in regions for year in years for season in seasons)

    # Solve model
    linear_model.solve()

    # 确保求解后可以访问变量值
    results = []
    for year in years:
        for crop in crops:
            for region in regions:
                for season in seasons:
                    # 始终导出值（即使为零）以保持格式一致 
                    area = planting_area[(crop, region, year, season)].varValue if planting_area[(crop, region, year, season)].varValue else 0
                    results.append([year, crop, region, season, area])

    # 导出
    df = pd.DataFrame(results, columns=['Year', 'Crop', 'Region', 'Season', 'Planted Area'])
    df.to_excel("result1_" + str(index) + "_modified.xlsx", index=False)

    #终端输出每年的任务值
    for k in years:
        yearly_obj_value = lpSum(
            (get_price(crop, season) * get_yield_per_acre(crop, region) - get_cost(crop, region)) * planting_area[crop, region, k, season].varValue
            for crop in crops for region in regions for season in seasons
            if planting_area[crop, region, k, season].varValue > 0
        )
        print(f"Year {k} objective function value: {yearly_obj_value}")

if __name__ == "__main__":
    main(1, 1)
    main(0.5, 2)
