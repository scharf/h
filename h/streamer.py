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

def _init_streamer():
    StreamerRouter = SockJSRouter(StreamerConnection, '/streamer')

    app = web.Application(StreamerRouter.urls)
    app.listen(5001)
    ioloop.IOLoop.instance().start()

def init_streamer():
    t = threading.Thread(target=_init_streamer)
    t.daemon = True
    t.start()


def after_save(annotation):
    for connection in StreamerConnection.connections :
    	#connection.send(json.dumps(annotation))
    	connection.send(annotation)


