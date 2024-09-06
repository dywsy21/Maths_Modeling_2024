import csv
import pandas as pd

the_csv_to_be_appended = pd.read_csv('附件/附件(csv)/附件2_2023年的农作物种植情况.csv', encoding='utf-8-sig')
file_1 = pd.read_csv('附件/附件(csv)/附件1_乡村的现有耕地.csv', encoding='utf-8-sig')
file_2 = pd.read_csv('附件/附件(csv)/附件2_2023年统计的相关数据.csv', encoding='utf-8-sig')

# add 地块类型 from 附件1_乡村的现有耕地 to 附件2_2023年的农作物种植情况
def add_from_file_1():
    # Assuming 'common_key' is the column to join on
    merged_df = pd.merge(the_csv_to_be_appended, file_1[['common_key', '地块类型']], on='common_key', how='left')
    return merged_df
def add_from_file_1():
