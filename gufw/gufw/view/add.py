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
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk
from gi.repository.Gdk import Color
import os, glob, configparser

import gettext
from gettext import gettext as _
gettext.textdomain('gufw')

DIR_PROFILES = '/etc/gufw/app_profiles'


class Add:
    def __init__(self, gufw):
        self.gufw = gufw
        
        self.apps = AppProfiles()
        
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('gufw')
        self.builder.add_from_file('/usr/share/gufw/ui/add.ui')
        
        self._set_objects_name()
        self._set_initial_values()
        
        self.win_add.set_transient_for(gufw.winMain)
        self.updating_subcategories = False
        
        self.builder.connect_signals(self)
    
    def _set_objects_name(self):
        self.win_add = self.builder.get_object('AddRule')
        self.tabs    = self.builder.get_object('addTabs')
        self.add_btn = self.builder.get_object('btnAddRuleWin')
        
        self.preconfig_policy      = self.builder.get_object('preconfig_policy')
        self.preconfig_direction   = self.builder.get_object('preconfig_direction')
        self.preconfig_category    = self.builder.get_object('preconfig_category')
        self.app_filter            = self.builder.get_object('app_filter')
        self.preconfig_subcategory = self.builder.get_object('preconfig_subcategory')
        self.preconfig_app         = self.builder.get_object('preconfig_app')
        self.preconfig_description = self.builder.get_object('preconfig_description')
        self.img_description       = self.builder.get_object('img_description')
        self.warningbox            = self.builder.get_object('warningbox')
        self.lbl_inforule          = self.builder.get_object('lbl_preconfig_info')
        
        self.simple_rule_name = self.builder.get_object('simple_rule_name')
        self.simple_policy    = self.builder.get_object('simple_policy')
        self.simple_direction = self.builder.get_object('simple_direction')
        self.simple_protocol  = self.builder.get_object('simple_protocol')
        self.simple_port      = self.builder.get_object('simple_port')
        
        self.advanced_rule_name  = self.builder.get_object('advanced_rule_name')
        self.advanced_insert     = self.builder.get_object('advanced_insert')
        self.advanced_policy     = self.builder.get_object('advanced_policy')
        self.advanced_direction  = self.builder.get_object('advanced_direction')
        self.advanced_iface      = self.builder.get_object('advanced_iface')
        self.advanced_routed_img = self.builder.get_object('routed_img')
        self.advanced_routed     = self.builder.get_object('advanced_routed')
        self.advanced_log        = self.builder.get_object('advanced_log')
        self.advanced_protocol   = self.builder.get_object('advanced_protocol')
        self.advanced_from_ip    = self.builder.get_object('advanced_from_ip')
        self.advanced_from_port  = self.builder.get_object('advanced_from_port')
        self.advanced_to_ip      = self.builder.get_object('advanced_to_ip')
        self.advanced_to_port    = self.builder.get_object('advanced_to_port')
    
    def _set_initial_values(self):
        self._set_app_combobox()
        
        # Bug gnome #549478
        self.preconfig_policy.set_active(0)
        self.preconfig_direction.set_active(0)
        
        self.simple_policy.set_active(0)
        self.simple_direction.set_active(0)
        self.simple_protocol.set_active(0)
        
        self.advanced_policy.set_active(0)
        self.advanced_direction.set_active(0)
        # Translators: About the network interfaces in the OS
        self.advanced_iface.append_text(_("All Interfaces"))
        # Translators: About traffic
        self.advanced_routed.append_text(_("Not Forward"))
        for ifaceName in self.gufw.frontend.get_net_interfaces():
            self.advanced_iface.append_text(ifaceName)
            self.advanced_routed.append_text(ifaceName)
        self.advanced_iface.set_active(0)
        self.advanced_routed.set_active(0)
        self.advanced_log.set_active(0)
        self.advanced_protocol.set_active(0)
        
        if self.gufw.frontend.get_policy('routed') == 'disabled':
            self.advanced_routed_img.set_visible(False)
            self.advanced_routed.set_visible(False)
    
    def show_win(self):
        if self.app_filter.get_text():
            self.app_filter.set_text('')
        self.win_add.show()
        
    
    def set_add_from_report(self, protocol='', port='', address='', name=''):
        self.advanced_rule_name.set_text(name)
        if protocol[:3] == 'TCP':
            self.advanced_protocol.set_active(1)
        elif protocol[:3] == 'UDP':
            self.advanced_protocol.set_active(2)
        else:
            self.advanced_protocol.set_active(0)
        self.advanced_to_ip.set_text(address)
        self.advanced_to_port.set_text(port)        
        self.tabs.set_current_page(2)
        
    def _hide_win(self):
        self.win_add.hide()
    
    def _set_app_combobox(self):
        categories = self.apps.get_just_categories()
        for cat in categories:
            self.preconfig_category.append_text(cat)
        try:
            # Translators: ALL applications
            self.preconfig_category.set_active(categories.index(_("All")))
        except Exception:
            self.preconfig_category.set_active(0)
        
        subcategories = self.apps.get_subcategories(self.preconfig_category.get_active_text())
        for subcat in subcategories:
            self.preconfig_subcategory.append_text(subcat)
        self.preconfig_subcategory.set_active(0)
        
        apps = self.apps.get_apps_cat_subcat(self.preconfig_category.get_active_text(), self.preconfig_subcategory.get_active_text())
        for app in apps:
            self.preconfig_app.append_text(app)
        self.preconfig_app.set_active(0)
        
        tooltip = self.apps.get_app(self.preconfig_app.get_active_text())[0] + '\n' + _("Ports: ") + self.apps.get_app(self.preconfig_app.get_active_text())[1]
        self.img_description.set_tooltip_text(tooltip)
    
    def on_btnAddClose_clicked(self, widget, data=None):
        self._win_close()
    
    def on_AddRule_delete_event(self, widget, data=None):
        self._win_close()
        return True # Overwrite event
    
    def _win_close(self):
        self.gufw.show_add_btn.set_sensitive(self.gufw.frontend.get_status())
        self.gufw.edit_rule_btn.set_sensitive(self.gufw.frontend.get_status())
        self.gufw.report_rule_btn.set_sensitive(self.gufw.frontend.get_status())
        self._hide_win()
    
    def on_copy_from_IP_clicked(self, widget, data=None):
        self.advanced_from_ip.set_text(self.gufw.frontend.get_internal_ip())
    
    def on_copy_to_IP_clicked(self, widget, data=None):
        self.advanced_to_ip.set_text(self.gufw.frontend.get_internal_ip())
    
    def on_copy_simple_to_advanced_clicked(self, widget, data=None):
        self.advanced_rule_name.set_text(self.simple_rule_name.get_text())
        self.advanced_policy.set_active(self.simple_policy.get_active())
        self.advanced_direction.set_active(self.simple_direction.get_active())
        self.advanced_protocol.set_active(self.simple_protocol.get_active())
        self.advanced_to_port.set_text(self.simple_port.get_text())
        self.tabs.set_current_page(2)
    
    def on_copy_preconfig_to_advanced_clicked(self, widget, data=None):
        self.advanced_rule_name.set_text(self.preconfig_app.get_active_text())
        self.advanced_policy.set_active(self.preconfig_policy.get_active())
        self.advanced_direction.set_active(self.preconfig_direction.get_active())
        self.advanced_protocol.set_active(0)
        self.advanced_to_port.set_text(self.apps.get_app(self.preconfig_app.get_active_text())[1])
        self.tabs.set_current_page(2)
    
    def _set_advanced_addBtn_control(self, ntab):
        # Not allow Both Protocol with a range of ports in Simple and Advanced tab
        if ntab == 2 and (':' in self.advanced_to_port.get_text() or ':' in self.advanced_from_port.get_text()) and not self.advanced_protocol.get_active():
            self.add_btn.set_sensitive(False)
            self.add_btn.set_tooltip_text(_("Choose a TCP or UDP Protocol with a range of ports"))
        else:
            self.add_btn.set_sensitive(True)
            self.add_btn.set_tooltip_text('')
    
    def _set_simple_addBtn_control(self, ntab):
        # Not allow Both Protocol with a range of ports in Simple and Advanced tab
        if ntab == 1 and ':' in self.simple_port.get_text() and not self.simple_protocol.get_active():
            self.add_btn.set_sensitive(False)
            self.add_btn.set_tooltip_text(_("Choose a TCP or UDP Protocol with a range of ports"))
        else:
            self.add_btn.set_sensitive(True)
            self.add_btn.set_tooltip_text('')
    
    def on_addTabs_switch_page(self, widget, data=None, change_to_ntab=None):
        if change_to_ntab == 1:
            self._set_simple_addBtn_control(change_to_ntab)
        elif change_to_ntab == 2:
            self._set_advanced_addBtn_control(change_to_ntab)
        else:
            self.add_btn.set_sensitive(True)
            self.add_btn.set_tooltip_text('')
    
    def on_simple_protocol_changed(self, widget, data=None):
        self._set_simple_addBtn_control(self.tabs.get_current_page())
    
    def on_simple_port_changed(self, widget, data=None):
        self._set_simple_addBtn_control(self.tabs.get_current_page())
    
    def on_advanced_protocol_changed(self, widget, data=None):
        self._set_advanced_addBtn_control(self.tabs.get_current_page())
    
    def on_advanced_from_port_changed(self, widget, data=None):
        if '/' in self.advanced_from_port.get_text():
            self._set_from_port_sensitive(False)
        else:
            self._set_from_port_sensitive(True)
        
        self._set_advanced_addBtn_control(self.tabs.get_current_page())
    
    def on_advanced_to_port_changed(self, widget, data=None):
        if '/' in self.advanced_to_port.get_text():
            self._set_to_port_sensitive(False)
        else:
            self._set_to_port_sensitive(True)
        
        self._set_advanced_addBtn_control(self.tabs.get_current_page())
    
    def _set_from_port_sensitive(self, value=True):
        self.advanced_protocol.set_sensitive(value)
        self.advanced_from_ip.set_sensitive(value)
        self.advanced_to_ip.set_sensitive(value)
        self.advanced_to_port.set_sensitive(value)
    
    def _set_to_port_sensitive(self, value=True):
        self.advanced_protocol.set_sensitive(value)
        self.advanced_from_ip.set_sensitive(value)
        self.advanced_to_ip.set_sensitive(value)
        self.advanced_from_port.set_sensitive(value)
    
    def on_preconfig_category_changed(self, widget, data=None):
        self.updating_subcategories = True
        self.app_filter.set_text('')
        self.preconfig_subcategory.set_sensitive(False)
        self.preconfig_app.set_sensitive(False)
        # Delete all subcategories & apps
        self.preconfig_subcategory.remove_all()
        self.preconfig_app.remove_all()
        # Append new subcategories
        subcategories = self.apps.get_subcategories(self.preconfig_category.get_active_text())
        for subcat in subcategories:
            self.preconfig_subcategory.append_text(subcat)
        # Append new apps
        # Translators: ALL applications
        apps = self.apps.get_apps_cat_subcat(self.preconfig_category.get_active_text(), _("All"))
        for app in apps:
            self.preconfig_app.append_text(app)
        # Set initial subcat and app
        self.preconfig_subcategory.set_active(0)
        self.preconfig_app.set_active(0)

        self.preconfig_subcategory.set_sensitive(True)
        self.preconfig_app.set_sensitive(True)
        self.updating_subcategories = False
    
    def on_preconfig_subcategory_changed(self, widget, data=None):
        if self.updating_subcategories:
            return
        self.updating_subcategories = True
        self.app_filter.set_text('')
        self.preconfig_app.set_sensitive(False)
        # Delete all apps
        self.preconfig_app.remove_all()
        # Append new entries
        apps = self.apps.get_apps_cat_subcat(self.preconfig_category.get_active_text(), self.preconfig_subcategory.get_active_text())
        for app in apps:
            self.preconfig_app.append_text(app)
        # Set initial app
        self.preconfig_app.set_active(0)
        self.preconfig_app.set_sensitive(True)
        self.updating_subcategories = False
    
    def on_app_filter_search_changed(self, widget, data=None):
        if self.updating_subcategories:
            return
        
        user_filter = self.app_filter.get_text().lower()
        if not user_filter:
            # Refresh apps
            self.preconfig_app.remove_all()
            apps = self.apps.get_apps_cat_subcat(self.preconfig_category.get_active_text(), self.preconfig_subcategory.get_active_text())
            for app in apps:
                self.preconfig_app.append_text(app)
            
            self.preconfig_app.set_active(0)
            self.app_filter.modify_fg(Gtk.StateFlags.NORMAL, None)
            return
        
        # Apps
        new_apps = []
        apps = self.apps.get_apps_cat_subcat(self.preconfig_category.get_active_text(), self.preconfig_subcategory.get_active_text())
        for app in apps:
            if (app.lower().find(user_filter) != -1 or                       # Search in name
                self.apps.get_app(app)[0].lower().find(user_filter) != -1 or # Search in description
                self.apps.get_app(app)[1].lower().find(user_filter) != -1):  # Search in ports
                if new_apps.count(app) == 0:
                    new_apps.append(app)
        
        if len(new_apps) > 0:
            self.preconfig_app.remove_all()
            for app in new_apps:
                self.preconfig_app.append_text(app)
            self.preconfig_app.set_active(0)
            self.app_filter.modify_fg(Gtk.StateFlags.NORMAL, None)
        else:
            self.app_filter.modify_fg(Gtk.StateFlags.NORMAL, Color(50000, 0, 0))
    
    def on_app_filter_icon_press(self, widget, data=None, data2=None):
        self.app_filter.set_text('')
    def on_simple_rule_name_icon_press(self, widget, data=None, data2=None):
        self.simple_rule_name.set_text('')
    def on_simple_port_icon_press(self, widget, data=None, data2=None):
        self.simple_port.set_text('')
    def on_advanced_rule_name_icon_press(self, widget, data=None, data2=None):
        self.advanced_rule_name.set_text('')
    def on_advanced_to_ip_icon_press(self, widget, data=None, data2=None):
        self.advanced_to_ip.set_text('')
    def on_advanced_from_ip_icon_press(self, widget, data=None, data2=None):
        self.advanced_from_ip.set_text('')
    def on_advanced_from_port_icon_press(self, widget, data=None, data2=None):
        self.advanced_from_port.set_text('')
    def on_advanced_to_port_icon_press(self, widget, data=None, data2=None):
        self.advanced_to_port.set_text('')
    
    def on_advanced_iface_changed(self, widget, data=None, data2=None):
        # Translators: About the network interfaces in the OS
        if self.advanced_iface.get_active_text() != _("All Interfaces"):
            self.advanced_routed.set_sensitive(True)
            self.advanced_routed.set_tooltip_text(_("The IP/Port will be forward to this interface"))
        else:
            self.advanced_routed.set_sensitive(False)
            self.advanced_routed.set_tooltip_text(_("You need to set an Interface for forwarding to this another interface"))
        
        # Not allow same iface when is routed
        if self.gufw.frontend.get_policy('routed') != 'disabled':
            self.advanced_routed.remove_all()
            # Translators: About traffic
            self.advanced_routed.append_text(_("Not Forward"))
            for ifaceName in self.gufw.frontend.get_net_interfaces(self.advanced_iface.get_active_text()):
                self.advanced_routed.append_text(ifaceName)
            self.advanced_routed.set_active(0)
    
    def on_preconfig_app_changed(self, widget, data=None):
        if self.preconfig_app.get_active_text() != None:
            tooltip = self.apps.get_app(self.preconfig_app.get_active_text())[0] + '\n' + _("Ports: ") + self.apps.get_app(self.preconfig_app.get_active_text())[1]
            self.img_description.set_tooltip_text(tooltip)
            if self.apps.get_app(self.preconfig_app.get_active_text())[3]:
                self.lbl_inforule.set_text(self.apps.get_app(self.preconfig_app.get_active_text())[3])
                self.warningbox.show()
            else:
                self.warningbox.hide()
    
    def on_btnAddRuleWin_clicked(self, widget, data=None):
        if not self.gufw.frontend.get_status():
            self.gufw.show_dialog(self.win_add, _("Error: Firewall is disabled"), _("The firewall has to be enabled first"))
            return
        
        if self.tabs.get_current_page() == 0:
            self._add_rule_preconfig()
        elif self.tabs.get_current_page() == 1:
            self._add_rule_simple()
        elif self.tabs.get_current_page() == 2:
            self._add_rule_advanced()
    
    def _add(self, profile='', name='', policy='', direction='', proto='', from_ip='', from_port='', to_ip='', to_port='', insert='', iface='', routed='', logging=''):
        flag_OK = True
        flag_Warning = False
        
        # Split possible ports > 135,139,445/tcp|137,138/udp
        for from_split in from_port.split('|'):
            for to_split in to_port.split('|'):
                from_port = from_split
                to_port = to_split
                if direction == 'both':
                    cmd = self.gufw.frontend.add_rule(name, insert, policy, 'in',  iface, routed, logging, proto, from_ip, from_port, to_ip, to_port)
                    cmd = self.gufw.frontend.add_rule(name, insert, policy, 'out', iface, routed, logging, proto, from_ip, from_port, to_ip, to_port)
                else:
                    cmd = self.gufw.frontend.add_rule(name, insert, policy, direction, iface, routed, logging, proto, from_ip, from_port, to_ip, to_port)
                
                if cmd[0]:
                    flag_Warning = True
                    self.gufw.add_to_log(cmd[1])
                else:
                    flag_OK = False
                    self.gufw.add_to_log(_("Error running: ") + cmd[1] + ' > ' + cmd[2].replace('\n', ' | '))
        
        # OK
        if flag_OK and flag_Warning:
            self.gufw.set_statusbar_msg(_("Rule(s) added"))
        # Some OK, some KO
        elif flag_OK and not flag_Warning:
            self.gufw.set_statusbar_msg(_("Warning: Some rules added. Review the log"))
        # KO
        else:
            self.gufw.set_statusbar_msg(_("Error: No rules added. Review the log"))
    
    def _add_rule_preconfig(self):
        self._add(self.gufw.frontend.get_profile(),                                    # profile
                 self.preconfig_app.get_active_text(),                           # name
                 self.gufw.NUM2POLICY[self.preconfig_policy.get_active()],       # policy
                 self.gufw.NUM2DIRECTION[self.preconfig_direction.get_active()], # direction
                 '',                                                             # proto
                 '',                                                             # from IP
                 '',                                                             # from port
                 '',                                                             # to IP
                 self.apps.get_app(self.preconfig_app.get_active_text())[1])     # to port[/proto][|port[/proto]]
        self.gufw.print_rules(self.gufw.frontend.get_rules())
    
    def _add_rule_simple(self):
        if not self.simple_port.get_text():
            self.gufw.show_dialog(self.win_add, _("Insert Port"), _("You need to insert a port in the port field"))
            return
        
        if self.simple_port.get_text().upper() == 'PRISM':
            self.gufw.show_dialog(self.win_add, _("Edward Snowden's Greatest Fear"), _('"Nothing Will Change"'))
            return
        
        self._add(self.gufw.frontend.get_profile(),                                 # profile
                 self.simple_rule_name.get_text(),                            # name
                 self.gufw.NUM2POLICY[self.simple_policy.get_active()],       # policy
                 self.gufw.NUM2DIRECTION[self.simple_direction.get_active()], # direction
                 self.gufw.NUM2PROTO[self.simple_protocol.get_active()],      # protocol
                 '',                                                          # from IP
                 '',                                                          # from port
                 '',                                                          # to IP
                 self.simple_port.get_text())                                 # to port
        self.gufw.print_rules(self.gufw.frontend.get_rules())
    
    def _add_rule_advanced(self):
        # Validations
        if not self.gufw.validate_rule(self.win_add, self.advanced_from_ip.get_text(), self.advanced_from_port.get_text(), self.advanced_to_ip.get_text(), self.advanced_to_port.get_text(), self.advanced_insert.get_text(), self.advanced_routed.get_active_text()):
            return
        
        insert = self.advanced_insert.get_text()
        if insert == '0':
            insert = ''
        
        iface = ''
        # Translators: About traffic
        if self.advanced_iface.get_sensitive() and self.advanced_iface.get_active_text() != _("All Interfaces"):
            iface = self.advanced_iface.get_active_text()
        
        routed = ''
        # Translators: About traffic
        if self.advanced_routed.get_sensitive() and self.advanced_routed.get_active_text() != _("Not Forward"):
            routed = self.advanced_routed.get_active_text()
        
        to_ip = to_port = from_ip = from_port = ''
        from_ip = self.advanced_from_ip.get_text()
        from_port = self.advanced_from_port.get_text()
        to_ip = self.advanced_to_ip.get_text()
        to_port = self.advanced_to_port.get_text()
        
        self._add(self.gufw.frontend.get_profile(),                                   # profile
                 self.advanced_rule_name.get_text(),                            # name
                 self.gufw.NUM2POLICY[self.advanced_policy.get_active()],       # policy
                 self.gufw.NUM2DIRECTION[self.advanced_direction.get_active()], # direction
                 self.gufw.NUM2PROTO[self.advanced_protocol.get_active()],      # protocol
                 from_ip,                                                       # from IP
                 from_port,                                                     # from port
                 to_ip,                                                         # to IP
                 to_port,                                                       # to port
                 insert,                                                        # insert number
                 iface,                                                         # interface
                 routed,                                                        # routed
                 self.gufw.NUM2LOGGING[self.advanced_log.get_active()])         # logging        
        self.gufw.print_rules(self.gufw.frontend.get_rules())


class AppProfiles:
    """Load app profiles"""
    def __init__(self):
        self.all_apps = self._load_from_files()
        self.all_categories = self._get_all_categories()
    
    def _load_from_files(self):
        apps = {}
        os.chdir(DIR_PROFILES)
        cfg = configparser.ConfigParser()  
        cfg.read(glob.glob('*.*'))
        
        for section in cfg.sections():
            title = description = ports = categories = warning = ''
            
            if cfg.has_option(section, 'title'):
                title = cfg.get(section, 'title')
            if cfg.has_option(section, 'description'):
                description = cfg.get(section, 'description')
            if cfg.has_option(section, 'ports'):
                ports = cfg.get(section, 'ports')
            if cfg.has_option(section, 'categories'):
                categories = cfg.get(section, 'categories')
            if cfg.has_option(section, 'warning'):
                warning = cfg.get(section, 'warning')
                
            if title and description and ports and categories:
                if warning != '':
                    apps[_(title)] = [_(description), ports, _(categories), _(warning)]
                else:
                    apps[_(title)] = [_(description), ports, _(categories), '']
        return apps
    
    def _get_all_categories(self):
        all_categ = []
        for app in self.all_apps:
            categories = self.all_apps[app][2].split('|')
            for category in categories:
                if not all_categ.count(category):
                    all_categ.append(category)
        return all_categ
    
    def get_just_categories(self):
        categ = []
        for cat in self.all_categories:
            current_cat = cat.split(';')[0]
            if not categ.count(current_cat):
                categ.append(current_cat)
        categ.sort()
        # Translators: About categories
        categ.insert(0, _("All"))
        return categ
    
    def get_subcategories(self, category):
        subcateg = []
        for cat in self.all_categories:
            current_cat = cat.split(';')[0]
            # Translators: About categories
            if current_cat == category or category == _("All"):
                try:
                    current_subcat = cat.split(';')[1]
                except Exception:
                    current_subcat = ''
                if not subcateg.count(current_subcat) and current_subcat:
                    subcateg.append(current_subcat)
        subcateg.sort()
        # Translators: About subcategories
        subcateg.insert(0, _("All"))
        return subcateg
    
    def get_apps_cat_subcat(self, cat, subcat):
        apps = []
        for app in self.all_apps:
            categories = self.all_apps[app][2].split('|')
            for category in categories:
                current_cat = category.split(';')[0]
                try:
                    current_subcat = category.split(';')[1]
                except Exception:
                    current_subcat = ''
                
                # Translators: About categories
                # Translators: About subcategories
                if cat == _("All") and subcat == _("All"):
                    apps.append(app)
                # Translators: About categories
                elif cat == _("All") and subcat == current_subcat:
                    apps.append(app)
                # Translators: About categories
                elif cat == current_cat and subcat == _("All"):
                    apps.append(app)
                elif cat == current_cat and subcat == current_subcat:
                    apps.append(app)
        
        apps.sort()
        return apps
    
    def get_app(self, app):
        return self.all_apps[app]
