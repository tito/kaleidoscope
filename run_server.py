'''Kaleidoscope - Server

Start a new server, according to the configuration file.
'''

if __name__ == '__main__':
    from kaleidoscope.server import KalServerApp
    KalServerApp().run()

