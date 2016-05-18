import re
import os
import datetime
import zipfile
import StringIO
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("data")
logger.setLevel(logging.DEBUG)


_filetypes = {
    'text' : re.compile(r'^(.+)(\.txt|\.dat|\.gz)$'),
    'gzip' : re.compile(r'^(.+)(\.gz)$'),
    'hdf5' : re.compile(r'^(.+)(\.h5|\.hdf5)$')
}

def __get_file_info_by_filename(fname):
    '''分离 fname 中的目录、文件名及扩展名，并根据扩展名判断文件类型。'''
    fileInfo = None
    for filetype in _filetypes:
        m = _filetypes[filetype].search(fname)
        if m is not None:
            fileInfo = dict(
                path = os.path.dirname(m.group(1)),
                basename = os.path.basename(m.group(1)),
                ext = m.group(2),
                type = filetype
            )
            break
    return fileInfo

class Index(object):
    def __init__(self, name, unit=""):
        self.name = name
        self.unit = unit
        self.data = None

    def values(self):
        return np.array(self.data[self.name])

class Column(object):
    def __init__(self, name, unit="", with_err=False, *kw):
        super(Column, self).__init__(*kw)
        self.name     = name
        self.unit     = unit
        self.with_err = with_err
        self.data     = None
        if self.with_err:
            self.err_name = "Error of " + self.name
        else:
            self.err_name = ""

    def values(self):
        return np.array(self.data[self.name])

    def errors(self):
        return np.array(self.data[self.err_name])

class MetaData():
    def __init__(self, data):
        self.data = data
        self.index = []
        self.cols = []

    def as_header(self):
        return ''

class Record():
    def __init__(self):
        self.shape = None
        self.fname = None
        self.fileInfo = None

        self.df = None
        self.meta_data = None

        self.index = []
        self.cols = []

        self._index_dict = None
        self._cols_dict = None

    def __getitem__(self, col_name):
        if self._index_dict is None:
            self._index_dict = dict(self.index)
        if self._cols_dict is None:
            self._cols_dict = dict(self.cols)

        if col_name in self._index_dict.keys():
            return np.array(self.df.index.get_level_values(col_name))
        else:
            for c in self._cols_dict.keys():
                if c.name == col_name:
                    if c.with_err:
                        return np.array(self.df[col_name]), np.array(self.df[c.err_name])
                    else:
                        return np.array(self.df[col_name])
                elif c.err_name == col_name:
                    return np.array(self.df[col_name])
                else:
                    pass
        return None

    def header(self):
        pass

    def savetxt(self, fname):
        if isinstance(fname, str):
            path = os.path.dirname(fname)
            if path != '' and not os.path.exists(path):
                os.makedirs(path)
        np.savetxt(fname, self.asarray(), header=self.header(), comments='#')

    def loadtxt(self, fname):
        pass

    def savehdf5(self, fname):
        pass

    def loadhdf5(self, fname):
        pass

    def save(self, fname = None):
        '''
        保存记录到文件名 fname, 默认为 self.fname，若为 None 则直接返回
        该方法会根据文件名的后缀自动判断文件类型，并调用相应的方法来保存文件。
        '''
        if fname is None:
            if self.fname is not None:
                fname = self.fname
            else:
                return
        fileInfo = __get_file_info_by_filename(fname)
        if fileInfo is None or filetypes['type'] in ['text', 'gzip']:
            self.savetxt(fname)
        elif fileInfo['type'] == 'hdf5':
            self.savehdf5(fname)

    def load(self, fname):
        '''
        从 fname 载入记录
        该方法会根据文件名的后缀自动判断文件类型，并调用相应的方法来读取文件。
        '''
        fileInfo = __get_file_info_by_filename(fname)
        if fileInfo is None or filetypes['type'] in ['text', 'gzip']:
            self.loadtxt(fname)
        elif fileInfo['type'] == 'hdf5':
            self.loadhdf5(fname)

    def tar(self, zipfname, name):
        '''
        将记录归档到 zip 文件中

        zipfname : zip 文件名
        name : zip 文件中的路径
        '''
        if not os.path.exists(zipfname) or zipfile.is_zipfile(zipfname):
            if isinstance(zipfname, str):
                path = os.path.dirname(zipfname)
                if path != '' and not os.path.exists(path):
                    os.makedirs(path)
            with zipfile.ZipFile(zipfname, "a") as tar:
                tmp = StringIO.StringIO()
                self.savetxt(tmp)
                tmp.seek(0)
                try:
                    tar.writestr(name, tmp.read(), compress_type=zipfile.ZIP_DEFLATED)
                except:
                    logger.exception("failed to write '%s' tozip file '%s'." % (name, zipfname))
                    raise
                tmp.close()
        else:
            pass

class Template():
    def __init__(self):
        pass

    def makeRecord(self):
        record = Record()
        return record

from PyQt4 import QtCore

class Data(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self, manager):
        super(Data, self).__init__()
        self.manager = manager
        self.df = None
        self.is_auto_save = False
        self.is_saved = True
        self.fname = None
        self.paramenters = []
        self.time       = datetime.datetime.now()
        self.start_time = datetime.datetime.now()
        self.end_time   = datetime.datetime.now()
        self.updated.connect(self.setFinishedTime)

    @QtCore.pyqtSlot()
    def timeIt(self):
        self.time = datetime.datetime.now()

    def setStartTime(self):
        self.start_time = datetime.datetime.now()

    @QtCore.pyqtSlot()
    def setFinishedTime(self):
        self.end_time = datetime.datetime.now()

    def __getitem__(self, col_name):
        if col_name in self.index_names:
            return np.array(self.df.index.get_level_values(col_name))
        else:
            for c in self._cols:
                if c.name == col_name:
                    if c.with_err:
                        return np.array(self.df[col_name]), np.array(self.df[c.err_name])
                    else:
                        return np.array(self.df[col_name])
                elif c.err_name == col_name:
                    return np.array(self.df[col_name])
                else:
                    pass
        return None

    def __setitem__(self, key, value):
        pass

    def reset_values(self, values):
        self.is_saved = False
        self.setStartTime()
        self.timeIt()
        path, fname = self.manager.gen_fname(self)
        if path == '':
            self.fname = fname
        else:
            self.fname = path + '/' + fname
        self.df = pd.DataFrame(values)
        self.updated.emit()

    def set_values(self, index, values):
        self.is_saved = False
        if self.index_names is []:
            df = pd.DataFrame(values,
                              columns = self.column_names)
        else:
            mult_index = pd.MultiIndex.from_tuples(index,
                                              names = self.index_names)
            df = pd.DataFrame(values,
                              index = mult_index,
                              columns = self.column_names)
        if self.df is None:
            self.df = df
        else:
            self.df = self.df.append(df)

        self.updated.emit()

    def append(self, **values):
        self.is_saved = False
        index = self.get_current_index()
        v = {}
        for key in values.keys():
            if isinstance(values[key], tuple):
                v[key] = values[key][0]
                v['Error of '+key] = values[key][1]
            else:
                v[key] = values[key]
        self.set_values([index], [v])

    def extend(self, **values):
        self.is_saved = False
        index = self.get_current_index()
        n = len(values.items()[0][1])
        v = [dict() for i in range(n)]

        for key in values.keys():
            if isinstance(values[key], tuple):
                for i in range(n):
                    v[i][key] = values[key][0][i]
                    v[i]['Error of '+key] = values[key][1][i]
            else:
                for i in range(n):
                    v[i][key] = values[key][i]
        self.set_values([index]*n, v)

    def get_current_index(self):
        return self.manager.get_current_index(self)

    def get_current_paramenters(self):
        return self.manager.get_current_paramenters(self)

    def from_txt(self, fname):
        data = np.loadtxt(fname)
        i = 0
        idx = []
        values = {}
        while len(self.index_names) > i:
            idx.append(data[:,i])
            i += 1
        index = zip(*idx)
        while i < data.shape[1]:
            values[self.column_names[i-len(self.index_names)]] = data[:,i]
            i += 1

        self.set_values(index, values)

    def save(self, fname=None):
        if fname is not None:
            self.savetxt(fname)
        elif self.fname is not None:
            self.savetxt(self.fname)
        else:
            pass
        self.is_saved = True

    def savehd5(self, hdf, path):
        self.df.to_hdf(hdf, path)
        self.is_saved = True

    def asarray(self):
        values = np.array(self.df)
        rows, cols = values.shape
        #cols += len(self.index_names)
        #dtypes=[]
        #for i in range(len(self.index_names)):
        #    self.df.index.levels[i].dtype.type
        #    dtypes.append((self.index_names[i], np.float64))
        #for c in self.column_names:
        #    dtypes.append((c, self.df.dtypes[c].type))
        #data = np.array(np.zeros((rows, cols)), dtype=np.dtype(dtypes))
        data = []
        for i in range(len(self.index_names)):
            data.append(np.array([x for x in self.df.index.get_level_values(i)]))
        for i in range(cols):
            data.append(values[:,i])
        return np.array(data).T

    def savetxt(self, fname=None):
        if fname == None:
            return
        if isinstance(fname, str):
            path = os.path.dirname(fname)
            if path != '' and not os.path.exists(path):
                os.makedirs(path)
        np.savetxt(fname, self.asarray(),
                   header=self.make_header(), fmt='%20.12e', comments="#")
        self.is_saved = True

    def make_header(self):
        title_line = "{datatype} --- generated by {program} {version} <{time}>".format(
            datatype = self.__class__.__name__,
            program  = self.manager.program(),
            version  = self.manager.version(),
            time     = self.time
        )

        split_line = "#" * 76
        table_head = self._table_head()

        info = ""
        info += "\n        User : %s" % self.manager.app.user()
        info += "\n        Sample ID : %s" % self.manager.app.sampleID()

        paramenters = "Paramenters:"
        for k, v, u in self.paramenters:
            paramenters += "\n        %s (%s) : %s" % (k, u, v)

        settings = "Settings:\n" + self.manager.app.get_settings()

        times = """Times:
        Start  : %s
        Finish : %s
        """ % (self.start_time, self.end_time)

        return '\n'.join([title_line,
                          info,
                          '',
                          'Notes: ',
                          self.manager.app.notes(),
                          '',
                          'Introduction:',
                          self.doc,
                          split_line,
                          paramenters,
                          '',
                          settings,
                          '',
                          split_line,
                          times,
                          table_head,
                          ''])

    def _table_head(self):
        top_line        = ""
        table_head_line = ""
        table_unit_line = ""
        botton_line     = ""
        for col in self._index:
            top_line    += "------------------------+-"
            botton_line += "------------------------+-"
            table_head_line += "%23s | " % col.name
            if col.unit != '':
                table_unit_line += "%23s | " % ('('+col.unit+')')
            else:
                table_unit_line += "                        | "

        for col in self._cols:
            top_line    += "------------------------+-"
            botton_line += "------------------------+-"
            table_head_line += "%23s | " % col.name
            if col.unit != '':
                table_unit_line += "%23s | " % ('('+col.unit+')')
            else:
                table_unit_line += "                        | "
            if col.with_err:
                top_line    += "------------------------+-"
                botton_line += "------------------------+-"
                table_head_line += "%23s | " % col.err_name
                if col.unit != '':
                    table_unit_line += "%23s | " % ('('+col.unit+')')
                else:
                    table_unit_line += "                        | "

        return "\n".join([top_line,
                          table_head_line,
                          table_unit_line,
                          botton_line])

    def tar(self, zipfname, name):
        if not os.path.exists(zipfname) or zipfile.is_zipfile(zipfname):
            if isinstance(zipfname, str):
                path = os.path.dirname(zipfname)
                if path != '' and not os.path.exists(path):
                    os.makedirs(path)
            with zipfile.ZipFile(zipfname, "a") as tar:
                tmp = StringIO.StringIO()
                self.savetxt(tmp)
                tmp.seek(0)
                try:
                    tar.writestr(name, tmp.read(), compress_type=zipfile.ZIP_DEFLATED)
                except:
                    logger.exception("failed writing zip file.")
                    raise
                tmp.close()
        else:
            pass
        self.is_saved = True


def datatype_factory(name,
                     index=None,
                     cols=None,
                     doc = ''):
    index = [] if index == None else index
    cols  = [] if cols  == None else cols
    index_names = []
    column_names= []

    dic = {'_index': index, '_cols': cols, 'doc': doc}

    for i in index:
        index_names.append(i.name)
    for c in cols:
        column_names.append(c.name)
        if c.with_err:
            column_names.append(c.err_name)

    dic['index_names']  = index_names
    dic['column_names'] = column_names

    return type(name, (Data, QtCore.QObject), dic)
