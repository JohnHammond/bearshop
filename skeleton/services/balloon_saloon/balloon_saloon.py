#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: john
# @Date:   2016-02-08 08:44:14
# @Last Modified by:   john
# @Last Modified time: 2016-02-14 17:03:36

import threading
import SocketServer
from colorama import *
from random import randint, choice, seed
from time import mktime, gmtime, sleep
from string import digits as nums
from json import loads
import sys

service_name = "Balloon Saloon"

debug = True
init( autoreset = True )

if (debug):

    def success( string ):
        print Fore.GREEN + Style.BRIGHT + "[+] " + string

    def error( string ):
        sys.stderr.write( Fore.RED + Style.BRIGHT + "[-] " + string + "\n" )

    def warning( string ):
        print Fore.YELLOW + "[!] " + string + "\n"

    def info( string ):
        print Fore.CYAN + "[.] " + string + "\n"


else:
    def success( string ): pass
    def error( string ): pass
    def warning( string ): pass
    def info( string ): pass

def get_port():
    handle = open("../../services.json")
    data = handle.read()
    data = loads(data.replace("\n",'').replace('\t',''))
    handle.close()

    port = None
    for service in data['services']:
        if service_name == service['title']:
            port = int(service['port'])

    if port == None:
        error("Port number not found in the configuration file!")
        exit(-1)
    else:
        return port

# DECLARE ALL INITIAL CONSTANTS
host = '0.0.0.0'
port = get_port()
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
        info( "Received connection from " + str(self.client_address) + "!" )

        # Client-side: ...
        '''
        try:
            # run self.functions()...
            pass
            
        except:
            log( Fore.YELLOW + self.client_address[0] + " dropped connection!" )
        '''

        self.send("There are 9 places the balloon can land, but it floats away at RANDOM!")
        self.send( board )
        self.send("Can you hit the balloon? I'm going to let the balloon go ... RIGHT NOW!")

        random_seed = int( mktime(gmtime()) )
        seed(random_seed)

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

        info( "Ended connection with " + str(self.client_address) + "." )

class ThreadedService(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass



def main():

    try:
        get_flag()
    except:
        error( "Could not get flag file!")
        exit(-1)

    info("Starting server..." )

    server = ThreadedService((host, port), Service)
    server.allow_reuse_address = True


    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    success( service_name + " started on " + str(server.server_address) + "!")
    
    # Now let the main thread just wait...
    while ( True ): sleep(10)

if __name__ == "__main__":
    main()
    