import socket
import selectors
import traceback

from network.client_message import ClientMessage


class Client:
    def __init__(self, server_ip, app):
        self.app = app

        self.client_ip = server_ip  # need a way to search for IPs using a port?
        self.network_port = 25574  # Port to listen on (non-privileged ports are > 1023)
        self.client_socket = None
        self.client_selector = selectors.DefaultSelector()
        self.client_num_registered_event_handlers = 0

        print('Joining server')
        request = self.create_request('on_connection', self.client_ip)
        self.start_connection(self.client_ip, self.network_port, request)

    def update(self):
        if self.client_socket is not None and self.client_num_registered_event_handlers > 0:
            events = self.client_selector.select(timeout=0.005)
            for key, mask in events:
                self.service_connection(key, mask)

    def start_connection(self, host, port, request):
        server_addr = (host, port)
        print("starting connection to", server_addr)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setblocking(False)
        self.client_socket.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        message = ClientMessage(self.client_selector, self.client_socket, server_addr, request, self.app)
        self.client_selector.register(self.client_socket, events, data=message)
        self.client_num_registered_event_handlers += 1

    def service_connection(self, key, mask):
        message = key.data
        try:
            message.process_events(mask)
            new_message = message.get_latest_text_from_server()
            if new_message is not None and self.app.chat_window is not None:
                self.app.chat_window.add_new_chat_line_to_log(new_message)
        except Exception:
            print(
                "main: error: exception for",
                f"{message.addr}:\n{traceback.format_exc()}",
            )
            message.close()

    def create_request(self, action, value):
        if action == "send_message":
            return dict(
                type="text/json",
                encoding="utf-8",
                content=dict(action=action, value=value),
            )
        elif action == "on_connection":
            return dict(
                type="text/json",
                encoding="utf-8",
                content=dict(action=action, value=value),
            )
        elif action == "first_entry":
            return dict(
                type="text/json",
                encoding="utf-8",
                content=dict(action=action, value=value),
            )
        elif action == "change_name":
            return dict(
                type="text/json",
                encoding="utf-8",
                content=dict(action=action, value=value),
            )
        else:
            return dict(
                type="binary/custom-client-binary-type",
                encoding="binary",
                content=bytes(action + value, encoding="utf-8"),
            )

    def send_chat_message(self, message):
        request = self.create_request('send_message', message)
        message = ClientMessage(self.client_selector, self.client_socket,
                                (self.client_ip, self.network_port), request, self.app)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.client_selector.modify(self.client_socket, events, data=message)

    def send_name_change(self, new_name):
        request = self.create_request('change_name', new_name)
        message = ClientMessage(self.client_selector, self.client_socket,
                                (self.client_ip, self.network_port), request, self.app)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.client_selector.modify(self.client_socket, events, data=message)

    def first_entry(self, name):
        request = self.create_request('first_entry', name)
        message = ClientMessage(self.client_selector, self.client_socket,
                                (self.client_ip, self.network_port), request, self.app)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.client_selector.modify(self.client_socket, events, data=message)
