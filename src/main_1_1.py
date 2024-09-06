import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

# read data from 4 csv files
file1 = pd.read_csv('附件\附件(csv)\附件1_乡村的现有耕地.csv')
file2 = pd.read_csv('附件\附件(csv)\附件1_乡村种植的农作物.csv')
file3 = pd.read_csv('附件\附件(csv)\附件2_2023年的农作物种植情况.csv')
file4 = pd.read_csv('附件\附件(csv)\附件2_2023年统计的相关数据.csv')

# create dict
crop_prices = dict()