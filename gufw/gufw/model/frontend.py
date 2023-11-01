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

from gufw.model.firewall import Firewall


class Frontend():
    def __init__(self):
        self.firewall = Firewall()
    
    
    # PROFILE
    def get_profile(self):
        return self.firewall.get_profile()
    
    def set_profile(self, profile):
        return self.firewall.set_profile(profile)
    
    def get_all_profiles(self):
        return self.firewall.get_all_profiles()
    
    def add_profile(self, profile):
        self.firewall.add_profile(profile)
    
    def delete_profile(self, profile):
        self.firewall.delete_profile(profile)
    
    def rename_profile(self, old_name, new_name):
        self.firewall.rename_profile(old_name, new_name)
    
    def import_profile(self, profile_file):
        self.firewall.import_profile(profile_file)
    
    def export_profile(self, profile_file):
        self.firewall.export_profile(profile_file)
    
    # FIREWALL > For current profile!
    def get_status(self):
        return self.firewall.get_status()
    
    def set_status(self, status):
        self.firewall.set_status(status)
    
    def get_policy(self, policy):
        return self.firewall.get_policy(policy)
    
    def set_policy(self, policy, value):
        self.firewall.set_policy(policy, value)
    
    def reset(self):
        self.firewall.reset()
    
    
    # RULES > For current profile!
    def get_rules(self, force_fw_on=True):
        return self.firewall.get_rules(force_fw_on)
    
    def get_number_rules(self):
        return self.firewall.get_number_rules()
    
    def add_rule(self, description, insert='', policy='', direction='', iface='', routed='', logging='', proto='', from_ip='', from_port='', to_ip='', to_port=''):
        return self.firewall.add_rule(description, insert, policy, direction, iface, routed, logging, proto, from_ip, from_port, to_ip, to_port)
    
    def delete_rule(self, num):
        return self.firewall.delete_rule(num)
    
    
    
    # LOGGING
    # ufw LOGGING
    def get_ufw_logging(self):
        return self.firewall.get_ufw_logging()
    
    def set_ufw_logging(self, level):
        self.firewall.set_ufw_logging(level)
    
    # Gufw LOGGING
    def get_logging(self):
        return self.firewall.get_logging()
    
    def set_logging(self, status):
        self.firewall.set_logging(status)
    
    def get_log(self):
        return self.firewall.get_log()
    
    def add_to_log(self, msg):
        return self.firewall.add_to_log(msg)
    
    def refresh_log(self):
        self.firewall.refresh_log()
    
    
    
    # LISTENING REPORT
    def get_listening_report(self):
        return self.firewall.get_listening_report()
    
    
    
    # GUI needs
    def get_config_value(self, attrib):
        return self.firewall.get_cfg_value(attrib)
    
    def set_config_value(self, attrib, value):
        self.firewall.set_cfg_value(attrib, value)
    
    def get_internal_ip(self):
        return self.firewall.get_internal_ip()
    
    def get_net_interfaces(self, exclude_iface=''):
        return self.firewall.get_net_interfaces(exclude_iface)
