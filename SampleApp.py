# -*- coding: utf-8 -*-
from qulab import Application

from scipy.stats import beta
def get_probility(x, N, a=0.05):
    '''计算 N 此重复实验，事件 A 发生 x 次时，事件 A 的发生概率

    x : 事件发生次数
    N : 总实验次数
    a : 设置显著性水平 1-a，默认 0.05

    返回事件 A 发生概率 P 的最概然取值、期望、以及其置信区间
    '''
    P = x/N
    E = (x+1.0)/(N+2.0)
    std = np.sqrt(E*(1-E)/(N+3))
    low, high = beta.ppf(0.5*a,x+1,N-x+1), beta.ppf(1-0.5*a,x+1,N-x+1)
    return P, E, std, (low, high)

class SubsubApp(Application):
    __title__ = 'One Point'
    __version__ = 'v0.1'

    def discription(self):
        pass

    def plots(self):
        pass

    def measurement(self):
        P, _, _, (down_bond, up_bond) = get_probility(x, N)
        return P, down_bond, up_bond

class SubApp(Application):
    __title__ = 'Line'
    __version__ = 'v0.1'

    def discription(self):
        pass

    def measurement(self):
        pass

class SampleApp(Application):
    __title__ = 'Image'
    __version__ = 'v0.1'

    def discription(self):
        pass

    def prepare(self):
        pass

    def measurement(self):
        pass

if __name__ == "__main__":
    import sys
    app = SampleApp(sys.argv)
    sys.exit(app.run())
