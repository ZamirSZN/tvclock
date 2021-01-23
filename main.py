from socket import gethostname
from datetime import datetime
import json
from os.path import exists

from oscpy.server import OSCThreadServer

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.properties import ColorProperty, StringProperty, NumericProperty

PORT = 9999
PEER_PORT = 9998

CONF = 'conf.json'
TIME_FORMAT = "%H:%M:%S"


def get_screen_pos_size():
    return (0, 1080), (1920, 1080)


class Application(App):
    background_color = ColorProperty('#000000FF')
    clock_color = ColorProperty('#FFFFFFFF')
    clocktime = StringProperty("")
    clock_font_size = NumericProperty('100dp')

    def on_start(self, *_):
        Clock.schedule_interval(self.update_clocktime, .1)
        pos, size = get_screen_pos_size()
        Window.borderless = True
        Window.size = size
        Window.top, Window.left = pos

        if exists(CONF):
            with open(CONF) as f:
                conf = json.load(f)

            for k, v in conf.items():
                setattr(self, k, v)

    def update_clocktime(self, dt):
        self.clocktime = datetime.now().strftime(TIME_FORMAT)

    def on_stop(self, *_):
        conf = {
            'background_color': self.background_color,
            'clock_color': self.clock_color,
            'clock_font_size': self.clock_font_size,
        }

        with open(CONF, 'w') as f:
            json.dump(conf, f)


if __name__ == '__main__':
    APP = Application()
    SERVER = OSCThreadServer(encoding='utf8')
    SERVER.listen(address='0.0.0.0', port=PORT, default=True)

    @SERVER.address(b'/probe')
    def _probe(*_):
        print("got probe")
        host = gethostname()
        SERVER.answer(b'/found', values=[host], port=9998)

    @SERVER.address(b'/color/background')
    @mainthread
    def _background_color(r, g, b, a):
        print(r, g, b, a)
        APP.background_color = r, g, b, 1

    @SERVER.address(b'/color/clock')
    @mainthread
    def _clock_color(r, g, b, a):
        print(r, g, b, a)
        APP.clock_color = r, g, b, 1

    @SERVER.address(b'/font_size/clock')
    @mainthread
    def _clock_font_size(font_size):
        APP.clock_font_size = font_size

    @SERVER.address(b'/get_conf')
    def _send_conf():
        SERVER.answer(
            b'/conf',
            tuple(
                APP.background_color[:3]
                + APP.clock_color[:3]
                + [APP.clock_font_size]
            ),
            port=PEER_PORT
        )

    APP.run()
