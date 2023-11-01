#!/usr/bin/env python3
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

from gufw.controller import Controller 
from gufw.instance   import Instance
from gufw.view.gufw  import Gufw


if __name__ == '__main__':
    
    app_instance = Instance()
    
    controler = Controller()
    
    gufw = Gufw(controler.get_frontend())
    
    app_instance.exit_app()
