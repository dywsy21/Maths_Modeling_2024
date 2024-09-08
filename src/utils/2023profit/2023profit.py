import pandas as pd
from pulp import *

if __name__ == "__main__":
    full_table = pd.read_csv('src\\data\\full_table.csv')
    profit = 0
    for i, row in full_table.iterrows():
        profit += row['种植面积/亩'] * (row['亩产量/斤'] * row['平均价格/(元/斤)'] - row['种植成本/(元/亩)'])
    print(profit)

    # 5926348.25