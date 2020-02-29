# -*- coding: utf-8 -*-
import sys
import os
import cv2
import json

from os import path
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtGui import(QFont, QIcon, QImage) 
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout,QGridLayout, QMainWindow,  QAction, qApp, QWidget, QToolTip, 
    QPushButton, QApplication, QLabel, QTextEdit, QFileDialog, QSlider)


import pyqtgraph as pg
import pyqtgraph.console
import numpy as np
from stl import mesh

import pyqtgraph.metaarray as metaarray
import pyqtgraph.opengl as gl
import stl2pngfunc
import modelInfo
import pathengine
import mkspiral

#############################################
#Config management
#############################################
class Config(object):
    def __init__(self, config_file=""):
        self.data = {}
        if config_file == "":
            config_file = os.path.dirname(os.path.realpath(__file__)) + '\\configs\\' + 'config.json'            
        self.data['config_file'] = config_file
        self.load()
        
    def add(self, key, value):
        self.data[key] = value
    
    def get(self, key):
        r = self.data.get(key)
        if r == None:
            r = 0
        return r
        
    def save(self, config_file=""):
        if config_file == "":
            try:
                with open(self.data['config_file'], 'w') as fout:
                    json.dump(self.data, fout)                   
            except Exception as e:
                print("{} in Config.save.")
        return
    
    def load(self, config_file=""):
        if config_file == "":
            try:
                with open(self.data['config_file'], 'r') as fin:
                    self.data = json.load(fin)
            except Exception as e:
                print("{} in Config.save.")
        return self.data
                
                
            
class VView(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.conf = Config()
        self.initParam()
        self.initUI()
        return
        
        
    def initParam(self):
        ## Init members
        self.m_msg = ''
        self.m_last_msg = ''
        self.model_path = ''               
        self.vert = np.zeros(1)
        self.face = np.zeros(1)
        self.color = np.zeros(1)
        self.mesh = []
        self.mesh_info = modelInfo.ModelInfo()
       
        self.slices = {}
        self.out_path = ""
        
        self.is_fill_path = False 
        self.path_verts = []
        
        return 
    def quit(self):
        self.conf.save()
        QCoreApplication.instance().quit()
        return
    def message(self, msg, showLastMsg = True):
        self.m_last_msg = self.m_msg
        self.m_msg = msg
        show_msg = ""
        if(showLastMsg):
            show_msg = msg + "\n" + self.m_last_msg
        else:
            show_msg = msg
        
        self.view_status.setText(show_msg)
        self.repaint()
        
    def add_button(self, panel, label, width, height):
        button = QtGui.QPushButton(label)
        #button.setFixedWidth(width)        
        #button.setFixedHeight(height)
        panel.addWidget(button)
        return button
        
    def update_variable_first_layer_thickness(self):
        try:
            new_value = self.widget_arr['first_layer_thickness_edit'].text()
            self.mesh_info.first_layer_thickness = float(new_value)
            self.conf.data['first_layer_thickness'] = float(new_value)
        except ValueError:
            return
        return 
    def update_variable_layer_thickness(self):
        try:
            new_value = self.widget_arr['layer_thickness_edit'].text()
            self.mesh_info.layer_thickness = float(new_value)
            self.conf.data['layer_thickness'] = float(new_value)
        except ValueError:
            return
        return
    def update_variable_infill_offset(self):
        try:
            new_value = self.widget_arr['infill_offset_edit'].text()
            self.conf.data['infill_offset'] = float(new_value)  
        except Exception as e:
            return 
        return 
    def update_var(self):
        self.update_variable_infill_offset()
        self.update_variable_layer_thickness()
        self.update_variable_first_layer_thickness()
        
        
    def update_ui(self):
        self.widget_arr['first_layer_thickness_edit'].setText(str(self.conf.get('first_layer_thickness')))
        self.widget_arr['layer_thickness_edit'].setText      (str(self.conf.get('layer_thickness')))
        self.widget_arr['infill_offset_edit'].setText      (str(self.conf.get('infill_offset')))
        self.update()
       
    def initUI(self):      
        
        self.widget_arr = {} 
        self.view_status = QTextEdit()        
        #self.view_status.setDisabled(True)
        self.message(self.mesh_info.get_info())
        self.message("Start from loading a mesh.")

        # Create window layout
        main_window = QtGui.QWidget()
        left_window = QtGui.QWidget()

        self.setCentralWidget(main_window)
        
        layout = QtGui.QGridLayout()
        main_window.setLayout(layout)
        
        # Create left window layout
        layout.addWidget(left_window, 0, 0, 4, 1)
        
        lw_layout = QtGui.QVBoxLayout()
        left_window.setLayout(lw_layout)

        
        self.widget_arr['method_label'] = QtGui.QLabel('Process Selection')        
        self.widget_arr['cb_process'] = QtGui.QComboBox()  
        self.widget_arr['fillpattern_label'] = QtGui.QLabel('Filling Pattern')
        self.widget_arr['cb_fillpattern'] = QtGui.QComboBox()           
        
        self.widget_arr['first_layer_thickness'] = QtGui.QLabel('First Layer Thickness')
        self.widget_arr['first_layer_thickness_edit'] = QtGui.QLineEdit();
        self.widget_arr['first_layer_thickness_edit'].textChanged.connect(self.update_variable_first_layer_thickness)
       
        self.widget_arr['layer_thickness'] = QtGui.QLabel('Layer Thickness')
        self.widget_arr['layer_thickness_edit'] = QtGui.QLineEdit();
        self.widget_arr['layer_thickness_edit'].textChanged.connect(self.update_variable_layer_thickness)
        
        self.widget_arr['infill_offset'] = QtGui.QLabel('infill_offset')
        self.widget_arr['infill_offset_edit'] = QtGui.QLineEdit();
        self.widget_arr['infill_offset_edit'].textChanged.connect(self.update_variable_infill_offset)        
        
   
        # Add widgets     
        for wt in self.widget_arr.values():            
            lw_layout.addWidget(wt)       
        # Buttons       
        bt_height = 75
        bt_width = 200
        load_button       = self.add_button(lw_layout, "LOAD", bt_width, bt_height)
        autolayout_button = self.add_button(lw_layout, "Auto Layout", bt_width, bt_height)
        slice_button      = self.add_button(lw_layout, "SLICE", bt_width, bt_height)
        fill_button       = self.add_button(lw_layout, "FILL", bt_width, bt_height)
        connectp_button   = self.add_button(lw_layout, "Connect Printer...", bt_width, bt_height)
        print_seq_button  = self.add_button(lw_layout, "Print Sequence", bt_width, bt_height)
        print_path_button = self.add_button(lw_layout, "Gen Path", bt_width, bt_height)
        gcode_button      = self.add_button(lw_layout, "Gen GCode", bt_width, bt_height)        
        printto_button    = self.add_button(lw_layout, "Print...", bt_width, bt_height)
        clear_button      = self.add_button(lw_layout, "CLEAR", bt_width, bt_height)
        quit_button       = self.add_button(lw_layout, "QUIT", bt_width, bt_height)       

        # Act connection        
        quit_button.clicked.connect(self.quit)    
        load_button.clicked.connect(self.openStlDialog)
        slice_button.clicked.connect(self.slice)
        print_seq_button.clicked.connect(self.print_sequence)
        fill_button.clicked.connect(self.fill)
        print_path_button.clicked.connect(self.gen_path)
        gcode_button.clicked.connect(self.gen_gcode)
        clear_button.clicked.connect(self.clear)      

        # Create right window
        self.view = gl.GLViewWidget()
        self.view_slice = gl.GLViewWidget()
        
        self.view.opts['distance'] = 200
        self.view_slice.opts['distance'] = 200
        # https://groups.google.com/forum/#!topic/pyqtgraph/mTlUfT0ozT8
        self.view_slice.sizeHint = self.view.sizeHint = lambda: pg.QtCore.QSize(640, 480)
        self.view.setSizePolicy(self.view_slice.sizePolicy())
        
        self.add_3d_printing_region()        
        
        # Add slider
        self.sl = QtGui.QSlider(Qt.Horizontal)
        self.sl.setMinimum(0)
        self.sl.setMaximum(1)  
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1)        
        
        
        layout.addWidget(self.view, 0, 1)
        layout.addWidget(self.view_slice, 0, 2)
        layout.addWidget(self.sl, 1,1,1,2)
        layout.addWidget(self.view_status, 2, 1, 2, 2)
        
        
        #self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('suCAM-6D')
        #self.setWindowIcon(QIcon('icon.jpg'))
        self.show()
        self.update_ui()

    def add_3d_printing_region(self):
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
        
    def openStlDialog(self):

        fname = QFileDialog.getOpenFileName(self, 'Open file', '', 
                                            "Mesh (*.stl);")

        if fname[0]:
            ext_file = path.splitext(fname[0])[1]
            if  ext_file.lower() in fname[1]:
                self.initParam()
                self.message("Load " + fname[0])
                self.model_path = fname[0]
            else:
                return
            
            #self.mesh = mesh.Mesh.from_file(fname[0])
            #self.mesh_info = modelInfo.ModelInfo(self.mesh)
            #self.mesh_info.path = fname[0]
            self.mesh = self.mesh_info.load(fname[0])
            self.message(self.mesh_info.get_info())
            verts = self.mesh.vectors.reshape(self.mesh.vectors.shape[0]*3,3)
            n_face = self.mesh.vectors.shape[0]
            faces = np.arange(n_face*3)
            faces = faces.reshape(n_face, 3)
            colors = [1,0,0,0.3]
            colors = colors * n_face
            colors = np.array(colors).reshape(n_face, 4)            
            self.update_ui()
        else:
            return
        #verts = np.array([
            #[0, 0, 0],
            #[2, 0, 0],
            #[1, 2, 0],
            #[1, 1, 1],
        #])*50
        #faces = np.array([
            #[0, 1, 2],
            #[0, 1, 3],
            #[0, 2, 3],
            #[1, 2, 3]
        #])
        #colors = np.array([
            #[1, 0, 0, 0.3],
            #[0, 1, 0, 0.3],
            #[0, 0, 1, 0.3],
            #[1, 1, 0, 0.3]
        #])
        # clear and reset view
        self.view.items = []     
        self.add_3d_printing_region()  
        # add new model
        m1 = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=colors, smooth=False)
        m1.translate(5, 5, 0)
        m1.setGLOptions('additive')
        self.view.addItem(m1)  
        
        # reset slider
        self.sl.setMinimum(0)
        self.sl.setMaximum(0)  
        self.sl.setValue(0)        
                
    def slice(self):
        if( len(self.mesh) == 0):
            self.message('Load mesh first!')
            return
    
        self.slices.clear()
        curdir = os.getcwd()        
        if(path.isdir("images")):
            #remove all files in images
            filelist = [ f for f in os.listdir("./images") if f.endswith(".png") ]            
            for f in filelist:
                os.remove(os.path.join(curdir+"/images", f))  
        else:
            os.mkdir("images")
        self.out_path = os.path.join(curdir, "images/slice-%d.png")
    
        self.message('Slicing mesh...')
    
        self.update_var()
        self.mesh_info.first_layer_thicknes = self.conf.get("first_layer_thickness")
        self.mesh_info.layer_thickness = self.conf.get("layer_thickness")
        nLayer = self.mesh_info.get_layers()
        z_list = self.mesh_info.get_z_list()
        str_layers = str(nLayer)
    
        x_pixel_size, y_pixel_size, x0, y0 = stl2pngfunc.stl2png(self.mesh_info.path, 
                                                                     z_list, 
                                                                     self.mesh_info.image_width, self.mesh_info.image_height, 
                                                                     self.out_path,
                                                                     self.mesh_info.border_size,
                                                                     func = lambda i: self.message("slicing layer " + str(i+1) + "/" + str_layers, False)
                                )
    
    
        self.mesh_info.real_pixel_size, self.mesh_info.real_pixel_size, self.gcode_minx, self.gcode_miny = x_pixel_size, y_pixel_size, x0, y0 
        self.message('Slicing mesh into ' + self.out_path)
        self.message(self.mesh_info.get_info() )
    
        im = cv2.imread(self.out_path % 0)
        tex1 = cv2.cvtColor(im, cv2.COLOR_BGR2RGBA) 
        v1 = gl.GLImageItem(tex1)
        v1.translate(0, 0, 0)        
        self.view_slice.addItem(v1)  
    
        # activate slider 
        self.sl.setMinimum(0)
        self.sl.setMaximum(self.mesh_info.get_layers() - 1)  
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1) 
        self.sl.valueChanged.connect(self.show_slice)
        return
    
    def print_sequence(self):
        try:
            self.message("Generate print sequence...")
        except Exception as e:
            self.message(str(e))  
   
    def fill(self):
        try:
            i = self.sl.value()
            self.message("Show slice {}.".format(i+1), False)
            curdir = os.getcwd()
            filepath = self.out_path % i
            offset = self.conf.get("infill_offset")
            line_width = 1#int(abs(offset)/2)
            pe = pathengine.pathEngine()    
            pe.generate_contours_from_img(filepath, True)
            pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
            contour_tree = pe.convert_hiearchy_to_PyPolyTree()  
            group_contour = pe.get_contours_from_each_connected_region(contour_tree, '0')
                  
            #draw boundaries
            #################################
            # Generate N color list
            #################################
            def generate_RGB_list(N):
                import colorsys
                HSV_tuples = [(x*1.0/N, 0.8, 0.9) for x in range(N)]
                RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
                rgb_list = tuple(RGB_tuples)
                return np.array(rgb_list) * 255   
            N = 50
            colors = generate_RGB_list(N)
            
            bg_img = pe.im.copy()
            bg_img = np.full(bg_img.shape, 255, dtype=np.uint8)
            for boundary in group_contour.values():
                spiral = mkspiral.spiral(pe, boundary, offset)
                pathengine.suPath2D.draw_line(spiral, bg_img, colors[0],line_width)                 
              
            # for show
            cv2.imwrite(filepath, bg_img)
            tex1 = cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGBA) 
            v1 = gl.GLImageItem(tex1)
            
            v1.translate(0, 0, i * self.mesh_info.layer_thickness)        
            self.view_slice.items = []
            self.view_slice.addItem(v1)            
        
        except Exception as e:
            self.message(str(e))
        return              
  
    def gen_path(self):
        if self.mesh_info.mesh == None:
            return
        self.view_slice.items = [] 
        self.update_var()
        self.mesh_info.first_layer_thicknes = self.conf.get("first_layer_thickness")
        self.mesh_info.layer_thickness = self.conf.get("layer_thickness")        
        #self.mesh_info.init(self.mesh_info.pixel_size, self.mesh_info.first_layer_thickness, self.mesh_info.layer_thickness)
        self.message(self.mesh_info.get_info())
        curdir = os.getcwd()        
        if(path.isdir("images")):
            #remove all files in images
            filelist = [ f for f in os.listdir("./images") if f.endswith(".png") ]            
            for f in filelist:
                os.remove(os.path.join(curdir+"/images", f))  
        else:
            os.mkdir("images")
        self.out_path = os.path.join(curdir, "images")        
        #self.path_verts = mkspiral.gen_continuous_path(self.mesh_info, self.out_path, 2000, self.conf.get("infill_offset"))
        self.path_verts = mkspiral.gen_continuous_path_with_constraint(self.mesh_info, self.out_path, 2000, 60,self.conf.get("infill_offset"))  
        plt = gl.GLLinePlotItem(pos=self.path_verts, color=pg.glColor('r'), width= 1, antialias=True)
        
        self.view_slice.addItem(plt)      
        self.view_slice.setBackgroundColor(pg.mkColor('w'))
        return
    def show_slice(self):
        #if len(self.slices) == 0:            
        #    return
        i = self.sl.value()
        if i < 0:
            return
        self.message("Show slice {}.".format(i+1), False)
        curdir = os.getcwd()
        
        im = cv2.imread(self.out_path % i)
        #self.slices[i] = im
        tex1 = cv2.cvtColor(im, cv2.COLOR_BGR2RGBA) 
        v1 = gl.GLImageItem(tex1)
        
        v1.translate(0, 0, i * self.mesh_info.layer_thickness)        
        self.view_slice.items = []
        self.view_slice.addItem(v1)
        
    def gen_gcode(self):
        if len(self.path_verts) == 0:
            self.message("Please press `Gen Path` first")
            return
        fname = QFileDialog.getSaveFileName(self, 'Save file', '', 
                                            "Mesh (*.gcode);")

        if fname[0]:
            ext_file = path.splitext(fname[0])[1]
            if  ext_file.lower() not in fname[1]:
                
                self.gcode_path = fname[0] + '.gcode'
            else:
                self.gcode_path = fname[0]
        else:
            return
        
        np.savetxt(self.gcode_path+'.txt', self.path_verts, fmt='%.4f')                
          
        return
    def clear(self):
        self.message(self.mesh_info.get_info())
        self.is_fill_path = False
        self.slices.clear()
        self.path_verts = []
        
        str = ''
        for wt in self.widget_arr.keys():            
            str += wt + '\n'
            
        self.message(str)   
        self.update_ui()
        return
        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = VView()
 
    
    #plot.sizeHint = view.sizeHint = lambda: pg.QtCore.QSize(600, 400)
    #view.setSizePolicy(plot.sizePolicy())
     
    sys.exit(app.exec_())
