import pandas as pd

the_csv_to_be_appended = pd.read_csv('附件/附件(csv)/附件2_2023年的农作物种植情况.csv', encoding='utf-8-sig')
file_1 = pd.read_csv('附件/附件(csv)/附件1_乡村的现有耕地.csv', encoding='utf-8-sig')
file_2 = pd.read_csv('附件/附件(csv)/附件2_2023年统计的相关数据.csv', encoding='utf-8-sig')

# add 地块类型 from 附件1_乡村的现有耕地 to 附件2_2023年的农作物种植情况
def add_from_file_1():
    land_type_dict = dict(zip(file_1['地块名称'], file_1['地块类型']))
    the_csv_to_be_appended['地块类型'] = the_csv_to_be_appended['种植地块'].map(land_type_dict)

def add_from_file_2():
    land_type_mapping1 = file_2.set_index(['作物名称', '地块类型', '种植季次']).to_dict()['亩产量/斤']
    land_type_mapping2 = file_2.set_index(['作物名称', '地块类型', '种植季次']).to_dict()['种植成本/(元/亩)']
    land_type_mapping3 = file_2.set_index(['作物名称', '地块类型', '种植季次']).to_dict()['销售单价/(元/斤)']

    the_csv_to_be_appended['亩产量/斤'] = the_csv_to_be_appended.apply(lambda row: land_type_mapping1.get((row['作物名称'], row['地块类型'], row['种植季次'])), axis=1)
    the_csv_to_be_appended['种植成本/(元/亩)'] = the_csv_to_be_appended.apply(lambda row: land_type_mapping2.get((row['作物名称'], row['地块类型'], row['种植季次'])), axis=1)
    the_csv_to_be_appended['销售单价/(元/斤)'] = the_csv_to_be_appended.apply(lambda row: land_type_mapping3.get((row['作物名称'], row['地块类型'], row['种植季次'])), axis=1)
    # (2) 智慧大棚第一季可种植的蔬菜作物及其亩产量、种植成本和销售价格均与普通大棚相同，表中省略。
    # apply this logic to the data
    for column in ['亩产量/斤', '种植成本/(元/亩)', '销售单价/(元/斤)']:
        ordinary_rows = file_2[
            (file_2['地块类型'] == '普通大棚') & 
            (file_2['种植季次'] == '第一季')
        ]

        for idx, smart_row in the_csv_to_be_appended[
            (the_csv_to_be_appended['地块类型'] == '智慧大棚') & 
            (the_csv_to_be_appended['种植季次'] == '第一季')
        ].iterrows():
            matching_ordinary_row = ordinary_rows[
                ordinary_rows['作物名称'] == smart_row['作物名称']
            ]
            if not matching_ordinary_row.empty:
                the_csv_to_be_appended.at[idx, column] = matching_ordinary_row.iloc[0][column]
            else:
                # If no match is found, retain the existing data
                the_csv_to_be_appended.at[idx, column] = smart_row[column]


def calculate_expected_sales_volume():
    the_csv_to_be_appended['预期销售量/斤'] = the_csv_to_be_appended['种植面积/亩'] * the_csv_to_be_appended['亩产量/斤']

def calculate_average_price():
    def get_average_price(price_range):
        if price_range and '-' in price_range:
            low, high = map(float, price_range.split('-'))
            return (low + high) / 2
        if price_range:
            return float(price_range)
        return None
    
    the_csv_to_be_appended['平均价格/元'] = the_csv_to_be_appended['销售单价/(元/斤)'].apply(get_average_price)


if __name__ == '__main__':
    add_from_file_1()
    add_from_file_2()
    calculate_expected_sales_volume()
    calculate_average_price()
    the_csv_to_be_appended.to_csv('full_table.csv', index=False, encoding='utf-8-sig')
