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
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, WebKit2
from string import Template

import os, re, sys, subprocess, platform

import gettext
from gettext import gettext as _
gettext.textdomain('gufw')

from gufw.view.preferences import Preferences
from gufw.view.add         import Add
from gufw.view.update      import Update
from gufw.view.listening   import ListeningReport
from gufw.view.about       import About


class Gufw:
    GRAY   = '#BAB5AB'
    GREEN  = '#267726'
    RED    = '#DF421E'
    ORANGE = '#D1940C'
    BLUE   = '#314E6C'
    BLACK  = '#000000'

    POLICY2NUM = {'allow': 0,
                  'deny': 1,
                  'reject': 2,
                  'limit': 3,
                  'disabled': 4 }
    POLICY2COLOR = {'allow': RED,
                    'deny': GREEN,
                    'reject': BLUE,
                    'limit': ORANGE,
                    'disabled': GRAY,
                    'others': BLACK}
                     
    NUM2POLICY = {0: 'allow',
                  1: 'deny',
                  2: 'reject',
                  3: 'limit' }
    NUM2DIRECTION = {0: 'in',
                     1: 'out',
                     2: 'both'}
    NUM2PROTO = {0: '',
                 1: 'tcp',
                 2: 'udp' }
    NUM2LOGGING = {0: '',
                   1: 'log',
                   2: 'log-all'}

    def __init__(self, frontend):
        self.frontend = frontend
        
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('gufw')
        self.builder.add_from_file('/usr/share/gufw/ui/gufw.ui')
        
        self._set_objects_name()
        self._set_initial_values()
        self.winadd = Add(self)
        
        self.builder.connect_signals(self)
        
        Gtk.main()
    
    def _set_objects_name(self):
        self.winMain = self.builder.get_object('main')
        
        self.profile      = self.builder.get_object('profile')
        self.switchStatus = self.builder.get_object('switchStatus')
        self.incoming     = self.builder.get_object('incoming')
        self.outgoing     = self.builder.get_object('outgoing')
        self.routed_lbl   = self.builder.get_object('routed_lbl')
        self.box_routed   = self.builder.get_object('box_routed')
        self.routed       = self.builder.get_object('routed')
        self.shield       = self.builder.get_object('shield')
        
        self.rules_box       = self.builder.get_object('boxRules')
        self.rules           = self.builder.get_object('Rules')
        self.show_add_btn    = self.builder.get_object('btnAddRule')
        self.detele_rule_btn = self.builder.get_object('btnDeleteRule')
        self.edit_rule_btn   = self.builder.get_object('btnEditRule')
        
        self.report_box      = self.builder.get_object('boxReport')
        self.report          = self.builder.get_object('Report')
        self.report_rule_btn = self.builder.get_object('btnReportRule')
        self.report_waiting  = self.builder.get_object('report_waiting')
        
        self.log_box      = self.builder.get_object('boxLog')
        self.log          = self.builder.get_object('log')
        self.log_txt      = self.log.get_buffer()
        self.log_copy     = self.builder.get_object('btnLogCopy')
        self.log_delete   = self.builder.get_object('btnLogCopy')
        
        self.web = self.builder.get_object('boxWeb')
        self.web_content = WebKit2.WebView()
        self.web_content.connect('context-menu', self.context_menu_cb)

        settings = self.web_content.get_settings()
        self.web_content.set_settings(settings)
        self.web.add(self.web_content)
        # For ORCA
        self.tuto_label = Gtk.Label()
        self.tuto_label.set_text(_("Getting started"))
        self.tuto_label.set_mnemonic_widget(self.web)
        
        settings = self.web_content.get_settings()
        settings.set_property('enable-caret-browsing', True)
        
        self.statusbar = self.builder.get_object('statusmsg')
        self.progress  = self.builder.get_object('progress')
        
        # Rules
        self.rules_model = Gtk.ListStore(str,  # 0  ufw rule
                                          str,  # 1  description
                                          str,  # 2  command
                                          str,  # 3  policy
                                          str,  # 4  direction
                                          str,  # 5  proto
                                          str,  # 6  from_ip
                                          str,  # 7  from_port
                                          str,  # 8  to_ip
                                          str,  # 9  to_port
                                          str,  # 10 iface
                                          str,  # 11 routed
                                          str,  # 12 logging
                                          str,  # 13 color
                                          int)  # 14 number (for deleting and updating)
        self.tv_rules = self.rules
        self.tv_rules.set_model(self.rules_model)
        self.tv_rules.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        
        # Listening report
        self.listening_model = Gtk.ListStore(str, # 0  protocol
                                             int, # 1 port
                                             str, # 2 address
                                             str, # 3 app
                                             str, # 4 color
                                             int) # 5 number
        self.tv_report = self.report
        self.tv_report.set_model(self.listening_model)
        self.tv_report.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        
        self.txt_tag_green  = self.log_txt.create_tag('color_green',    foreground=self.GREEN)
        self.txt_tag_red    = self.log_txt.create_tag('color_red',      foreground=self.RED)
        self.txt_tag_orange = self.log_txt.create_tag('colored_orange', foreground=self.ORANGE)
        self.txt_tag_blue   = self.log_txt.create_tag('colored_blue',   foreground=self.BLUE)
        self.txt_tag_gray   = self.log_txt.create_tag('colored_gray',   foreground=self.GRAY)
        self.txt_tag_black  = self.log_txt.create_tag('colored_black',  foreground=self.BLACK)
        
        self.btn_report_pause = self.builder.get_object('btnReportPause')
        self.btn_report_play  = self.builder.get_object('btnReportPlay')
        
        # Stack init
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(700)
        # Stack 1 = Tutorial
        vbox_home = Gtk.Box()
        self.viewport_home  = self.builder.get_object('viewport_home')
        self.viewport_home.reparent(vbox_home)
        stack.add_titled(vbox_home, "tutorial", _("Getting started"))
        stack.child_set_property(vbox_home, "icon-name", "go-home") # Set icon
        # Stack 2 = Rules
        vbox_rules = Gtk.Box()
        self.viewport_rules  = self.builder.get_object('viewport_rules')
        self.viewport_rules.reparent(vbox_rules)
        stack.add_titled(vbox_rules, "rules", _("Rules"))
        # Stack 3 = Report
        vbox_report = Gtk.Box()
        self.viewport_report  = self.builder.get_object('viewport_report')
        self.viewport_report.reparent(vbox_report)
        stack.add_titled(vbox_report, "report", _("Report"))
        # Stack 4 = Log
        vbox_log = Gtk.Box()
        self.viewport_log  = self.builder.get_object('viewport_log')
        self.viewport_log.reparent(vbox_log)
        # Translators: Noun
        stack.add_titled(vbox_log, "log", _("Log"))
        # Stack Compose
        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        # Horizontal center in 1st row
        vbox_1row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        aspect1 = Gtk.Alignment()
        aspect2 = Gtk.Alignment()
        vbox_1row.pack_start(aspect1, True, True, 0)
        vbox_1row.pack_start(stack_switcher, False, False, 0)
        vbox_1row.pack_start(aspect2, True, True, 0)
        # Pack
        self.stack_vbox = self.builder.get_object('stack_vbox')
        self.stack_vbox.pack_start(vbox_1row, False, True, 0)
        self.stack_vbox.pack_end(stack, True, True, 0)
    
    def _set_initial_values(self):
        for profile in self.frontend.get_all_profiles():
            self.profile.append_text(profile)
        self.profile.set_active(self.frontend.get_all_profiles().index(self.frontend.get_profile()))
        
        self.switchStatus.set_active(self.frontend.get_status())
        
        self.incoming.set_active(self.POLICY2NUM[self.frontend.get_policy('incoming')])
        self.outgoing.set_active(self.POLICY2NUM[self.frontend.get_policy('outgoing')])
        self.routed.set_active(self.POLICY2NUM[self.frontend.get_policy('routed')])
        self.incoming.set_sensitive(self.frontend.get_status())
        self.outgoing.set_sensitive(self.frontend.get_status())
        self.routed.set_sensitive(self.frontend.get_status())
        self.show_add_btn.set_sensitive(self.frontend.get_status())
        self.detele_rule_btn.set_sensitive(self.frontend.get_status())
        self.edit_rule_btn.set_sensitive(self.frontend.get_status())
        self.report_rule_btn.set_sensitive(self.frontend.get_status())
        
        render_txt = Gtk.CellRendererText()
        
        # Rules
        # Translators: Number of  rule
        tree_header = Gtk.TreeViewColumn(_("Nº"), render_txt, text=14, foreground=13)
        tree_header.set_resizable(True)
        tree_header.set_sort_column_id(14)
        tree_header.set_sizing(1)
        self.tv_rules.append_column(tree_header)
        # Translators: Of rule
        tree_header = Gtk.TreeViewColumn(_("Rule"), render_txt, text=0, foreground=13)
        tree_header.set_resizable(True)
        tree_header.set_sort_column_id(0)
        tree_header.set_sizing(1)
        self.tv_rules.append_column(tree_header)
        # Translators: Of rule
        tree_header = Gtk.TreeViewColumn(_("Name"), render_txt, text=1, foreground=13)
        tree_header.set_resizable(True)
        tree_header.set_sort_column_id(1)
        tree_header.set_sizing(1)
        self.tv_rules.append_column(tree_header)
        
        # Listening Report
        # Translators: Number of  rule
        tree_header = Gtk.TreeViewColumn(_("Nº"), render_txt, text=5, foreground=4)
        tree_header.set_resizable(True)
        tree_header.set_sort_column_id(5)
        tree_header.set_sizing(1)
        self.tv_report.append_column (tree_header)
        tree_header = Gtk.TreeViewColumn(_("Protocol"), render_txt, text=0, foreground=4)
        tree_header.set_resizable(True)
        tree_header.set_sort_column_id(0)
        tree_header.set_sizing(1)
        self.tv_report.append_column (tree_header)
        tree_header = Gtk.TreeViewColumn(_("Port"), render_txt, text=1, foreground=4)
        tree_header.set_resizable(True)
        tree_header.set_sort_column_id(1)
        tree_header.set_sizing(1)
        self.tv_report.append_column(tree_header)
        tree_header = Gtk.TreeViewColumn(_("Address"), render_txt, text=2, foreground=4)
        tree_header.set_resizable(True)
        tree_header.set_sort_column_id(2)
        tree_header.set_sizing(1)
        self.tv_report.append_column(tree_header)
        tree_header = Gtk.TreeViewColumn (_("Application"), render_txt, text=3, foreground=4)
        tree_header.set_sort_column_id(3)
        tree_header.set_sizing(1)
        self.tv_report.append_column(tree_header)
        
        self.listening = ListeningReport(self)
        
        self.add_to_log(self.frontend.get_log(), self.GRAY, False)
        
        self._load_tutorial()
        
        self._set_shield()
        
        self._restore_window_size(self.winMain)
        self.winMain.show_all()
        
        if self.frontend.get_policy('routed') == 'disabled':
            self.routed_lbl.set_visible(False)
            self.box_routed.set_visible(False)
        
        self.print_rules(self.frontend.get_rules(False))
        
        self.btn_report_play.hide()

    # Disable the context menu
    def context_menu_cb(webview, context_menu, event, hit_test_result, error):
        return True

    def _load_tutorial(self):
        f = open('/usr/share/gufw/media/tutorial/index.html', 'r')
        html_content = f.read()
        f.close()
        
        replace_html = dict(heading1=_("Getting started"),
                            intro=_("An uncomplicated way to manage your firewall, powered by ufw. Easy, simple, nice and useful! :)"),
                            heading2=_("Basic"),
                            heading3=_("FAQ"),
                            best_conf=_("If you are a normal user, you will be safe with this setting (Status=On, Incoming=Deny, Outgoing=Allow). Remember to append allow rules for your P2P apps:"),
                            rename_profile=_("You can rename your profiles with just 2 clicks on them:"),
                            rule_name=_("The Rule Name will help you to identify your rules in the future:"),
                            faq1_q=_("How to autostart Gufw with the system?"),
                            faq1_a=_("You do not need it. After you do all of the changes in Gufw, the settings are still in place until the next changes."),
                            faq2_q=_("Why is Gufw disabled by default?"),
                            faq2_a=_("By default, the firewall does not open ports to the outside world."),
                            faq3_q=_("Some rules are added by themselves?"),
                            faq3_a=_("Well, the behaviour is such that when you change or import a profile, or when you edit a rule, Gufw will add that rule again, then ufw re-adds that rule for IPv4 and IPv6."),
                            faq4_q=_("What is Allow, Deny, Reject and Limit?"),
                            faq4_a1=_("Allow: Will allow traffic."),
                            faq4_a2=_("Deny: Will deny traffic."),
                            faq4_a3=_("Reject: Will deny traffic and will inform that it has been rejected."),
                            faq4_a4=_("Limit: Will deny traffic if an IP tried several connections."),
                            faq5_q=_("I see some rules in all profiles"),
                            faq5_a=_("All the ufw rules will be appear in all profiles."),
                            faq6_q=_("What do I see in the Listening Report?"),
                            faq6_a=_("The ports on the live system in the listening state for TCP and the open state for UDP."),
                            faq8_q=_("I want even more!"),
                            faq8_a=_("You'll find more information in the community documentation :)"))
        html = Template(html_content).safe_substitute(replace_html)
        self.web_content.load_html(html, "file:///")
    
    def _show_web(self, url):
        distro = platform.linux_distribution()[0].lower()
        try:
            user = sys.argv[1]
        except Exception:
            self.show_dialog(self.winMain, _("Visit this web (please, copy & paste in your browser):"), url)
            return
        
        if distro != 'ubuntu' and distro != 'linuxmint' and distro != 'debian':
            self.show_dialog(self.winMain, _("Visit this web (please, copy & paste in your browser):"), url)
            return
        if user == 'root' or user == '-ssh' or not user:
            self.show_dialog(self.winMain, _("Visit this web (please, copy & paste in your browser):"), url)
            return
        
        # Launching browser
        cmd = "su -c 'python -m webbrowser -t \"" + url + "\"' - " + user
        subprocess.Popen(cmd, shell=True)
    
    def on_menu_import_activate(self, widget, data=None):
        import_profile = self._file_dialog('open', _("Import Profile"))
        
        profile = os.path.basename(import_profile) #Filename
        profile = os.path.splitext(profile)[0] # Ext
        
        if not profile:
            self.set_statusbar_msg(_("Import cancelled"))
            return
        
        if oct(os.stat(import_profile).st_mode & 0o777) != oct(0o600):
            self.show_dialog(self.winMain, _("Error"), _("Filename has wrong permissions (not 600). Trust only on your exported profiles"))
            return
        
        if not re.match('^[A-Za-z0-9_-]*$', profile):
            self.show_dialog(self.winMain, _("Error"), _("Filename has not valid characters. Rename the file\nto only letters, numbers, dashes and underscores"))
            return
        
        if profile in self.frontend.get_all_profiles():
            self.set_statusbar_msg(_("Operation cancelled"))
            self.show_dialog(self.winMain, _("Profile already exists"), _("Delete it before from the Preferences Window or rename the file (the profile will be the filename)"))
        else:
            self.frontend.import_profile(import_profile)
            self.profile.append_text(profile)
            self.add_to_log(_("Profile imported: ") + import_profile)
            self.set_statusbar_msg(_("Profile imported, now you can choose it in the profiles"))
    
    def on_menu_export_activate(self, widget, data=None):
        export_profile = self._file_dialog('save', _("Export Profile"))
        
        if not export_profile:
            self.set_statusbar_msg(_("Export cancelled"))
            return
        
        if export_profile[-8:] != '.profile':
            export_profile = export_profile + '.profile'
        
        self.frontend.export_profile(export_profile)
        self.add_to_log(_("Profile exported: ") + export_profile)
        self.set_statusbar_msg(_("Profile exported"))
    
    def on_main_delete_event(self, widget, data=None):
        self._exit_gufw()
    
    def on_menu_quit_activate(self, widget, data=None):
        self._exit_gufw()
    
    def _exit_gufw(self):
        self._save_window_size(self.winMain)
        self.listening.stopping()
        Gtk.main_quit()
    
    def _set_shield(self):
        if self.frontend.get_status():
            file_shield = os.path.join('/usr/share/gufw/media/shields/', self.frontend.get_policy('incoming').lower() + '_' + self.frontend.get_policy('outgoing').lower() + '_' + self.frontend.get_policy('routed').lower() + '.png')
        else:
            if self.frontend.get_policy('routed') == 'disabled':
                file_shield = os.path.join('/usr/share/gufw/media/shields/', 'disabled_disabled_disabled.png')
            else:
                file_shield = os.path.join('/usr/share/gufw/media/shields/', 'disabled_disabled_enabled.png')
        self.shield.set_from_file(file_shield)
    
    def on_menu_reset_activate(self, widget, data=None):
        answer = self._show_question(self.winMain, _("Reset Firewall"), _("This will remove all rules in the current\nprofile and disable the firewall"), _("Do you want to continue?"))
        if answer:
            if self.frontend.get_status():
                self.switchStatus.set_active(False)
            self.frontend.reset()
            self.add_to_log(_("Removed rules and reset firewall!"))
    
    def on_btnLogRemove_clicked(self, widget, data=None):
        self.frontend.refresh_log()
        self.log_txt.set_text('')
        self.add_to_log(_("Gufw Log: Removed"))
        self.set_statusbar_msg(_("Gufw Log removed"))
    
    def on_btnLogCopy_clicked(self, widget, data=None):
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard.set_text(self.frontend.get_log(), -1)
        self.set_statusbar_msg(_("Text copied to clipboard"))
    
    def on_menu_about_activate(self, widget, data=None):
        aboutwin = About(self)
    
    def on_menu_preferences_activate(self, widget, data=None):
        preferenceswin = Preferences(self)
    
    def on_incoming_changed(self, widget, data=None):
        self.frontend.set_policy('incoming', self.NUM2POLICY[self.incoming.get_active()].lower())
        self._set_shield()
        # Translators: Policy
        self.add_to_log(_("Incoming: ") + self.incoming.get_active_text(), self.POLICY2COLOR[self.frontend.get_policy('incoming')])
        self.set_statusbar_msg(_("Incoming policy changed"))
        if self.frontend.get_policy('incoming') != self.NUM2POLICY[self.incoming.get_active()].lower():
            self.show_dialog(self.winMain, _("There was an error changing the incoming policy"), _("Restart your firewall to refresh to the real status\nand please report this bug"))
    
    def on_outgoing_changed(self, widget, data=None):
        self.frontend.set_policy('outgoing', self.NUM2POLICY[self.outgoing.get_active()].lower())
        self._set_shield()
        self.add_to_log(_("Outgoing: ") + self.outgoing.get_active_text(), self.POLICY2COLOR[self.frontend.get_policy('outgoing')])
        self.set_statusbar_msg(_("Outgoing policy changed"))
        if self.frontend.get_policy('outgoing') != self.NUM2POLICY[self.outgoing.get_active()].lower():
            self.show_dialog(self.winMain, _("There was an error changing the outgoing policy"), _("Restart your firewall to refresh to the real status\nand please report this bug"))
    
    def on_routed_changed(self, widget, data=None):
        try: # Could be inconsistent between imports and changes of Routed status
            self.frontend.set_policy('routed', self.NUM2POLICY[self.routed.get_active()].lower())
        except Exception:
            return
        self._set_shield()
        # Translators: Routed firewall changed
        self.add_to_log(_("Routed: ") + self.routed.get_active_text(), self.POLICY2COLOR[self.frontend.get_policy('routed')])
        self.set_statusbar_msg(_("Routed policy changed"))
        if self.frontend.get_policy('routed') != self.NUM2POLICY[self.routed.get_active()].lower():
            self.show_dialog(self.winMain, _("There was an error changing the routed policy"), _("Restart your firewall to refresh to the real status\nand please report this bug"))
    
    def on_btnAddRule_clicked(self, widget, data=None):
        self.show_add_btn.set_sensitive(False)
        self.edit_rule_btn.set_sensitive(False)
        self.report_rule_btn.set_sensitive(False)
        self.winadd.show_win()
    
    def on_btnReportRule_clicked(self, widget, data=None):
        select_this_row = -1
        protocol = port = address = app = ''
        (model, rows) = self.tv_report.get_selection().get_selected_rows()
        if len(rows) == 1:
            iter_row = self.listening_model.get_iter(rows[0],)
            protocol = self.listening_model.get_value(iter_row, 0)
            port     = str(self.listening_model.get_value(iter_row, 1))
            address  = self.listening_model.get_value(iter_row, 2)
            app      = self.listening_model.get_value(iter_row, 3)
            if address == '*':
                address = ''
        else:
            self.show_dialog(self.winMain, _("Select just one row"), _("You can create a rule from just one row selected"))
            return
        
        self.show_add_btn.set_sensitive(False)
        self.edit_rule_btn.set_sensitive(False)
        self.report_rule_btn.set_sensitive(False)
        self.winadd.set_add_from_report(protocol, port, address, app)
        self.winadd.show_win()        
    
    def on_btnReportPause_clicked(self, widget, data=None):
        self.btn_report_pause.hide()
        self.btn_report_play.show()
        self.listening.set_pause(True)
    
    def on_btnReportPlay_clicked(self, widget, data=None):
        self.btn_report_pause.show()
        self.btn_report_play.hide()
        self.listening.set_pause(False)
    
    def on_switchStatus_active_notify(self, widget, data=None):
        self.frontend.set_status(self.switchStatus.get_active())
        self.print_rules(self.frontend.get_rules(False))
        
        if self.frontend.get_status():
            # Translators: About firewall
            self.add_to_log(_("Status: Enabled"), self.GREEN)
            self.set_statusbar_msg(_("Firewall enabled"))
        else:
            # Translators: About firewall
            self.add_to_log(_("Status: Disabled"), self.RED)
            self.set_statusbar_msg(_("Firewall disabled"))
        
        self.incoming.set_sensitive(self.frontend.get_status())
        self.outgoing.set_sensitive(self.frontend.get_status())
        self.routed.set_sensitive(self.frontend.get_status())
        self.show_add_btn.set_sensitive(self.frontend.get_status())
        self.detele_rule_btn.set_sensitive(self.frontend.get_status())
        self.edit_rule_btn.set_sensitive(self.frontend.get_status())
        self.report_rule_btn.set_sensitive(self.frontend.get_status())
        self._set_shield()
        if self.frontend.get_status() != self.switchStatus.get_active():
            self.show_dialog(self.winMain, _("There was an error changing the firewall status"), _("Restart your firewall to refresh to the real status and please report this bug"))

    def on_btnDeleteRule_clicked(self, widget, data=None):
        total_rules = []
        rules_selected = False
        (model, rows) = self.tv_rules.get_selection().get_selected_rows()
        
        # Compose real numbers
        for row in rows:
            iter_row = self.rules_model.get_iter(row,)
            total_rules.append(self.rules_model.get_value(iter_row, 14))
        total_rules = sorted(total_rules, key=int, reverse=True)
        
        # Confirm?
        if (self.frontend.get_config_value('ConfirmDeteleRule') == 'yes') and (len(total_rules) > 0):
            answer = self._show_question(self.winMain, _("Delete rule"), _("You will delete all selected rules"), _("Do you want to continue?"))
            if not answer:
                return
        
        for row in total_rules:
            rules_selected = True            
            rules_before = self.frontend.get_rules()
            cmd = self.frontend.delete_rule(row)
            rules_after = self.frontend.get_rules()
            
            if len(rules_before) != len(rules_after):
                self.add_to_log(cmd[0])
                self.set_statusbar_msg(_("Rule(s) deleted"))
            else:
                # Translators: Error running an ufw command
                self.add_to_log(_("Error running: ") + cmd[0] + ' > ' + cmd[1].replace('\n', ' | '))
                self.set_statusbar_msg(_("Error. Review Gufw Log"))
        
        if rules_selected:
            self.print_rules(self.frontend.get_rules())
        else:
            self.show_dialog(self.winMain, _("No rule selected"), _("You have to select a rule"))
    
    def _get_total_rows(self, model):
        i = 0
        while True:
            try:
                iter_row = model.get_iter(i,)
            except Exception:
                return i
            i += 1
    
    def on_btnEditRule_clicked(self, widget, data=None):
        (model, rows) = self.tv_rules.get_selection().get_selected_rows()
        
        if len(rows) != 1:
            self.show_dialog(self.winMain, _("Select just one row"), _("You can edit just one rule"))
            return
        
        # Just one rule selected
        iter_row = self.rules_model.get_iter(rows[0],)
        cmd = self.rules_model.get_value(iter_row, 2)
        
        if not cmd: # ufw rule > inmutable
            self.show_dialog(self.winMain, _("Immutable Rule"), _("You can't edit a rule added from ufw"))
            return
        
        description = self.rules_model.get_value(iter_row, 1)
        policy      = self.rules_model.get_value(iter_row, 3)
        direction   = self.rules_model.get_value(iter_row, 4)
        proto       = self.rules_model.get_value(iter_row, 5)
        from_ip     = self.rules_model.get_value(iter_row, 6)
        from_port   = self.rules_model.get_value(iter_row, 7)
        to_ip       = self.rules_model.get_value(iter_row, 8)
        to_port     = self.rules_model.get_value(iter_row, 9)
        iface       = self.rules_model.get_value(iter_row, 10)
        routed      = self.rules_model.get_value(iter_row, 11)
        logging     = self.rules_model.get_value(iter_row, 12)
        ufw_row     = self.rules_model.get_value(iter_row, 14)
        
        updatewin = Update(self, ufw_row, description, cmd, policy, direction, proto, from_ip, from_port, to_ip, to_port, iface, routed, logging)

    def on_profile_changed(self, widget, data=None):
        operation = self.frontend.set_profile(self.profile.get_active_text())
        self.add_to_log(_("Changing profile: ") + self.profile.get_active_text())
        
        self.incoming.set_active(self.POLICY2NUM[self.frontend.get_policy('incoming')])
        self.outgoing.set_active(self.POLICY2NUM[self.frontend.get_policy('outgoing')])
        self.routed.set_active(self.POLICY2NUM[self.frontend.get_policy('routed')])
        self.switchStatus.set_active(self.frontend.get_status())
        
        self.print_rules(self.frontend.get_rules())
        
        for msg in operation:
            self.add_to_log(msg)
    
    def show_dialog(self, win, header, msg):
        dialog = Gtk.MessageDialog(win, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, header)
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()
        
    def _show_question(self, win, header, msg, question):
        reset_dialog = Gtk.MessageDialog(win,
                       Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                       Gtk.MessageType.WARNING, Gtk.ButtonsType.NONE,
                       msg)
        reset_dialog.format_secondary_markup(question)
        reset_dialog.set_title(header)
        reset_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.YES)
        reset_answer = reset_dialog.run()
        reset_dialog.destroy()
        if reset_answer == Gtk.ResponseType.YES:
            return True
        else:
            return False
    
    def _get_log_color(self, color):
        if color == self.GREEN:
            return self.txt_tag_green
        if color == self.RED:
            return self.txt_tag_red
        if color == self.ORANGE:
            return self.txt_tag_orange
        if color == self.BLUE:
            return self.txt_tag_blue
        if color == self.GRAY:
            return self.txt_tag_gray
        
        return self.txt_tag_black
            
    def add_to_log(self, msg, color=BLACK, force_save=True):
        if not self.frontend.get_logging():
            return
        
        if force_save:
            new_line = self.frontend.add_to_log(msg)
            self.log_txt.insert_with_tags(self.log_txt.get_start_iter(), new_line, self._get_log_color(color)) 
        else:
            self.log_txt.insert_with_tags(self.log_txt.get_end_iter(), msg, self._get_log_color(color)) 
    
    def set_statusbar_msg(self, msg):
        cid = self.statusbar.get_context_id('default context')
        self.statusbar.push(cid, msg)
    
    def print_rules(self, rules):
        self.rules_model.clear()
        if not self.frontend.get_status():
            return
        
        row = 1
        for rule in (rules):
            iter_row = self.rules_model.insert(row)
            # Translators: ufw string
            translated_rule = rule['ufw_rule'].replace(" ALLOW ",  _(" ALLOW "))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" DENY ",    _(" DENY "))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" REJECT ",  _(" REJECT "))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" LIMIT ",   _(" LIMIT "))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" OUT ",     _(" OUT "))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" IN ",      _(" IN "))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" FWD ",     _(" FWD "))
            # Translators: ufw string
            translated_rule = translated_rule.replace("Anywhere",  _("Anywhere"))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" (log) ",     _("(log)"))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" (log-all) ", _("(log-all)"))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" (out)",    _(" (out)"))
            # Translators: ufw string
            translated_rule = translated_rule.replace(" on ",      _(" on "))
            
            self.rules_model.set_value(iter_row, 0,  translated_rule)     # ufw rule
            self.rules_model.set_value(iter_row, 1,  rule['description']) # description
            self.rules_model.set_value(iter_row, 2,  rule['command'])     # command
            self.rules_model.set_value(iter_row, 3,  rule['policy'])      # policy
            self.rules_model.set_value(iter_row, 4,  rule['direction'])   # direction
            self.rules_model.set_value(iter_row, 5,  rule['protocol'])    # proto
            self.rules_model.set_value(iter_row, 6,  rule['from_ip'])     # from_ip
            self.rules_model.set_value(iter_row, 7,  rule['from_port'])   # from_port
            self.rules_model.set_value(iter_row, 8,  rule['to_ip'])       # to_ip
            self.rules_model.set_value(iter_row, 9,  rule['to_port'])     # to_port
            self.rules_model.set_value(iter_row, 10, rule['iface'])       # iface
            self.rules_model.set_value(iter_row, 11, rule['routed'])      # routed
            self.rules_model.set_value(iter_row, 12, rule['logging'])     # logging
            self.rules_model.set_value(iter_row, 14, row)                 # number
            
            if 'ALLOW' in rule['ufw_rule']:
                self.rules_model.set_value(iter_row, 13, self.POLICY2COLOR['allow'])  # color
            elif 'DENY' in rule['ufw_rule']:
                self.rules_model.set_value(iter_row, 13, self.POLICY2COLOR['deny'])   # color
            elif 'REJECT' in rule['ufw_rule']:
                self.rules_model.set_value(iter_row, 13, self.POLICY2COLOR['reject']) # color
            elif 'LIMIT' in rule['ufw_rule']:
                self.rules_model.set_value(iter_row, 13, self.POLICY2COLOR['limit'])  # color
            else:
                self.rules_model.set_value(iter_row, 13, self.POLICY2COLOR['others']) # color
            
            row += 1
    
    def _file_dialog(self, type_dialog, title):
        if type_dialog == 'open':
            type_win = Gtk.FileChooserAction.OPEN
            stock_win = Gtk.STOCK_OPEN
        else:
            type_win = Gtk.FileChooserAction.SAVE
            stock_win = Gtk.STOCK_SAVE
        
        dialog = Gtk.FileChooserDialog(title, None,
                                       type_win,
                                      (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                       stock_win, Gtk.ResponseType.OK))
        filter_profile = Gtk.FileFilter()
        filter_profile.set_name(_("Gufw profile"))
        filter_profile.add_pattern("*.profile")
        dialog.add_filter(filter_profile)
        filter_all = Gtk.FileFilter()
        filter_all.set_name(_("All files"))
        filter_all.add_pattern('*')
        dialog.add_filter(filter_all)
        dialog.set_do_overwrite_confirmation(True)
        
        response = dialog.run()
        select = ''
        if response == Gtk.ResponseType.OK:
            select = dialog.get_filename()
        
        dialog.destroy()    
        return select
    
    def _restore_window_size(self, win):
        # Fix GUI for small screens:
        if Gdk.Screen.height() <= 600:
            win.set_size_request(365, 480)
        if Gdk.Screen.height() <= 480:
            win.set_size_request(365, 390)
        
        width = 0
        height = 0
        if self.frontend.get_config_value('WindowWidth'):
            width = int(self.frontend.get_config_value('WindowWidth'))
        if self.frontend.get_config_value('WindowHeight'):
            height = int(self.frontend.get_config_value('WindowHeight'))
        
        if width >= Gdk.Screen.width() and height >= Gdk.Screen.height():
            win.maximize()
        elif width != 0 and height != 0:
            win.resize(width, height)            
            
    def _save_window_size(self, win):
        width, height = win.get_size()
        self.frontend.set_config_value('WindowWidth',  str(width))
        self.frontend.set_config_value('WindowHeight', str(height))
    
    def validate_rule(self, win, from_ip, from_port, to_ip, to_port, insert='', routed=''):
        # At least 1 Port/IP
        if not from_ip and not from_port and not to_ip and not to_port and routed == "Not Forward":
            self.show_dialog(win, _("Insert IP/Ports"), _("You need to insert IP/ports in to/from fields"))
            return False
        
        # Not allow insert number bigger that number of rules
        if not insert:
            insert_into = 0
        else:
            insert_into = int(insert)
        if insert_into > 0 and insert_into > self.frontend.get_number_rules():
            self.show_dialog(win, _("Insert number bigger that number of rules"), _("By example, if you have 3 rules, you can't insert a rule into position 4"))
            return False
        
        return True
