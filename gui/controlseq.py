#
#    Copyright (C) 2013 Stanislav Bohm
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

import re
import gtk
import gtkutils
import objectlist
import xml.etree.ElementTree as xml

command_parser = re.compile(
   "(?P<process>\d+) (?P<action>[SFTR])( ((?P<arg_int>\d+)|(?P<arg_str>.*)))?"
)

def sequence_dialog(sequence, mainwindow):
    builder = gtkutils.load_ui("sequence-dialog")
    dlg = builder.get_object("sequence-dialog")
    try:
        name = builder.get_object("name")
        name.set_text(sequence.name)
        name.select_region(0, -1)
        dlg.set_transient_for(mainwindow)
        if dlg.run() == gtk.RESPONSE_OK:
            sequence.name = name.get_text()
            return True
        return False
    finally:
        dlg.destroy()


class ControlSequenceException(Exception):
    pass

class ControlSequence:

    view = None

    def __init__(self, name=None, commands=None, element=None):
        if element is not None:
            self.name = element.get("name")
            text = element.text
            if text is None:
                self.commands = []
            else:
                self.commands = [ command for command in text.split("\n")
                                  if command ]
        else:
            self.name = name
            if commands is None:
                self.commands = []
            else:
                self.commands = commands

    def copy(self):
        return ControlSequence(self.name, self.commands)

    def as_xml(self):
        element = xml.Element("sequence")
        element.set("name", self.name)
        element.text = "\n".join(self.commands)
        return element

    def execute(self, on_fire, on_transition_start, on_transition_finish, on_receive):
        for i in xrange(len(self.commands)):
            self.execute_command(i, on_fire, on_transition_start, on_transition_finish, on_receive)

    def execute_command(self, i, on_fire, on_transition_start, on_transition_finish, on_receive):
        line = self.commands[i]
        match = command_parser.match(line)
        if match is None:
            raise ControlSequenceException("Invalid format: ", line)

        process = int(match.group("process"))
        action = match.group("action")

        if action == "T":
            if match.group("arg_int"):
                arg = match.group("arg_int")
            else:
                arg = match.group("arg_str")
            return on_fire(process, arg)
        elif action == "R":
            arg_int = match.group("arg_int")
            if arg_int is None:
                raise ControlSequenceException("Invalid format of receive")
            return on_receive(process, int(arg_int))
        elif action == "S":
            if match.group("arg_int"):
                arg = match.group("arg_int")
            else:
                arg = match.group("arg_str")
            return on_transition_start(process, arg)
        else: # action == "F":
            return on_transition_finish(process)

    def get_commands_size(self):
        return len(self.commands)

    def add_fire(self, process, transition):
        self.commands.append("{0} T {1}".format(process, transition))
        if self.view:
            self.view.add_fire(process, transition)

    def add_transition_start(self, process, transition):
        self.commands.append("{0} S {1}".format(process, transition))
        if self.view:
            self.view.add_transition_start(process, transition)

    def add_transition_finish(self, process):
        self.commands.append("{0} F".format(process))
        if self.view:
            self.view.add_transition_finish(process)

    def add_receive(self, process, from_process):
        self.commands.append("{0} R {1}".format(process, from_process))
        if self.view:
            self.view.add_receive(process, from_process)


class SequenceView(gtkutils.SimpleTree):

    def __init__(self, sequence=None, show_init_state=None):
        gtkutils.SimpleTree.__init__(
            self, (("I", str), ("B", str), ("P", str), ("Action|markup", str), ("Arg", str),))
        if show_init_state:
            self.append(None, ("0", "0", "", "<b><span background='grey'>Init</span></b>", ""))
        if sequence:
            self.load_sequence(sequence)
        self.branch_id = 0
        self.index_id = 1
        self._parent = None
        self.current_iter = self.get_first_iter()
        self.path = None
        self.setstate_phase = 0
        self.setstate_state = False

    def load_sequence(self, sequence):
        self.clear()
        sequence.execute(self.add_fire,
                         self.add_transition_start,
                         self.add_transition_finish,
                         self.add_receive)

    def add_fire(self, process_id, transition):
        row_data = (str(self.index_id), str(self.branch_id), str(process_id),
                     "<b><span background='green'>Fire</span></b>",
                     transition)
        if self.setstate_phase is 2:
            self.prepend(self._parent, row_data)
        else:
            self.append(self._parent, row_data)
            
        self.increment_index_id()
        self.unbold_prev_row()

    def add_transition_start(self, process_id, transition):
        row_data = (str(self.index_id), str(self.branch_id), str(process_id),
                     "<b><span background='lightgreen'>StartT</span></b>",
                     transition)
        if self.setstate_phase is 2:
            self.prepend(self._parent, row_data)
        else:
            self.append(self._parent, row_data)
            
        self.increment_index_id()
        self.unbold_prev_row()

    def add_transition_finish(self, process_id):
        row_data = (str(self.index_id), str(self.branch_id), str(process_id),
                     "<b><span background='#FF7070'>FinishT</span></b>",
                     "")
        if self.setstate_phase is 2:
            self.prepend(self._parent, row_data)
        else:
            self.append(self._parent, row_data)
            
        self.increment_index_id()
        self.unbold_prev_row()

    def add_receive(self, process_id, from_process):
        row_data = (str(self.index_id), str(self.branch_id), str(process_id),
                     "<b><span background='lightblue'>Receive</span></b>",
                     str(from_process))
        if self.setstate_phase is 2:
            self.prepend(self._parent, row_data)
        else:
            self.append(self._parent, row_data)
            
        self.increment_index_id()
        self.unbold_prev_row()
    
    def increment_index_id(self):
        self.index_id = self.index_id + 1
    
    def set_branch_id(self, branch):
        self.branch_id = branch
        self.index_id = 0
        
    def set_parent(self, par):
        self._parent = par
        
    def set_current_row(self, curr):
        self.current_row = curr
        
    def add_bold_tags(self, str):
        str = "<b>" + str + "</b>"
        return str
        
    def remove_bold_tags(self, str):
        return str[3:-4]
    
    def make_path_to_setstate(self, n_child, path):
        n_child = n_child - 1
        tup = (n_child,)
        path = path + tup
        return(path)
    
    def modify_path(self, path):
        path = path + (0,)
        return path
    
    def unbold_prev_row(self):
        if self.setstate_phase is 3:
            self.unbold_row(self._parent)
            self.setstate_state = False
            self.setstate_phase = 2
        elif self.setstate_phase is 2:
            self.unbold_row(self._parent)
            self.path = self.get_path(self._parent)
            self.path = self.modify_path(self.path)
            self._parent = self.get_iter(self.path)
            self.setstate_state = False
            self.setstate_phase = 1
        elif self.setstate_phase is 1:
            self.unbold_row(self._parent)
            self.path = self.modify_path(self.path)
            if self.setstate_state is False:
                self.current_iter = self.get_iter(self.path)
            self.setstate_state = False
            self.setstate_phase = 0
        elif self.setstate_phase is 0:
            self.unbold_row(self.current_iter)
            self.current_iter = self.iter_next(self.current_iter)
            self.setstate_state = False
    
    def unbold_row(self, iter):
        row = self.get_row(iter)
        edit = self.remove_bold_tags(row[3])
        newrow = (row[0], row[1], row[2], edit, row[4])
        self.update_row(self.get_path(iter), newrow)
        
    def bold_row(self, path):
        iter = self.get_iter(path)
        row = self.get_row(iter)
        edit = self.add_bold_tags(row[3])
        newrow = (row[0], row[1], row[2], edit, row[4])
        self.update_row(path, newrow)
        
class SequenceListWidget(gtk.HPaned):

    def __init__(self, project):
        gtk.HPaned.__init__(self)
        self.project = project
        buttons = [
            (None, gtk.STOCK_REMOVE, self._remove_sequence)
        ]

        self.objlist = objectlist.ObjectList([("_", object), ("Sequences", str) ], buttons)
        self.objlist.object_as_row = lambda obj: [ obj, obj.name ]
        self.objlist.cursor_changed = self.on_cursor_changed
        self.objlist.set_size_request(150, 0)
        self.event = self.project.set_callback(
            "sequences_changed",
            lambda: self.objlist.refresh(project.sequences))
        self.pack1(self.objlist, False)

        self.view = SequenceView()
        self.pack2(self.view, True)
        self.show_all()

        self.objlist.fill(project.sequences)

    def close(self):
        self.event.remove()

    def on_cursor_changed(self, obj):
        if obj is None:
            self.view.clear()
        else:
            self.view.load_sequence(obj)

    def _remove_sequence(self, obj):
        if obj:
            self.project.remove_sequence(obj)
