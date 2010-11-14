
def usage():
    import sys
    import os
    print 'Usage: %s <server ip> <nickname>' % \
        os.path.basename(sys.argv[0])
    sys.exit(0)

if __name__ == '__main__':
    from pymt import runTouchApp, getWindow
    from kaleidoscope.client import KalClientInteractive
    import sys

    options = {}
    l_argv = len(sys.argv)
    if l_argv != 3:
        usage()
    options['host'] = sys.argv[1]
    options['nickname'] = sys.argv[2]

    client = KalClientInteractive(size=getWindow().size, **options)
    runTouchApp(client)
