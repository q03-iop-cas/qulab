# -*- coding: utf-8 -*-
import numpy as np

def get_unit_prefix(value):
    '''获取 value 合适的单位前缀，以及相应的倍数'''

    prefixs = ['y', 'z', 'a', 'f', 'p', 'n', 'u', 'm',
                '', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    x = np.floor(np.log10(value)/3)
    if x < -8:
        x = -8
    if x > 8:
        x = 8
    return prefixs[int(x)+8], 1000**(x)

# 单位转换
def dBm2W(p):
    return 10**(p/10.0 - 3)

def W2dBm(p):
    return np.log10(p)*10.0 + 30

class QuantTypes:
    INTEGER = 0
    DOUBLE  = 1
    VECTOR  = 2
    STRING  = 3
    OPTION  = 4
    BOOL    = 5

class Quantity():
    def __init__(self, name, value=None, type=QuantTypes.DOUBLE, unit=None, dimension=None):
        self.name = name
        self.value = value
        self.type = type
        self.unit = unit
        self.dimension = dimension

    def __str__(self):
        '''当量带单位时，将数值折算到 0-1000 以内，并配合恰当的单位前缀
        如： 1.5e4 m  -> 15 km
        '''
        if self.type == QuantType.VECTOR:
            return '<%d dem vector>' % len(self.value)
        elif self.type == QuantType.NUMBER and self.unit != '':
            p, r  = get_unit_prefix(self.value)
            value = self.value/r
            unit  = p+self.unit
            return '%g %s' % (value, unit)
        else:
            return '%g' % self.value

if __name__ == '__main__':
    def test(value):
        p, r = get_unit_prefix(value)
        print ('%g = %.3f %s' % (value, value/r, p))

    test(1.23e-34)
    test(1.23e-24)
    test(1.23e-14)
    test(1.23e-4)
    test(1.23)
    test(1.23e4)
