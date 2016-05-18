# -*- coding: utf-8 -*-
from qulab import Application
from qulab.utils import get_probility


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
