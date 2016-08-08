# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

#!/usr/bin/python

import os
import json
import gi
import copy
import dbus
import pprint

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk



from subprocess import call

class MainWindow(Gtk.Window):
    
    def __init__(self):
        Gtk.Window.__init__(self, title = "PiPyPanel")
        self.maximize()
        self.grid = Gtk.Grid()
        self.add(self.grid)
        
        layout = self.read_layout()
        self.buttons = [];
        
        for b in layout:
            self.buttons.append(Gtk.Button.new())
            if ('image' in b):
                image = Gtk.Image.new_from_file(b['image'])
                self.buttons[-1].set_image(image)
            else:
                self.buttons[-1].set_label(b['label'])
                
            self.buttons[-1].connect('clicked', self.on_button_clicked, b)
            self.buttons[-1].set_hexpand(True)
            self.buttons[-1].set_vexpand(True)
            self.grid.attach(self.buttons[-1], b['left'], b['top'], b['width'], b['height'])
            
        self.bus = dbus.SessionBus()
        self.calculate_quads()
            
    def read_layout(self):
        layout_file = open('layout.json', 'r')
        layout_json = layout_file.read()
        layout_file.close()
        return json.loads(layout_json)


    def on_button_clicked(self, widget, data):
        pprint.pprint(data)
        if ('cmd' in data):
            call('DISPLAY=:0 ' + data['cmd'], shell = True)
        elif ('compiz' in data):
            self.compiz_activate(data['compiz']['plugin'], data['compiz']['action'])
        elif ('quad' in data):
            self.window_to_quad(data['quad'])
        elif ('dbus' in data):
            self.dbus_send(data['dbus']['bus'], data['dbus']['object'], data['dbus']['interface'], data['dbus']['method'])
        
    def compiz_activate(self, plugin, action):
        proxy = self.bus.get_object('org.freedesktop.compiz', '/org/freedesktop/compiz/%s/screen0/%s' % (plugin, action))
        obj = dbus.Interface(proxy, 'org.freedesktop.compiz')
        obj.activate()


    def dbus_send(self, bus_name, object_name, interface_name, method_name):
        obj = self.bus.get_object(bus_name, object_name)
        obj.get_dbus_method(method_name, dbus_interface = interface_name)._proxy_method.call_async()
        

    def calculate_quads(self):
        screen = Gdk.Screen.get_default()
        
        self.q = []
        
        for m in range(2):
            self.q.append([])
            self.q[m].append(screen.get_monitor_workarea(m))
            self.q[m][0].width /= 2
            
            self.q[m].append(screen.get_monitor_workarea(m))
            self.q[m][1].width /= 2
            self.q[m][1].x += self.q[m][1].width

        for m in range(2):
            for h in range(2):
                print("Q%dx%d: %d,%d,%d,%d" % (m, h, self.q[m][h].x, self.q[m][h].y, self.q[m][h].width, self.q[m][h].height))
                
    def window_to_quad(self, q):
        m = q / 2
        h = q % 2
        print ("m = %d, h=%d" % (m, h))
        cmd = "wmctrl -r :ACTIVE: -e 0,%d,%d,%d,%d" % (self.q[m][h].x, self.q[m][h].y, self.q[m][h].width, self.q[m][h].height)
        print(cmd)
        
        call('DISPLAY=:0 ' + cmd, shell = True)
        
        
win = MainWindow()
win.connect('delete-event', Gtk.main_quit)
win.show_all()
Gtk.main()

