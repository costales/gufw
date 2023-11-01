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

import os, sys
from stat import *

class Instance:
    def __init__(self):
        self.pid_file = '/tmp/gufw.pid'
        self._check_is_root()
        self._check_dir_writable('/etc')
        self._check_dir_writable('/lib')
        self._check_instance()
        self._start_application()
    
    def _check_is_root(self):
        if os.geteuid() != 0:
            from gi.repository import Gtk
            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Run as superuser")
            dialog.format_secondary_text("Just run this command in the shell: gufw  or  sudo gufw")
            dialog.run()
            dialog.destroy()
            exit(0)
    
    def _check_dir_writable(self, directory):
        if bin(os.stat(directory)[ST_MODE])[-5] == '0' and bin(os.stat(directory)[ST_MODE])[-2] == '0': # get chmod /etc
            return
        
        from gi.repository import Gtk
        import gettext
        from gettext import gettext as _
        gettext.textdomain('gufw')
        
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, _("Error: %s is writable" % directory))
        dialog.format_secondary_text(_("Your %s directory is writable.\nFix it running from Terminal:" % directory) + "\n\nsudo chmod 755 " + directory)
        dialog.run()
        dialog.destroy()
        exit(0)

    def _check_instance(self):
        if not os.path.isfile(self.pid_file):
            return
        
        # Read the pid from file
        pid = 0
        try:
            pid_file = open(self.pid_file, 'rt')
            data = pid_file.read()
            pid_file.close()
            pid = int(data)
        except Exception:
            pass
        
        # Check whether the process specified exists
        if pid == 0:
            return
        try:
            os.kill(pid, 0) # exception if the pid is invalid
        except Exception:
            return
        
        from gi.repository import Gtk
        import gettext
        from gettext import gettext as _
        gettext.textdomain('gufw')
        
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, _("Please, just one Gufw's instance"))
        dialog.format_secondary_text(_("Gufw is already running. If this is wrong, remove the file: ") + self.pid_file)
        dialog.run()
        dialog.destroy()
        exit(0)
    
    def _start_application(self):
        if self._under_ssh():
            return
        
        pid_file = open(self.pid_file, 'wt')
        pid_file.write(str(os.getpid()))
        pid_file.close()
    
    def _under_ssh(self):
        try:
            if sys.argv[1] == '-ssh':
                return True
        except Exception:
            pass
        
        return False
    
    def exit_app(self):
        try:
            os.remove(self.pid_file)
        except Exception:
            pass
