# This file is part of gnome-tweak-tool.
#
# Copyright (c) 2011 John Stowers
#
# gnome-tweak-tool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gnome-tweak-tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gnome-tweak-tool.  If not, see <http://www.gnu.org/licenses/>.

import gtweak
from gtweak.gshellwrapper import GnomeShellFactory
from gtweak.tweakmodel import TWEAK_GROUP_WINDOWS, Tweak
from gtweak.widgets import ListBoxTweakGroup, GSettingsComboEnumTweak, GSettingsComboTweak, GSettingsSwitchTweak, Title, GSettingsSwitchTweakValue, build_label_beside_widget
from gtweak.utils import XSettingsOverrides
import gettext

from gi.repository import Gtk, GLib

_shell = GnomeShellFactory().get_shell()
_shell_loaded = _shell is not None
            
class ShowWindowButtons(GSettingsSwitchTweakValue):

    def __init__(self, name, value, **options):
        self.value = value
        GSettingsSwitchTweakValue.__init__(self,
                                           name,
                                           "org.gnome.desktop.wm.preferences",
                                           "button-layout",
                                           loaded=_shell_loaded,
                                           **options)
    def get_active(self):
        return self.value in self.settings.get_string(self.key_name)
            
    def set_active(self, v):
        val = self.settings.get_string(self.key_name)
        if v:
            if val == ":close":
                val = val.replace(":", ":"+self.value+",")
            else:
                val = ":minimize,maximize,close"
        else:
            val = val.replace(self.value+",", "")

        self.settings.set_string(self.key_name, val)

class WindowScalingFactorTweak(Gtk.Box, Tweak):
    def __init__(self, **options):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        Tweak.__init__(self, _("Window scaling"), _("Adjust GDK window scaling factor for HiDPI"), **options)

        self._xsettings = XSettingsOverrides()
        self._original_factor = self._xsettings.get_window_scaling_factor()

        adjustment = Gtk.Adjustment(lower=1, upper=2, step_increment=1, page_increment=1)
        w = Gtk.SpinButton()
        w.set_adjustment(adjustment)
        w.set_digits(0)
        adjustment.set_value(self._xsettings.get_window_scaling_factor())
        w.connect("value-changed", self._on_value_changed)

        build_label_beside_widget(self.name, w, hbox=self)
        self.widget_for_size_group = w

    def _timeout_func (self):
        self._countdown -= 1

        if self._countdown == 0:
            self._source = 0
            self._dialog.response(Gtk.ResponseType.NO)
            return False

        self._update_countdown_message()
        self._dialog.format_secondary_text(self._second_message % self._countdown)
        return True

    def _update_countdown_message(self):
        self._second_message = gettext.ngettext("Settings will be reverted in %d second",
                                                "Settings will be reverted in %d seconds",
                                                self._countdown)

    def _close(self):
        if self._source > 0:
            GLib.Source.remove(self._source)
            self._source = 0

    def _on_value_changed(self, adj):
        if adj.get_value() == self._original_factor:
            return

        self._xsettings.set_window_scaling_factor(adj.get_value())
        self._countdown = 20

        first_message = _("Do you want to keep these HiDPI settings?")
        self._update_countdown_message()

        self._dialog = Gtk.MessageDialog(
                               transient_for=self.main_window,
                               message_type=Gtk.MessageType.QUESTION,
                               text=first_message)
        self._dialog.add_buttons(_("Revert Settings"), Gtk.ResponseType.NO,
                                _("Keep Changes"), Gtk.ResponseType.YES)
        self._dialog.format_secondary_text(self._second_message % self._countdown)

        self._source = GLib.timeout_add_seconds(interval=1, function=self._timeout_func)

        response = self._dialog.run()

        if response == Gtk.ResponseType.YES:
            self._original_factor = self._xsettings.get_window_scaling_factor()
        else:
            self._xsettings.set_window_scaling_factor(self._original_factor)
            adj.set_value(self._original_factor)

        self._close()
        self._dialog.destroy()

TWEAK_GROUPS = [ 
    ListBoxTweakGroup(TWEAK_GROUP_WINDOWS,
        GSettingsSwitchTweak(_("Attached Modal Dialogs"),"org.gnome.mutter", "attach-modal-dialogs"),
        GSettingsSwitchTweak(_("Automatically Raise Windows"),"org.gnome.desktop.wm.preferences", "auto-raise"),
        GSettingsSwitchTweak(_("Resize with Secondary-click"),"org.gnome.desktop.wm.preferences", "resize-with-right-button"),
        GSettingsComboTweak(_("Window Action Key"),
                        "org.gnome.desktop.wm.preferences",
                        "mouse-button-modifier",
                        [("disabled", _("Disabled")), ("<Alt>", "Alt"), ("<Super>", "Super")]),
        GSettingsComboEnumTweak(_("Focus Mode"), "org.gnome.desktop.wm.preferences", "focus-mode"),
        Title(_("Titlebar Actions"), "", uid="title-titlebar-actions"),
        GSettingsComboEnumTweak(_("Double-click"),"org.gnome.desktop.wm.preferences", "action-double-click-titlebar"),
        GSettingsComboEnumTweak(_("Middle-click"),"org.gnome.desktop.wm.preferences", "action-middle-click-titlebar"),
        GSettingsComboEnumTweak(_("Secondary-click"),"org.gnome.desktop.wm.preferences", "action-right-click-titlebar"),
        Title(_("Titlebar Buttons"), "", uid="title-theme"),
        ShowWindowButtons(_("Maximize"), "maximize"),
        ShowWindowButtons(_("Minimize"), "minimize"),
        Title(_("HiDPI"), "", uid="title-hidpi"),
        WindowScalingFactorTweak(),
    )
]

