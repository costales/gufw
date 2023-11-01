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

import glob, os
from gufw.model.ufw_backend import Backend

import gettext
from gettext import gettext as _
gettext.textdomain('gufw')


class Firewall():
    """Set or get the Firewall properties"""
    def __init__(self):
        self.backend = Backend()
        
        self.status = self.backend.get_status()
        self.incoming = self.backend.get_policy('incoming')
        self.outgoing = self.backend.get_policy('outgoing')
        self.routed   = self.backend.get_policy('routed')
        self.ufw_logging = self.backend.get_ufw_logging()
        
        self.gufw_logging = True # By default
        if self.get_cfg_value('GufwLogging') == 'no':
            self.gufw_logging = False
        
        self.profile = ''
        self._user_changed_language() # Rename profile files
        self.all_profiles = self._read_all_profiles()
        self.profile = self._read_default_profile()
        
    # PROFILES
    def get_profile(self):
        return self.profile
    
    def set_profile(self, profile):
        operation = []
        # Force show current rules
        if not self.status:
            self.backend.set_status(True)
        # Remove Gufw rules previous profile
        old_rules = self.get_rules(False)
        ind = len(old_rules)
        for old_row in reversed(old_rules):
            if old_row['command']: # It's a gufw rule
                result = self.backend.delete_rule(str(ind))
                line = _("Deleting previous rules: ") + str(ind) + ' ' + result[0] + ' > ' + result[1].replace('\n', ' | ')
                operation.append(line)
            ind -= 1
        
        # Set new profile in cfg file
        self.profile = profile
        self.set_cfg_value('Profile', profile)
        
        # Get new profile
        (new_status, new_incoming, new_outgoing, new_routed, new_rules) = self.backend.get_profile_values(profile)
        
        # Adding Gufw rules in new profile
        for new_row in new_rules:
            if new_row['command']: # It's a gufw rule
                result = self.backend.add_rule('', # Insert in order
                                                new_row['policy'],
                                                new_row['direction'],
                                                new_row['iface'],
                                                new_row['routed'],
                                                new_row['logging'],
                                                new_row['protocol'],
                                                new_row['from_ip'],
                                                new_row['from_port'],
                                                new_row['to_ip'],
                                                new_row['to_port'])
                line = _("Appending new rules: ") + result[0] + ' > ' + result[1].replace('\n', ' | ')
                operation.append(line)
        
        # New status, incoming, outgoing, routed
        self.status   = new_status
        self.incoming = new_incoming
        self.outgoing = new_outgoing
        if new_routed == 'disabled' and self.backend.get_policy('routed') != 'disabled':
            self.routed = self.backend.get_policy('routed')
        else:
            self.routed = new_routed
        
        return operation
    
    def get_all_profiles(self):
        return self.all_profiles
    
    def add_profile(self, profile):
        self.all_profiles.append(profile)
        self.backend.set_profile_values(profile, self.status, self.incoming, self.outgoing, self.routed, []) # Will create profile
    
    def delete_profile(self, profile):
        self.all_profiles.remove(profile)
        self.backend.delete_file_profile(profile)
    
    def rename_profile(self, old, new):
        if old == self.profile:
            return
        self.backend.rename_file_profile(old, new)
        self.all_profiles[self.all_profiles.index(old)] = new
    
    def import_profile(self, profile_file):
        new_profile = os.path.basename(profile_file)
        new_profile = os.path.splitext(new_profile)[0]
        (status, incoming, outgoing, routed, rules) = self.backend.get_profile_values(profile_file)
        self.add_profile(new_profile)
        self.backend.set_profile_values(new_profile, status, incoming, outgoing, routed, rules)
        
    def export_profile(self, profile_file):
        self.backend.export_profile(self.profile, profile_file)
        
    
    # BASIC
    def get_status(self):
        return self.status
    
    def set_status(self, status):
        self.status = status
        self.backend.set_status(status)
        self.backend.set_profile_values(self.profile, status, self.incoming, self.outgoing, self.routed, self.get_rules(not status))
    
    def get_policy(self, policy):
        if policy == 'incoming':
            return self.incoming
        elif policy == 'outgoing':
            return self.outgoing
        elif policy == 'routed':
            if self.backend.get_policy('routed') != 'disabled':
                return self.routed
            else:
                return self.backend.get_policy('routed')
    
    def set_policy(self, policy, value):
        if policy == 'incoming':
            self.incoming = value
            self.backend.set_policy(policy, value)
        elif policy == 'outgoing':
            self.outgoing = value
            self.backend.set_policy(policy, value)
        elif policy == 'routed':
            self.routed = value
            self.backend.set_policy(policy, value)
        
        self.backend.set_profile_values(self.profile, self.status, self.incoming, self.outgoing, self.routed, self.get_rules(True))
    
    def reset(self):
        self.backend.set_profile_values(self.profile, self.status, self.incoming, self.outgoing, self.routed, [])
        self.backend.reset_fw()
    
    # RULES
    def get_rules(self, force_fw_on):
        if self.backend.get_status():
            ufw_rules = self.backend.get_rules()
        else:
            if force_fw_on:
                self.backend.set_status(True)
            ufw_rules = self.backend.get_rules()
            if force_fw_on:
                self.backend.set_status(False)
        profile_rules = self._get_rules_profile()
        return self._compose_rules(ufw_rules, profile_rules)
    
    def get_number_rules(self):
        return self.backend.get_number_rules()
    
    def add_rule(self, description, insert, policy, direction, iface, routed, logging, proto, from_ip, from_port, to_ip, to_port):
        rules_before = self.get_rules(True)
        rules_profile_before = self._get_rules_profile()
        
        cmd = self.backend.add_rule(insert, policy, direction, iface, routed, logging, proto, from_ip, from_port, to_ip, to_port)
        rules_after = self.get_rules(True)
        
        if len(rules_before) != len(rules_after):
            cmd.insert(0, True)
            self._regenerate_file_profile(rules_before, rules_profile_before, rules_after, description, cmd[1], policy, direction, iface, routed, logging, proto, from_ip, from_port, to_ip, to_port)
        else:
            cmd.insert(0, False)
        return cmd # For logging
    
    def delete_rule(self, num):
        rules_before = self.get_rules(True)
        rules_profile_before = self._get_rules_profile()
        result = self.backend.delete_rule(str(num))
        rules_after = self.get_rules(True)
        self._regenerate_file_profile(rules_before, rules_profile_before, rules_after)
        return result # For logging
    
    # LOGGING
    # ufw
    def get_ufw_logging(self):
        return self.ufw_logging

    def set_ufw_logging(self, level):
        self.ufw_logging = level
        self.backend.set_ufw_logging(level)
    
    # Gufw
    def get_logging(self):
        return self.gufw_logging
    
    def set_logging(self, status):
        self.gufw_logging = status
        if status:
            self.set_cfg_value('GufwLogging', 'yes')
        else:
            self.set_cfg_value('GufwLogging', 'no')
    
    def get_log(self):
        return self.backend.get_log()
        
    def add_to_log(self, msg):
        if self.gufw_logging:
            return self.backend.add_to_log(msg)
        return ''
    
    def refresh_log(self):
        self.backend.refresh_log()
    
    
    # LISTENING
    def get_listening_report(self):
        return self.backend.get_listening_report()
    
    
    # CFG FILES
    def get_cfg_value(self, attrib):
        return self.backend.get_cfg_value(attrib)
    
    def set_cfg_value(self, attrib, value):
        self.backend.set_cfg_value(attrib, value)
    
    
    # NET
    def get_internal_ip(self):
        return self.backend.get_net_ip()
    
    def get_net_interfaces(self, exclude_iface=''):
        all_faces = self.backend.get_net_interfaces()
        
        if exclude_iface:
            try:
                all_faces.remove(exclude_iface)
            except Exception:
                pass
        
        return all_faces
    
    # STUFF
    def _read_default_profile(self):
        default_profile = self.get_cfg_value('Profile')
        # Just be sure
        if not default_profile:
            default_profile = _("Home")
        # Error in config file? > Regenerate
        if default_profile and (not default_profile in self.all_profiles):
            self.backend.set_profile_values(default_profile, self.status, self.incoming, self.outgoing, self.routed, [])
            self.all_profiles.append(default_profile)

        return default_profile
    
    def _read_all_profiles(self):
        profiles = []
        while not profiles:
            files = glob.glob('/etc/gufw/*.profile')
            files.sort(key=lambda x: os.path.getctime(x)) # Sort by time and date
            
            for profile in files:
                profiles.append(os.path.splitext(os.path.basename(profile))[0].replace(' ', '_')) # Filename without path and extension
            
            if not profiles: # First run
                self.backend.set_profile_values(_("Public").replace(' ', '_'), True, 'reject',  'allow', 'allow', [])
                self.backend.set_profile_values(_("Office").replace(' ', '_'), True, 'deny',    'allow', 'allow', [])
                self.backend.set_profile_values(_("Home").replace(' ', '_'), self.status, self.incoming, self.outgoing, self.routed, [])
                self.set_cfg_value('Profile', _("Home").replace(' ', '_'))
        
        return profiles
    
    def _user_changed_language(self):
        # Rename profiles file
        profiles = []
        default_profile = self.get_cfg_value('Profile')
        files = glob.glob('/etc/gufw/*.profile')
        files.sort(key=lambda x: os.path.getctime(x)) # Sort by time and date
        
        for profile in files:
            profiles.append(_(os.path.splitext(os.path.basename(profile))[0]).replace(' ', '_')) # Filename without path and extension
        
        for profile in profiles:
            if profile == _("Home") and profile != 'Home':
                self.backend.rename_file_profile('Home', _("Home"))
                self.add_to_log(_("Renamed profile: ") + 'Home' + " > " + _("Home"))
                if default_profile == 'Home':
                    self.set_cfg_value('Profile', _("Home"))
            if profile == _("Office") and profile != 'Office':
                self.backend.rename_file_profile('Office', _("Office"))
                self.add_to_log(_("Renamed profile: ") + 'Office' + " > " + _("Office"))
                if default_profile == 'Office':
                    self.set_cfg_value('Profile', _("Office"))
            if profile == _("Public") and profile != 'Public':
                self.backend.rename_file_profile('Public', _("Public"))
                self.add_to_log(_("Renamed profile: ") + 'Public' + " > " + _("Public"))
                if default_profile == 'Public':
                    self.set_cfg_value('Profile', _("Public"))
    
    def _compose_rules(self, ufw_rules, profile_rules):
        rules = []
        for ufw_rule in ufw_rules:
            rule = {'ufw_rule'   : ufw_rule, # ufw rule
                    'description': '', # description
                    'command'    : '', # command
                    'policy'     : '', # policy
                    'direction'  : '', # direction
                    'protocol'   : '', # proto
                    'from_ip'    : '', # from_ip
                    'from_port'  : '', # from_port
                    'to_ip'      : '', # to_ip
                    'to_port'    : '', # to_port
                    'iface'      : '', # iface
                    'routed'     : '', # routed
                    'logging'    : ''} # logging
            
            for profile_rule in profile_rules:
                if ufw_rule == profile_rule['ufw_rule']:
                    rule = {'ufw_rule'    : profile_rule['ufw_rule'],    # ufw rule
                            'description' : profile_rule['description'], # description
                            'command'     : profile_rule['command'],     # command
                            'policy'      : profile_rule['policy'],      # policy
                            'direction'   : profile_rule['direction'],   # direction
                            'protocol'    : profile_rule['protocol'],    # proto
                            'from_ip'     : profile_rule['from_ip'],     # from_ip
                            'from_port'   : profile_rule['from_port'],   # from_port
                            'to_ip'       : profile_rule['to_ip'],       # to_ip
                            'to_port'     : profile_rule['to_port'],     # to_port
                            'iface'       : profile_rule['iface'],       # iface
                            'routed'      : profile_rule['routed'],      # routed
                            'logging'     : profile_rule['logging']}     # logging
                    break
            
            rules.append(rule)
            
        return rules
    
    def _get_rules_profile(self):
        rules_profile = []
        (status, incoming, outgoing, routed, rules) = self.backend.get_profile_values(self.profile)
        for rule in rules:
            conver_rules = {'ufw_rule'    : rule['ufw_rule'],
                            'description' : rule['description'],
                            'command'     : rule['command'],
                            'policy'      : rule['policy'],
                            'direction'   : rule['direction'],
                            'protocol'    : rule['protocol'],
                            'from_ip'     : rule['from_ip'],
                            'from_port'   : rule['from_port'],
                            'to_ip'       : rule['to_ip'],
                            'to_port'     : rule['to_port'],
                            'iface'       : rule['iface'],
                            'routed'      : rule['routed'],
                            'logging'     : rule['logging']}
            rules_profile.append(conver_rules)
        
        return rules_profile
        
    def _regenerate_file_profile(self, ufw_before, profile_before, ufw_after, description='', cmd='', policy='', direction='', iface='', routed='', logging='', proto='', from_ip='', from_port='', to_ip='', to_port=''):
        """Here there are dragons!"""
        final_rules = []            
        # Operation ufw_before  ufw_after   profile_before  profile_after
        #     +         A         A+B             A               A+B   <-- A completed from profile_before | B completed from parameters
        #     -        A+B         A             A+B               A    
        #     x        A+B        A+C            A+B              A+C   <-- A completed from profile_before | C completed from parameters
        # We have here profile_before + ufw_after + parameters > Just complete!
        for ufw_rule in ufw_after:
            found = False
            for profile_rule in profile_before:
                if ufw_rule['ufw_rule'] == profile_rule['ufw_rule']: # Complete from previous profile
                    found = True
                    new_rule = {'ufw_rule'    : profile_rule['ufw_rule'],
                                'description' : profile_rule['description'],
                                'command'     : profile_rule['command'],
                                'policy'      : profile_rule['policy'],
                                'direction'   : profile_rule['direction'],
                                'protocol'    : profile_rule['protocol'],
                                'from_ip'     : profile_rule['from_ip'],
                                'from_port'   : profile_rule['from_port'],
                                'to_ip'       : profile_rule['to_ip'],
                                'to_port'     : profile_rule['to_port'],
                                'iface'       : profile_rule['iface'],
                                'routed'      : profile_rule['routed'],
                                'logging'     : profile_rule['logging']}
            if not found:
                if ufw_before.count(ufw_rule) == 0: # New: Complete from parameters
                    new_rule = {'ufw_rule'    : ufw_rule['ufw_rule'],
                                'description' : description,
                                'command'     : cmd,
                                'policy'      : policy,
                                'direction'   : direction,
                                'protocol'    : proto,
                                'from_ip'     : from_ip,
                                'from_port'   : from_port,
                                'to_ip'       : to_ip,
                                'to_port'     : to_port,
                                'iface'       : iface,
                                'routed'      : routed,
                                'logging'     : logging}
                else: # Old ufw rule: Nothing
                    continue
                    
            final_rules.append(new_rule) # Just adding rules, a regenerate will be update the rules
        
        self.backend.set_profile_values(self.profile, self.status, self.incoming, self.outgoing, self.routed, final_rules)
