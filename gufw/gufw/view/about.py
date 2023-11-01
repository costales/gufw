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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class About:
    def __init__(self, gufw):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('gufw')
        self.builder.add_from_file('/usr/share/gufw/ui/about.ui')
        
        self.win_about = self.builder.get_object('about')
        self.win_about.set_transient_for(gufw.winMain)
        self.win_about.connect('response', lambda d, r: d.destroy())
        self.win_about.show()

