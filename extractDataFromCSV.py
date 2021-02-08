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

Python 3.7+ on Windows 10 is recommended for this script.
"""
import multiprocessing  # 多线程

import meshio  # 读写网格
import numpy as np  # 向量操作
import pandas as pd  # 读写表格
import yaml  # 配置文件


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
        self.pitotTubes = {}     # 皮托管，1根测总压，1根测静压

        self.configParams = None
        self.maxScannerPoints = 0

    def staticPressure(self):
        pass

    def dynamicPressure(self):
        pass

    def config(self):
        """
        读取配置文件_config.yml.
        """
        with open('_config.yml', 'r') as f:
            # add Loader=yaml.FullLoader in Linux
            self.configParams = yaml.load(f)

        try:
            self.configParams['dataFile'][self.angle]
        except KeyError:
            print("Error: Cannot find angle " +
                  str(self.angle)+" in config file.")
            exit()

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
                df = np.array(df.dropna(axis=0))
                for item in df:
                    mtube = measureTube(int(item[0]), str(item[1]), scanner)
                    if scanner not in self.measureTubes.keys():
                        self.measureTubes[scanner] = {}
                    if int(item[0]) not in self.measureTubes[scanner].keys():
                        self.measureTubes[scanner][int(item[0])] = {}
                    self.measureTubes[scanner][int(item[0])][scanTimes] = mtube
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
                        s_index)*self.configParams['scanner'][s_index] + scanner_tube[i_tube].index + self.maxScannerPoints*i_tube
                    print(index)
        """
            for i in col[1:]:
                mtube = measureTube(i, np.array(df[i]))
                mtube.getCharacters()
        """

    def rotate(self):
        """
        修改风攻角
        """
        pass


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

    def getCharacters(self):
        self.characters['max'] = np.max(self.data)
        self.characters['min'] = np.min(self.data)
        self.characters['avg'] = np.mean(self.data)
        self.characters['std'] = np.std(self.data)


exp = pressureMeasurement(angle=0)
exp.config()
exp.readScannerInfo()
exp.readDataFile()
