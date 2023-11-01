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

DIRECTION2NUM = {'in': 0,
                 'out': 1,
                 'both': 1}
LOGGING2NUM = {'': 0,
               'log': 1,
               'log-all': 2}
PROTO2NUM = {'': 0,
             'tcp': 1,
             'udp': 2 }


class Update:
    def __init__(self, gufw, ufw_row, description, cmd, policy, direction, proto, from_ip, from_port, to_ip, to_port, iface, routed, logging):
        self.gufw = gufw
        self.ufw_row = str(ufw_row)
        self.rule_description = description
        self.rule_cmd         = cmd
        self.rule_policy      = policy
        self.rule_direction   = direction
        self.rule_proto       = proto
        self.rule_from_ip     = from_ip
        self.rule_from_port   = from_port
        self.rule_to_ip       = to_ip
        self.rule_to_port     = to_port
        self.rule_iface       = iface
        self.rule_routed      = routed
        self.rule_logging     = logging

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('gufw')
        self.builder.add_from_file('/usr/share/gufw/ui/update.ui')
        
        self._set_objects_name()
        self._set_initial_values()
        
        self.win_update.set_transient_for(gufw.winMain)
        self.builder.connect_signals(self)
        self.win_update.show_all()
        
        if self.gufw.frontend.get_policy('routed') == 'disabled':
            self.update_routed_img.set_visible(False)
            self.update_routed.set_visible(False)
        
        # Set sensitive values
        self.update_from_ip.set_text(self.rule_from_ip)
        self.update_from_port.set_text(self.rule_from_port)
        self.update_to_ip.set_text(self.rule_to_ip)
        self.update_to_port.set_text(self.rule_to_port)
        # Translators: About the network interfaces in the OS
        if self.update_iface.get_active_text() == _("All Interfaces"):
            self.update_routed.set_sensitive(False)
            # Translators: About the network interfaces in the OS
            self.update_routed.set_tooltip_text(_("You need to set an Interface"))
    
    def _set_objects_name(self):
        self.win_update        = self.builder.get_object('UpdateRule')
        self.update_rule_name  = self.builder.get_object('update_rule_name')
        self.update_policy     = self.builder.get_object('update_policy')
        self.update_direction  = self.builder.get_object('update_direction')
        self.update_iface      = self.builder.get_object('update_iface')
        self.update_routed     = self.builder.get_object('update_routed')
        self.update_routed_img = self.builder.get_object('update_routed_img')
        self.update_log        = self.builder.get_object('update_log')
        self.update_protocol   = self.builder.get_object('update_protocol')
        self.update_from_ip    = self.builder.get_object('update_from_ip')
        self.update_from_port  = self.builder.get_object('update_from_port')
        self.update_to_ip      = self.builder.get_object('update_to_ip')
        self.update_to_port    = self.builder.get_object('update_to_port')
        self.warning           = self.builder.get_object('lbl_preconfig_info')
        self.warning_box       = self.builder.get_object('warningbox')
        self.update_btn        = self.builder.get_object('btnUpdate')
    
    def _set_initial_values(self):
        iface_num = 0
        routed_num = 0
        i = 0
        # Translators: About the network interfaces in the OS
        self.update_iface.append_text(_("All Interfaces"))
        self.update_routed.append_text(_("Not Forward"))
        for ifaceName in self.gufw.frontend.get_net_interfaces():
            self.update_iface.append_text(ifaceName)
            self.update_routed.append_text(ifaceName)
            if ifaceName == self.rule_iface:
                iface_num = i + 1
            if ifaceName == self.rule_routed:
                routed_num = i + 1
            i += 1
        self.update_rule_name.set_text(self.rule_description)
        self.update_policy.set_active(self.gufw.POLICY2NUM[self.rule_policy])
        self.update_direction.set_active(DIRECTION2NUM[self.rule_direction])
        self.update_iface.set_active(iface_num)
        self.update_routed.set_active(routed_num)
        self.update_log.set_active(LOGGING2NUM[self.rule_logging])
        self.update_protocol.set_active(PROTO2NUM[self.rule_proto])
    
    def _set_from_port_sensitive(self, value=True):
        self.update_protocol.set_sensitive(value)
        self.update_from_ip.set_sensitive(value)
        self.update_to_ip.set_sensitive(value)
        self.update_to_port.set_sensitive(value)
    
    def _set_to_port_sensitive(self, value=True):
        self.update_protocol.set_sensitive(value)
        self.update_from_ip.set_sensitive(value)
        self.update_to_ip.set_sensitive(value)
        self.update_from_port.set_sensitive(value)
    
    def _set_update_btn_control(self):
        if (':' in self.update_to_port.get_text() or ':' in self.update_from_port.get_text()) and not self.update_protocol.get_active():
            self.update_btn.set_sensitive(False)
            self.update_btn.set_tooltip_text(_("Choose a TCP or UDP Protocol with a range of ports"))
        else:
            self.update_btn.set_sensitive(True)
            self.update_btn.set_tooltip_text('')
    
    def on_update_protocol_changed(self, widget, data=None):
        self._set_update_btn_control()
    
    def on_update_to_port_changed(self, widget, data=None):
        if '/' in self.update_to_port.get_text():
            self._set_to_port_sensitive(False)
        else:
            self._set_to_port_sensitive(True)
        
        self._set_update_btn_control()
    
    def on_update_from_port_changed(self, widget, data=None):
        if '/' in self.update_from_port.get_text():
            self._set_from_port_sensitive(False)
        else:
            self._set_from_port_sensitive(True)
        
        self._set_update_btn_control()
    
    def on_btnUpdateCancel_clicked(self, widget, data=None):
        self.win_update.destroy()
    
    def on_UpdateRule_delete_event(self, widget, data=None):
        self.win_update.destroy()
    
    def on_update_copy_from_IP_clicked(self, widget, data=None):
        self.update_from_ip.set_text(self.gufw.frontend.get_internal_ip())
    
    def on_update_copy_to_IP_clicked(self, widget, data=None):
        self.update_to_ip.set_text(self.gufw.frontend.get_internal_ip())
    
    def on_update_rule_name_icon_press(self, widget, data=None, data2=None):
        self.update_rule_name.set_text('')
    
    def on_update_from_ip_icon_press(self, widget, data=None, data2=None):
        self.update_from_ip.set_text('')
    
    def on_update_to_ip_icon_press(self, widget, data=None, data2=None):
        self.update_to_ip.set_text('')
    
    def on_update_from_port_icon_press(self, widget, data=None, data2=None):
        self.update_from_port.set_text('')
    
    def on_update_to_port_icon_press(self, widget, data=None, data2=None):
        self.update_to_port.set_text('')
    
    def on_update_iface_changed(self, widget, data=None, data2=None):
        # Translators: About the network interfaces in the OS
        if self.update_iface.get_active_text() != _("All Interfaces"):
            self.update_routed.set_sensitive(True)
            self.update_routed.set_tooltip_text(_("The IP/Port will be forward to this interface"))
        else:
            self.update_routed.set_sensitive(False)
            self.update_routed.set_tooltip_text(_("You need to set an Interface for forwarding to this another interface"))
        
        # Not allow same iface when is routed
        if self.gufw.frontend.get_policy('routed') != 'disabled':
            self.update_routed.remove_all()
            # Translators: About traffic
            self.update_routed.append_text(_("Not Forward"))
            for ifaceName in self.gufw.frontend.get_net_interfaces(self.update_iface.get_active_text()):
                self.update_routed.append_text(ifaceName)
            self.update_routed.set_active(0)
    
    def on_btnUpdate_clicked(self, widget, data=None):
        if not self.gufw.validate_rule(self.win_update, self.update_from_ip.get_text(), self.update_from_port.get_text(), self.update_to_ip.get_text(), self.update_to_port.get_text(), '', self.update_routed.get_active_text()):
            return
        
        new_description = self.update_rule_name.get_text()
        new_policy      = self.gufw.NUM2POLICY[self.update_policy.get_active()]
        new_direction   = self.gufw.NUM2DIRECTION[self.update_direction.get_active()]
        new_logging     = self.gufw.NUM2LOGGING[self.update_log.get_active()]
        
        new_proto = ''
        if self.update_protocol.get_sensitive():
            new_proto = self.gufw.NUM2PROTO[self.update_protocol.get_active()]
        
        new_iface = ''
        # Translators: About the network interfaces in the OS
        if self.update_iface.get_sensitive() and self.update_iface.get_active_text() != _("All Interfaces"):
            new_iface = self.update_iface.get_active_text()
        
        new_routed = ''
        # Translators: About traffic
        if self.update_routed.get_sensitive() and self.update_routed.get_active_text() != _("Not Forward"):
            new_routed = self.update_routed.get_active_text()
        
        new_from_ip = new_from_port = new_to_ip = new_to_port = ''
        if self.update_from_ip.get_sensitive():
            new_from_ip = self.update_from_ip.get_text()
        if self.update_from_port.get_sensitive():
            new_from_port = self.update_from_port.get_text()
        if self.update_to_ip.get_sensitive():
            new_to_ip = self.update_to_ip.get_text()
        if self.update_to_port.get_sensitive():
            new_to_port = self.update_to_port.get_text()
        
        if (self.rule_description == new_description and
            self.rule_policy      == new_policy      and
            self.rule_direction   == new_direction   and
            self.rule_proto       == new_proto       and
            self.rule_from_ip     == new_from_ip     and
            self.rule_from_port   == new_from_port   and
            self.rule_to_ip       == new_to_ip       and
            self.rule_to_port     == new_to_port     and
            self.rule_iface       == new_iface       and
            self.rule_routed      == new_routed      and
            self.rule_logging     == new_logging):
            self.warning_box.set_message_type(3)
            self.warning.set_text(_("No changes were made!"))
            return
        
        # Delete the same rules
        same_rules_rows = self._get_same_rules(self.rule_cmd)
        for same_row in same_rules_rows:
            cmd = self.gufw.frontend.delete_rule(same_row)
            self.gufw.add_to_log(_("Editing rule (Removing): ") + new_description + ' | ' + cmd[0] + ' > ' + cmd[1].replace('\n', ' | '))
        
        # Add new
        insert_row = ''
        cmd = self.gufw.frontend.add_rule(new_description, insert_row, new_policy, new_direction, new_iface, new_routed, new_logging, new_proto, new_from_ip, new_from_port, new_to_ip, new_to_port)

        self.gufw.add_to_log(_("Editing rule (Adding): ") + new_description + ' | ' + cmd[1] + ' > ' + cmd[2].replace('\n', ' | '), self.gufw.POLICY2COLOR[new_policy])
        self.gufw.set_statusbar_msg(_("Updated rule ") + str(self.ufw_row))
        
        self.gufw.print_rules(self.gufw.frontend.get_rules())
        self.win_update.destroy()
    
    def _get_same_rules(self, rule_cmd):
        i = 0
        rules_rows = []
        while True:
            try:
                iter_row = self.gufw.rules_model.get_iter(i,)
                cmd = self.gufw.rules_model.get_value(iter_row, 2)
                real_row = self.gufw.rules_model.get_value(iter_row, 14)
                if cmd == rule_cmd:
                    rules_rows.append(real_row)
            except Exception:
                rules_rows = sorted(rules_rows, key=int, reverse=True)
                return rules_rows
            i += 1
