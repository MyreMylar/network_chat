import sys
import selectors
import json
import io
import struct
import html
import pygame
import math


class ServerMessage:
    def __init__(self, selector, sock, addr, all_clients):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False

        self.all_clients = all_clients
        self.golden_ratio = ((5 ** 0.5) - 1) / 2

    def clear_server_message_on_new_read(self):
        self._recv_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _broadcast(self):
        # Should be ready to broadcast
        all_buffers_empty = True
        for client_address in self.all_clients:
            if self.all_clients[client_address]['send_buffer']:
                print("broadcasting", repr(self.all_clients[client_address]['send_buffer']), "to", client_address)
                try:
                    sent = self.all_clients[client_address]['socket'].send(self.all_clients[client_address]['send_buffer'])
                except BlockingIOError:
                    # Resource temporarily unavailable (errno EWOULDBLOCK)
                    pass
                else:
                    self.all_clients[client_address]['send_buffer'] = self.all_clients[client_address]['send_buffer'][sent:]
                    if len(self.all_clients[client_address]['send_buffer']) != 0:
                        all_buffers_empty = False
        if all_buffers_empty:
            self._set_selector_events_mask("r")

    @staticmethod
    def _json_encode(obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    @staticmethod
    def _json_decode(json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message(
        self, *, content_bytes, content_type, content_encoding
    ):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        return message_hdr + jsonheader_bytes + content_bytes

    def _create_response_json_content(self):
        action = self.request.get("action")
        if action == "send_message":
            message = html.escape(self.request.get("value"))
            message_and_name = '<font color=' + self.all_clients[self.addr]['colour'] + '><b>&lt;' + self.all_clients[self.addr]['name'] + '&gt;</b> ' + message + '</font>'
            content = {"result": message_and_name}
        elif action == "change_name":
            name = html.escape(self.request.get("value"))
            self.all_clients[self.addr]['name'] = name
            content = {'result': 'Name successfully changed to ' + name}
        elif action == "on_connection":
            print(self.request.get("value") + ' Connected')
            return {}
        elif action == "first_entry":
            color = pygame.Color("#000000")
            color.hsla = 360 * ((len(self.all_clients) * self.golden_ratio) % 1), 50, 70, 100
            hex_code_map = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
            red_first = hex_code_map[int(math.floor(color.r / 16.0))]
            red_second = hex_code_map[int(math.floor((color.r % 16.0)))]
            green_first = hex_code_map[int(math.floor(color.g / 16.0))]
            green_second = hex_code_map[int(math.floor((color.g % 16.0)))]
            blue_first = hex_code_map[int(math.floor(color.b / 16.0))]
            blue_second = hex_code_map[int(math.floor((color.b % 16.0)))]
            color_code = '#' + red_first + red_second + green_first + green_second + blue_first + blue_second

            name = html.escape(self.request.get("value"))
            self.all_clients[self.addr]['name'] = name
            self.all_clients[self.addr]['colour'] = color_code
            content = {'result': name + ' has entered the chat...'}
        elif action == "quit":
            self.close()
            return {}
            # message = self.request.get("value")
            # content = {"result": message}
        else:
            content = {"result": f'Error: invalid action "{action}".'}
        content_encoding = "utf-8"
        return {
                "content_bytes": self._json_encode(content, content_encoding),
                "content_type": "text/json",
                "content_encoding": content_encoding,
            }

    def _create_response_binary_content(self):
        return {
                "content_bytes": b"First 10 bytes of request: "
                + self.request[:10],
                "content_type": "binary/custom-server-binary-type",
                "content_encoding": "binary",
            }

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.broadcast()

    def read(self):
        self.clear_server_message_on_new_read()
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None and self.jsonheader is None:
            self.process_jsonheader()

        if self.jsonheader and self.request is None:
            self.process_request()

    def broadcast(self):
        if self.request and not self.response_created:
            self.create_response()

        self._broadcast()

    def close(self):
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                f"error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None
            self.all_clients[self.addr] = None

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_request(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.request = self._json_decode(data, encoding)
            print("received request", repr(self.request), "from", self.addr)
        else:
            # Binary or unknown content-type
            self.request = data
            print(
                f'received {self.jsonheader["content-type"]} request from',
                self.addr,
            )
        # Set selector to listen for broadcast events, we're done reading.
        self._set_selector_events_mask("w")

    def create_response(self):
        if self.jsonheader["content-type"] == "text/json":
            response = self._create_response_json_content()
        else:
            # Binary or unknown content-type
            response = self._create_response_binary_content()

        if len(response) > 0:
            message = self._create_message(**response)
            self.response_created = True
            for client_addr in self.all_clients:
                self.all_clients[client_addr]['send_buffer'] += message
