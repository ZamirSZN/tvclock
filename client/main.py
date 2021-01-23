import inspect
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST

from kivy.app import App
from kivy.properties import (
    StringProperty, ListProperty, ColorProperty, NumericProperty
)

from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer

PORT = 9998
PEER_PORT = 9999


class Remote(App):
    "Remote"
    host = StringProperty()
    scan_results = ListProperty()
    background_color = ColorProperty('#000000FF')
    clock_color = ColorProperty('#000000FF')
    clock_font_size = NumericProperty()

    def __init__(self, **kwargs):
        super(Remote, self).__init__(**kwargs)
        self.osc_server = None
        self.scan_client = None

    def on_start(self, **args):
        "stuff"
        self.current_screen = 'connect'
        self.osc_server = server = OSCThreadServer()
        self.osc_server.listen(address='0.0.0.0', port=PORT, default=True)
        server.bind(b'/found', callback=self.found)
        server.bind(b'/conf', callback=self.conf)

        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.settimeout(1)
        self.scan_client = OSCClient(
            address='255.255.255.255',
            port=PEER_PORT,
            sock=sock,
        )

    def found(self, *values):
        "when peer is found"
        print("peer found", values)
        frames = inspect.getouterframes(inspect.currentframe())
        for frame, filename, line, function, lines, index in frames:
            if function == '_listen' and 'oscpy/server.py' in filename:
                break
        else:
            raise RuntimeError('answer() not called from a callback')

        host, _ = frame.f_locals.get('sender')
        self.scan_results.append(
            {
                'name': values[0].decode('utf8'),
                'host': host
            }
        )

    def conf(
        self,
        background_r,
        background_g,
        background_b,
        clock_r,
        clock_g,
        clock_b,
        clock_font_size,
    ):
        self.background_color = background_r, background_g, background_b
        self.clock_color = clock_r, clock_g, clock_b
        self.clock_font_size = clock_font_size

    def scan(self):
        "look for peers"
        self.scan_results = []
        self.scan_client.send_message(b'/probe', [])

    def select_host(self, host):
        "select peer"
        self.host = host
        print(self.host)
        self.current_screen = 'remote'
        self.send('get_conf')

    def send(self, address, *values):
        "send to peer"
        print(address, values)
        print(self.osc_server.send_message(
            b'/%s' % address.encode('utf8'),
            values,
            ip_address=self.host,
            port=PEER_PORT
        ))


if __name__ == '__main__':
    Remote().run()
