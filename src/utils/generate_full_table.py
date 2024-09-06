import csv
import pandas as pd

the_csv_to_be_appended = pd.read_csv('附件/附件(csv)/附件2_2023年的农作物种植情况.csv', encoding='utf-8-sig')
file_1 = pd.read_csv('附件/附件(csv)/附件1_乡村的现有耕地.csv', encoding='utf-8-sig')
file_2 = pd.read_csv('附件/附件(csv)/附件2_2023年统计的相关数据.csv', encoding='utf-8-sig')

# add 地块类型 from 附件1_乡村的现有耕地 to 附件2_2023年的农作物种植情况
def add_from_file_1():
    land_type_dict = dict(zip(file_1['地块名称'], file_1['地块类型']))
    the_csv_to_be_appended['地块类型'] = the_csv_to_be_appended['种植地块'].map(land_type_dict)

def add_from_file_2():
    # 作物名称种植季次_to_亩产量种植成本销售单价_dict = dict(zip((file_2['作物名称'], file_2['种植季次']), (file_2['亩产量/斤'], file_2['种植成本/(元/亩)'], file_2['销售单价/(元/斤)'])))
    # Create a multi-index mapping for 作物编号, 地块类型, and 种植季次 to 亩产量
    land_type_mapping1 = file_2.set_index(['作物名称', '地块类型', '种植季次']).to_dict()['亩产量/斤']
    land_type_mapping2 = file_2.set_index(['作物名称', '地块类型', '种植季次']).to_dict()['种植成本/(元/亩)']
    land_type_mapping3 = file_2.set_index(['作物名称', '地块类型', '种植季次']).to_dict()['销售单价/(元/斤)']

    the_csv_to_be_appended['亩产量/斤'] = the_csv_to_be_appended.apply(lambda row: land_type_mapping1.get((row['作物名称'], row['地块类型'], row['种植季次'])), axis=1)
    the_csv_to_be_appended['种植成本/(元/亩)'] = the_csv_to_be_appended.apply(lambda row: land_type_mapping2.get((row['作物名称'], row['地块类型'], row['种植季次'])), axis=1)
    the_csv_to_be_appended['销售单价/(元/斤)'] = the_csv_to_be_appended.apply(lambda row: land_type_mapping3.get((row['作物名称'], row['地块类型'], row['种植季次'])), axis=1)


if __name__ == '__main__':
    add_from_file_1()
    add_from_file_2()
    the_csv_to_be_appended.to_csv('full_table.csv', index=False, encoding='utf-8-sig')