#
#    Copyright (C) 2010, 2011 Stanislav Bohm
#
#    This file is part of Kaira.
#
#    Kaira is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License, or
#    (at your option) any later version.
#
#    Kaira is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Kaira.  If not, see <http://www.gnu.org/licenses/>.
#

import gtk
from objectlist import ObjectList
from codeedit import CodeEditor
import gtkutils

def extern_type_new_dialog(mainwindow):
    builder = gtkutils.load_ui("externtype-new-dialog")
    dlg = builder.get_object("externtype-new-dialog")
    try:
        dlg.set_title("New extern type")
        dlg.set_transient_for(mainwindow)
        if dlg.run() == gtk.RESPONSE_OK:
            item = builder.get_object("native")
            if item.get_active():
                return "native"
            item = builder.get_object("protobuffer")
            if item.get_active():
                return "protobuffer"
            return None
    finally:
       dlg.destroy()

def extern_type_dialog(obj, mainwindow):
    builder = gtkutils.load_ui("externtype-dialog")
    dlg = builder.get_object("externtype-dialog")
    try:

        wname = builder.get_object("name")
        wname.set_text(obj.get_name())

        wrtype = builder.get_object("raw_type")
        wrtype.set_text(obj.get_raw_type())

        mode_disabled = builder.get_object("mode_disabled")
        mode_direct = builder.get_object("mode_direct")
        mode_custom = builder.get_object("mode_custom")

        if obj.get_transport_mode() == "Custom":
            mode_custom.set_active(True)
        elif obj.get_transport_mode() == "Direct":
            mode_direct.set_active(True)
        else:
            mode_disabled.set_active(True)

        dlg.set_title("Extern type")
        dlg.set_transient_for(mainwindow)
        if dlg.run() == gtk.RESPONSE_OK:
            obj.set_name(wname.get_text())
            obj.set_raw_type(wrtype.get_text())
            if mode_custom.get_active():
                obj.set_transport_mode("Custom")
            elif mode_direct.get_active():
                obj.set_transport_mode("Direct")
            else:
                obj.set_transport_mode("Disabled")

            return True
        return False
    finally:
        dlg.destroy()

class ExternTypesWidget(ObjectList):

    def __init__(self, project, app):
        defs = [("_", object), ("Name", str), ("Type", str), ("Note", str) ]
        buttons = [
            (None, gtk.STOCK_ADD, self._add_type),
            (None, gtk.STOCK_REMOVE, self._remove_type),
            (None, gtk.STOCK_EDIT, self._edit_type),
            ("Code", gtk.STOCK_EDIT, self._edit_code)
        ]

        ObjectList.__init__(self, defs, buttons)
        self.project = project
        self.app = app
        self.fill(project.get_extern_types())

    def row_activated(self, selected):
        self._edit_type(selected)

    def object_as_row(self, obj):
        return [ obj, obj.get_name(), obj.get_type(), obj.get_note() ]

    def _add_type(self, selected):
        #t = extern_type_new_dialog(self.app.window)
        #if t:
        #    print t
        obj = self.project.get_extern_type_class("native")()
        if extern_type_dialog(obj, self.app.window):
            self.add_object(obj)
            self.project.add_extern_type(obj)

    def _edit_type(self, selected):
        if selected and extern_type_dialog(selected, self.app.window):
            self.update_selected(selected)

    def _edit_code(self, selected):
        if selected:
            self.app.extern_type_functions_edit(selected)

    def _remove_type(self, selected):
        if selected:
            obj = self.get_and_remove_selected()
            self.project.remove_extern_type(obj)

class ExternTypeEditor(CodeEditor):

    def __init__(self, project, externtype):
        self.extern_type = externtype
        highlight = project.get_syntax_highlight_key()
        sections = externtype.get_sections()
        header = externtype.get_header()
        CodeEditor.__init__(self, highlight, sections, ("getstring", 1, 1), header)

    def buffer_changed(self, buffer):
        for section in self.sections:
            section_name = section[0]
            self.extern_type.set_function_code(section_name, self.get_text(section_name))
        #self.change_callback(self.extern_type, self.fn_name)
