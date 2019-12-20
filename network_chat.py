import pygame
import pygame_gui

from network.server import Server
from network.client import Client

from pygame_gui.ui_manager import UIManager
from pygame_gui.elements.ui_button import UIButton

from gui.chat_room_window import ChatWindow
from gui.enter_name_window import EnterNameWindow


class NetworkChatApp:
    def __init__(self):
        pygame.init()
        self.app_title = 'Pygame Chat'
        self.window_size = (800, 600)
        pygame.display.set_caption(self.app_title)
        self.window_surface = pygame.display.set_mode(self.window_size)

        self.background_surface = pygame.Surface(self.window_size)
        self.background_surface.fill(pygame.Color('#404040'))

        self.ui_manager = UIManager(self.window_size)

        self.start_server_button = UIButton(relative_rect=pygame.Rect(325, 200, 150, 40),
                                            text='Start Server',
                                            manager=self.ui_manager)

        self.join_server_button = UIButton(relative_rect=pygame.Rect(325, 300, 150, 40),
                                           text='Join Server',
                                           manager=self.ui_manager)

        self.chat_window = None
        self.name_entry_window = None

        # networking
        self.server = None
        self.client = None

        self.clock = pygame.time.Clock()
        self.running = True

    def run(self):
        while self.running:
            time_delta = self.clock.tick(60)/1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.USEREVENT and event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.start_server_button:
                        self.server = Server()

                    if event.ui_element == self.join_server_button:
                        self.client = Client(server_ip='192.168.1.26', app=self)
                        enter_name_rect = pygame.Rect(100, 100, 300, 60)
                        enter_name_rect.center = (int(self.window_size[0]/2), int(self.window_size[1]/2))
                        self.name_entry_window = EnterNameWindow(rect=enter_name_rect,
                                                                 manager=self.ui_manager)

                if event.type == pygame.USEREVENT and event.user_type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                    if self.chat_window is not None and event.ui_element == self.chat_window.chat_entry:
                        self.client.send_chat_message(event.text)
                        self.chat_window.chat_entry.set_text('')
                    elif self.name_entry_window is not None and event.ui_element == self.name_entry_window.name_entry:
                        self.client.first_entry(event.text)
                        self.name_entry_window.kill()
                        if self.chat_window is not None:
                            self.chat_window.kill()
                        self.chat_window = ChatWindow(rect=pygame.Rect(50, 50, 700, 500),
                                                      room_name='Hello World',
                                                      manager=self.ui_manager)

                self.ui_manager.process_events(event)

            if self.server is not None:
                self.server.update()

            if self.client is not None:
                self.client.update()

            self.ui_manager.update(time_delta)

            self.window_surface.blit(self.background_surface, (0, 0))
            self.ui_manager.draw_ui(self.window_surface)

            pygame.display.flip()


if __name__ == '__main__':
    app = NetworkChatApp()
    app.run()
