import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

def main():
    full_table = pd.read_csv('src\\data\\full_table.csv')
    file2 = pd.read_csv('附件\\附件(csv)\\附件1_乡村种植的农作物.csv')
    
    # create dict of land areas
    region_areas = dict(zip(full_table['种植地块'],full_table['种植面积/亩']))

    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    # Create a sole decision variable: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season]
    x = LpVariable.dicts("planting_area", ((crop, region, year, season) for crop in full_table['作物名称'] for region in full_table['种植地块'].unique() for year in range(2024, 2031) for season in full_table['种植季次'].unique()), lowBound=0, cat='Continuous')

    text: str = file2['种植耕地']
    land_seasons = text.split(';')
    land_seasons_dict: dict = {}
    for land_season in land_seasons:
        land_season = land_season.split(':')
        land = land_season[0]
        if len(land_season) > 1:
            seasons = land_season[1].split(' ')
            land_seasons_dict[land] = seasons

if __name__ == '__main__':
    main()