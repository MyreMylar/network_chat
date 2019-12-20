from typing import List, Union

import pygame

from pygame_gui.core.ui_window import UIWindow
from pygame_gui.ui_manager import UIManager
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.core.drawable_shapes import RoundedRectangleShape, RectDrawableShape


class EnterNameWindow(UIWindow):
    def __init__(self,
                 rect: pygame.Rect,
                 manager: UIManager):
        super().__init__(rect, manager, ['chat_window'])

        self.menu_bar = UIButton

        self.menu_bar_height = 20
        self.close_button_width = 20
        self.grabbed_window = False
        self.starting_grab_difference = (0, 0)

        self.shadow_width = None  # type: Union[None, int]
        self.border_width = None  # type: Union[None, int]
        self.background_colour = None
        self.border_colour = None

        self.border_rect = None
        self.background_rect = None

        self.menu_bar = None
        self.close_window_button = None
        self.name_entry = None

        self.drawable_shape = None
        self.shape_type = 'rectangle'
        self.shape_corner_radius = None

        self.rebuild_from_changed_theme_data()

        self.menu_bar = UIButton(relative_rect=pygame.Rect((0, 0),
                                                           ((self.rect.width -
                                                             (self.shadow_width * 2)) - self.close_button_width,
                                                            self.menu_bar_height)),
                                 text='Enter your name',
                                 manager=manager,
                                 container=self.get_container(),
                                 parent_element=self,
                                 object_id='#message_window_title_bar'
                                 )
        self.menu_bar.set_hold_range((100, 100))

        self.close_window_button = UIButton(relative_rect=pygame.Rect(((self.rect.width - self.shadow_width * 2) -
                                                                       self.close_button_width,
                                                                       0),
                                                                      (self.close_button_width, self.menu_bar_height)),
                                            text='╳',
                                            manager=manager,
                                            container=self.get_container(),
                                            parent_element=self,
                                            object_id='#close_button'
                                            )

        remaining_space = pygame.Rect(0, self.menu_bar_height,
                                      self.background_rect.width,
                                      self.background_rect.height - self.menu_bar_height)

        self.name_entry = UITextEntryLine(pygame.Rect(0, self.menu_bar_height,
                                                      self.background_rect.width,
                                                      self.background_rect.height - self.menu_bar_height),
                                          manager=manager,
                                          container=self.get_container(),
                                          parent_element=self,
                                          object_id='#name_entry')

    def rebuild(self):
        """

        """
        border_rect_width = self.rect.width - (self.shadow_width * 2)
        border_rect_height = self.rect.height - (self.shadow_width * 2)
        self.border_rect = pygame.Rect((self.shadow_width,
                                        self.shadow_width),
                                       (border_rect_width, border_rect_height))

        background_rect_width = border_rect_width - (self.border_width * 2)
        background_rect_height = border_rect_height - (self.border_width * 2)
        self.background_rect = pygame.Rect((self.shadow_width + self.border_width,
                                            self.shadow_width + self.border_width),
                                           (background_rect_width, background_rect_height))

        theming_parameters = {'normal_bg': self.background_colour,
                              'normal_border': self.border_colour,
                              'border_width': self.border_width,
                              'shadow_width': self.shadow_width,
                              'shape_corner_radius': self.shape_corner_radius}

        if self.shape_type == 'rectangle':
            self.drawable_shape = RectDrawableShape(self.rect, theming_parameters,
                                                    ['normal'], self.ui_manager)
        elif self.shape_type == 'rounded_rectangle':
            self.drawable_shape = RoundedRectangleShape(self.rect, theming_parameters,
                                                        ['normal'], self.ui_manager)

        self.image = self.drawable_shape.get_surface('normal')

        self.get_container().relative_rect.width = self.rect.width - self.shadow_width * 2
        self.get_container().relative_rect.height = self.rect.height - self.shadow_width * 2
        self.get_container().relative_rect.x = self.relative_rect.x + self.shadow_width
        self.get_container().relative_rect.y = self.relative_rect.y + self.shadow_width
        self.get_container().update_containing_rect_position()

        if self.menu_bar is not None:
            self.menu_bar.set_dimensions(((self.rect.width - (self.shadow_width * 2)) - self.close_button_width,
                                          self.menu_bar_height))
        if self.close_window_button is not None:
            self.close_window_button.set_relative_position(((self.rect.width - self.shadow_width * 2) -
                                                            self.close_button_width, 0))

        if self.name_entry is not None:
            self.name_entry.set_relative_position(self.background_rect.topleft)
            # TODO: UI library - may need set dimensions on text_entry

    def update(self, time_delta: float):
        """
        Called every update loop of our UI manager. Handles moving and closing the window.

        :param time_delta: The time in seconds between calls to this function.
        """
        if self.alive():

            if self.menu_bar.held:
                mouse_x, mouse_y = self.ui_manager.get_mouse_position()
                if not self.grabbed_window:
                    self.window_stack.move_window_to_front(self)
                    self.grabbed_window = True
                    self.starting_grab_difference = (mouse_x - self.rect.x,
                                                     mouse_y - self.rect.y)

                current_grab_difference = (mouse_x - self.rect.x,
                                           mouse_y - self.rect.y)

                adjustment_required = (current_grab_difference[0] - self.starting_grab_difference[0],
                                       current_grab_difference[1] - self.starting_grab_difference[1])

                self.rect.x += adjustment_required[0]
                self.rect.y += adjustment_required[1]
                self.relative_rect.x = self.rect.x - self.ui_container.rect.x
                self.relative_rect.y = self.rect.y - self.ui_container.rect.y
                self.get_container().relative_rect.x += adjustment_required[0]
                self.get_container().relative_rect.y += adjustment_required[1]
                self.get_container().update_containing_rect_position()

            else:
                self.grabbed_window = False

            if self.close_window_button.check_pressed():
                self.kill()

        super().update(time_delta)

    def rebuild_from_changed_theme_data(self):
        """
        Called by the UIManager to check the theming data and rebuild whatever needs rebuilding for this element when
        the theme data has changed.
        """
        has_any_changed = False

        shape_type = 'rectangle'
        shape_type_string = self.ui_theme.get_misc_data(self.object_ids, self.element_ids, 'shape')
        if shape_type_string is not None and shape_type_string in ['rectangle', 'rounded_rectangle']:
            shape_type = shape_type_string
        if shape_type != self.shape_type:
            self.shape_type = shape_type
            has_any_changed = True

        corner_radius = 2
        shape_corner_radius_string = self.ui_theme.get_misc_data(self.object_ids,
                                                                 self.element_ids, 'shape_corner_radius')
        if shape_corner_radius_string is not None:
            try:
                corner_radius = int(shape_corner_radius_string)
            except ValueError:
                corner_radius = 2
        if corner_radius != self.shape_corner_radius:
            self.shape_corner_radius = corner_radius
            has_any_changed = True

        border_width = 1
        border_width_string = self.ui_theme.get_misc_data(self.object_ids, self.element_ids, 'border_width')
        if border_width_string is not None:
            try:
                border_width = int(border_width_string)
            except ValueError:
                border_width = 1

        if border_width != self.border_width:
            self.border_width = border_width
            has_any_changed = True

        shadow_width = 2
        shadow_width_string = self.ui_theme.get_misc_data(self.object_ids, self.element_ids, 'shadow_width')
        if shadow_width_string is not None:
            try:
                shadow_width = int(shadow_width_string)
            except ValueError:
                shadow_width = 2
        if shadow_width != self.shadow_width:
            self.shadow_width = shadow_width
            has_any_changed = True

        background_colour = self.ui_theme.get_colour_or_gradient(self.object_ids, self.element_ids, 'dark_bg')
        if background_colour != self.background_colour:
            self.background_colour = background_colour
            has_any_changed = True

        border_colour = self.ui_theme.get_colour_or_gradient(self.object_ids, self.element_ids, 'normal_border')
        if border_colour != self.border_colour:
            self.border_colour = border_colour
            has_any_changed = True

        if has_any_changed:
            self.rebuild()
