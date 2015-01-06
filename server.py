#!/usr/bin/env python
import asyncore
import socket
from pytwradio import Pytwradio
import tempfile
import subprocess as sp

class RadioHandler(asyncore.dispatcher):
    def __init__(self, client_socket, client_address, radio_id ):
        print 'init Handler.'
        self.client_address = client_address
        self.radio_id = radio_id
        self.radio = Pytwradio(radio_id)
        asyncore.dispatcher.__init__(self, client_socket)

    # normally shouldn't really be reading much from the client.
    # should be just once at the beginning (the request/headers),
    #   and then once at the end when they disconnect (I believe this is for
    #   clients that send connection:close in the headers
    def readable(self):
        return True
    # Shoutcast servers should always be able to write data
    def writable(self):
        return True

    def handle_read(self):
        data = self.recv(8192)
        print data

    def handle_write(self):
      for dat in self.radio.capture_nonblocking(t=-1,DEBUG=True):
        wavdata = Pytwradio.ts2mp3(dat)
        print 'send data %d' % len(wavdata)
        self.send( wavdata )

    # closing connection
    def handle_close(self):
        print "lost client"
        self.close()

class RadioServer(asyncore.dispatcher):

    def __init__(self, host, port, radio_id):
        asyncore.dispatcher.__init__(self)
        self.radio_id = radio_id
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.clientHandler = RadioHandler
        self.listen(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            self.clientHandler(sock, addr, self.radio_id)

    # start serving requests
    def run(self):
        print 'Listerning...'
        asyncore.loop()

if __name__ == "__main__":
    server = RadioServer('localhost', 8888, 1490)
    server.run() 
