import json
import logging
import threading

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection

log = logging.getLogger(__name__)

class StreamerConnection(SockJSConnection):
    connections = set()

    def on_open(self, info):
	self.connections.add(self)

    def on_message(self, msg):
        self.send(msg)

    def on_close(self):
	self.connections.remove(self)

_port = 5001

def _init_streamer():
    StreamerRouter = SockJSRouter(StreamerConnection, '/streamer')

    app = web.Application(StreamerRouter.urls)
    app.listen(_port)
    ioloop.IOLoop.instance().start()

def init_streamer(port = 5001):
    _port = int(port)
    t = threading.Thread(target=_init_streamer)
    t.daemon = True
    t.start()

def add_port():
    return { 'port' : _port }

def after_save(annotation):
    for connection in StreamerConnection.connections :
    	#connection.send(json.dumps(annotation))
    	connection.send(annotation)


