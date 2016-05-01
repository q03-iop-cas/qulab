# -*- coding: utf-8 -*-
__author__ = 'feihoo87'

import os, ConfigParser

class Config(object):

    def __init__(self, fname="", tag="main"):
        super(Config, self).__init__()
        self.fname = fname
        self.tag = tag
        self.cfg = ConfigParser.SafeConfigParser()
        self.cfg.read(self.fname)

    def _get_section_option(self, key):
        klist = key.split(":")
        if len(klist) == 1:
            section = "Basic"
            option = key
        else:
            section, option = klist[0], '_'.join(klist[1:])
        return section, option

    def has_key(self, key):
        section, option = self._get_section_option(key)
        if self.cfg.has_section(section) and self.cfg.has_option(section, option):
            return True
        else:
            return False

    def get(self, key, default=""):
        if self.has_key(key):
            section, option = self._get_section_option(key)
            s = self.cfg.get(section, option)
            try:
                return eval(s)
            except:
                return s
        else:
            return default

    def set(self, key, value):
        section, option = self._get_section_option(key)
        if not self.cfg.has_section(section):
            self.cfg.add_section(section)
        self.cfg.set(section, option, value.__repr__())
        self.save(self.fname)

    def set_default(self, key, value):
        if not self.has_key(key):
            self.set(key, value)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def save(self, fname):
        with open(fname, 'wb') as configfile:
            self.cfg.write(configfile)

    def __str__(self):
        return "Config : %s" % self.fname

    def __repr__(self):
        return "Config(%s, %s)" % (self.fname, self.tag)

    def _sec_to_dict(self, section):
        ret = {}
        opts = self.cfg.options(section)
        for opt in opts:
            ret[opt] = self.cfg.get(section, opt)
        return ret

    def as_dict(self):
        ret = {}
        for section in self.cfg.sections():
            ret[section] = self._sec_to_dict(section)
        return ret


class History(Config):        
    def get(self, key, defalut=None):
        s = super(History, self).get(key)
        if s == "":
            self.set(key, defalut)
            return defalut
        else:
            return s


history = History('history.ini')
main_config = Config('main.ini')

if main_config["Basic:path"] == "":
    main_config["Basic:path"] = "."

__configs = {
    'main'    : main_config,
    'history' : history
}


def config(key='main'):
    if key in __configs.keys():
        return __configs[key]
    else:
        fname = os.path.join(main_config["Basic:path"], key+'.ini')
        main_config.set(("Configs:%s" % key), fname)
        __configs[key] = Config(fname, key)
        return __configs[key]

