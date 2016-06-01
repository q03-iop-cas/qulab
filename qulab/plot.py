# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 11:44:19 2016

@author: feihoo87
"""
from qulab.base import Manager
from PyQt4 import QtCore
import matplotlib.pyplot as plt


class PlotDataGetter(QtCore.QObject):
    def __init__(self, fig):
        super(PlotDataGetter, self).__init__()
        self.fig = fig
        
    @QtCore.pyqtSlot()
    def get_plot_data(self):
        self.fig._get_plot_data()
        
        
class Figure(QtCore.QObject):
    __title__ = "Figure"
    
    refresh_time = 0.05
    need_data = QtCore.pyqtSignal()
    windowHided = QtCore.pyqtSignal()
    windowShowed = QtCore.pyqtSignal()
    
    def __init__(self):
        super(Figure, self).__init__()
        self.fig    = plt.figure(self.__title__)
        self.canvas = self.fig.canvas
        self.window = self.canvas.window()
        self.app    = None
        self.inited = False
        self.get_data_busy = False
        self.last_data = ()
        self.last_repaint_time = time.time()
        self.t = QtCore.QThread()
        self.getter = PlotDataGetter(self)
        self.need_data.connect(self.getter.get_plot_data)
        self.getter.moveToThread(self.t)
        self.t.start()
           
    def isHidden(self):
        return self.window.isHidden()
    
    def hide(self):
        self.window.hide()
        self.windowHided.emit()
        
    def show(self):
        self._repaint()
        self.window.show()
        self.windowShowed.emit()
        
    def savefig(self, fname, *kw):
        self.fig.savefig(fname, *kw)
        
    @QtCore.pyqtSlot(bool)
    def repaint(self, flag=True):
        if not flag:
            return
        if self.isHidden():
            return
        self._repaint()
            
    def _repaint(self):
        if self.inited:
            self.set_data()
        else:
            self._plot()
        self.fig.canvas.draw()
        
    def _plot(self):
        self.plot()
        self.window.show()
        self.inited = True
        
    def plot(self):
        pass
    
    def set_data(self):
        pass
    
    def _get_plot_data(self):
        if self.get_data_busy and self.last_data is not ():
            return
        else:
            self.get_data_busy = True
            #for d in self.last_data:
            #    del d
            self.last_data = self.get_plot_data()
            self.get_data_busy = False
            
    def get_plot_data(self):
        pass
    
    def get_latest_data(self):
        if self.get_data_busy and self.last_data is not ():
            #self.need_data.emit()
            return self.last_data
        elif self.last_data is ():
            self.last_data = self.get_plot_data()
            return self.last_data
        else:
            self.need_data.emit()
            return self.last_data
    
class ListPlot(Figure):
    __title__ = ""
    
    def plot(self):
        x, y = self.get_latest_data()
        
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(x, y, '.r', alpha=0.2)
        #self.linef, = self.ax.plot(x, y, '.b')
        self.ax.set_title(self.__title__)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
    
    def set_data(self):
        x, y = self.get_latest_data()
        
        self.line.set_data(x, y)
        lim = max(np.abs(x).max(),np.abs(y).max()) * 1.1
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)
        
    def get_plot_data(self):
        x, y = self.get_data[0]()
        
        return x, y
        
def listplot(title, xlabel, ylabel, get_data):
    dct = dict(
        __title__ = title,
        xlabel = xlabel,
        ylabel = ylabel,
        get_data=(get_data,))
    cls = type('ListPlotPlot', (ListPlot, Figure, QtCore.QObject), dct)
    
    return cls
    
class Curve(Figure):
    __title__ = "Curve"
        
    def plot(self):
        x, y = self.get_data[0]()
        
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(x,y,'-o')
        self.ax.set_title(self.__title__)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
    
    def set_data(self):
        x, y = self.get_data[0]()
        
        self.line.set_data(x, y)
        self.ax.set_xlim(x.min(), x.max())
        self.ax.set_ylim(y.min(), y.max())
        
        
def curve(title, xlabel, ylabel, get_data):
    dct = dict(
        __title__ = title,
        xlabel = xlabel,
        ylabel = ylabel,
        get_data=(get_data,))
    cls = type('CurvePlot', (Curve, Figure, QtCore.QObject), dct)
    
    return cls 

class MultiCurve(Figure):
    __title__ = "Curves"
        
    def plot(self):
        x, ys = self.get_data[0]()
        
        self.ax = self.fig.add_subplot(111)
        
        for i in range(len(ys)):
            line, = self.ax.plot(x,ys[i],'-o')
            self.lines.append(line)
        if self.labels is not None:
            for i in range(len(ys)):
                self.lines[i].set_label(self.labels[i])
                
        self.ax.set_title(self.__title__)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        
        self.ax.legend(prop={'size':16})
    
    def set_data(self):
        x, ys = self.get_data[0]()
        
        for i in range(len(ys)):
            self.lines[i].set_data(x, ys[i])
        self.ax.set_xlim(x.min(), x.max())
        
        ys = np.array(ys)
        self.ax.set_ylim(ys.min(), ys.max())
        
        
def curves(title, xlabel, ylabel, get_data, labels=None):
    dct = dict(
        __title__ = title,
        xlabel = xlabel,
        ylabel = ylabel,
        labels = labels,
        lines = [],
        get_data=(get_data,))
    cls = type('MultiCurvePlot', (MultiCurve, Figure, QtCore.QObject), dct)
    
    return cls
    
import numpy as np
from scipy.interpolate import griddata

class Image(Figure):
    __title__ = "Image"
    
    def plot(self):
        x, y, z = self.get_latest_data()
        #self.last_data = (x, y, z)
        
        self.ax = self.fig.add_subplot(111)
        self.img = self.ax.imshow(z, extent=(x.min(),x.max(),y.min(),y.max()), origin='lower', aspect='auto', cmap=self.cmap)
        self.img.set_interpolation('nearest')
        self.cbar = self.fig.colorbar(self.img, ax=self.ax)
        self.ax.set_title(self.__title__)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        
        if self.zlabel != '':
            self.cbar.set_label(self.zlabel)
    
    def set_data(self):
        x, y, z = self.get_latest_data()
        
        self.img.set_data(z)
        vmin = z.min()
        vmax = z.max()
        if vmin >= vmax:
            vmax = vmin + 0.01
        self.img.set_clim(vmin, vmax)
        self.img.set_extent((x.min(), x.max(), y.min(), y.max()))
        self.cbar.update_bruteforce(self.img)
        
    def get_plot_data(self):
        x, y, z = self.get_data[0]()
        
        if x.min() == x.max():
            xx = np.array([x.min()-0.1, x.min(), x.min()+0.1])
        else:
            xx = np.linspace(x.min(), x.max(), 501)
        if y.min() == y.max():
            yy = np.array([y.min()-0.1, y.min(), y.min()+0.1])
        else:
            yy = np.linspace(y.min(), y.max(), 501)
        
        grid_x, grid_y = np.meshgrid(xx, yy)
        grid_z = griddata(np.array([x,y]).T, z, (grid_x,grid_y), method='nearest')
        
        return xx, yy, grid_z


def image(title, xlabel, ylabel, get_data, zlabel = '', cmap='jet'):
    dct = dict(
        __title__ = title,
        xlabel = xlabel,
        ylabel = ylabel,
        zlabel = zlabel,
        get_data=(get_data,),
        cmap = cmap)
    cls = type('ImagePlot', (Image, Figure, QtCore.QObject), dct)
    cls.refresh_time = 10
    
    return cls 
    

import time

class PlotManager(Manager):
    repaint = QtCore.pyqtSignal(bool)
    
    def __init__(self, app):
        super(PlotManager, self).__init__(app)
        self.Figures = []
        self.figures = []
        #self._threads = []
        
    def add_item(self, Fig, datas=None):
        datas = [] if datas is None else datas
        self.Figures.append((Fig, datas))
        
    def init(self):
        self.app.data_manager.data_updated.connect(self.on_data_updated)
        for fig, datas in self.figures:
            del fig
            del datas
        self.figures = []
        for Fig, datas in self.Figures:
            fig = Fig()
            fig.app = self.app
            #t = QtCore.QThread()
            #fig.moveToThread(t)
            #self._threads.append(t)
            self.figures.append((fig, datas))
            #self.repaint.connect(fig.repaint)
            pass
            
    def show_all(self):
        #return
        for fig, _ in self.figures:
            try:
                fig.show()
            except:
                pass
            
    def hide_all(self):
        for fig, _ in self.figures:
            fig.hide()
            
    def save_figs(self):
        pass
    
    @QtCore.pyqtSlot(str)
    def on_data_updated(self, data):
        for fig, datas in self.figures:
            if data in datas:
                if fig.isHidden():
                    pass
                else:
                    t = time.time()
                    if t-fig.last_repaint_time > fig.refresh_time:
                        fig.last_repaint_time = t
                        fig.repaint(data in datas)
                    else:
                        pass

