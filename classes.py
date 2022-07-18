from __future__ import annotations # for type hints
import pygame # graphics library
from pygame.locals import * # for keyboard input (ex: 'K_w')
import math
import copy

class User():
	def __init__(self, walk_left = K_a, walk_right = K_d, jump = K_SPACE, slide = K_LCTRL, music_on = True):
		self.walk_left = walk_left
		self.walk_right = walk_right
		self.jump = jump
		self.slide = slide
		self.music_on = music_on
		self.settings = [self.walk_left, self.walk_right, self.jump, self.slide, self.music_on]

	def set_setting(self, i, val):
		if i == 0:
			self.walk_left = val
		elif i == 1:
			self.walk_right = val
		elif i == 2:
			self.jump = val
		elif i == 3:
			self.slide = val
		elif i == 4:
			self.music_on = val
		self.settings = [self.walk_left, self.walk_right, self.jump, self.slide, self.music_on]

class DownPress():
	def __init__(self):
		self.was_down = False

	def down(self, condition) -> bool:
		if not self.was_down and condition:
			self.was_down = True
			return True
		elif not condition:
			self.was_down = False
		return False

class Vector(): # vec
	def __init__(self, x: float, y: float):
		self._x: float = x
		self._y: float = y

	def __str__(self) -> str:
		return "<%f, %f>" % (self.get_x(), self.get_y())

	def get_x(self) -> float:
		return self._x
	def set_x(self, x: float) -> None:
		self._x = x
	def get_y(self) -> float:
		return self._y
	def set_y(self, y: float) -> None:
		self._y = y
	def get_tuple(self) -> tuple[float, float]:
		return (self.get_x(), self.get_y())
	def get_angle(self) -> float:
		try:
			angle = math.atan(self.get_y()/self.get_x()) * 180/math.pi
			if self.get_x() < 0: angle += 180
		except ZeroDivisionError:
			angle = 90 if self.get_y() > 0 else 270
		return angle % 360
	def set_angle(self, angle: float) -> None:
		current_length = self.calc_length()
		self.set_x(math.cos(angle * math.pi/180))
		self.set_y(math.sin(angle * math.pi/180))
		self.set_vec(self.scale(current_length))
	def set_vec(self, vec: Vector) -> None:
		self.set_x(vec.get_x())
		self.set_y(vec.get_y())

	def calc_length(self) -> float:
		return math.sqrt(self.get_x() ** 2 + self.get_y() ** 2)

	def add(self, vec: Vector) -> Vector:
		return Vector(self.get_x() + vec.get_x(), self.get_y() + vec.get_y())

	def apply(self, vec: Vector) -> None:
		self.set_vec(self.add(vec))

	def subtract(self, vec: Vector) -> Vector:
		return self.add(vec.scalar(-1))

	def scalar(self, s: float) -> Vector:
		return Vector(self.get_x() * s, self.get_y() * s)

	def scale(self, length: float) -> Vector:
		try:
			return Vector(self.get_x() * length/self.calc_length(), self.get_y() * length/self.calc_length())
		except ZeroDivisionError:
			return Vector(0, 0)


class Hitbox(): # hb
	def __init__(self, pt: Vector, w: float, h: float, color: str = "#ffffff"):
		self._pt: Vector = pt
		self._w: float = w
		self._h: float = h
		self._color: str = color

	def __str__(self) -> str:
		return "(%s, %f, %f)" % (self.get_pt(), self.get_w(), self.get_h())

	def get_pt(self) -> Vector:
		return self._pt
	def get_center(self) -> Vector:
		return Vector(self.get_pt().get_x() + self.get_w()/2, self.get_pt().get_y() + self.get_h()/2)
	def set_pt(self, pt: Vector) -> None:
		self._pt = pt
	def get_w(self) -> float:
		return self._w
	def set_w(self, w: float) -> None:
		self._w = w
	def get_h(self) -> float:
		return self._h
	def set_h(self, h: float) -> None:
		self._h = h
	def get_rect(self) -> pygame.Rect:
		return pygame.Rect(self.get_pt().get_x(), self.get_pt().get_y(), self.get_w(), self.get_h())
	def get_color(self) -> str:
		return self._color
	def set_color(self, color: str) -> None:
		self._color = color

	def check_collide(self, hb: Hitbox) -> bool:
		return (
			self.get_pt().get_x() < hb.get_pt().get_x() + hb.get_w()
			and hb.get_pt().get_x() < self.get_pt().get_x() + self.get_w()
			and self.get_pt().get_y() < hb.get_pt().get_y() + hb.get_h()
			and hb.get_pt().get_y() < self.get_pt().get_y() + self.get_h()
		)

	def draw(self, win: pygame.Surface) -> None:
		pygame.draw.rect(win, self.get_color(), self.get_rect())


class HitboxPart(Hitbox): # hbp
	def __init__(self, pt: Vector, vec_offset: Vector, w: float, h: float, color: str = "#ffffff"):
		super().__init__(pt, w, h, color)
		self._vec_offset: Vector = vec_offset

	def __str__(self) -> str:
		return "Hitbox Part: %s" % super().__str__()

	def get_vec_offset(self) -> Vector:
		return self._vec_offset
	def set_vec_offset(self, vec_offset: Vector) -> None:
		self._vec_offset = vec_offset

	def update_pt_from_master(self, ahb_master: AdvancedHitbox) -> None:
		self.set_pt(ahb_master.get_pt().add(self.get_vec_offset()))


class AdvancedHitbox(Hitbox): # ahb
	def __init__(self, pt: Vector, w: float, h: float, color: str = "#ffffff"):
		super().__init__(pt, w, h, color)
		self._hbps: list[HitboxPart] = []

	def __str__(self) -> str:
		return "Advanced Hitbox: %s" % super().__str__()

	def get_hbps(self) -> list[HitboxPart]:
		return self._hbps
	def add_hbp(self, hbp: HitboxPart) -> None:
		self.get_hbps().append(hbp)

	def check_collisions(self, hb: Hitbox) -> bool:
		for hbp in self.get_hbps():
			if hbp.check_collide(hb):
				return True
		return False

	def check_advanced_collisions(self, ahb: AdvancedHitbox) -> bool:
		for hbp_self in self.get_hbps():
			for hbp_other in ahb.get_hbps():
				if hbp_self.check_collide(hbp_other):
					return True
		return False

	def update_hbps(self) -> None:
		for hbp in self.get_hbps():
			hbp.update_pt_from_master(self)

	# def draw(self, win: pygame.Surface) -> None:
	# 	super().draw(win)
	# 	for hbp in self.get_hbps():
	# 		hbp.draw(win)

class Player(AdvancedHitbox): # p
	def __init__(self, user):
		super().__init__(Vector(100, 760), 25, 40, "#00ff00")
		self.add_hbp(HitboxPart(Vector(100, 760), Vector(0, 0), 25, 40))
		# self.add_hbp(HitboxPart(Vector(150, 855), Vector(0, 10), 25, 25))
		# self.add_hbp(HitboxPart(Vector(150, 875), Vector(2.5, 35), 20, 10))

		self.user = user

		self._ms: float = 200
		self._terminal_vel: float = 250
		self._vec_move: Vector = Vector(0, 0)
		self._is_grounded = False
		self._is_sliding = False
		self._is_stuck = False
		self._can_double_jump = True
		self._space_was_down = False # space bar was down
		self._jumped_while_sliding = False
		self._can_fly = False
		self._is_alive = True
		self._is_finished = False

	def __str__(self) -> str:
		return "Player: %s" % super().__str__()

	def get_is_finished(self) -> bool:
		return self._is_finished
	def set_is_finished(self, is_finished: bool) -> None:
		self._is_finished = is_finished
	def set_terminal_vel(self, terminal_vel: float) -> None:
		self._terminal_vel = terminal_vel
	def get_terminal_vel(self) -> float:
		return self._terminal_vel
	def get_ms(self) -> float:
		return self._ms
	def set_ms(self, ms: float) -> None:
		self._ms = ms
	def get_is_alive(self) -> float:
		return self._is_alive
	def set_is_alive(self, is_alive: float) -> None:
		self._is_alive = is_alive
	def get_vec_move(self) -> Vector:
		return self._vec_move
	def set_vec_move(self, vec_move: Vector) -> None:
		self._vec_move = vec_move
	def get_is_grounded(self) -> bool:
		return self._is_grounded
	def set_is_grounded(self, is_grounded: bool) -> None:
		self._is_grounded = is_grounded
	def get_can_fly(self) -> bool:
		return self._can_fly
	def set_can_fly(self, can_fly: bool) -> None:
		self._can_fly = can_fly
	def get_can_double_jump(self) -> bool:
		return self._can_double_jump
	def set_can_double_jump(self, double_jump: bool) -> None:
		self._can_double_jump = double_jump
	def get_space_was_down(self) -> bool:
		return self._space_was_down
	def set_space_was_down(self, space_down: bool) -> None:
		self._space_was_down = space_down
	def get_jumped_while_sliding(self) -> bool:
		return self._jumped_while_sliding
	def set_jumped_while_sliding(self, jumped_while_sliding: bool) -> None:
		self._jumped_while_sliding = jumped_while_sliding
	def get_is_stuck(self) -> bool:
		return self._is_stuck
	def set_is_stuck(self, is_stuck: bool) -> None:
		self._is_stuck = is_stuck
	def get_is_sliding(self) -> bool:
		return self._is_sliding
	def set_is_sliding(self, is_sliding: bool, walls: list[Surface], delta, keys_down: list[bool]) -> None:
		p_temp = copy.deepcopy(self)
		if not self._is_sliding and is_sliding:
			p_temp.change_dimensions()
			can_slide = True
			for wall in walls:
				if p_temp.check_collisions(wall):
					can_slide = False
			if can_slide:
				self.change_dimensions()
				if keys_down[K_d]:
					self.get_vec_move().set_x(800)
				elif keys_down[K_a]:
					self.get_vec_move().set_x(-800)
				# print(self.get_pt().get_x())
			self._is_sliding = can_slide
		elif self._is_sliding and not is_sliding:
			if self.get_vec_move().get_x() < 0:
				# print("\n\n\n\n",self.get_pt().get_x(), "\n\n\n\n")
				p_temp.get_pt().set_x(p_temp.get_pt().get_x() + (p_temp.get_w() - self.get_h()))
				hb = p_temp.get_hbps()[0]
				hb.get_pt().set_x(hb.get_pt().get_x() + (hb.get_w() - self.get_h()))
			p_temp.change_dimensions()
			can_stand = True
			for wall in walls:
				if p_temp.check_collisions(wall):
					can_stand = False
			if can_stand:
				if self.get_vec_move().get_x() < 0:
					# print(self.get_pt().get_x())
					self.get_pt().set_x(self.get_pt().get_x() + (self.get_w() - self.get_h()))
					hb = self.get_hbps()[0]
					hb.get_pt().set_x(hb.get_pt().get_x() + (hb.get_w() - self.get_h()))
					# print(self.get_pt().get_x())
				self.change_dimensions()
				self.set_is_stuck(False)
			else:
				self.set_is_stuck(True)
			# print("\n\n\n\n",self.get_pt().get_x(), "\n\n\n\n")
			self._is_sliding = not can_stand

	def change_dimensions(self) -> None:
		temp = self.get_h()
		self.set_h(self.get_w())
		self.set_w(temp)
		self.get_pt().set_y(self.get_pt().get_y() + (self.get_w() - self.get_h()))
		can_slide = True
		for hb in self.get_hbps():
			temp = hb.get_h()
			hb.set_h(hb.get_w())
			hb.set_w(temp)
			hb.get_pt().set_y(hb.get_pt().get_y() + (hb.get_w() - hb.get_h()))

	def handle_keys(self, keys_down: list[bool], hb_mouse: Hitbox, delta: float, walls: list[Surface], teleporters: list[Teleporter]) -> None:
		if not self.get_can_fly():
			self.get_vec_move().set_y(self.get_vec_move().get_y() + 1000 * delta)
			# if self.get_vec_move().get_y() > self.get_terminal_vel():
			# 	self.get_vec_move().set_y(self.get_terminal_vel())
		# print(self.get_space_was_down())
			if keys_down[self.user.jump] and self.get_is_grounded() and not self.get_jumped_while_sliding():
				# print(self.get_is_grounded())
				# print(self.get_vec_move().get_y() - 500)
				self.get_vec_move().set_y(self.get_vec_move().get_y() - 500)
				# print(self.get_vec_move().get_y(), self.get_vec_move().get_y() - 500)
				# print(self.get_space_was_down(), "aaaaaaaa")
				self.set_is_grounded(False)
				self.set_space_was_down(False)
				if self.get_is_sliding():
					self.set_jumped_while_sliding(True)
			elif keys_down[self.user.jump] and not self.get_is_grounded() and self.get_can_double_jump() and self.get_space_was_down() and not self.get_jumped_while_sliding():
				self.get_vec_move().set_y(0)
				self.get_vec_move().set_y(self.get_vec_move().get_y() - 350)
				self.set_can_double_jump(False)
				self.set_space_was_down(False)
				if self.get_is_sliding():
					self.set_jumped_while_sliding(True)
			elif not keys_down[self.user.jump] and not self.get_space_was_down():
				self.set_space_was_down(True)
			if keys_down[self.user.walk_left] and not self.get_is_sliding():
				move = -self.get_ms()
				if not self.get_is_grounded():
					move *= .45
				self.get_vec_move().set_x(move)
			if keys_down[self.user.walk_right] and not self.get_is_sliding():
				move = self.get_ms()
				if not self.get_is_grounded():
					move *= .45
				self.get_vec_move().set_x(move)
			if keys_down[self.user.walk_left] and self.get_is_sliding() and self.get_is_stuck():
				self.set_is_sliding(False, walls, delta, keys_down)
				move = -self.get_ms()
				self.get_vec_move().set_x(move)
			if keys_down[self.user.walk_right] and self.get_is_sliding() and self.get_is_stuck():
				self.set_is_sliding(False, walls, delta, keys_down)
				move = self.get_ms()
				self.get_vec_move().set_x(move)
			if keys_down[self.user.slide] and self.get_is_grounded() and not self.get_is_sliding():
				self.set_is_sliding(True, walls, delta, keys_down)
		else:
			if keys_down[K_p]:
				self.set_can_fly(not self.get_can_fly())
			else:
				if keys_down[K_SPACE]:
					self.get_vec_move().set_y(self.get_vec_move().get_y() - 10)
				elif keys_down[K_LCTRL]:
					self.get_vec_move().set_y(self.get_vec_move().get_y() + 10)
				else:
					self.get_vec_move().set_y(0)
				if keys_down[K_a]:
					self.get_vec_move().set_x(-self.get_ms())
				elif keys_down[K_d]:
					self.get_vec_move().set_x(self.get_ms())
				else:
					self.get_vec_move().set_x(0)
		# print(self.get_vec_move())
		# force = (keys_down[K_d] * self.get_ms() + keys_down[K_a] * -1 * self.get_ms())
		p_temp = copy.deepcopy(self)
		# print(p_temp)

		p_temp.get_pt().set_y(p_temp.get_pt().get_y() + p_temp.get_vec_move().get_y() * delta)
		# print(p_temp.get_pt())
		p_temp.update_hbps()
		is_grounded = False
		for wall in walls:
			if p_temp.check_collisions(wall):
				if wall.get_is_teleport():
					if wall.get_is_active():
						if wall.get_next_tp() != wall:
							wall.teleport(self, walls)
					elif wall.get_num() != 0 and not teleporters[0].get_is_active():
						wall.set_is_active(True)
						teleporters[0].set_is_active(True)
						for tp in teleporters:
							if tp.get_is_active():
								tp.set_next_tp(wall)
					elif wall.get_num() != 0:
						wall.set_is_active(True)
						# print(wall.get_num(), teleporters[0].get_next_tp().get_num())
						if wall.get_num() > teleporters[0].get_next_tp().get_num():
							for tp in teleporters:
								if tp.get_is_active():
									tp.set_next_tp(wall)
						else:
							wall.set_next_tp(teleporters[0].get_next_tp())

				# print(type(wall))
				elif wall.get_can_kill():
					self.set_is_alive(False)
					break
				elif wall.get_is_finish():
					self.set_is_finished(True)
					break
				# print("Yes")
				p_temp.get_pt().set_y(p_temp.get_pt().get_y() - p_temp.get_vec_move().get_y() * delta)
				if self.get_vec_move().get_y() > 0:
					# print("Yes")
					# self.get_vec_move().set_x(0)
					is_grounded = True
					# if self.get_is_sliding():
					# 	friction_reduction = abs(self.get_vec_move().get_x()) - (abs(self.get_vec_move().get_x()) * wall.get_friction() * 108 * delta)
					# 	# print(friction_reduction)
					# else:
					# 	friction_reduction = abs(self.get_vec_move().get_x()) - (abs(self.get_vec_move().get_x()) * wall.get_friction() * 100 * delta)
					# print(wall.get_friction())
					self.get_vec_move().set_x(self.get_vec_move().get_x() + (self.get_vec_move().get_x() * wall.get_friction()) * 60 * delta)
					# print(self.sget_vec_move())
					if abs(self.get_vec_move().get_x()) < .08:
						# print("Yes?")
						self.set_is_sliding(False, walls, delta, keys_down)
						self.get_vec_move().set_x(0)
						self.set_jumped_while_sliding(False)
					# print(self.get_vec_move().get_y())
					# if self.get_vec_move().get_y() > 1000:
					# 	print("Splat sfx")
				self.get_vec_move().set_y(0)
				break
		p_temp.get_pt().set_x(p_temp.get_pt().get_x() + p_temp.get_vec_move().get_x() * delta)
		p_temp.update_hbps()
		if self.get_is_alive() or self.get_is_finished():
			for wall in walls:
				if p_temp.check_collisions(wall):
					if wall.get_can_kill():
						self.set_is_alive(False)
						break
					if wall.get_is_finish():
						self.set_is_finished(True)
						break
					p_temp.get_pt().set_x(p_temp.get_pt().get_x() - p_temp.get_vec_move().get_x())
					if p_temp.get_is_sliding() and not p_temp.get_is_grounded():
						self.get_vec_move().set_x(-self.get_vec_move().get_x() * .3)
					else:
						self.get_vec_move().set_x(0)
					break
		# print("B", self.get_vec_move(), self.get_is_grounded())
		# print(self.get_vec_move(), "Delta:", delta, "FPS:", (1/delta))
		self.set_is_grounded(is_grounded)
		if is_grounded:
			self.set_can_double_jump(True)

		self.get_pt().set_x(self.get_pt().get_x() + self.get_vec_move().get_x() * delta)
		# print("X * delta^2:", self.get_vec_move().get_x() * 100 * (delta ** 2), "Delta:", delta, "FPS:", (1/delta))
		# print(self.get_vec_move().get_y() * delta, "What")
		for wall in walls:
			wall.get_pt().set_y(wall.get_pt().get_y() - self.get_vec_move().get_y() * delta)
		# print(self.get_vec_move())
		# print(self.get_vec_move().get_y() * delta)
		# print(self.get_pt())
		self.update_hbps()

	def draw(self, win: pygame.Surface, color: str = "#00ff00") -> None:
		super().draw(win)

class Surface(Hitbox):
	def __init__(self, pt: Vector, w: float, h: float, friction: float, color: str = "#000000", can_kill: bool = False, is_finish: bool = False, is_teleport: bool = False):
		super().__init__(pt, w, h, color)
		self._friction = friction
		self._can_kill = can_kill
		self._is_finish = is_finish
		self._is_teleport = is_teleport

	def get_friction(self) -> float:
		return self._friction
	def set_friction(self, friction: float) -> None:
		self._friction = friction
	def get_can_kill(self) -> bool:
		return self._can_kill
	def set_can_kill(self, can_kill: bool) -> None:
		self._can_kill = can_kill
	def get_is_finish(self) -> bool:
		return self._is_finish
	def set_is_finish(self, is_finish: bool) -> None:
		self._is_finish = is_finish
	def get_is_teleport(self) -> bool:
		return self._is_teleport
	def set_is_finish(self, is_teleport: bool) -> None:
		self._is_teleport = is_teleport

class Teleporter(Surface):
	def __init__(self, pt: Vector, w: float, h: float, next_tp: Teleporter, num: int, friction: float = -.15, color: str = "#7c7c7c"):
		super().__init__(pt, w, h, friction, color, False, False, True)
		self._next_tp = next_tp
		self._is_active = False
		self._num = num
		self._not_active_color = "#7c7c7c"
		self._active_color = "#990099"

	def get_next_tp(self) -> Teleporter:
		return self._next_tp
	def set_next_tp(self, tp: Teleporter) -> None:
		self._next_tp = tp
	def get_is_active(self) -> bool:
		return self._is_active
	def set_is_active(self, is_active: bool) -> None:
		self._is_active = is_active
		self.set_color(self._active_color)
	def get_num(self) -> int:
		return self._num
	def set_num(self, num: int) -> None:
		self._num = num

	def calc_height(self) -> float:
		dis = self.get_next_tp().get_pt().get_y() - self.get_pt().get_y()
		return dis

	def teleport(self, player: Player, walls: list[Surface]) -> None:
		player.get_pt().set_x(self.get_next_tp().get_pt().get_x() + (self.get_next_tp().get_w() / 2) - (player.get_w() / 2))
		player.get_vec_move().set_x(0)
		player.get_vec_move().set_y(0)
		dif = self.calc_height()
		# print("teleport sfx")
		for wall in walls:
			wall.get_pt().set_y(wall.get_pt().get_y() - dif)



class Button(Hitbox):
	def __init__(self, pt: Vector, w: float, h: float, text: String, has_border: bool, location: String, font: pygame.font, color: str = "#ffffff"):
		super().__init__(pt, w, h, color)
		self._text = text
		self._has_border = has_border
		self._next_loc = location
		self._font = font
		self.toggle = False

	def get_text(self) -> str:
		return self._text
	def set_text(self, text: str) -> None:
		self._text = text
	def get_border(self):
		return self._has_border
	def set_border(self, has_border):
		self._has_border = has_border
	def get_next_loc(self) -> String:
		return self._next_loc
	def set_next_loc(self, loc: String) -> None:
		self._next_loc = loc
	def get_font(self) -> pygame.font:
		return self._font
	def set_font(self, font: pygame.font) -> None:
		self._font = font

	def draw(self, win: pygame.Surface):
		# super().draw(win)
		# 40 font
		font = self.get_font()
		surf_text = font.render(self.get_text(), True, self.get_color())
		win.blit(surf_text, ((self.get_pt().get_x(), self.get_pt().get_y())))

class ToggleButton(Button):
	def __init__(self, pt: Vector, w: float, h: float, text, user, value: bool, has_border: bool, location: String, font: pygame.font, color: str = "#ff0000"):
		super().__init__(pt, w, h, text, has_border, location, font, color)
		self.on_color = "#00ff00"
		self.off_color = "#ff0000"
		self.value = value
		self.toggle = True
		self.setting = 4
		self.user = user

	def draw(self, win: pygame.Surface):
		# super().draw(win)
		# 40 font
		font = self.get_font()
		surf_text = font.render(self.get_text(), True, self.get_color())
		win.blit(surf_text, ((self.get_pt().get_x(), self.get_pt().get_y())))

class Map():
	def __init__(self, name: str, size: str, difficultly: str, description: str):
		self._vert_offset = 0
		self._name = name
		self._size = size
		self._difficulty = difficultly
		self._description = description
		self._best_times = []


	def get_name(self) -> str:
		return self._name
	def set_name(self, name: str) -> None:
		self._name = name
	def get_size(self) -> str:
		return self._size
	def set_size(self, size: str) -> None:
		self._size = size
	def get_difficulty(self) -> str:
		return self._difficulty
	def set_difficulty(self, difficulty: str) -> None:
		self._difficulty = difficulty
	def get_description(self) -> str:
		return self._description
	def set_description(self, description: str) -> None:
		self._description = description
	def get_vert_offset(self) -> float:
		return self._vert_offset
	def set_vert_offset(self, vert_offset: float) -> None:
		self._vert_offset = vert_offset
	def add_vert_offset(self, vert_offset: float) -> None:
		self._vert_offset += vert_offset
