import socket
import selectors
import traceback

from network.server_message import ServerMessage


class Server:
    def __init__(self):
        # network server stuff
        self.server_hosting_ip = self.get_ip_for_hosting()
        self.network_port = 25574  # Port to listen on (non-privileged ports are > 1023)
        self.server_listening_socket = None
        self.client_connection_sockets = {}
        # network event stuff
        self.server_selector = selectors.DefaultSelector()
        self.server_num_registered_event_handlers = 0

        self.server_listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_listening_socket.bind((self.server_hosting_ip, self.network_port))
        self.server_listening_socket.listen()
        print('Starting server on', (self.server_hosting_ip, self.network_port))
        self.server_listening_socket.setblocking(False)
        self.server_selector.register(self.server_listening_socket, selectors.EVENT_READ, data=None)
        self.server_num_registered_event_handlers += 1

    def update(self):
        if self.server_num_registered_event_handlers > 0:
            events = self.server_selector.select(timeout=0.005)
            for key, mask in events:
                if key.data is None:
                    self.accept_wrapper(key.fileobj)
                else:
                    self.service_connection(key, mask)

    @staticmethod
    def get_ip_for_hosting():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def accept_wrapper(self, listening_socket):
        new_connection, connection_address = listening_socket.accept()
        self.client_connection_sockets[connection_address] = {'socket': new_connection,
                                                              'send_buffer': b"",
                                                              'name': "Dan",
                                                              'colour': '#FFFFFF'}
        print('Accepted connection from', connection_address)
        new_connection.setblocking(False)

        # separate this ?
        message = ServerMessage(self.server_selector, new_connection,
                                connection_address, self.client_connection_sockets)
        self.server_selector.register(new_connection, selectors.EVENT_READ, data=message)
        self.server_num_registered_event_handlers += 1

    def service_connection(self, key, mask):
        message = key.data
        try:
            message.process_events(mask)
        except Exception:
            print(
                "main: error: exception for",
                f"{message.addr}:\n{traceback.format_exc()}",
            )
            message.close()
