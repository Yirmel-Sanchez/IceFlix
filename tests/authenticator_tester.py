'''AuthenticatorTester.'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import sys
import uuid
import logging
import threading
import Ice
import IceStorm

Ice.loadSlice("iceflix.ice")
import IceFlix # pylint: disable=import-error, wrong-import-position

########################################################################################
############################## Authenticator Servant ###################################

class AuthenticatorTester(IceFlix.Authenticator):
    '''AuthenticatorTester class.'''
    def isAuthorized(self, userToken, current=None): # pylint: disable=unused-argument, invalid-name, no-self-use
        '''indica si el usuario esta autorizado.'''
        if userToken == "user01":
            return True
        return False

    def isAdmin(self, adminToken, current=None): # pylint: disable=unused-argument, invalid-name, no-self-use
        '''indica si el usuario es administrador.'''
        if adminToken == "admin01":
            return True
        return False

########################################################################################
############################### Authenticator Server ###################################

class Server(Ice.Application): # pylint: disable=too-many-instance-attributes
    '''Server class.'''
    def __init__(self):
        super().__init__()
        self.id_service = str(uuid.uuid4())
        self.servant = AuthenticatorTester()
        self.proxy = None
        self.adapter = None
        self.fin = True
        self.interfaz_anuncios = None

        # variables TopicManager
        self.topic_manager_str_prx = "IceStorm/TopicManager -t:tcp -h localhost -p 10000"
        self.topic_manager = None

        #variables topics
        self.topic_announce_str = "Announcement"
        self.topic_announce = None
        self.anuncios_publisher = None

    def anunciar_servicio(self):
        """ Anunciar el servicio al main. """
        while self.fin:
            self.anuncios_publisher.announce(self.proxy, self.id_service)
            logging.info("Authenticator Tester anunciado\n")
            time.sleep(10)

    def recuperar_topic(self, topic_name):
        ''' Recuperar un topic del topic manager. '''
        try:
            topic = self.topic_manager.create(topic_name)
        except IceStorm.TopicExists: # pylint: disable=no-member
            topic = self.topic_manager.retrieve(topic_name)
        return topic

    def run(self, args):
        """ Run the application, adding the needed objects to the adapter. """
        logging.info("Running Authenticator application\n")
        broker = self.communicator()

        self.adapter = broker.createObjectAdapter("TestAuthenticatorAdapter")
        self.proxy = self.adapter.add(self.servant, broker.stringToIdentity("AuthenticatorTester"))
        self.adapter.activate()

        # conectarse al topic manager
        self.topic_manager = IceStorm.TopicManagerPrx.checkedCast( # pylint: disable=no-member
            broker.stringToProxy(self.topic_manager_str_prx),)

        if not self.topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        # establecer los topic
        self.topic_announce = self.recuperar_topic(self.topic_announce_str)

        ## publicador announcement
        anuncios_publisher_proxy = self.topic_announce.getPublisher()
        self.anuncios_publisher = IceFlix.AnnouncementPrx.uncheckedCast(anuncios_publisher_proxy)

        # Anunciamos el servicio al topic
        hilo_aux = threading.Thread(target=self.anunciar_servicio)
        hilo_aux.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        self.fin = False
        return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = Server()
    sys.exit(server.main(sys.argv))
