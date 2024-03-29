"""
Copyright 2021 Chen Xiaoxiao

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Python 3.7+ is recommended for this script.
"""
# import multiprocessing  # 多线程
from progressbar import *

import meshio  # 读写网格
import numpy as np  # 向量操作
import pandas as pd  # 读写表格
import yaml  # 配置文件
import platform


class pressureMeasurement:
    """
    测压试验.
    """

    def __init__(self, angle=None):
        """
        使用风攻角初始化一次测量.
        """
        self.measureTubes = {}  # {851:[tube1,tube2,tube3,...],...}
        self.angle = angle       # 风攻角
        self.pitotTubes = {'pitot_0': [], 'pitot_1': []}     # 皮托管，1根测总压，1根测静压

        self.configParams = None
        self.maxScannerPoints = 0

        self.dynamicPressure = []
        self.staticPressure = []
        self.referenceVelocity = []

    def config(self):
        """
        读取配置文件_config.yml.
        """
        with open('_config.yml', 'r') as f:
            # add Loader=yaml.FullLoader in Linux
            if platform.system() == 'Linux':
                self.configParams = yaml.load(f, Loader=yaml.FullLoader)
            elif platform.system() == 'Windows':
                self.configParams = yaml.load(f)
            else:
                print("Unknown system.")
                exit()
        try:
            self.configParams['dataFile'][self.angle]
        except KeyError:
            print("Error: Cannot find angle " +
                  str(self.angle) + " in config file.")
            exit()

        if len(self.configParams['referenceVelocity']) != 0:
            if len(self.configParams['referenceVelocity']) == self.configParams['scanTimes']:
                self.referenceVelocity = self.configParams['referenceVelocity']
            else:
                raise Exception(
                    'Error: scanTimes does not equal to the length of referenceVelocity.')
        else:
            pass

    def readScannerInfo(self):
        """
        读取扫描阀和测点的连接关系.
        """
        # 获取单次测量的测压管总数
        for tubeNumber in self.configParams['scanner'].values():
            self.maxScannerPoints += tubeNumber

        # 依据外部表格实例化测压管对象
        scanTimes = 0
        for file in self.configParams['scannerLinkfile']:
            for scanner in self.configParams['scanner']:
                df = pd.read_excel(file, sheet_name=str(scanner), header=None)
                df = df.iloc[:,:2]
                df = np.array(df.dropna(axis=0))
                for item in df:
                    mtube = measureTube(int(item[0]), str(item[1]), scanner)
                    if scanner not in self.measureTubes.keys():
                        self.measureTubes[scanner] = {}
                    if int(item[0]) not in self.measureTubes[scanner].keys():
                        self.measureTubes[scanner][int(item[0])] = {}
                    self.measureTubes[scanner][int(item[0])][scanTimes] = mtube

            pitot_tube_0 = measureTube(self.configParams['pitotTubesLinkName']['pitot_0'][scanTimes][1],
                                       'pitot_0',
                                       self.configParams['pitotTubesLinkName']['pitot_0'][scanTimes][0])
            self.pitotTubes['pitot_0'].append(pitot_tube_0)

            pitot_tube_1 = measureTube(self.configParams['pitotTubesLinkName']['pitot_1'][scanTimes][1],
                                       'pitot_1',
                                       self.configParams['pitotTubesLinkName']['pitot_1'][scanTimes][0])
            self.pitotTubes['pitot_1'].append(pitot_tube_1)
            scanTimes += 1

    def readDataFile(self):
        data = []
        for file in self.configParams['dataFile'][self.angle]:
            df = pd.read_csv(file)
            col = [i for i in range(df.shape[1])]
            df = pd.read_csv(file, header=None, usecols=col)
            data.append(df)
        # 此处可考虑多线程优化
        key_list = list(self.configParams['scanner'].keys())

        for s_index in self.measureTubes:
            for scanner_tube in self.measureTubes[s_index].values():
                for i_tube in scanner_tube:
                    index = key_list.index(
                        s_index) * self.configParams['scanner'][s_index] + scanner_tube[i_tube].index
                    scanner_tube[i_tube].data = np.array(data[i_tube][index])

        for pitot in self.pitotTubes.values():
            for pitot_i in range(len(pitot)):
                index = key_list.index(
                    pitot[pitot_i].scanner) * self.configParams['scanner'][pitot[pitot_i].scanner] + pitot[pitot_i].index
                pitot[pitot_i].data = np.array(data[pitot_i][index])
                pitot[pitot_i].getCharacters()

    def classifyPitotTubes(self):
        for i in range(self.configParams['scanTimes']):
            p_0 = self.pitotTubes['pitot_0'][i].characters['avg']
            p_1 = self.pitotTubes['pitot_1'][i].characters['avg']

            self.dynamicPressure.append(abs(p_0 - p_1))
            self.staticPressure.append(min(p_0, p_1))

            if len(self.referenceVelocity) != self.configParams['scanTimes']:
                self.referenceVelocity.append(
                    (self.dynamicPressure[i] / self.configParams['rho'] * 2) ** 0.5)

            if p_0 >= p_1:
                self.pitotTubes['pitot_0'][i].pitotProperty = 2
                self.pitotTubes['pitot_1'][i].pitotProperty = 1
            else:
                self.pitotTubes['pitot_0'][i].pitotProperty = 1
                self.pitotTubes['pitot_1'][i].pitotProperty = 2

    def generateCoeff(self):
        for s_index in self.measureTubes:
            for scanner_tube in self.measureTubes[s_index].values():
                for i_tube in scanner_tube:
                    scanner_tube[i_tube].convertPressureCoeff(
                        self.configParams['rho'], self.referenceVelocity, self.staticPressure, i_tube)
                    scanner_tube[i_tube].getCharacters()

    def rotate(self):
        """
        修改风攻角
        """
        pass

    def write(self, writer, sort_law):
        """
        """
        tubeList = []
        tubeNameList = []
        for scanner in self.measureTubes.values():
            for MeasureTube in scanner.values():
                for singleMeasureTube in MeasureTube.values():
                    tubeList.append([singleMeasureTube.characters['avg'],
                                     singleMeasureTube.characters['max'],
                                     singleMeasureTube.characters['min'],
                                     singleMeasureTube.characters['std']])
                    tubeNameList.append(singleMeasureTube.name)
        df = pd.DataFrame(data=tubeList, columns=['avg', 'max', 'min', 'std'])
        df.index = tubeNameList
        tubeNameList.sort(key=sort_law)
        df = df.loc[tubeNameList]
        df.to_excel(writer, sheet_name=str(self.angle))


class measureTube:
    """
    测压管.
    """

    def __init__(self, index, name, scanner_index):
        self.name = name              # 编号
        self.scanner = scanner_index
        self.index = index
        self.data = None                # 数据向量
        self.samplingFrequency = None   # 采样频率
        self.samplingTime = None        # 采样时间
        self.linkPoint = None           # 链接名称
        self.characters = {}
        self.pitotProperty = 0          # 0:不是皮托管  1: 测静压皮托管  2: 测总压皮托管

    def getCharacters(self):
        self.characters['max'] = np.max(self.data)
        self.characters['min'] = np.min(self.data)
        self.characters['avg'] = np.mean(self.data)
        self.characters['std'] = np.std(self.data)

    def convertPressureCoeff(self, rho, refVelocity, staticPressure, scanTimes):
        self.data -= staticPressure[scanTimes]
        self.data /= 0.5 * rho * refVelocity[scanTimes]**2


def main(angle_i, exp_list):
    # print("Processing angle " + str(angle_i*15)+"...\r",end='')
    exp = pressureMeasurement(angle=angle_i)
    exp.config()
    exp.readScannerInfo()
    exp.readDataFile()
    exp.classifyPitotTubes()
    exp.generateCoeff()
    exp_list[angle_i] = exp


if __name__ == '__main__':
    exp_list = {}
    widgets = ['Progress: ', Percentage(), ' ', Bar(
        marker='#'), ' ', ETA(), '  ', FormatLabel('Processing angle %(value)d..'), AnimatedMarker(markers='|/-\\')]
    pbar = ProgressBar(widgets=widgets, maxval=345).start()
    for i in range(24):
        main(i * 15, exp_list)
        pbar.update(i * 15)
    pbar.finish()

    print('Output Excel file...', end="")
    writer = pd.ExcelWriter('result.xlsx')

    def sort_law(x):
        return (int(x.split('-')[0]), int(x.split('-')[1]), int(x.split('-')[2]))

    for exp in exp_list.values():
        exp.write(writer, sort_law)
    writer.close()
    print('done.')
