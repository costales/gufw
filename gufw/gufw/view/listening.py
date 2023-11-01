# Gufw - https://costales.github.io/projects/gufw/
# Copyright (C) 2008-2023 Marcos Alvarez Costales https://costales.github.io
#
# Gufw is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Gufw is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gufw; if not, see http://www.gnu.org/licenses for more
# information.

import gi
import re
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk


REFRESH_TIME = 3 # Default interval refresh


class ListeningReport():
    
    def __init__(self, gufw):
        self.gufw = gufw
        self.previous_report = []
        self.running_listening = True
        self.paused_listening = False
        
        self._show_report()
        
        if self.gufw.frontend.get_config_value('RefreshInterval'):
            time = int(self.gufw.frontend.get_config_value('RefreshInterval'))
        else:
            time = REFRESH_TIME
        GLib.timeout_add((time * 1000), self._show_report)
        
    def _show_report(self):
        if not self.running_listening:
            return False
        
        report = self.gufw.frontend.get_listening_report()
        self._view_report(report, self.previous_report)
        self.previous_report = report
        
        while Gtk.events_pending(): # Not freeze main win
            Gtk.main_iteration()
        
        return True
    
    def stopping(self):
        self.running_listening = False
    
    def set_pause(self, value):
        self.paused_listening = value
    
    def _view_report(self, report, previous_report):
        if self.paused_listening:
            return
        # Selected?
        protocol = port = address = app = ''
        (model, rows) = self.gufw.tv_report.get_selection().get_selected_rows()
        if len(rows) == 1:
            iter_row = self.gufw.listening_model.get_iter(rows[0],)
            protocol = self.gufw.listening_model.get_value(iter_row, 0)
            port     = str(self.gufw.listening_model.get_value(iter_row, 1))
            address  = self.gufw.listening_model.get_value(iter_row, 2)
            app      = self.gufw.listening_model.get_value(iter_row, 3)
        
        row = 0
        self.gufw.listening_model.clear()
        
        for line in report:
            line_split = line.split('%')
            row += 1
            iter_row = self.gufw.listening_model.insert(row)
            self.gufw.listening_model.set_value(iter_row, 0, line_split[0].strip())      # protocol
            self.gufw.listening_model.set_value(iter_row, 1, int(line_split[1].strip())) # port
            self.gufw.listening_model.set_value(iter_row, 2, line_split[2].strip())      # address
            self.gufw.listening_model.set_value(iter_row, 3, line_split[3].strip())      # app
            self.gufw.listening_model.set_value(iter_row, 5, row)                        # number
            
            if self.gufw.frontend.get_status():
                if line_split[4] == 'allow':
                    self.gufw.listening_model.set_value(iter_row, 4, self.gufw.RED)
                elif line_split[4] == 'deny':
                    self.gufw.listening_model.set_value(iter_row, 4, self.gufw.GREEN)
                elif line_split[4] == 'reject':
                    self.gufw.listening_model.set_value(iter_row, 4, self.gufw.BLUE)
                elif line_split[4] == 'limit':
                    self.gufw.listening_model.set_value(iter_row, 4, self.gufw.ORANGE)
        
        # Previously selected? > Get current row because treeview could be sorted
        if protocol and port:
            select_this_row = -1
            i = 0
            while True:
                try:
                    iter_row = self.gufw.listening_model.get_iter(i,)
                    if (protocol == self.gufw.listening_model.get_value(iter_row, 0) and
                        port     == str(self.gufw.listening_model.get_value(iter_row, 1)) and
                        address  == self.gufw.listening_model.get_value(iter_row, 2) and
                        app      == self.gufw.listening_model.get_value(iter_row, 3)):
                        select_this_row = i
                except Exception:
                    break
                i += 1
            
            if select_this_row != -1:
                self.gufw.tv_report.set_cursor(select_this_row)
