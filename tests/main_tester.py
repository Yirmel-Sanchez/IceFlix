'''Main Tester'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import Ice

Ice.loadSlice("../iceflix/iceflix.ice")
import IceFlix # pylint: disable=import-error, wrong-import-position


class MainTester(IceFlix.Main):
    '''MainTester class.'''
    def __init__(self):
        self.proxy_service = None

    def getAuthenticator(self, current=None): # pylint: disable=unused-argument, invalid-name
        '''Obtiene el proxy del authenticator.'''
        return IceFlix.AuthenticatorPrx.uncheckedCast(server.proxy_auth)

    def newService(self, proxy, service_id, current=None): # pylint: disable=unused-argument, invalid-name
        '''Agregar un nuevo servicio.'''
        self.proxy_service = proxy
        logging.info("New service: %s\n", service_id)
        with open('../configs/catalog_proxy.proxy', 'w', encoding="utf-8") as file:
            file.write(server.communicator().proxyToString(self.proxy_service))

    def announce(self, proxy, service_id, current=None): # pylint: disable=unused-argument, invalid-name
        '''Anunciar un servicio.'''
        logging.info("Announce service: %s\n", service_id)


class Server(Ice.Application):
    '''Server class.'''
    def __init__(self):
        super().__init__()
        self.servant = MainTester()
        self.proxy = None
        self.proxy_auth = None
        self.adapter = None
        self.str_proxy_auth = ""

    def run(self, args):
        comm = self.communicator()

        self.adapter = comm.createObjectAdapter("TestMainAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.add(self.servant, comm.stringToIdentity("MainTester"))
        logging.info("Proxy MainTester: %s\n", self.proxy)

        with open('../configs/main_proxy.proxy', 'w', encoding="utf-8") as file:
            file.write(comm.proxyToString(self.proxy))

        # Authenticator
        with open('../configs/auth_proxy.proxy', 'r', encoding="utf-8") as file:
            self.str_proxy_auth = file.readline()

        self.proxy_auth = self.communicator().stringToProxy(self.str_proxy_auth)
        #logging.info("Proxy AuthenticatorTester: %s\n", self.proxy_auth)

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = Server()
    sys.exit(server.main(sys.argv))
