import numpy as np
import pandas as pd


class point():
    def __init__(self, name, avg, max):
        self.name = name
        self.avg = avg
        self.max = max


class building():
    def __init__(self):
        self.floor = {}
        self.force = {}


def readExcel(filename):
    floor_info = pd.read_csv('floor.csv')
    floor_info_array = np.array(floor_info)
    #print(floor_info_array)
    data_list = {}
    for angle in range(0, 360, 15):
        data = pd.read_excel(filename, sheet_name=str(angle))

        points = []
        for item in data.itertuples():
            p = point(item[1], item[2], item[3])
            points.append(p)

        building_test = building()

        for p in points:
            p_key = int(p.name.split('-')[0])
            if p_key > 43:
                continue
            if p_key not in building_test.floor.keys():
                building_test.floor[p_key] = np.array([0., 0., 0.])
                building_test.force[p_key] = np.array([0., 0., 0.])
                
            if int(p.name.split('-')[2]) < 4:
                building_test.floor[p_key] += np.array([-p.avg, 0., 0.])
                building_test.force[p_key] += np.array(
                    [-p.avg, 0., 0.])*0.25*floor_info_array[p_key-1][1]*54.5*1.225*0.5*86**2/1000
            elif int(p.name.split('-')[2]) < 7:
                building_test.floor[p_key] += np.array([0., -p.avg, 0.])
                building_test.force[p_key] += np.array(
                    [0., -p.avg, 0.])*0.333*floor_info_array[p_key-1][1]*34*1.225*0.5*86**2/1000
            elif int(p.name.split('-')[2]) < 11:
                building_test.floor[p_key] += np.array([p.avg, 0., 0.])
                building_test.force[p_key] += np.array(
                    [p.avg, 0., 0.])*0.25*floor_info_array[p_key-1][1]*54.5*1.225*0.5*86**2/1000
            else:
                building_test.floor[p_key] += np.array([0., p.avg, 0.])
                building_test.force[p_key] += np.array(
                    [0., p.avg, 0.])*0.333*floor_info_array[p_key-1][1]*34*1.225*0.5*86**2/1000

        coeff = []
        force = []
        force_vector = []
        for i in range(1, 44):
            coeff.append(np.linalg.norm(building_test.floor[i]))
            force.append(np.linalg.norm(building_test.force[i]))
            force_vector.append(building_test.force[i])
        force_vector=np.array(force_vector)

        df = pd.DataFrame(data=coeff, columns=['coeff'])

        df = floor_info.join(df)
        df = df.join(pd.DataFrame(data=force_vector.astype(int), columns=['Fx','Fy','Fz']))
        df = df.join(pd.DataFrame(data=force, columns=['force']))
        # print(df)
        angle_t = 270 - angle
        if angle_t < 0:
            angle_t += 360
        print(angle_t)
        data_list[angle_t] = df

    writer = pd.ExcelWriter('shearResult.xlsx')
    for i in range(0, 360, 15):
        data_list[i].to_excel(writer, sheet_name=str(i))
    writer.close()

readExcel('result.xlsx')