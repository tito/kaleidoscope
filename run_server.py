'''Kaleidoscope - Server

Start a new server, according to the configuration file.
'''

if __name__ == '__main__':
    from pymt import runTouchApp, getWindow
    from kaleidoscope.server import KalServerInteractive

    server = KalServerInteractive(size=getWindow().size)
    runTouchApp(server)

    '''
    import asyncore
    from kaleidoscope.server import KalServer, KalControler
    from kaleidoscope import config
    print '# Start Kaleidoscope server at', (config.server_ip, config.server_port)
    s = KalServer(config.server_ip, config.server_port)
    try:
        while True:
            asyncore.loop(timeout=.05, count=1)
            KalControler.get_instance().tick()
    except:
        print '# Close the socket...'
        s.close()
        raise
    '''

