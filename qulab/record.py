import re
import os

_filetypes = {
    'text' : re.compile(r'^(.+)(\.txt|\.dat|\.gz)$'),
    'hdf5' : re.compile(r'^(.+)(\.h5|\.hdf5)$')
}

def __get_file_info_by_filename(fname):
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

class Record():
    def __init__(self):
        self.shape = None
        self.fname = None
        self.fileInfo = None

        self.data = None
        pass

    def savetxt(self, fname):
        pass

    def loadtxt(self, fname):
        pass

    def savehdf5(self, fname):
        pass

    def loadhdf5(self, fname):
        pass

    def save(self, fname = None):
        if fname is None:
            if self.fname is not None:
                fname = self.fname
            else:
                return
        fileInfo = __get_file_info_by_filename(fname)
        if fileInfo is None or filetypes['type'] == 'text':
            self.savetxt(fname)
        elif fileInfo['type'] == 'hdf5':
            self.savehdf5(fname)

    def load(self, fname):
        fileInfo = __get_file_info_by_filename(fname)
        if fileInfo is None or filetypes['type'] == 'text':
            self.loadtxt(fname)
        elif fileInfo['type'] == 'hdf5':
            self.loadhdf5(fname)

class Template():
    def __init__(self):
        pass

    def makeRecord(self):
        record = Record()
        return record
