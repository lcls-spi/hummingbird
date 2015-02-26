from interface.Qt import QtGui, QtCore
from interface.ui import Ui_plotWindow
import pyqtgraph
import numpy
import os

class PlotWindow(QtGui.QMainWindow, Ui_plotWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self,parent)
        self.setupUi(self)
        self.plot = pyqtgraph.PlotWidget(self.plotFrame)
        self.plot.hideAxis('bottom')
        layout = QtGui.QVBoxLayout(self.plotFrame)
        layout.addWidget(self.plot)
        icon_path = os.path.dirname(os.path.realpath(__file__)) + "/../images/logo_48_transparent.png"
        icon = QtGui.QPixmap(icon_path); 
        self.logoLabel.setPixmap(icon)
        self.menuData_Sources.aboutToShow.connect(self.onMenuShow)
        self._enabled_sources = []
    def onMenuShow(self):
        # Go through all the available data sources and add them
        self.menuData_Sources.clear()
        for ds in self.parent()._data_sources:
            menu =  self.menuData_Sources.addMenu(ds.name())
            for key in ds.keys:
                action = QtGui.QAction(key, self)
                action.setData([ds,key])
                action.setCheckable(True)
                if((ds.uuid+key) in self._enabled_sources):
                    action.setChecked(True)
                else:
                    action.setChecked(False)
                menu.addAction(action)
                action.triggered.connect(self._source_key_triggered)

    def _source_key_triggered(self):
        action = self.sender()
        source,key = action.data()
        if(action.isChecked()):
            source.subscribe(key)
            self._enabled_sources.append(source.uuid+key)
        else:
            source.unsubscribe(key)
            self._enabled_sources.remove(source.uuid+key)

    def replot(self):
        self.plot.clear()
        for key in self._enabled_sources:
            # There might be no data yet, so no plotdata
            if(key in self.parent()._plotdata):
                pd = self.parent()._plotdata[key]
                if(pd._x is not None):
                    self.plot.plot(x=numpy.array(pd._x, copy=False),
                                   y=numpy.array(pd._y, copy=False), clear=False)
                else:
                    self.plot.plot(numpy.array(pd._y, copy=False), clear=False)
        