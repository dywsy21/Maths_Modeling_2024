import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary

def main():
    full_table = pd.read_csv('data/full_table.csv')

    # create dict
    crop_prices = dict()


    linear_model = LpProblem(name="profit_maximization", sense=LpMaximize)
    