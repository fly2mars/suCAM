import sys

from os import path
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtGui import(QFont, QIcon, QImage) 
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QMainWindow,  QAction, qApp, QWidget, QToolTip, 
    QPushButton, QApplication, QLabel, QTextEdit, QFileDialog)

import pyqtgraph as pg
import pyqtgraph.console
import numpy as np
import pyqtgraph.metaarray as metaarray
import pyqtgraph.opengl as gl
import stlgenerator


class VView(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initParam()
        self.initUI()
        return
        
        
    def initParam(self):
        ## Init members
        self.m_msg = ''
        self.widget_arr = {}
        return 
    
    def message(self, msg):
        self.m_msg += msg
        self.textEdit.setText(self.m_msg)        
        
    def add_button(self, panel, label, width, height):
        button = QtGui.QPushButton(label)
        button.setFixedWidth(width)
        button.setFixedHeight(height)
        panel.addWidget(button)
        return button
        
    def initUI(self):      

        self.textEdit = QTextEdit()        
        self.textEdit.setDisabled(True)
        self.message("Start from loading a mesh.")

        # Create window layout
        main_window = QtGui.QWidget()
        left_window = QtGui.QWidget()

        self.setCentralWidget(main_window)
        
        layout = QtGui.QGridLayout()
        main_window.setLayout(layout)
        
        # Create left window layout
        layout.addWidget(left_window, 0, 0, 2, 1)
        
        lw_layout = QtGui.QVBoxLayout()
        left_window.setLayout(lw_layout)

        
        self.widget_arr['method_label'] = QtGui.QLabel('Process Selection')        
        self.widget_arr['cb_process'] = QtGui.QComboBox()  
        self.widget_arr['fillpattern_label'] = QtGui.QLabel('Filling Pattern')
        self.widget_arr['cb_fillpattern'] = QtGui.QComboBox()           
        
        self.widget_arr['layer_thickness'] = QtGui.QLabel('Layer Thickness')
        self.widget_arr['layer_thickness_edit'] = QtGui.QLineEdit();
   
        # Add widgets     
        for wt in self.widget_arr.values():            
            lw_layout.addWidget(wt)       
        # Buttons       
        bt_height = 80
        bt_width = 200
        load_button       = self.add_button(lw_layout, "LOAD", bt_width, bt_height)
        autolayout_button = self.add_button(lw_layout, "Auto Layout", bt_width, bt_height)
        slice_button      = self.add_button(lw_layout, "SLICE", bt_width, bt_height)
        fill_button       = self.add_button(lw_layout, "FILL", bt_width, bt_height)
        clear_button      = self.add_button(lw_layout, "CLEAR", bt_width, bt_height)
        quit_button       = self.add_button(lw_layout, "QUIT", bt_width, bt_height)       

        # Act connection        
        quit_button.clicked.connect(QCoreApplication.instance().quit)    
        load_button.clicked.connect(self.openStlDialog)
        slice_button.clicked.connect(self.slice)
        fill_button.clicked.connect(self.analysis)
        clear_button.clicked.connect(self.clear)      

        # Create right window
        self.view = gl.GLViewWidget()
        self.view_slice = gl.GLViewWidget()
        
        self.view.opts['distance'] = 200
        self.view_slice.opts['distance'] = 200
        # https://groups.google.com/forum/#!topic/pyqtgraph/mTlUfT0ozT8
        self.view_slice.sizeHint = self.view.sizeHint = lambda: pg.QtCore.QSize(640, 480)
        self.view.setSizePolicy(self.view_slice.sizePolicy())
        
        xScale = 5
        yScale = 5
        zScale = 5
        gx = gl.GLGridItem()
        gx.scale(xScale, yScale, zScale)
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10*xScale, 0, 10*zScale)
        self.view.addItem(gx)
        gy = gl.GLGridItem()
        gy.scale(xScale, yScale, zScale)
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10*yScale, 10*zScale)
        self.view.addItem(gy)
        gz = gl.GLGridItem()
        gz.scale(xScale, yScale, zScale)
        #gz.translate(0, 0, -10*zScale)
        self.view.addItem(gz)        
        ax = gl.GLAxisItem()
        self.view.addItem(ax)         
        
        
        layout.addWidget(self.view, 0, 1)
        layout.addWidget(self.view_slice, 0, 2)
        layout.addWidget(self.textEdit, 1, 1, 1, 2)
        
        #self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('suCAM')
        #self.setWindowIcon(QIcon('icon.jpg'))
        self.show()


    def openStlDialog(self):

        fname = QFileDialog.getOpenFileName(self, 'Open file', '', 
                                            "Mesh (*.stl);")

        if fname[0]:
            ext_file = path.splitext(fname[0])[1]
            if  ext_file in fname[1]:
                self.initParam()
                self.message("Load " + fname[0])
            else:
                return
            
            sr = stlgenerator.stlreader(path)
            
        verts = np.array([
            [0, 0, 0],
            [2, 0, 0],
            [1, 2, 0],
            [1, 1, 1],
        ])*50
        faces = np.array([
            [0, 1, 2],
            [0, 1, 3],
            [0, 2, 3],
            [1, 2, 3]
        ])
        colors = np.array([
            [1, 0, 0, 0.3],
            [0, 1, 0, 0.3],
            [0, 0, 1, 0.3],
            [1, 1, 0, 0.3]
        ])
                       
        m1 = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=colors, smooth=False)
        m1.translate(5, 5, 0)
        m1.setGLOptions('additive')
        self.view.addItem(m1)                
                
    def slice(self):
        ## create volume data set for mesh and slice images from
        shape = (100,100,70)
        data = pg.gaussianFilter(np.random.normal(size=shape), (4,4,4))
        data += pg.gaussianFilter(np.random.normal(size=shape), (15,15,15))*15    
        ## slice out three planes, convert to RGBA for OpenGL texture
        levels = (-0.08, 0.08)
        tex1 = pg.makeRGBA(data[shape[0]//2], levels=levels)[0]       # yz plane
        tex2 = pg.makeRGBA(data[:,shape[1]//2], levels=levels)[0]     # xz plane
        tex3 = pg.makeRGBA(data[:,:,shape[2]//2], levels=levels)[0]   # xy plane    
        ## Create three image items from textures, add to view
        v1 = gl.GLImageItem(tex1)
        v1.translate(-shape[1]/2, -shape[2]/2, 0)
        #v1.rotate(90, 0,0,1)
        #v1.rotate(-90, 0,1,0)
        
        self.view_slice.addItem(v1)     
        
        return
    
    
    def analysis(self):
        n = 51
        y = np.linspace(-10,10,n)
        x = np.linspace(-10,10,100)
        for i in range(n):
            yi = np.array([y[i]]*100)
            d = (x**2 + yi**2)**0.5
            z = 10 * np.cos(d) / (d+1)
            pts = np.vstack([x,yi,z]).transpose()
            plt = gl.GLLinePlotItem(pos=pts, color=pg.glColor((i,n*1.3)), width=(i+1)/10., antialias=True)
            self.view_slice.addItem(plt)        
        return
    
    def clear(self):
        
        return
        

        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = VView()
 
    
    #plot.sizeHint = view.sizeHint = lambda: pg.QtCore.QSize(600, 400)
    #view.setSizePolicy(plot.sizePolicy())
     
    sys.exit(app.exec_())
