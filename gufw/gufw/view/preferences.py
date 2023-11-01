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
from gi.repository import Gtk

import gettext
from gettext import gettext as _
gettext.textdomain('gufw')

NUM2UFW_LEVEL = {0 : 'off',
                 1 : 'low',
                 2 : 'medium',
                 3 : 'high',
                 4 : 'full'}
UFW_LEVEL2NUM = {'off'    : 0,
                 'low'    : 1,
                 'medium' : 2,
                 'high'   : 3,
                 'full'   : 4}

class Preferences:
    def __init__(self, gufw):
        self.gufw = gufw
        
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('gufw')
        self.builder.add_from_file('/usr/share/gufw/ui/preferences.ui')
        
        self._set_objects_name(gufw.profile)
        self._set_initial_values()
        
        self.win_preferences.set_transient_for(gufw.winMain)
        self.builder.connect_signals(self)
        self.win_preferences.show_all()

    def _set_objects_name(self, profile_cb):
        self.win_preferences     = self.builder.get_object('preferences')
        self.ufw_logging         = self.builder.get_object('ufw_logging')
        self.gufw_logging        = self.builder.get_object('gufw_logging')
        self.gufw_confirm_delete = self.builder.get_object('gufw_confirm_delete')
        self.report_interval     = self.builder.get_object('report_interval')
        self.list_profiles       = self.builder.get_object('profiles_list')
        self.list_selection      = self.builder.get_object('profiles_selection')
    
    def _set_initial_values(self):
        self.ufw_logging.set_active(UFW_LEVEL2NUM[self.gufw.frontend.get_ufw_logging()])
        if self.gufw.frontend.get_logging():
            self.gufw_logging.set_active(True)
        if self.gufw.frontend.get_config_value('ConfirmDeteleRule') == 'yes':
            self.gufw_confirm_delete.set_active(True)
        
        if self.gufw.frontend.get_config_value('RefreshInterval'):
            self.report_interval.set_value(int(self.gufw.frontend.get_config_value('RefreshInterval')))
        else:
            self.report_interval.set_value(3)
        
        # Profiles (model)
        self.profile_rows = Gtk.ListStore(str)
        for profile in self.gufw.frontend.get_all_profiles():
            self.profile_rows.append([profile])
        self.list_profiles.set_model(self.profile_rows)
        # Profiles (Editable one column)
        renderer_editable_profile = Gtk.CellRendererText()
        renderer_editable_profile.set_property('editable', True)
        type_profile_column = Gtk.TreeViewColumn(_("Profile"), renderer_editable_profile, text=0)
        self.list_profiles.append_column(type_profile_column)
        # Profiles (Edit row event)
        renderer_editable_profile.connect('edited', self._rename_profile)
    
    def _rename_profile(self, widget, path, new_name):
        """2 Click on profile"""
        # None is for internal use
        if new_name == 'None':
            self.gufw.show_dialog(self.win_preferences, _("Profile not valid"), _("You can't use this profile name"))
            return
        # Not empty
        if not new_name:
            self.gufw.show_dialog(self.win_preferences, _("Profile not valid"), _("Enter at least one character"))
            return
        # Length
        if len(new_name) > 15:
            self.gufw.show_dialog(self.win_preferences, _("Profile not valid"), _("Too long! (max. 15 characters)"))
            return
        # Check only ASCII characters and no spaces
        if not re.match('^[A-Za-z0-9_-]*$', new_name):
            self.gufw.show_dialog(self.win_preferences, _("Profile not valid"), _("Use only letters, numbers, dashes and underscores"))
            return
        # Exist?
        for searched_profile in self.profile_rows:
            if searched_profile[0] == new_name:
                self.gufw.show_dialog(self.win_preferences, _("Profile exist"), _("There is a profile with the same name"))
                return
        # Not the default
        previous_name = self.profile_rows[path][0]
        if previous_name == self.gufw.frontend.get_profile():
            self.gufw.show_dialog(self.win_preferences, _("Current profile"), _("You can't rename the current profile"))
            return
        
        self.gufw.frontend.rename_profile(self.profile_rows[path][0], new_name)
        self.profile_rows[path][0] = new_name
        self.gufw.profile.remove(int(path))
        self.gufw.profile.insert_text(int(path), new_name)
        self.gufw.add_to_log(_("Edited Profile: ") + new_name)
    
    def on_AddProfile_btn_clicked(self, widget, data=None):
        ind = 0
        exist_profile = True
        while exist_profile:
            ind += 1
            new_name = _("Profile") + str(ind)
            exist_profile = False
            for searched_profile in self.profile_rows:
                if searched_profile[0] == new_name:
                    exist_profile = True
                    break # Next ind
        
        self.gufw.frontend.add_profile(new_name)
        ind = self.gufw.frontend.get_all_profiles().index(new_name)
        self.profile_rows.append([new_name])
        self.gufw.profile.append_text(new_name)
        self.gufw.add_to_log(_("Created Profile: ") + new_name)
        
    def on_DeleteProfile_btn_clicked(self, widget, data=None):
        model, treeiter = self.list_selection.get_selected()
        if treeiter == None:
            self.gufw.show_dialog(self.win_preferences, _("Select a profile"), _("You need to select a profile for deleting"))
        else:
            deleted_profile = model.get_value(treeiter, 0)
            if deleted_profile == self.gufw.frontend.get_profile():
                self.gufw.show_dialog(self.win_preferences, _("Profile not erasable"), _("You can't remove the current profile"))
            else:
                self.gufw.profile.remove(self.gufw.frontend.get_all_profiles().index(deleted_profile))
                self.gufw.frontend.delete_profile(deleted_profile)
                self.profile_rows.remove(treeiter)
                self.gufw.add_to_log(_("Deleted Profile: ") + deleted_profile)
    
    def on_ufw_logging_changed(self, widget, data=None):
        self.gufw.frontend.set_ufw_logging(NUM2UFW_LEVEL[self.ufw_logging.get_active()])
        self.gufw.add_to_log(_("ufw Logging: ") + self.ufw_logging.get_active_text())
    
    def on_gufw_logging_toggled(self, widget, data=None):
        if self.gufw_logging.get_active():
            self.gufw.frontend.set_logging(True)
            self.gufw.add_to_log(_("Gufw Logging: Enabled"))
        else:
            self.gufw.add_to_log(_("Gufw Logging: Disabled"))
            self.gufw.frontend.set_logging(False)
    
    def on_gufw_confirm_delete_toggled(self, widget, data=None):
        if self.gufw_confirm_delete.get_active():
            self.gufw.frontend.set_config_value('ConfirmDeteleRule', 'yes')
            self.gufw.add_to_log(_("Confirm Delete Dialog: Enabled"))
        else:
            self.gufw.frontend.set_config_value('ConfirmDeteleRule', 'no')
            self.gufw.add_to_log(_("Confirm Delete Dialog: Disabled"))
    
    def on_close_btn_clicked(self, widget, data=None):
        self.win_preferences.destroy()
    
    def on_preferences_delete_event(self, widget, data=None):
        self.win_preferences.destroy()
    
    def on_report_interval_scale_button_release_event(self, widget, data=None):
        refresh_time = int(self.report_interval.get_value())
        self.gufw.frontend.set_config_value('RefreshInterval', refresh_time)
        # Translators: Refresh the live traffic on GUI
        self.gufw.add_to_log(_("Refresh Interval: ") + str(refresh_time) + '"')
