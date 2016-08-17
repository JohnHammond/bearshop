#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: john
# @Date:   2016-02-08 08:44:14
# @Last Modified by:   John Hammond
# @Last Modified time: 2016-02-10 17:16:36

import threading
import SocketServer
from colorama import *
from random import randint, choice, seed
from time import mktime, gmtime
from string import digits as nums


# DECLARE ALL INITIAL CONSTANTS
host, port = "0.0.0.0", 5029
logging = True

service_name = "Balloon Saloon"

board = \
'''
      |     |
   1  |  2  |  3
  ____|_____|_____
      |     |
   4  |  5  |  6
  ____|_____|_____
      |     |
   7  |  8  |  9
      |     |

'''

def get_flag():

    h = open( 'flag' )
    the_flag = h.read()
    h.close()
    return the_flag

class Service(SocketServer.BaseRequestHandler):

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
        '''
        try:
            # run self.functions()...
            pass
            
        except:
            log( Fore.YELLOW + self.client_address[0] + " dropped connection!" )
        '''

        self.send("There are now 100 places the balloon can land, but it floats away at RANDOM!")
        self.send( board )
        self.send("Can you hit the balloon? I'm going to let the balloon go ... RIGHT NOW!")

        random_seed = int( mktime(gmtime()) )

        position = None
        entered = -1
        while int(entered) - 1 != position:
            self.send("What spot will you shoot?")
            entered = self.receive()
            position = randint(0, 8)
            try:
                if ( int(entered) - 1 == position ):
                    self.send("You shot the balloon! Here is your reward")
                    self.send(get_flag())
                    break
                else:
                    self.send( "Aww, you missed! Here's where the balloon was:")
                    balloon = board.replace( str(position + 1), 'O' )
                    for i in nums:
                        balloon = balloon.replace( str(i), ' ' ) 
                    self.send( balloon )
                    self.send("Try again!")
                    
                    continue
            except ValueError:
                continue

class ThreadedService(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def log( string ):
    if logging: print string

def main():

    # Turn on colors...
    init( autoreset=True )

    log( Fore.CYAN + "Starting server..." )

    server = ThreadedService((host, port), Service)
    server.allow_reuse_address = True

    log( Fore.MAGENTA + Style.BRIGHT + service_name + \
         Fore.GREEN + " server started on " + str(server.server_address) + "!")

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

if __name__ == "__main__":
    main()
    