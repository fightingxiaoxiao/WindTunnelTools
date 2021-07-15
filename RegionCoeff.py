import pandas as pd
import numpy as np


def main(angle):
    filename = 'result.xlsx'
    df = pd.read_excel(filename, sheet_name=str(angle))
    df = np.array(df)
    region_list = {}
    key_list = []
    for p in df:
        region_name = p[0].split('-')[1]+'-'+p[0].split('-')[2]
        if region_name not in region_list.keys():
            region_list[region_name] = 0.
            key_list.append(region_name)
        region_list[region_name] += p[1]
    return region_list, key_list


angle_list = {}
for i in range(24):
    angle_true = 270 - i*15
    if angle_true < 0:
        angle_true += 360
    angle_list[angle_true], angle_key_list = main(i*15)

array_by_floor = {}
for key in angle_key_list:
    if key.split('-')[0] not in array_by_floor.keys():
        array_by_floor[key.split('-')[0]] = {}
    array_by_floor[key.split('-')[0]][key] = {}
    for i in range(24):
        array_by_floor[key.split('-')[0]][key][i*15] = angle_list[i*15][key]

writer = pd.ExcelWriter('RegionCoeff.xlsx')
for i in range(11):
    df = pd.DataFrame(data=array_by_floor[str(i)])
    df = df.round(2)
    df.to_excel(writer, sheet_name=str(i))
writer.close()
