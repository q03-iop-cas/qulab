# -*- coding: utf-8 -*-
import os
import re
import numpy as np

inline_mod  = re.compile(r'^\s*(.*)#(.*){{{setting}}}\s*$')
block_begin = re.compile(r'^(\s*)#{{{')
block_end   = re.compile(r'^(\s*)#}}}')

def _get_settings_from_script(fneme):
    '''从脚本中提取设置

    设置可以是单行代码，也可以多行代码
    单行代码以行末注释中的 `{{{setting}}}` 为标示
    多行代码以 `#{{{` 作为开始标示，以 `#}}}` 作为结束标示
    '''
    settings = []
    in_setting_section = False
    indent = 0

    with open(fneme) as f:
        lines = f.readlines()
        for line in lines:
            if not in_setting_section:
                m = block_begin.search(line)
                if m != None:
                    in_setting_section = True
                    indent = len(m.group(1))
            elif in_setting_section:
                m = block_end.search(line)
                if m != None:
                    in_setting_section = False
                    indent = 0
                else:
                    settings.append(line[indent:])
            else:
                m = inline_mod.search(line)
                if m != None:
                    s = m.group(1)+'#'+m.group(2)
                    settings.append(s.strip())

    return "".join(settings)

def _get_local_config_dir():
    '''获取配置所在的文件夹，若不存在则创建之。'''

    appdata = os.getenv('LOCALAPPDATA')
    homepath = os.getenv('HOMEPATH')
    home = os.getenv('HOME')

    if appdata is not None:
        localdata_base = appdata
    elif homepath is not None:
        localdata_base = homepath
    elif home is not None:
        localdata_base = home
    else:
        localdata_base = '.'

    config_dir = os.path.join(localdata_base, 'QuLab')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


from scipy.stats import beta
def get_probility(x, N, a=0.05):
    '''计算 N 此重复实验，事件 A 发生 x 次时，事件 A 的发生概率

    x : 事件发生次数
    N : 总实验次数
    a : 设置显著性水平 1-a，默认 0.05

    返回事件 A 发生概率 P 的最概然取值、期望、以及其置信区间
    '''
    P = 1.0*x/N
    E = (x+1.0)/(N+2.0)
    std = np.sqrt(E*(1-E)/(N+3))
    low, high = beta.ppf(0.5*a,x+1,N-x+1), beta.ppf(1-0.5*a,x+1,N-x+1)
    return P, E, std, (low, high)

def get_threshold(data, delta=1e-7):
    '''给定一组成双峰分布的数据 data 计算双峰之间的分界值

    data : 数据类型 numpy.array
    delta: 精确度，默认 delta = 1e-7
    '''
    threshold = m1 = m2 = data.mean()
    while True:
        g1 = data[data<threshold]
        g2 = data[data>threshold]
        m1 = g1.mean()
        m2 = g2.mean()
        t = (m1+m2)/2
        if abs(threshold-t) < delta:
            break
        threshold = t
    return threshold
