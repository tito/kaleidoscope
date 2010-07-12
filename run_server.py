'''Kaleidoscope - Server

Start a new server, according to the configuration file.
'''

if __name__ == '__main__':
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
