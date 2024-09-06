import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary
# timo
def main():
    full_table = pd.read_csv('src\data\\full_table.csv')

    # create dict of land areas
    land_areas = dict(zip(full_table['种植地块'],full_table['种植面积/亩']))

    # create dict
    crop_prices = dict()


    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    
    # Create a sole decision variable: the number of hectares to plant with [each crop] in [each region] at [each year] at [each season]
    x = LpVariable.dicts