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

import pandas as pd
import numpy as np

sheet_names = ['851', '853', '854', '855', '857']
writer = pd.ExcelWriter('out_1.xlsx')

for name in sheet_names:
    df = pd.read_excel('测点-测压阀-第1批.xlsx', sheet_name=name, header=None, dtype=str)
    df = df.dropna(axis=0)
    df = np.array(df, dtype=int)

    link = {}

    for d in df:
        try:
            link[d[0]] = str(d[1])+'-'+str(d[2])+'-'+str(d[3])
        except:
            print(d)
    for i in range(1,65):
        if i not in link.keys():
            link[i] = ''
    df = pd.DataFrame([link])
    df = df.T
    df.sort_index(inplace=True)
    print(df)
    df.to_excel(writer,sheet_name=name,header=None)

writer.close()