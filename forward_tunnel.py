import SocketServer, paramiko, threading, select

class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler (SocketServer.BaseRequestHandler):
    def handle(self):

        try:
            chan = self.ssh_transport.open_channel('direct-tcpip',
                    (self.chain_host, self.chain_port),
                    self.request.getpeername())
        except Exception, e:
            print('Incoming request to %s:%d failed: %s' % (self.chain_host,
                self.chain_port,
                repr(e)))
            return
        if chan is None:
            print('Incoming request to %s:%d was rejected by the SSH server.' %
                    (self.chain_host, self.chain_port))
            return

        print('Connected!  Tunnel open %r -> %r -> %r' % (self.request.getpeername(),
            chan.getpeername(), (self.chain_host, self.chain_port)))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)

        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        print('Tunnel closed from %r' % (peername,))

def forward_tunnel(local_port, remote_host, remote_port, transport):

    # this is a little convoluted, but lets me configure things for the Handler
    # object.  (SocketServer doesn't give Handlers any way to access the outer
    # server normally.)

    class SubHander (Handler):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport

    server_thread = threading.Thread(target=ForwardServer(('', local_port), SubHander).serve_forever)
    server_thread.daemon = True
    server_thread.start()
