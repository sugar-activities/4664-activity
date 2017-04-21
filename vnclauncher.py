#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013, Ignacio Rodríguez
# Version especial de VncLauncher con nuevos cambios.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import time
import gobject
import os
import commands
import platform
from threading import Thread

from gettext import gettext as _

from sugar.activity import activity
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import StopButton
from sugar.activity.widgets import ActivityToolbarButton


class VncLauncherActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.max_participants = 1

        self.toolbarbox = ToolbarBox()
        self.toolbar = self.toolbarbox.toolbar

        self.start_vnc = RadioToolButton(icon_name="start_vnc",
                                         tooltip=_("Start VNC Server"))

        self.stop_vnc = RadioToolButton(icon_name="stop_vnc",
                                        tooltip=_("Stop VNC Server"),
                                        group=self.start_vnc)

        self.stop_vnc.set_active(True)

        self.get_ipbutton = ToolButton(icon_name="get_ip",
                                       tooltip=_("Get the current IP"))

        ##
        self.messages = gtk.TreeView()
        self.messages.set_rules_hint(True)
        modelo = gtk.ListStore(str, str, gtk.gdk.Color)
        self.messages.set_model(modelo)
        render = gtk.CellRendererText()
        render1 = gtk.CellRendererText()

        column1 = gtk.TreeViewColumn(_("Hour"), render, markup=0)
        column2 = gtk.TreeViewColumn(_("Message"), render1, markup=1)
        column1.add_attribute(render, 'foreground-gdk', 2)
        column2.add_attribute(render1, 'foreground-gdk', 2)

        self.messages.append_column(column1)
        self.messages.append_column(column2)
        color = gtk.gdk.color_parse("dark blue")
        modelo.insert(0, [time.strftime("\n<b>%H:%M:%S</b>\n"),
            _("\n<b>Start of activity.</b>\n"), color])

        self.showed_message_stop = True
        self.showed_message_start = False
        self.isrunning = True

        self.stop_vnc.connect("clicked", self.__stop_vnc)
        self.start_vnc.connect("clicked", self.__start_vnc)
        self.clear_model = ToolButton(icon_name="clear_console",
                                      tooltip=_("Delete messages"))
        self.clear_model.connect("clicked", lambda x: modelo.clear())
        self.get_ipbutton.connect("clicked", self.__get_ip)
        self.last_message = 1

        self.__get_x11vnc_path()
        ##
        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)

        self.stop_activity = StopButton(self)

        self.toolbar.insert(ActivityToolbarButton(self), -1)
        self.toolbar.insert(gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.start_vnc, -1)
        self.toolbar.insert(self.stop_vnc, -1)
        self.toolbar.insert(gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.get_ipbutton, -1)
        self.toolbar.insert(self.clear_model, -1)
        self.toolbar.insert(separator, -1)
        self.toolbar.insert(self.stop_activity, -1)

        self.messages_scroll = gtk.ScrolledWindow()
        self.messages_scroll.set_policy(gtk.POLICY_AUTOMATIC,
            gtk.POLICY_AUTOMATIC)
        self.messages_scroll.add_with_viewport(self.messages)

        self.set_toolbar_box(self.toolbarbox)
        self.set_canvas(self.messages_scroll)

        self.show_all()
        gobject.timeout_add(100, self.__check_is_on)

    def __check_is_on(self):
        pid = commands.getoutput("pidof x11vnc")
        if self.start_vnc.get_active() and pid == "" and self.isrunning:
            self.showed_message_stop = True
            self.stop_vnc.set_active(True)
            self.start_vnc.set_active(False)
            self.showed_message_start = False

            color = gtk.gdk.color_parse("dark red")
            self.messages.get_model().insert(self.last_message,
                [time.strftime("\n<b>%H:%M:%S</b>\n"),
                    ("\n<b>It has stopped unexpectedly the server..</b>\n"),
                    color])
            self.last_message += 1

        return True

    def __get_x11vnc_path(self):
        system = platform.machine()
        color = gtk.gdk.color_parse("dark red")
        if os.path.exists("/usr/bin/x11vnc"):
            self.path = "/usr/bin/x11vnc"
            message = _("PATH: %s") % self.path
        else:
            if "arm" in system:
                self.path = os.path.join(activity.get_bundle_path(),
                    "bin", "arm", "x11vnc")
            elif "64" in system:
                self.path = os.path.join(activity.get_bundle_path(),
                    "bin", "x64", "x11vnc")
            else:
                self.path = os.path.join(activity.get_bundle_path(),
                    "bin", "i586", "x11vnc")

            os.environ["LD_LIBRARY_PATH"] = self.path.replace("x11vnc", "lib/")
            message = _("PATH: %s") % self.path

        self.messages.get_model().insert(self.last_message,
            [time.strftime("\n<b>%H:%M:%S</b>\n"),
                "<b>" + message + "</b>", color])
        self.last_message += 1

    def __start_vnc(self, widget):

        def servidor():
            commands.getoutput(self.path)
        Thread(target=servidor).start()

        if not self.showed_message_start:
            self.showed_message_start = True
            pass
        else:
            return

        self.showed_message_stop = False
        self.isrunning = True
        color = gtk.gdk.color_parse("green")
        self.messages.get_model().insert(self.last_message,
            [time.strftime("\n<b>%H:%M:%S</b>\n"),
                ("\n<b>VNC server is started</b>\n"), color])
        self.last_message += 1

    def __stop_vnc(self, widget):

        if not self.showed_message_stop:
            self.showed_message_stop = True
            pass
        else:
            return

        self.showed_message_start = False
        self.pid_nuevo = commands.getoutput("pidof x11vnc")
        color = gtk.gdk.color_parse('red')

        os.system("kill " + self.pid_nuevo)

        self.messages.get_model().insert(self.last_message,
            [time.strftime("\n<b>%H:%M:%S</b>\n"),
            ("\n<b>The VNC server is now stopped.</b>\n"),
            color])
        self.last_message += 1

    def close(self):
        self.isrunning = False
        pid = commands.getoutput("pidof x11vnc")
        os.system("kill " + pid)
        self.destroy()

    def __get_ip(self, widget):
        system = platform.platform()
        if "olpc" in system:
            target = "eth0"
        else:
            target = "wlan0"

        ifconfig = "/sbin/ifconfig"
        cmd = "%s %s" % (ifconfig, target)
        output = commands.getoutput(cmd)
        error = _("No wireless connection.")
        ip = error
        inet = output.find('inet')
        if inet >= 0:
            start = inet + len('inet')
            end = output.find(" ", start + 1)
            ip = output[start:end]
        else:
            ip = error

        if ip == _("No wireless connection."):
            mensaje = error
        else:
            ip = ip.replace(":", "")
            ip = ip.replace("addr", "")
            ip = ip.replace(" ", "")
            mensaje = "IP: " + ip
        color = gtk.gdk.color_parse("dark blue")
        self.messages.get_model().insert(self.last_message,
            [time.strftime("\n<b>%H:%M:%S</b>\n"),
                "\n<b>" + mensaje + "</b>\n", color])

        self.last_message += 1
