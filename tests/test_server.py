'''Tester.'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import uuid
import logging
import threading
import json
import Ice
import IceStorm

Ice.loadSlice("../iceflix/iceflix.ice")
import IceFlix  # pylint: disable=import-error, wrong-import-position

########################################################################################
################################# Controlador BD #######################################


class DBController():
    '''Clase que controla la base de datos'''

    def __init__(self):
        '''Inicializador de la clase'''
        self.db_name = '../DB/media.json'
        self.media = self.cargar_media()

    def cargar_media(self):
        '''Carga la base de datos en memoria y la devuelve en forma de json'''
        try:
            with open(self.db_name, 'r', encoding='utf-8') as file:
                return json.load(file)
        except:  # pylint: disable=bare-except
            logging.error("Error al cargar la base de datos")
            return json.loads('{"medios":[]}')

    def guardar_media(self):
        '''Guarda la base de datos en disco'''
        try:
            with open(self.db_name, 'x', encoding='utf-8') as file:
                json.dump(self.media, file, indent=4)
        except FileExistsError:
            # El archivo ya existe, así que lo abrimos en modo escritura
            with open(self.db_name, 'w', encoding='utf-8') as file:
                json.dump(self.media, file, indent=4)

    def eliminar_medio(self, media_id):
        '''Elimina un medio de la base de datos'''
        for video in self.media["medios"]:
            if video["id"] == media_id:
                self.media["medios"].remove(video)
        return self.guardar_media()

########################################################################################
############################### Topic Announcement #####################################


class Announces(IceFlix.Announcement): # pylint: disable=too-few-public-methods
    '''Servant for the IceFlix.Announcement interface.'''

    def __init__(self):
        self.mains = {}
        self.authenticators = {}
        self.catalogs = {}
        self.files = {}
        self.service_id_file = server.id_service_file
        self.service_id_catalog = server.id_service_catalog

    def announce(self, service, serviceId, current=None):  # pylint: disable=unused-argument, invalid-name
        '''Recoge los eventos de anuncios.'''
        if serviceId == self.service_id_file:  # el servicio anunciado es el propio
            return

        if serviceId == self.service_id_catalog:  # el servicio anunciado es el propio
            return

        all_services = {}
        all_services.update(self.mains)
        all_services.update(self.authenticators)
        all_services.update(self.catalogs)
        all_services.update(self.files)

        if serviceId in all_services:  # el servicio ya está registrado
            return

        if service.ice_isA("::IceFlix::Main"):
            self.mains.update({serviceId: service})
            logging.info("new Main service: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::Authenticator"):
            self.authenticators.update({serviceId: service})
            logging.info("new Authenticator service: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::MediaCatalog"):
            self.catalogs.update({serviceId: service})
            logging.info("new MediaCatalog service: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::FileService"):
            self.files.update({serviceId: service})
            logging.info("new FileService service: %s\n", serviceId)

########################################################################################
############################## Topic Catalog Update ####################################


class CatalogUpdates(IceFlix.CatalogUpdate):
    '''Servant for the IceFlix.CatalogUpdate interface.'''

    def __init__(self, anuncios):
        '''Inicializador de la clase'''
        self.interfaz_anuncios = anuncios
        self.tests = server.tester

    def renameTile(self, mediaId, newName, serviceId, current=None): # pylint: disable=unused-argument, invalid-name
        '''captura evento de cambio de nombre'''
        if serviceId == server.get_catalog_obj(False):
            self.tests.rename_tile_publica_evento = True

        if newName == "Nombre prueba 1":
            self.tests.e_nom1 = True
        elif newName == "Nombre prueba 2":
            self.tests.e_nom2 = True

    def addTags(self, mediaId, user, tags, serviceId, current=None): # pylint: disable=unused-argument, invalid-name, too-many-arguments
        '''captura evento de añadir etiquetas'''
        if serviceId == server.get_catalog_obj(False):
            self.tests.add_tags_publica_evento = True

        if mediaId == "Test1":
            self.tests.e_tags1 = True
        elif mediaId == "Test2":
            self.tests.e_tags2 = True

    def removeTags(self, mediaId, user, tags, serviceId, current=None): # pylint: disable=unused-argument, invalid-name, too-many-arguments
        '''captura evento de eliminar etiquetas'''
        if serviceId == server.get_catalog_obj(False):
            self.tests.remove_tags_publica_evento = True

########################################################################################
###################################### Tests ###########################################


class Test():  # pylint: disable=too-many-instance-attributes
    '''Test class.'''

    def __init__(self):
        self.announce_files = False

        self.rename_tile_unauthorized = False
        self.rename_tile_wrong_media_id = False
        self.rename_tile_correcto = False

        self.add_tags_unauthorized = False
        self.add_tags_wrong_media_id = False
        self.add_tags_correcto = False
        self.add_tags_repetido = False

        self.remove_tags_unauthorized = False
        self.remove_tags_wrong_media_id = False
        self.remove_tags_correcto = False

        self.get_tile_unauthorized = False
        self.get_tile_wrong_media_id = False
        self.get_tile_correcto = False

        self.get_tiles_by_name_exact = False
        self.get_tiles_by_name_no_exact = False

        self.get_tiles_by_tags_unauthorized = False
        self.get_tiles_by_tags_any = False
        self.get_tiles_by_tags_all = False

        self.get_all_deltas = False
        self.e_nom1 = False
        self.e_nom2 = False
        self.e_tags1 = False
        self.e_tags2 = False

        self.rename_tile_publica_evento = False
        self.rename_tile_captura_evento = False
        self.add_tags_publica_evento = False
        self.add_tags_captura_evento = False
        self.remove_tags_publica_evento = False
        self.remove_tags_captura_evento = False

    def show_results(self):
        '''Muestra los resultados de los tests.'''
        logging.info("\tTest 01 - announceFiles capturado: %s\n",
                     self.announce_files)
        logging.info("\tTest 02 - renameTile_unauthorized: %s\n",
                     self.rename_tile_unauthorized)
        logging.info("\tTest 03 - renameTile_wrongMediaId: %s\n",
                     self.rename_tile_wrong_media_id)
        logging.info("\tTest 04 - renameTile_correcto: %s\n",
                     self.rename_tile_correcto)
        logging.info("\tTest 05 - addTags_unauthorized: %s\n",
                     self.add_tags_unauthorized)
        logging.info("\tTest 06 - addTags_wrongMediaId: %s\n",
                     self.add_tags_wrong_media_id)
        logging.info("\tTest 07 - addTags_correcto: %s\n",
                     self.add_tags_correcto)
        logging.info("\tTest 08 - addTags_repetido: %s\n",
                     self.add_tags_repetido)
        logging.info("\tTest 09 - removeTags_unauthorized: %s\n",
                     self.remove_tags_unauthorized)
        logging.info("\tTest 10 - removeTags_wrongMediaId: %s\n",
                     self.remove_tags_wrong_media_id)
        logging.info("\tTest 11 - removeTags_correcto: %s\n",
                     self.remove_tags_correcto)
        logging.info("\tTest 12 - getTile_unauthorized: %s\n",
                     self.get_tile_unauthorized)
        logging.info("\tTest 13 - getTile_wrongMediaId: %s\n",
                     self.get_tile_wrong_media_id)
        logging.info("\tTest 14 - getTile_correcto: %s\n",
                     self.get_tile_correcto)
        logging.info("\tTest 15 - getTilesByName_exact: %s\n",
                     self.get_tiles_by_name_exact)
        logging.info("\tTest 16 - getTilesByName_noExact: %s\n",
                     self.get_tiles_by_name_no_exact)
        logging.info("\tTest 17 - getTilesByTags_unauthorized: %s\n",
                     self.get_tiles_by_tags_unauthorized)
        logging.info("\tTest 18 - getTilesByTags_any: %s\n",
                     self.get_tiles_by_tags_any)
        logging.info("\tTest 19 - getTilesByTags_all: %s\n",
                     self.get_tiles_by_tags_all)
        logging.info("\tTest 20 - get_all_deltas capturado: %s\n",
                     self.get_all_deltas)
        logging.info("\tTest 21 - rename_tile evento publicado: %s\n",
                     self.rename_tile_publica_evento)
        logging.info("\tTest 22 - rename_tile evento capturado: %s\n",
                     self.rename_tile_captura_evento)
        logging.info("\tTest 23 - add_tags evento publicado: %s\n",
                     self.add_tags_publica_evento)
        logging.info("\tTest 24 - add_tags evento capturado: %s\n",
                     self.add_tags_captura_evento)
        logging.info("\tTest 25 - remove_tags evento publicado: %s\n",
                     self.remove_tags_publica_evento)
        logging.info("\tTest 26 - remove_tags evento capturado: %s\n",
                     self.remove_tags_captura_evento)

    def run_tests(self):  # pylint: disable=too-many-branches, too-many-statements
        '''Ejecuta los tests.'''
        proxy_catalog = server.get_catalog_obj(True)
        # print(proxy_catalog)
        catalog_service = IceFlix.MediaCatalogPrx.uncheckedCast(proxy_catalog)

        lista_medios = ["Test1", "Test2"]

        logging.info("\t\t--- TESTS ---")

        # announceFiles capturado
        server.files_publisher.announceFiles(
            lista_medios, server.id_service_file)

        media1 = catalog_service.getTile("Test1", "user01")
        media2 = catalog_service.getTile("Test2", "user01")

        if media1.mediaId == "Test1" and media2.mediaId == "Test2":
            self.announce_files = True

        # renameTile_unauthorized
        try:
            catalog_service.renameTile("Test1", "Nombre prueba 1", "user01")
        except IceFlix.Unauthorized:
            self.rename_tile_unauthorized = True

        # renameTile_wrongMediaId
        try:
            catalog_service.renameTile("Test15", "Nombre prueba 1", "admin01")
        except IceFlix.WrongMediaId:
            self.rename_tile_wrong_media_id = True

        # renameTile_correcto
        catalog_service.renameTile("Test1", "Nombre prueba 1", "admin01")
        catalog_service.renameTile("Test2", "Nombre prueba 2", "admin01")

        # addTags_unauthorized
        try:
            catalog_service.addTags("Test1", ["nada", "aqui"], "user02")
        except IceFlix.Unauthorized:
            self.add_tags_unauthorized = True

        # addTags_wrongMediaId
        try:
            catalog_service.addTags("Test15", ["nada", "aqui"], "user01")
        except IceFlix.WrongMediaId:
            self.add_tags_wrong_media_id = True

        # addTags_correcto
        catalog_service.addTags(
            "Test1", ["Test", "Prueba", "quitar"], "user01")

        # addTags_repetido
        catalog_service.addTags("Test2", ["Test", "Test"], "user01")

        # removeTags_unauthorized
        try:
            catalog_service.removeTags("Test1", ["quitar"], "user02")
        except IceFlix.Unauthorized:
            self.remove_tags_unauthorized = True

        # removeTags_wrongMediaId
        try:
            catalog_service.removeTags("Test15", ["quitar"], "user01")
        except IceFlix.WrongMediaId:
            self.remove_tags_wrong_media_id = True

        # removeTags_correcto
        catalog_service.removeTags("Test1", ["quitar"], "user01")

        # getTile_unauthorized
        try:
            catalog_service.getTile("Test1", "user02")
        except IceFlix.Unauthorized:
            self.get_tile_unauthorized = True

        # getTile_wrongMediaId
        try:
            catalog_service.getTile("Test15", "user01")
        except IceFlix.WrongMediaId:
            self.get_tile_wrong_media_id = True

        # getTile_correcto
        media_test1 = catalog_service.getTile("Test1", "user01")
        media_test2 = catalog_service.getTile("Test2", "user01")

        if media_test1.info.name == "Nombre prueba 1":
            self.rename_tile_correcto = True
            self.get_tile_correcto = True

        if "Test" in media_test1.info.tags and "Prueba" in media_test1.info.tags:
            self.add_tags_correcto = True
            self.remove_tags_correcto = True

        if media_test2.info.tags == ["Test"]:
            self.add_tags_repetido = True

        # getTilesByName_exact
        result = catalog_service.getTilesByName("Nombre prueba 1", True)
        if len(result) == 1 and result[0] == "Test1":
            self.get_tiles_by_name_exact = True

        # getTilesByName_noExact
        result = catalog_service.getTilesByName("Nombre prueba", False)
        if len(result) == 2 and result[0] == "Test1" and result[1] == "Test2":
            self.get_tiles_by_name_no_exact = True

        # getTilesByTags_unauthorized
        try:
            catalog_service.getTilesByTags(["Test"], False, "user02")
        except IceFlix.Unauthorized:
            self.get_tiles_by_tags_unauthorized = True

        # getTilesByTags_any
        result = catalog_service.getTilesByTags(
            ["Test", "Prueba"], False, "user01")
        if len(result) > 1:
            self.get_tiles_by_tags_any = True

        # getTilesByTags_all
        result = catalog_service.getTilesByTags(
            ["Test", "Prueba"], True, "user01")
        if len(result) == 1:
            self.get_tiles_by_tags_all = True

        # getAllDeltas
        if self.e_nom1 == True and self.e_nom2 == True and self.e_tags1 == True and self.e_tags2 == True: # pylint: disable=line-too-long, singleton-comparison
            self.get_all_deltas = True

        # logging.info("Test realizados: 23/26")
        # logging.info("Por favor espere")
        # time.sleep(20)

        # renameTile capturar evento
        # addTags capturar evento
        server.catalog_publisher.renameTile(
            "Test1", "Nombre prueba evento 1", server.id_service_catalog)

        server.catalog_publisher.addTags(
            "Test1", "user01", ["PruebaEvento"], server.id_service_catalog)

        res = catalog_service.getTile("Test1", "user01")

        if res.info.name == "Nombre prueba evento 1":
            self.rename_tile_captura_evento = True

        if "PruebaEvento" in res.info.tags:
            self.add_tags_captura_evento = True

        # removeTags capturar evento
        server.catalog_publisher.removeTags(
            "Test1", "user01", ["PruebaEvento"], server.id_service_catalog)

        res = catalog_service.getTile("Test1", "user01")

        if "PruebaEvento" not in res.info.tags:
            self.remove_tags_captura_evento = True

        # borrar los medios de prueba
        server.db_controller.eliminar_medio("Test1")
        server.db_controller.eliminar_medio("Test2")

        # mostrar resultados
        self.show_results()

########################################################################################
################################### File Servant #######################################


class FileTester(IceFlix.FileService):  # pylint: disable=too-few-public-methods
    """Example FileService servant."""

########################################################################################
############################## Servant MediaCatalog ####################################


class CatalogTester(IceFlix.MediaCatalog): # pylint: disable=too-few-public-methods
    """Servant for the IceFlix.MediaCatalog interface."""

    def getAllDeltas(self):  # pylint:disable=invalid-name, no-self-use
        "Envía la información de renombrado de archivo y de tags."
        logging.info("getAllDeltas solicitado")

########################################################################################
################################## Server Tester #######################################


class MainApp(Ice.Application): # pylint: disable=too-many-instance-attributes
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.db_controller = DBController()
        self.id_service_file = str(uuid.uuid4())
        self.id_service_catalog = str(uuid.uuid4())
        self.servant_file = FileTester()
        self.servant_catalogo_aux = CatalogTester()
        self.tester = Test()
        self.proxy_file = None
        self.proxy_catalog = None
        self.adapter_file = None
        self.adapter_catalog = None
        self.fin = True
        self.interfaz_anuncios = None
        self.interfaz_catalog_udt = None

        # variables TopicManager
        self.topic_manager_str_prx = "IceStorm/TopicManager -t:tcp -h localhost -p 10000"
        self.topic_manager = None

        # variables topics
        self.topic_announce_str = "Announcement"
        self.topic_catalog_udt_str = "CatalogUpdates"
        self.topic_files_str = "FileAvailabilityAnnounce"
        self.topic_announce = None
        self.topic_catalog_udt = None
        self.topic_files = None
        self.anuncios_subscriber_proxy = None
        self.catalog_udt_subscriber_proxy = None
        self.anuncios_publisher = None
        self.catalog_publisher = None
        self.files_publisher = None


    def anunciar_servicio(self):
        """ Anunciar los servicios al main. """
        while self.fin:
            self.anuncios_publisher.announce(
                self.proxy_file, self.id_service_file)
            #logging.info("File Tester anunciado\n")
            self.anuncios_publisher.announce(
                self.proxy_catalog, self.id_service_catalog)
            #logging.info("Catalog Aux anunciado\n")
            time.sleep(10)

    def recuperar_topic(self, topic_name):
        ''' Recuperar un topic del topic manager. '''
        try:
            topic = self.topic_manager.create(topic_name)
        except IceStorm.TopicExists: # pylint: disable=no-member
            topic = self.topic_manager.retrieve(topic_name)
        return topic

    def get_catalog_obj(self, proxy):
        ''' Devuelve el proxy del catalogo que se va a probar. '''
        lista_catalogos_keys = list(self.interfaz_anuncios.catalogs.keys())
        lista_catalogos_values = list(self.interfaz_anuncios.catalogs.values())

        if len(lista_catalogos_keys) < 1:
            raise IceFlix.TemporaryUnavailable()

        if proxy:
            return lista_catalogos_values[0]

        return lista_catalogos_keys[0]

    def run(self, args):
        """ Run the application, adding the needed objects to the adapter. """
        logging.info("Running Tester application\n")
        broker = self.communicator()

        self.adapter_file = broker.createObjectAdapter("TestFileAdapter")
        self.adapter_catalog = broker.createObjectAdapter("TestCatalogAdapter")

        self.proxy_file = self.adapter_file.add(
            self.servant_file, broker.stringToIdentity("FileTester"))
        self.proxy_catalog = self.adapter_catalog.add(
            self.servant_catalogo_aux, broker.stringToIdentity("CatalogAuxTester"))

        self.adapter_file.activate()
        self.adapter_catalog.activate()

        # conectarse al topic manager
        self.topic_manager = IceStorm.TopicManagerPrx.checkedCast( # pylint: disable=no-member
            broker.stringToProxy(self.topic_manager_str_prx),
        )

        if not self.topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        # interfaces de los topics
        self.interfaz_anuncios = Announces()
        self.interfaz_catalog_udt = CatalogUpdates(self.interfaz_anuncios)

        # establecer los topic
        self.topic_announce = self.recuperar_topic(self.topic_announce_str)
        self.topic_files = self.recuperar_topic(self.topic_files_str)
        self.topic_catalog_udt = self.recuperar_topic(
            self.topic_catalog_udt_str)

        # definir los subscriptores y publicadores
        # subscriptor announcement
        self.anuncios_subscriber_proxy = self.adapter_file.addWithUUID(
            self.interfaz_anuncios)
        self.topic_announce.subscribeAndGetPublisher(
            {}, self.anuncios_subscriber_proxy)
        # subscriptor catalogUpdates
        self.catalog_udt_subscriber_proxy = self.adapter_catalog.addWithUUID(
            self.interfaz_catalog_udt)
        self.topic_catalog_udt.subscribeAndGetPublisher(
            {}, self.catalog_udt_subscriber_proxy)

        # publicador announcement
        anuncios_publisher_proxy = self.topic_announce.getPublisher()
        self.anuncios_publisher = IceFlix.AnnouncementPrx.uncheckedCast(
            anuncios_publisher_proxy)
        # publicador FileAvailabilityAnnounce
        files_publisher_proxy = self.topic_files.getPublisher()
        self.files_publisher = IceFlix.FileAvailabilityAnnouncePrx.uncheckedCast(
            files_publisher_proxy)
        # publicador catalogUpdates
        catalog_udt_publisher_proxy = self.topic_catalog_udt.getPublisher()
        self.catalog_publisher = IceFlix.CatalogUpdatePrx.uncheckedCast(
            catalog_udt_publisher_proxy)

        logging.info("Por favor espera unos segundos...\n")
        # Anunciamos el servicio al topic
        time.sleep(20)
        hilo_aux = threading.Thread(target=self.anunciar_servicio)
        hilo_aux.start()

        # ejecutar los tests
        time.sleep(20)
        self.tester.run_tests()

        # self.shutdownOnInterrupt()
        # broker.waitForShutdown()
        self.fin = False

        # Desuscribirse de los topics
        self.topic_announce.unsubscribe(self.anuncios_subscriber_proxy)
        self.topic_catalog_udt.unsubscribe(self.catalog_udt_subscriber_proxy)

        return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = MainApp()
    sys.exit(server.main(sys.argv))
