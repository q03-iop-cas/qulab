class types:
    NUMBER = 0
    VECTOR = 1

class Quantity():
    def __init__(self):
        self.value = None
        self.type = None
        self.unit = None

        self._ins = None

        self.set_cmd = '{value}'
        self.get_cmd = ''

    def setValue(self, value, **kw):
        self.value = value
        if self._ins is not None:
            self._ins.write(self.set_cmd.format(value=value, **kw))

    def getValue(self, **kw):
        if self._ins is not None:
            self.value = self.fromstr(self._ins.query(self.get_cmd.format(**kw)))
        return self.value

    def fromstr(self, s):
        pass

class BaseDriver():
    def __init__(self, ins, addr=None):
        self.addr = addr
        self.ins = ins
        self.quantities = {}
        self._surport_modes = []
        self.mode = None

    def _add_quant(self, quant):
        quant._ins = self.ins
        self.quantities[quant.name] = quant

    def _load_config(self):
        pass

    def surport_modes(self):
        return self._surport_modes

    def getValue(self, name):
        if name in self.quantities:
            return self.performGetValue(self.quantities[name])
        else:
            return None

    def setValue(self, name, value):
        if name in self.quantities:
            self.performSetValue(self.quantities[name], value)

    def performGetValue(self, quant):
        return quant.getValue()

    def performSetValue(self, quant, value):
        quant.setValue(value)
