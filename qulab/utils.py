# -*- coding: utf-8 -*-
import os
import re

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
