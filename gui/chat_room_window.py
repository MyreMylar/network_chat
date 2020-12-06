import pygame

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.ui_manager import UIManager
from pygame_gui.elements.ui_text_box import UITextBox
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine


from pygame_gui.core import ObjectID


class ChatWindow(UIWindow):
    def __init__(self,
                 rect: pygame.Rect,
                 room_name: str,
                 manager: UIManager):
        super().__init__(rect, manager,
                         window_display_title=room_name,
                         object_id=ObjectID('#chat_room_window', None))

        self.room_name = room_name

        self.chat_log_list = []

        self.chat_log = UITextBox(html_text="",
                                  relative_rect=pygame.Rect((0, 0),
                                                            (self.get_container().get_size()[0],
                                                             self.get_container().get_size()[1]-40)),
                                  manager=manager,
                                  container=self,
                                  parent_element=self,
                                  object_id=ObjectID('#chat_log', None))

        self.chat_entry = UITextEntryLine(pygame.Rect(0,
                                                      self.chat_log.get_relative_rect().bottom,
                                                      self.get_container().get_size()[0],
                                                      40),
                                          manager=manager,
                                          container=self,
                                          parent_element=self,
                                          object_id=ObjectID('#chat_entry', None))

    def add_new_chat_line_to_log(self, chat_message):
        self.chat_log_list.append(chat_message)

        self.convert_log_to_formatted_block()

    def convert_log_to_formatted_block(self):
        text = "<br>".join(self.chat_log_list)
        self.chat_log.kill()
        self.chat_log = UITextBox(html_text=text,
                                  relative_rect=pygame.Rect((0, 0),
                                                            (self.get_container().get_size()[0],
                                                             self.get_container().get_size()[1] - 40)),
                                  manager=self.ui_manager,
                                  container=self,
                                  parent_element=self,
                                  object_id=ObjectID('#chat_log', None))
