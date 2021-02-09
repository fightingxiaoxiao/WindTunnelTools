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

import numpy as np
import pandas as pd


class aerodynamicalBalance:
    def __init__(self):
        self.F = None  # 力与力矩
        self.array = None  # 系数矩阵
        self.angle = None

    def getDelta(self):
        pass

    def setLinearArray(self, array):
        """
        读入系数矩阵并求逆.

        [input]
        array: 测力天平系数矩阵
        """
        try:
            self.array = np.linalg.inv(array)
        except(np.linalg.LinAlgError):
            print("Error: Singular matrix.\n")
            print("press any key to exit...")
            input()
            exit()

    def reverse(self):
        """
        用于倒置转动的方向.
        """
        self.F = self.F[::-1]

    def left_offset(self, offset):
        """
        用于攻角的偏移.
        """
        self.F = np.r_[self.F[offset:], self.F[:offset]]

    def solve(self):
        self.F = np.dot(self.array, self.F.T)
        self.F = self.F.T

    def readTXTFromDiv5(self, filename):
        """
        [input]
        filename: 测力天平输出的数据文件.txt, 要求第一行为初始标定行，其余为各风攻角数据行
        例：
        2021-1-28     14:13:54   -155.9  94.2  235.1  124.6  -187.1 #无风时的测量值
        2021-1-28     14:22:53   -67.9  159.9  245.8  147.3  -190.5 #第1个攻角的测量值
        ...
        2021-1-28     14:56:16   -48.6  152.0  279.1  155.3  -192.3 #第N个攻角的测量值
        """
        df = []
        with open(filename, 'r') as f:
            for line in f:
                if len(line.split()) < 7:
                    continue
                Fx = float(line.split()[2])  # 阻力
                Fy = float(line.split()[4])  # 侧力
                Mx = float(line.split()[5])
                My = float(line.split()[6])
                Mz = float(line.split()[3])  # 扭矩

                df.append([Fx, Fy, Mx, My, Mz])
        df = np.array(df)
        self.F = (df[1:] - df[0]*0.8)*9.8*3

    def writeCSV(self, filename):
        df = pd.DataFrame(self.F, columns=['Fx', 'Fy', 'Mx', 'My', 'Mz'])
        df.to_csv(filename)


exp = aerodynamicalBalance()
exp.readTXTFromDiv5("./2/S02sz.txt")


#                         A_x,        A_y,       A_Mx,      A_My,        A_Mz
linearArray = np.array([[657.25,    -5.75,      -2.75,      2.25,       -14.25],
                        [3.,        636.75,     -40.75,     4.,         3.5],
                        [-14.88,    41.67,      1005.95,    47.62,      68.45],
                        [-3.125,    -12.5,      12.5,       1450.,      -87.5],
                        [-36.46,    49.48,      20.83,      -10.42,     981.77]
                        ])
"""
#                         A_x,        A_y,       A_Mx,      A_My,        A_Mz
linearArray = np.array([[11.6291,   0.304683,   0.203510,   5.16915,    0.196532],
                        [0.537178,  11.7802,    0.844642,   13.7121,    -1.00839],
                        [-0.33640,  6.089970,   78.7836,    13.1332,    6.089971],
                        [0.149424,  0.037948,   -1.14801,   227.780,    1.077400],
                        [18.74630,  -0.38495,   0.580840,   -15.580,    227.7801]
                        ])
"""

exp.setLinearArray(linearArray)
exp.solve()

exp.reverse()
exp.left_offset(5)
print(exp.F)

exp.writeCSV("test2.csv")
