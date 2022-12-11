'''AuthenticatorTester.'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import logging
import Ice


Ice.loadSlice("iceflix.ice")
import IceFlix # pylint: disable=import-error, wrong-import-position

class AuthenticatorTester(IceFlix.Authenticator):
    '''AuthenticatorTester class.'''
    def isAuthorized(self, userToken, current=None): # pylint: disable=unused-argument, invalid-name
        '''indica si el usuario esta autorizado.'''
        if userToken == "user01":
            return True
        return False

    def isAdmin(self, adminToken, current=None): # pylint: disable=unused-argument, invalid-name
        '''indica si el usuario es administrador.'''
        if adminToken == "admin01":
            return True
        return False


class Server(Ice.Application):
    '''Server class.'''
    def __init__(self):
        super().__init__()
        self.servant = AuthenticatorTester()
        self.proxy_auth = None
        self.adapter = None

    def run(self, args):
        comm = self.communicator()

        self.adapter = comm.createObjectAdapter("TestAuthenticatorAdapter")
        self.adapter.activate()

        self.proxy_auth = self.adapter.add(self.servant,
                                           comm.stringToIdentity("AuthenticatorTester"))
        logging.info("Proxy AuthenticatorTester: %s\n", self.proxy_auth)

        with open('../configs/auth_proxy.proxy', 'w', encoding="utf-8") as file:
            file.write(comm.proxyToString(self.proxy_auth))

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = Server()
    sys.exit(server.main(sys.argv))
