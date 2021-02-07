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
        self.measurePoints = {}  # {851:[tube1,tube2,tube3,...],...}
        self.angle = angle       # 风攻角
        self.pitotTubes = {}     # 皮托管，1根测总压，1根测静压

        self.configParams = None

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

        for s_id, number in self.configParams['scanner'].items():
            try:
                self.measurePoints[s_id]
            except KeyError:
                self.measurePoints[s_id] = []
            finally:
                self.measurePoints[s_id] += [None for i in range(number)]

    def readScannerInfo(self):
        """
        读取扫描阀和测点的连接关系.
        """
        for file in self.configParams['scannerLinkfile']:
            for scanner in self.configParams['scanner']:
                df = pd.read_excel(file, sheet_name=str(scanner), header=None)
                df = df.dropna(axis=0)
                print(np.array(df))


    def readDataFile(self):
        for file in self.configParams['dataFile'][self.angle]:
            df = pd.read_csv(file)
            col = [i for i in range(df.shape[1])]
            df = pd.read_csv(file, header=None, usecols=col)

            # 按照每列数据实例化测压管对象
            # 此处可考虑多线程优化
            for i in col[1:]:
                mtube = measureTube(i, np.array(df[i]))
                mtube.getCharacters()

    def rotate(self):
        """
        修改风攻角
        """
        pass


class measureTube:
    """
    测压管.
    """

    def __init__(self, index, data):
        self.index = index              # 编号
        self.data = data                # 数据向量
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
exp.readDataFile()
exp.readScannerInfo()
