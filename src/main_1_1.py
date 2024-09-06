import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

full_table = pd.read_csv('src\data\\full_table.csv')

# create dict of land areas
land_areas = dict(zip(full_table['种植地块'],full_table['种植面积/亩']))
