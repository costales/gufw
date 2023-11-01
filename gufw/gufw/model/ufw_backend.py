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

import time, os, shutil, subprocess, configparser


class Backend():
    UFW_PATH    = '/usr/sbin/ufw'
    UFW_DEFAULT = '/etc/default/ufw'
    UFW_CONF    = '/etc/ufw/ufw.conf'
    UFW_SYSCTL  = '/etc/ufw/sysctl.conf'
    GUFW_PATH   = '/etc/gufw'
    GUFW_CFG    = '/etc/gufw/gufw.cfg'
    GUFW_LOG    = '/var/log/gufw.log'
    
    def __init__(self):
        pass
    
    def _run_cmd(self, cmd, lang_c=False):
        if lang_c:
            proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={'LANG':'C'})
        else:
            proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr=proc.communicate()
        
        if stderr and not stderr.decode().startswith("WARN") and not stderr.decode().startswith("DEBUG"): # Error
            while stderr[-1:] == '\n':
                stderr = stderr[:-1]
            return stderr.decode('utf-8')
        else: # OK
            while stdout[-1:] == '\n':
                stdout = stdout[:-1]
            return stdout.decode('utf-8')
    
    def get_status(self):
        if 'Status: active' in self._run_cmd([self.UFW_PATH, 'status'], True):
            return True
        else:
            return False
    
    def get_policy(self, policy):
        if policy == 'incoming':
            ufw_default_incoming = self._run_cmd(['grep', 'DEFAULT_INPUT_POLICY', self.UFW_DEFAULT])
            if 'ACCEPT' in ufw_default_incoming:
                return 'allow'
            elif 'DROP' in ufw_default_incoming:
                return 'deny'
            elif 'REJECT' in ufw_default_incoming:
                return 'reject'
        
        elif policy == 'outgoing':
            ufw_default_outgoing = self._run_cmd(['grep', 'DEFAULT_OUTPUT_POLICY', self.UFW_DEFAULT])
            if 'ACCEPT' in ufw_default_outgoing:
                return 'allow'
            elif 'DROP' in ufw_default_outgoing:
                return 'deny'
            elif 'REJECT' in ufw_default_outgoing:
                return 'reject'
        
        elif policy == 'routed':
            ufw_default_outgoing = self._run_cmd(['grep', 'net/ipv4/ip_forward=', self.UFW_SYSCTL])
            routed_status = ufw_default_outgoing.replace(" ", "")
            if "#net/ipv4/ip_forward=1" in routed_status:
                return 'disabled'
            
            ufw_default_outgoing = self._run_cmd(['grep', 'DEFAULT_FORWARD_POLICY', self.UFW_DEFAULT])
            if 'ACCEPT' in ufw_default_outgoing:
                return 'allow'
            elif 'DROP' in ufw_default_outgoing:
                return 'deny'
            elif 'REJECT' in ufw_default_outgoing:
                return 'reject'
    
    def get_ufw_logging(self):
        ufw_cmd = self._run_cmd(['cat', self.UFW_CONF])
        if 'LOGLEVEL=full' in ufw_cmd:
            return 'full'
        elif 'LOGLEVEL=high' in ufw_cmd:
            return 'high'
        elif 'LOGLEVEL=medium' in ufw_cmd:
            return 'medium'
        elif 'LOGLEVEL=low' in ufw_cmd:
            return 'low'
        else:
            return 'off'
    
    def set_status(self, status):
        if not status:
            cmd = [self.UFW_PATH, 'disable']
        else:
            cmd = [self.UFW_PATH, '--force', 'enable']
        
        self._run_cmd(cmd)
    
    def set_policy(self, policy, value):
        if policy == 'incoming':
            if value == 'allow':
                cmd = [self.UFW_PATH, 'default', 'allow', 'incoming']
            elif value == 'deny':
                cmd = [self.UFW_PATH, 'default', 'deny', 'incoming']
            elif value == 'reject':
                cmd = [self.UFW_PATH, 'default', 'reject', 'incoming']
        
        elif policy == 'outgoing':
            if value == 'allow':
                cmd = [self.UFW_PATH, 'default', 'allow', 'outgoing']
            elif value == 'deny':
                cmd = [self.UFW_PATH, 'default', 'deny', 'outgoing']
            elif value == 'reject':
                cmd = [self.UFW_PATH, 'default', 'reject', 'outgoing']
        
        elif policy == 'routed':
            if value == 'allow':
                cmd = [self.UFW_PATH, 'default', 'allow', 'routed']
            elif value == 'deny':
                cmd = [self.UFW_PATH, 'default', 'deny', 'routed']
            elif value == 'reject':
                cmd = [self.UFW_PATH, 'default', 'reject', 'routed']
        
        if cmd:
            self._run_cmd(cmd)
    
    def set_ufw_logging(self, logging):
        if logging == 'off':
            cmd = [self.UFW_PATH, 'logging', 'off']
        elif logging == 'low':
            cmd = [self.UFW_PATH, 'logging', 'low']
        elif logging == 'medium':
            cmd = [self.UFW_PATH, 'logging', 'medium']
        elif logging == 'high':
            cmd = [self.UFW_PATH, 'logging', 'high']
        elif logging == 'full':
            cmd = [self.UFW_PATH, 'logging', 'full']
        
        if cmd:
            self._run_cmd(cmd)
    
    def reset_fw(self):
        cmd = [self.UFW_PATH, '--force', 'reset']
        self._run_cmd(cmd, True)
    
    def get_cfg_value(self, attribute):
        cfg = configparser.ConfigParser()
        try:
            if not cfg.read([self.GUFW_CFG]):
                return ''
        except Exception:
            os.remove(self.GUFW_CFG)
            return ''
        
        if not cfg.has_option('GufwConfiguration', attribute):
            return ''
            
        return cfg.get('GufwConfiguration', attribute)
    
    def set_cfg_value(self, attr, value):
        cfg_file = self.GUFW_CFG
        if not os.path.isfile(cfg_file):
            f = open(cfg_file, 'w')
            cfg = configparser.ConfigParser()
            cfg.add_section("GufwConfiguration")
            cfg.write(f)  
            f.close()  
            os.chmod(cfg_file, 0o600) # Just an admin can read this file
        
        cfg = configparser.ConfigParser()
        cfg.read(cfg_file)
        cfg.set('GufwConfiguration', attr, str(value))
        f = open(cfg_file, 'w')
        cfg.write(f)  
        f.close()
    
    def set_profile_values(self, profile, status, incoming, outgoing, routed, rules):
        if not os.path.exists(self.GUFW_PATH):
            os.makedirs(self.GUFW_PATH)
        
        file_name = profile + '.profile'
        file_path = os.path.join(self.GUFW_PATH, file_name)
        
        cfg = configparser.ConfigParser()
        
        cfg.add_section("fwBasic")
        if status:
            cfg.set('fwBasic', 'status', 'enabled')
        else:
            cfg.set('fwBasic', 'status', 'disabled')
        cfg.set('fwBasic', 'incoming', incoming)
        cfg.set('fwBasic', 'outgoing', outgoing)
        cfg.set('fwBasic', 'routed',   routed)
        
        i = 0
        for rule in rules:
            if not rule['command']:
                continue
            section = 'Rule' + str(i)
            cfg.add_section(section)
            cfg.set(section, 'ufw_rule',    rule['ufw_rule'])
            cfg.set(section, 'description', rule['description'])
            cfg.set(section, 'command',     rule['command'])
            cfg.set(section, 'policy',      rule['policy'])
            cfg.set(section, 'direction',   rule['direction']) 
            cfg.set(section, 'protocol',    rule['protocol']) 
            cfg.set(section, 'from_ip',     rule['from_ip']) 
            cfg.set(section, 'from_port',   rule['from_port']) 
            cfg.set(section, 'to_ip',       rule['to_ip']) 
            cfg.set(section, 'to_port',     rule['to_port']) 
            cfg.set(section, 'iface',       rule['iface']) 
            cfg.set(section, 'routed',      rule['routed']) 
            cfg.set(section, 'logging',     rule['logging'] )
            i += 1
        
        f = open(file_path, 'w')
        cfg.write(f)  
        f.close()
        os.chmod(file_path, 0o600) # Just an admin can read this file
    
    def get_profile_values(self, profile):
        status = False
        incoming = ''
        outgoing = ''
        routed = ''
        rules = []
        
        if profile[:1] == '/':
            file_path = profile
        else:
            file_name = profile + '.profile'
            file_path = os.path.join('/etc', 'gufw', file_name)
        
        cfg = configparser.ConfigParser()
        if not cfg.read([file_path]):
            return (status, incoming, outgoing, routed, rules)
        
        if not cfg.has_section('fwBasic'):
            return (status, incoming, outgoing, routed, rules)
        
        for section in cfg.sections():
            
            if section == 'fwBasic':
                if cfg.get('fwBasic', 'status') == 'disabled':
                    status = False
                else:
                    status = True
                incoming = cfg.get('fwBasic', 'incoming')
                outgoing = cfg.get('fwBasic', 'outgoing')
                # Previous Gufw profiles
                try:
                    routed = cfg.get('fwBasic', 'routed')
                except configparser.NoOptionError:
                    routed = self.get_policy('routed')
                
            
            else:
                rule = {'ufw_rule'   : cfg.get(section, 'ufw_rule'), 
                        'description': cfg.get(section, 'description'),
                        'command'    : cfg.get(section, 'command'),
                        'policy'     : cfg.get(section, 'policy'),
                        'direction'  : cfg.get(section, 'direction'),
                        'protocol'   : cfg.get(section, 'protocol'),
                        'from_ip'    : cfg.get(section, 'from_ip'),
                        'from_port'  : cfg.get(section, 'from_port'),
                        'to_ip'      : cfg.get(section, 'to_ip'),
                        'to_port'    : cfg.get(section, 'to_port'),
                        'iface'      : cfg.get(section, 'iface'),
                        'logging'    : cfg.get(section, 'logging')}
                # Previous Gufw profiles
                try:
                    rule['routed'] = cfg.get(section, 'routed')
                except configparser.NoOptionError:
                    rule['routed'] = ''
                rules.append(rule)
        
        return (status, incoming, outgoing, routed, rules)
    
    
    def delete_file_profile(self, profile):
        dst = os.path.join(self.GUFW_PATH, profile + '.profile')
        try:
            os.remove(dst)
        except Exception:
            pass
    
    def rename_file_profile(self, old, new):
        src = os.path.join(self.GUFW_PATH, old + '.profile')
        dst = os.path.join(self.GUFW_PATH, new + '.profile')
        
        if os.path.isfile(dst): # User could import a profile with same English name > It's OK
            return
        print('renaming '+src+' a '+dst)
        try:
            os.rename(src, dst)
        except Exception:
            pass
    
    def export_profile(self, profile, dst):
        src = os.path.join(self.GUFW_PATH, profile + '.profile')
        try:
            shutil.copyfile(src, dst)
            os.chmod(dst, 0o600) # Avoid other users change a profile
        except Exception:
            pass
    
    def refresh_log(self):
        f = open(self.GUFW_LOG, 'w')
        f.close()
    
    def add_to_log(self, msg):
        try:
            f = open(self.GUFW_LOG, 'r')
            log = f.readlines()
            f.close()
        except Exception:
            log = ''
        
        new_line = '[' + time.strftime('%x %X') + '] ' + msg
        if log:
            new_line = new_line + '\n'
        
        f = open(self.GUFW_LOG, 'w')
        f.write(new_line)
        f.writelines(log)
        f.close()
        
        return new_line

    def get_log(self):
        if not os.path.isfile(self.GUFW_LOG):
            return ''
        
        cmd = self._run_cmd(['cat', self.GUFW_LOG])
        if not cmd:
            return ''
        
        return cmd
    
    def get_rules(self):
        rules = self._run_cmd([self.UFW_PATH, 'status', 'numbered'], True)
        lines = rules.split('\n')
        return_rules = []
        
        for line in lines:
            if line and 'ALLOW' in line or 'DENY' in line or 'LIMIT' in line or 'REJECT' in line:
                rule = line.split('] ')
                return_rules.append(' '.join(rule[1].split()))
        
        return return_rules
    
    def get_number_rules(self):
        numb = 0
        rules = self._run_cmd([self.UFW_PATH, 'status', 'numbered'], True)
        lines = rules.split('\n')
        return_rules = []
        
        for line in lines:
            if line and 'ALLOW' in line or 'DENY' in line or 'LIMIT' in line or 'REJECT' in line:
                numb = numb + 1
        
        return numb
    
    def add_rule(self, insert, policy, direction, iface, routed, logging, proto, from_ip, from_port, to_ip, to_port):
        # ufw [route] [insert NUM] allow|deny|reject|limit [in|out on INTERFACE] [log|log-all] [proto protocol] [from ADDRESS [port PORT]] [to ADDRESS [port PORT]]
        cmd_rule = [self.UFW_PATH]
        
        # route
        if routed:
            cmd_rule.append('route')
        
        # Insert Number
        if insert:
            cmd_rule.extend(['insert', str(int(insert))])
        
        # Policy
        cmd_rule.append(policy)
        
        # Direction
        cmd_rule.append(direction)
        
        # Interface
        if iface:
            cmd_rule.extend(['on', iface])
        
        # Routed on
        if routed:
            if direction == 'in':
                cmd_rule.extend(['out', 'on', routed])
            else:
                cmd_rule.extend(['in', 'on', routed])
        
        # Logging
        if logging:
            cmd_rule.append(logging)
        
        # Proto
        if '/tcp' in from_port or '/tcp' in to_port:
            cmd_rule.extend(['proto', 'tcp'])
        elif '/udp' in from_port or '/udp' in to_port:
            cmd_rule.extend(['proto', 'udp'])
        elif proto:
            cmd_rule.extend(['proto', proto])
        
        # From IP
        if not from_ip:
            cmd_rule.extend(['from', 'any'])
        else:
            cmd_rule.extend(['from', from_ip])
        # From Port
        if from_port:
            if '/tcp' in from_port:
                from_port = from_port.replace('/tcp', '')
            if '/udp' in from_port:
                from_port = from_port.replace('/udp', '')
            cmd_rule.extend(['port', from_port])
        
        # To IP
        if not to_ip:
            cmd_rule.extend(['to', 'any'])
        else:
            cmd_rule.extend(['to', to_ip])
        # To Port
        if to_port:
            if '/tcp' in to_port:
                to_port = to_port.replace('/tcp', '')
            if '/udp' in to_port:
                to_port = to_port.replace('/udp', '')
            cmd_rule.extend(['port', to_port])
        
        # Launch
        cmd = self._run_cmd(cmd_rule, True)
        
        result = []
        result.append(' '.join(cmd_rule))
        result.append(cmd)
        
        return result # cmd | ufw result
    
    def delete_rule(self, num):
        delete_rule = [self.UFW_PATH, '--force', 'delete', str(num)]
        cmd = self._run_cmd(delete_rule)
        
        result = []
        result.append(' '.join(delete_rule))
        result.append(cmd)
        
        return result # cmd | ufw result
    
    def get_net_interfaces(self):
        cmd_ifaces = ['ls', '/sys/class/net']
        cmd = self._run_cmd(cmd_ifaces)
        ifaces = cmd.split('\n')
        
        result = []
        for iface in ifaces:
            if iface:
                result.append(iface)
        
        return result
    
    def get_net_ip(self):
        cmd_ip = ['hostname', '--all-ip-addresses']
        cmd = self._run_cmd(cmd_ip)
        ips = cmd.split('\n')
        
        if len(ips) > 0:
            return ips[0].strip()
        else:
            return '127.0.0.1'
    
    def get_listening_report(self):
        return_report = []
        actual_protocol = 'None'
        ufw_report = self._run_cmd([self.UFW_PATH, 'show', 'listening'], True)
        report_lines = ufw_report.replace('\n   [', '%')
        report_lines = report_lines.split('\n')
        
        for descomponent_report in report_lines:
            # Set actual protocol
            if not descomponent_report:
                continue
            if 'tcp6:' in descomponent_report:
                actual_protocol = 'TCP6'
                continue
            if 'tcp:' in descomponent_report:
                actual_protocol = 'TCP'
                continue
            if 'udp6:' in descomponent_report:
                actual_protocol = 'UDP6'
                continue
            if 'udp:' in descomponent_report:
                actual_protocol = 'UDP'
                continue
            
            policy = 'None'
            descomponent_report = descomponent_report.strip()
            descomponent_report = descomponent_report.replace('(', '')
            descomponent_report = descomponent_report.replace(')', '')
            
            if ']' in descomponent_report:
                descomponent_policy = descomponent_report.split(']')
                if 'allow' in descomponent_policy[1]:
                    policy = 'allow'
                elif 'deny' in descomponent_policy[1]:
                    policy = 'deny'
                elif 'reject' in descomponent_policy[1]:
                    policy = 'reject'
                elif 'limit' in descomponent_policy[1]:
                    policy = 'limit'
            
            descomponent_report = descomponent_report.split('%')
            descomponent_fields = descomponent_report[0].split(' ')
            # Order: protocol % port % address % application % policy
            return_report.append('%'.join([actual_protocol, descomponent_fields[0], descomponent_fields[1], descomponent_fields[2], policy]))
        
        return return_report
