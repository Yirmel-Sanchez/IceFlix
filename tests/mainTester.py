#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import Ice

Ice.loadSlice("../iceflix/iceflix.ice")
import IceFlix


class MainTester(IceFlix.Main):
    def __init__(self):
        self.proxy_service = None

    def getAuthenticator(self, current):
        return IceFlix.AuthenticatorPrx.uncheckedCast(server.proxy_auth)

    def newService(self, proxy, service_id, current=None):
        self.proxy_service = proxy
        logging.info("New service: %s\n", service_id)
        with open('../configs/catalog_proxy.proxy', 'w') as f:
            f.write(server.communicator().proxyToString(self.proxy_service))

    def announce(self, proxy, service_id, current=None):
        logging.info("Announce service: %s\n", service_id)


class Server(Ice.Application):
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

        with open('../configs/main_proxy.proxy', 'w') as fw:
            fw.write(comm.proxyToString(self.proxy))

        # Authenticator
        with open('../configs/auth_proxy.proxy', 'r') as f:
            self.str_proxy_auth = f.readline()

        self.proxy_auth = self.communicator().stringToProxy(self.str_proxy_auth)
        #logging.info("Proxy AuthenticatorTester: %s\n", self.proxy_auth)

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = Server()
    sys.exit(server.main(sys.argv))