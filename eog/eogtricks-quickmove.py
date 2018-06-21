# Edit Filename “Tags” plugin for Eye of GNOME
# -*- encoding: utf-8 -*-
# Copyright (C) 2017 Andrew Chadwick <a.t.chadwick@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import print_function

import re
import os
import shutil
import logging

from gi.repository import Eog
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import GLib


logger = logging.getLogger(__name__)
if os.environ.get("EOGTRICKS_DEBUG"):
    logging.basicConfig(level=logging.DEBUG)

class QuickMove(GObject.GObject, Eog.WindowActivatable):

    ACTION_NEW_NAME = "new-quick-move-folder"
    ACTION_MOVE_NAME = "do-quick-move"

    window = GObject.property(type=Eog.Window)
    folder = None # os.path.expanduser('~')

    def __init__(self):
        super().__init__()
        self.action_new = Gio.SimpleAction(name=self.ACTION_NEW_NAME)
        self.action_move = Gio.SimpleAction(name=self.ACTION_MOVE_NAME)
        self.action_new.connect("activate", self._new_activated_cb)
        self.action_move.connect("activate", self._move_activated_cb)

    def do_activate(self):
        logger.debug("Activated. Adding action win.%s", self.ACTION_NEW_NAME)
        logger.debug("Activated. Adding action win.%s", self.ACTION_MOVE_NAME)
        self.window.add_action(self.action_new)
        self.window.add_action(self.action_move)
        app = self.window.get_application()
        app.set_accels_for_action( "win." + self.ACTION_NEW_NAME, ['N'], )
        app.set_accels_for_action( "win." + self.ACTION_MOVE_NAME, ['M'], )
        self.window.get_titlebar().set_subtitle("Target: None")

    def do_deactivate(self):
        logger.debug("Deactivated. Removing action win.%s", self.ACTION_NEW_NAME)
        logger.debug("Deactivated. Removing action win.%s", self.ACTION_MOVE_NAME)
        self.window.remove_action(self.ACTION_NEW_NAME)
        self.window.remove_action(self.ACTION_MOVE_NAME)

    def _move_activated_cb(self, action, param):
        if not self.folder:
            return

        img = self.window.get_image()
        if not img:
            return
        if not img.is_file_writable():
            return

        src = img.get_file().get_path()
        name = os.path.basename(src)
        dest = self.folder

        # Create directory if it doesn't exist.
        try:
            os.makedirs(dest)
        except OSError:
            pass
        shutil.move(src, dest)

        logger.debug("Move %r → %r", src, dest)
        store = self.window.get_store()
        old_pos = store.get_pos_by_image(img)

        # If you rename the current image, the image is
        # re-inserted at its new aphabetical location, and the
        # UI's idea of the current image resets to position
        # zero. This is confusing and makes things feel really
        # inconsistent.

        GLib.idle_add(self._set_current_idle_cb, old_pos)

    def _new_activated_cb(self, action, param):
        dialog = Gtk.FileChooserDialog("Choose new target directory", self.window,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        if not self.folder:
            self.folder = os.path.expanduser('~')

        dialog.set_local_only(True)
        dialog.set_current_folder(self.folder)
        dialog.set_position(Gtk.WindowPosition.MOUSE)
        dialog.set_default_response(Gtk.ResponseType.OK)
 
        response = dialog.run()

        try:
            if response != Gtk.ResponseType.OK:
                return

            self.folder = dialog.get_filename()
            tb = self.window.get_titlebar()
            tb.set_subtitle("Target: "+self.folder)

        except:
            raise
        finally:
            dialog.destroy()

    def _set_current_idle_cb(self, old_pos):
        # Keeps the cursor position in the sequence at +1/0/-1 away
        # from its previous position.
        view = self.window.get_thumb_view()
        store = self.window.get_store()
        img = store.get_image_by_pos(old_pos)
        view.set_current_image(img, True)
        return False

