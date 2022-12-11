#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import Ice
import logging

Ice.loadSlice("iceflix.ice")
import IceFlix


class AuthenticatorTester(IceFlix.Authenticator):
    def isAuthorized(self, userToken, current=None):
        if userToken == "user01":
            return True
        return False

    def isAdmin(self, adminToken, current=None):
        if adminToken == "admin01":
            return True
        return False


class Server(Ice.Application):
    def run(self, argv):
        comm = self.communicator()
        self.servant = AuthenticatorTester()

        self.adapter = comm.createObjectAdapter("TestAuthenticatorAdapter")
        self.adapter.activate()

        self.proxy_auth = self.adapter.add(self.servant, comm.stringToIdentity("AuthenticatorTester"))
        logging.info("Proxy AuthenticatorTester: %s\n", self.proxy_auth)

        with open('../configs/auth_proxy.proxy', 'w') as f:
            f.write(comm.proxyToString(self.proxy_auth))

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = Server()
    sys.exit(server.main(sys.argv))