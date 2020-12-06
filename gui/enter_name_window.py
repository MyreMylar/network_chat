from typing import Union

import pygame

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.ui_manager import UIManager
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.core import ObjectID


class EnterNameWindow(UIWindow):
    def __init__(self,
                 rect: pygame.Rect,
                 manager: UIManager):
        super().__init__(rect, manager,
                         window_display_title='Enter Name',
                         object_id=ObjectID('#enter_name_window', None))

        self.name_entry = UITextEntryLine(pygame.Rect(0, 0,
                                                      self.get_relative_rect().width,
                                                      40),
                                          manager=manager,
                                          container=self,
                                          parent_element=self,
                                          object_id=ObjectID('#name_entry', None))
