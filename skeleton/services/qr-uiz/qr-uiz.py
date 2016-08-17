#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: john
# @Date:   2016-02-08 08:44:14
# @Last Modified by:   john
# @Last Modified time: 2016-02-08 16:35:22

import threading
import SocketServer
from colorama import *
from random import randint, choice

# DECLARE ALL INITIAL CONSTANTS
host, port = "0.0.0.0", 5000
logging = True

service_name = "QR-uiz"

class Service(SocketServer.BaseRequestHandler):

    def get_flag():

        h = open( 'flag' )
        the_flag = h.read()
        h.close()
        return the_flag

    def send( self, string, newline = True ):
        if newline: string = string + "\n"

        self.request.sendall( string )

    def receive( self ):
        self.send( "> ", newline=False )
        return self.request.recv( 4096 ).strip()

    def handle(self):
        '''
        This handle() function is like the main function of the server;
        it is what is ran after each connection.
        '''

        # Server-side: ...
        log( Fore.CYAN + "Received connection from " + \
             str(self.client_address) + "!" )

        # Client-side: ...
        try:
            # run self.functions()...
            pass
            
        except:
            log( Fore.YELLOW + self.client_address[0] + " dropped connection!" )

class ThreadedService(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def log( string ):
    if logging: print string


def main():

    # Turn on colors...
    init( autoreset=True )

    try:
        get_flag()
    except:
        log( Fore.RED + Style.BRIGHT + "Could not get flag file!")
        exit(-1)

    log( Fore.CYAN + "Starting server..." )

    server = ThreadedService((host, port), Service)
    server.allow_reuse_address = True

    log( Fore.MAGENTA + Style.BRIGHT + service_name + \
         Fore.GREEN + " server started on " + str(server.server_address) + "!")

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

if __name__ == "__main__":
    main()