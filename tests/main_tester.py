'''Main Tester'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import uuid
import logging
import threading
import Ice
import IceStorm

Ice.loadSlice("../iceflix/iceflix.ice")
import IceFlix # pylint: disable=import-error, wrong-import-position

########################################################################################
############################### Topic Announcement #####################################

class Announces(IceFlix.Announcement): # pylint: disable=too-few-public-methods
    '''Servant for the IceFlix.Announcement interface.'''
    def __init__(self):
        self.mains = {}
        self.authenticators = {}
        self.catalogs = {}
        self.files = {}
        self.service_id = server.id_service

    def announce(self, service, serviceId, current=None):  # pylint: disable=unused-argument, invalid-name
        '''Recoge los eventos de anuncios.'''
        if serviceId == self.service_id: # el servicio anunciado es el propio
            return

        all_services = {}
        all_services.update(self.mains)
        all_services.update(self.authenticators)
        all_services.update(self.catalogs)
        all_services.update(self.files)

        if serviceId in all_services: # el servicio ya está registrado
            return

        if service.ice_isA("::IceFlix::Main"):
            self.mains.update({serviceId: service})
            logging.info(" New Main service: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::Authenticator"):
            self.authenticators.update({serviceId: service})
            logging.info(" New Authenticator service: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::MediaCatalog"):
            self.catalogs.update({serviceId: service})
            logging.info(" New MediaCatalog service: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::FileService"):
            self.files.update({serviceId: service})
            logging.info(" New File service: %s\n", serviceId)

########################################################################################
################################### Main Servant #######################################

class MainTester(IceFlix.Main): # pylint: disable=too-few-public-methods
    '''MainTester class.'''
    def __init__(self):
        self.proxy_service = None

    def getAuthenticator(self, current=None): # pylint: disable=unused-argument, invalid-name, no-self-use
        '''Obtiene el proxy del authenticator.'''
        if len(server.interfaz_anuncios.authenticators) < 1:
            raise IceFlix.TemporaryUnavailable()

        proxy = list(server.interfaz_anuncios.authenticators.values())[0]
        return IceFlix.AuthenticatorPrx.uncheckedCast(proxy)

########################################################################################
################################### Main Server ########################################

class Server(Ice.Application): # pylint: disable=too-many-instance-attributes
    '''Server class.'''
    def __init__(self):
        super().__init__()
        self.id_service = str(uuid.uuid4())
        self.servant = MainTester()
        self.proxy = None
        self.adapter = None
        self.fin = True
        self.interfaz_anuncios = None

        # variables TopicManager
        self.topic_manager_str_prx = "IceStorm/TopicManager -t:tcp -h localhost -p 10000"
        self.topic_manager = None

        #variables topics
        self.topic_announce_str = "Announcements"
        self.topic_announce = None
        self.anuncios_subscriber_proxy = None
        self.anuncios_publisher = None

    def anunciar_servicio(self):
        """ Anunciar el servicio al main. """
        while self.fin:
            self.anuncios_publisher.announce(self.proxy, self.id_service)
            logging.info(" Main Tester anunciado\n")
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
        logging.info(" Running Main application\n")
        broker = self.communicator()

        self.adapter = broker.createObjectAdapter("TestMainAdapter")

        self.proxy = self.adapter.add(self.servant, broker.stringToIdentity("MainTester"))

        logging.info(" ServiceID MainTester: %s\n", self.id_service)
        self.adapter.activate()

        # conectarse al topic manager
        self.topic_manager = IceStorm.TopicManagerPrx.checkedCast(  # pylint:disable=no-member
            self.communicator().propertyToProxy("IceStorm.TopicManager")
        )

        if not self.topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        # interfaces de los topics
        self.interfaz_anuncios = Announces()

        # establecer los topic
        self.topic_announce = self.recuperar_topic(self.topic_announce_str)

        # definir los subscriptores y publicadores
        ## subscriptor announcement
        self.anuncios_subscriber_proxy = self.adapter.addWithUUID(self.interfaz_anuncios)
        self.topic_announce.subscribeAndGetPublisher({}, self.anuncios_subscriber_proxy)

        ## publicador announcement
        anuncios_publisher_proxy = self.topic_announce.getPublisher()
        self.anuncios_publisher = IceFlix.AnnouncementPrx.uncheckedCast(anuncios_publisher_proxy)

        # Anunciamos el servicio al topic
        hilo_aux = threading.Thread(target=self.anunciar_servicio)
        hilo_aux.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        self.fin = False

        # Desuscribirse de los topics
        self.topic_announce.unsubscribe(self.anuncios_subscriber_proxy)

        return 0

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = Server()
    sys.exit(server.main(sys.argv))
