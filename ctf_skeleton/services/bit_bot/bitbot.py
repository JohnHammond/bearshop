#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: john
# @Date:   2016-02-08 08:44:14
# @Last Modified by:   john
# @Last Modified time: 2016-02-14 17:03:45

import threading
import SocketServer
from colorama import *
from random import randint, choice, seed
from time import mktime, gmtime, sleep
from string import digits as nums
from json import loads
import sys

service_name = "BitBot"

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

def get_flag():

    h = open( 'flag' )
    the_flag = h.read()
    h.close()
    return the_flag

class Service(SocketServer.BaseRequestHandler):

    def send( self, string, newline = True ):
        if newline: string = string + "\n"

        self.request.sendall( string )

    def receive( self, prompt = "" ):
        self.send( prompt, newline=False )
        return self.request.recv( 4096 ).strip()

    def handle(self):
        '''
        This handle() function is like the main function of the server;
        it is what is ran after each connection.
        '''

        # Server-side: ...
        info( "Received connection from " + str(self.client_address) + "!" )

        # Client-side: ...
        # try:
            # run self.functions()...

        flag = get_flag()

        try:
            for bit in flag:
                sent = bin(ord(bit))[2:]
                self.send( sent )
                entered = self.receive()
                if ( entered != sent ):
                    return
                else:
                    continue
            pass
        except:
            warning( "Dropped connection with " + str(self.client_address) + "." )                    

        

        info( "Ended connection with " + str(self.client_address) + "." )
        

        # except:
        #     log( Fore.YELLOW + self.client_address[0] + " dropped connection!" )

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