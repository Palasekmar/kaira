import gtk

import project
from canvas import NetCanvas, MultiCanvas
from net import VisualConfig
import gtkutils
import utils


class SimView(gtk.VBox):
	def __init__(self, app, simulation):
		gtk.VBox.__init__(self)
		self.simulation = simulation
		self.registered = False

		self.pack_start(self._buttons(), False, False)
		self.canvas_sc = gtk.ScrolledWindow()
		self.canvas = self._create_canvas()
		self.canvas.set_size_and_viewport_by_net()
		self.canvas_sc.add_with_viewport(self.canvas)

		self.instance_canvas_sc = gtk.ScrolledWindow()
		self.instance_canvas = self._create_instances_canvas()
		self.instance_canvas_sc.add_with_viewport(self.instance_canvas)
		self.instance_canvas.show_all()

		self.pack_start(self.canvas_sc)
		self.show_all()
		self.pack_start(self.instance_canvas_sc)

		simulation.set_callback("changed", self._simulation_changed)
		simulation.set_callback("inited", self._simulation_inited)
		simulation.set_callback("output", lambda line: app.console_write(line, "output"))

	def redraw(self):
		self.instance_canvas.redraw()
		self.canvas.redraw()

	def get_net(self):
		return self.simulation.get_net()

	def _buttons(self):
		button1 = gtk.ToggleButton("Instances")
		button1.connect("toggled", self._view_change)

		toolbar = gtk.Toolbar()
		toolbar.add(button1)
		toolbar.show_all()
		return toolbar

	def _view_change(self, button):
		if button.get_active():
			self.instance_canvas_sc.show()
			self.canvas_sc.hide()
		else:
			self.instance_canvas_sc.hide()
			self.canvas_sc.show()

	def _create_canvas(self):
		c = NetCanvas(self.get_net(), None, VisualConfig())
		c.connect("button_press_event", self._button_down)
		c.connect("button_release_event", self._button_up)
		c.connect("motion_notify_event", self._mouse_move)
		c.show()
		return c

	def _create_instances_canvas(self):
		c = MultiCanvas()
		return c

	def _button_down(self, w, event):
		if event.button == 3:
			self._context_menu(event)
			return
		position = (event.x, event.y)
		net = self.simulation.get_net()
		t = net.get_transition(position)
		if t:
			self.simulation.fire_transition_random_instance(t)

	def _context_menu(self, event):
		def fire_fn(i):
			return lambda w: self.simulation.fire_transition(t, i)
		position = (event.x, event.y)
		net = self.simulation.get_net()
		t = net.get_transition(position)
		if t:
			iids = self.simulation.enabled_instances_of_transition(t)
			if iids:
				gtkutils.show_context_menu([("Fire " + str(i), fire_fn(i)) for i in iids ], event)

	def _button_up(self, w, event):
		pass

	def _mouse_move(self, w, event):
		pass

	def _view_for_area(self, area):
		sz = utils.vector_add(area.get_size(), (80, 95))
		pos = utils.vector_diff(area.get_position(), (40, 55))
		return (sz, pos)

	def _on_instance_click(self, position, area, i):
		net = self.simulation.get_net()
		t = net.get_transition(position)
		# FIXME: Only transitions inside area can be clicked
		if t:
			self.simulation.fire_transition(t, i)

	def _instance_draw(self, cr, width, height, vx, vy, vconfig, area, i):
		self.simulation.get_net().draw(cr, vconfig)
		cr.set_source_rgba(0.3,0.3,0.3,0.5)
		cr.rectangle(vx,vy,width, 15)
		cr.fill()
		cr.move_to(vx + 10, vy + 11)
		cr.set_source_rgb(1.0,1.0,1.0)
		cr.show_text("node=%s   iid=%s" % (self.simulation.get_instance_node(area, i), i))
		cr.stroke()

		if not self.simulation.is_instance_running(area, i):
			cr.move_to(vx + 10, vy + 26)
			cr.set_source_rgb(1.0,0.1,0.1)
			cr.show_text("HALTED")
			cr.stroke()



	def _simulation_inited(self):
		def area_callbacks(area, i):
			vconfig = InstanceVisualConfig(self.simulation, area, i)
			draw_fn = lambda cr,w,h,vx,vy: self._instance_draw(cr, w, h, vx, vy, vconfig, area, i)
			click_fn = lambda position: self._on_instance_click(position, area, i)
			return (draw_fn, click_fn)
		if not self.registered:
			self.registered = True
			for area in self.get_net().areas():
				callbacks = [ area_callbacks(area, i) for i in xrange(self.simulation.get_area_instances_number(area)) ]
				sz, pos = self._view_for_area(area)
				self.instance_canvas.register_line(sz, pos, callbacks)
			self.instance_canvas.end_of_registration()
			self.canvas.set_vconfig(OverviewVisualConfig(self.simulation))
		self.redraw()

	def _simulation_changed(self):
		self.redraw()

class OverviewVisualConfig(VisualConfig):

	def __init__(self, simulation):
		self.simulation = simulation

	def get_token_strings(self, place):
		r = []
		tokens = self.simulation.get_tokens_of_place(place)
		for iid in tokens:
			r += [ t + "@" + str(iid) for t in tokens[iid] ]
		return r

	def get_highlight(self, item):
		if item.is_transition() and len(self.simulation.enabled_instances_of_transition(item)) > 0:
			return (0.1,0.90,0.1,0.5)

class InstanceVisualConfig(VisualConfig):

	def __init__(self, simulation, area, iid):
		self.simulation = simulation
		self.area = area
		self.iid = iid

	def get_token_strings(self, place):
		if self.area.is_inside(place):
			tokens = self.simulation.get_tokens_of_place(place)
			return tokens[self.iid]
		else:
			return []

	def get_highlight(self, item):
		if item.is_transition() and self.simulation.is_transition_enabled(item, self.iid):
			return (0.1, 0.90, 0.1, 0.5)
