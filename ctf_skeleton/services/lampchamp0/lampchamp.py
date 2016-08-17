#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: john
# @Date:   2016-02-08 08:44:14
# @Last Modified by:   john
# @Last Modified time: 2016-02-14 17:04:35

import threading
import SocketServer
from colorama import *
from random import randint, choice, seed
from time import mktime, gmtime, sleep
from string import digits as nums
from json import loads
import sys

service_name = "LampChamp 0"

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

def center_text( text, width ):
    sides = width / 2 -  len(text) / 2
    return " " * sides + text + " " * sides

class Service(SocketServer.BaseRequestHandler):

    def send( self, string, newline = True ):
        if newline: string = string + "\n"

        self.request.sendall( string )

    def receive( self ):
        self.send( "> ", newline=False )
        return self.request.recv( 4096 ).strip()

    def print_banner( self ):

        self.send( "=" * max_width)
        self.send( center_text( "Welcome to LampChamp!", max_width ) )

        self.send( "=" * max_width )
        self.send( "" )

    def prompt( self ):
        ready = False
        
        self.send( "To become the LampChamp, you must turn on ALL the lights!" )
        self.send( "How many will there be? Well, you'll never know!" )
        
        self.send("")
        self.send( "Are you ready for this challenge? (y/n)" )

        while ( not ready ):

            entered = self.receive()
            
            if ( entered.startswith( "y" ) ):
                ready = True
            else:
                self.send( "Awww, why not? Come on, think it over! Are you ready? (y/n)" )
                ready = False

        self.send( "Awesome! Good luck!" )
        self.send( "Here is your first task: " )
        self.send( "" )

    def test_lamps( self ):

        '''
        This initialize() function takes the place of the object's
        __init__() constructor because that is annoying to overwrite with
        a threaded SocketServer object.
        '''

        number_of_lamps = randint(100,300)

        for i in range( number_of_lamps ):

            self.send( lamps[i % len(lamps)] )
            self.send( "Turn ON this lamp!" )

            lamp_state = self.receive(  ).lower()
            if ( lamp_state == "on" or lamp_state == "turn on"):
                self.send( "Congrats! You've now turned on " + str(i+1) + " lamps! " +\
                         "You're almost the LampChamp!" )
            else:
                self.send("Boo! You weren't able to turn the lamp on!")
                self.send("You can't handle this challenge. Better luck next time!")

                return False

        self.send("")
        self.send("You did it! You got all the lamps!")
        self.send("YOU ARE THE NEW LAMPCHAMP!!!")
        self.send("Here is your reward:")
        self.send( get_flag() )



    def handle(self):
        '''
        This handle() function is like the main function of the server;
        it is what is ran after each connection.
        '''

        # Server-side: ...
        info( "Received connection from " + str(self.client_address) + "!" )

        # Client-side: ...
        try:
            self.print_banner()
            self.prompt()
            self.test_lamps()
        except:
            warning( self.client_address[0] + " dropped connection!" )

        info( "Ended connection with " + str(self.client_address) + "!" )

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