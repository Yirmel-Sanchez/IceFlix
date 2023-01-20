'''Service for the IceFlix.MediaCatalog interface.'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import uuid
import threading
import signal
import json
import logging

import Ice
import IceStorm

Ice.loadSlice("iceflix.ice")
import IceFlix  # pylint:disable=import-error, wrong-import-position

########################################################################################
################################# Controlador BD #######################################


class DBController():
    '''Clase que controla la base de datos'''

    def __init__(self):
        '''Inicializador de la clase'''
        self.db_name = '../DB/media.json'
        self.media = self.cargar_media()
        self.guardar_media()

    def cargar_media(self):
        '''Carga la base de datos en memoria y la devuelve en forma de json'''
        try:
            with open(self.db_name, 'r', encoding='utf-8') as file:
                return json.load(file)
        except:  # pylint:disable=bare-except
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

    def actualizar_medio(self, medio_json):
        '''Actualiza un medio en la base de datos'''
        for video in self.media["medios"]:
            if video["id"] == medio_json["id"]:
                video["provider"] = medio_json["provider"]
                video["info"] = medio_json["info"]
        return self.guardar_media()

    def eliminar_medio(self, media_id):
        '''Elimina un medio de la base de datos'''
        for video in self.media["medios"]:
            if video["id"] == media_id:
                self.media["medios"].remove(video)
        return self.guardar_media()

    def aniadir_medio(self, medio_json):
        '''Añade un medio a la base de datos'''
        self.media["medios"].append(medio_json)
        return self.guardar_media()

########################################################################################
############################### Topic Announcement #####################################


class Announces(IceFlix.Announcement): # pylint:disable=too-few-public-methods
    '''Servant for the IceFlix.Announcement interface.'''

    def __init__(self):
        self.mains = {}
        self.authenticators = {}
        self.catalogs = {}
        self.files = {}
        self.service_id = server_catalog.id_service
        self.tiempos_anuncios = {}

    def announce(self, service, serviceId, current=None):  # pylint:disable=unused-argument, invalid-name
        '''Recoge los eventos de anuncios.'''
        if serviceId == self.service_id:  # el servicio anunciado es el propio
            logging.info(" Announce ignorado: %s\n", serviceId)
            return

        all_services = {}
        all_services.update(self.mains)
        all_services.update(self.authenticators)
        all_services.update(self.catalogs)
        all_services.update(self.files)

        if serviceId in all_services:  # el servicio ya está registrado
            self.tiempos_anuncios[serviceId] = time.time()
            logging.info(" Tiempo de servicio actualizado: %s\n", serviceId)
            return

        if service.ice_isA("::IceFlix::Main"):
            self.mains.update({serviceId: service})
            self.tiempos_anuncios[serviceId] = time.time()
            logging.info(" Nuevo servicio Main: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::Authenticator"):
            self.authenticators.update({serviceId: service})
            self.tiempos_anuncios[serviceId] = time.time()
            logging.info(" Nuevo servicio Authenticator: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::MediaCatalog"):
            self.catalogs.update({serviceId: service})
            self.tiempos_anuncios[serviceId] = time.time()
            logging.info(" Nuevo servicio MediaCatalog: %s\n", serviceId)
        elif service.ice_isA("::IceFlix::FileService"):
            self.files.update({serviceId: service})
            self.tiempos_anuncios[serviceId] = time.time()
            logging.info(" Nuevo servicio FileService: %s\n", serviceId)

    def eliminar_servicio(self, service_id):
        '''Elimina un servicio de la lista de servicios disponibles'''
        if service_id in self.mains:
            del self.mains[service_id]
        elif service_id in self.authenticators:
            del self.authenticators[service_id]
        elif service_id in self.catalogs:
            del self.catalogs[service_id]
        elif service_id in self.files:
            del self.files[service_id]

        if service_id in self.tiempos_anuncios:
            del self.tiempos_anuncios[service_id]

########################################################################################
############################## Topic Catalog Update ####################################


class CatalogUpdates(IceFlix.CatalogUpdate):
    '''Servant for the IceFlix.CatalogUpdate interface.'''

    def __init__(self, anuncios):
        '''Inicializador de la clase'''
        self.interfaz_anuncios = anuncios
        self.media_catalog = server_catalog.servant

    def renameTile(self, mediaId, newName, serviceId, current=None): # pylint:disable=unused-argument, invalid-name
        '''captura evento de cambio de nombre'''
        if serviceId == self.interfaz_anuncios.service_id:
            return

        if serviceId in self.interfaz_anuncios.catalogs:
            try:
                # Comprobamos que el mediaId exista en la base de datos
                medio_aux = self.media_catalog.get_media_db(mediaId)

                # Renombramos el medio
                medio_aux["info"]["name"] = newName

                # Guardamos los cambios
                self.media_catalog.db_controller.actualizar_medio(medio_aux)
            except:  # pylint:disable=bare-except
                json_media = {"id": mediaId, "provider": "None",
                              "info": {"name": newName, "tags": []}}
                self.media_catalog.db_controller.aniadir_medio(json_media)
            logging.info(" Media %s renombrado a %s", mediaId, newName)

    def addTags(self, mediaId, user, tags, serviceId, current=None): # pylint:disable=unused-argument, invalid-name, too-many-arguments
        '''captura evento de añadir etiquetas'''
        if serviceId == self.interfaz_anuncios.service_id:
            return

        if serviceId in self.interfaz_anuncios.catalogs:
            try:
                # Comprobamos que el mediaId exista en la base de datos
                medio_aux = self.media_catalog.get_media_db(mediaId)

                # Añadimos los tags
                lista_nueva = medio_aux["info"]["tags"] + tags
                medio_aux["info"]["tags"] = list(set(lista_nueva))

                # Guardamos los cambios
                self.media_catalog.db_controller.actualizar_medio(medio_aux)
            except:  # pylint:disable=bare-except
                json_media = {"id": mediaId, "provider": "None",
                              "info": {"name": mediaId, "tags": list(tags)}}
                self.media_catalog.db_controller.aniadir_medio(json_media)
            logging.info(" Media %s etiquetado con %s", mediaId, tags)

    def removeTags(self, mediaId, user, tags, serviceId, current=None): # pylint:disable=unused-argument, invalid-name, too-many-arguments
        '''captura evento de eliminar etiquetas'''
        if serviceId == self.interfaz_anuncios.service_id:
            return

        if serviceId in self.interfaz_anuncios.catalogs:
            try:
                # Comprobamos que el mediaId exista en la base de datos
                medio_aux = self.media_catalog.get_media_db(mediaId)

                # Eliminar los tags
                lista_nueva = self.media_catalog.remove_tag(
                    tags, medio_aux["info"]["tags"])
                medio_aux["info"]["tags"] = lista_nueva

                # Guardamos los cambios
                self.media_catalog.db_controller.actualizar_medio(medio_aux)
            except:  # pylint:disable=bare-except
                json_media = {"id": mediaId, "provider": "None",
                              "info": {"name": mediaId, "tags": []}}
                self.media_catalog.db_controller.aniadir_medio(json_media)

########################################################################################
######################## Topic File Availability Announce ##############################


class FilesAnnounce(IceFlix.FileAvailabilityAnnounce): # pylint:disable=too-few-public-methods
    '''servant para la interfaz IceFlix.FileAvailabilityAnnounce'''

    def __init__(self, anuncios):
        '''Inicializador de la clase'''
        self.interfaz_anuncios = anuncios
        self.media_catalog = server_catalog.servant

    def announceFiles(self, mediaIds, serviceId, current=None): # pylint:disable=unused-argument, invalid-name
        '''captura evento de anuncio de ficheros'''
        if serviceId in self.interfaz_anuncios.files:
            str_provider = self.interfaz_anuncios.files[serviceId]

            for idx in mediaIds:
                try:
                    medio = self.media_catalog.get_media_db(id)

                    json_media = {"id": idx, "provider": str(str_provider),
                                  "info": {"name": medio["info"]["name"],
                                  "tags": medio["info"]["tags"]}}
                    self.media_catalog.db_controller.actualizar_medio(
                        json_media)
                except IceFlix.WrongMediaId:
                    # si no existe en la base de datos, se crea
                    json_media = {"id": idx, "provider": str_provider.ice_toString(),
                                  "info": {"name": idx, "tags": []}}
                    self.media_catalog.db_controller.aniadir_medio(json_media)

########################################################################################
############################## Servant MediaCatalog ####################################


class Catalog(IceFlix.MediaCatalog):
    """Servant for the IceFlix.MediaCatalog interface."""

    # metodos auxiliares
    def __init__(self):
        """ Inicializador del catálogo. """
        self.db_controller = DBController()

    def autenticate(self, user_token): # pylint:disable=no-self-use
        '''Autentica al usuario'''
        try:
            main = server_catalog.server_main()
            return main.getAuthenticator().isAuthorized(user_token)
        except IceFlix.TemporaryUnavailable as exc:
            raise IceFlix.TemporaryUnavailable() from exc

    def authorized(self, user_token):
        "Lanza una excepción si el usuario no está autorizado."
        authorized = self.autenticate(user_token)
        if not authorized:
            raise IceFlix.Unauthorized()

    def get_media_db(self, media_id):
        "Devuelve el medio cuyo identificador sea igual a mediaId si está en la BD."
        media = self.db_controller.media
        for video in media["medios"]:
            if video["id"] == media_id:
                return video
        raise IceFlix.WrongMediaId()

    def remove_tag(self, tags_rem, list_tags):  # pylint:disable=no-self-use
        "Elimina los tags de la lista list_tags."
        for tag in tags_rem:
            if tag in list_tags:
                list_tags.remove(tag)
        return list_tags

    # metodos de la interfaz
    def getTile(self, mediaId, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve el medio cuyo identificador sea igual a mediaId."
        # Comprobamos que el usuario está autorizado
        self.authorized(userToken)

        # Comprobamos que el mediaId exista en la base de datos
        medio_aux = self.get_media_db(mediaId)

        # Creamos el medio
        medio_info = IceFlix.MediaInfo()
        medio_info.name = medio_aux["info"]["name"]
        medio_info.tags = medio_aux["info"]["tags"]

        medio = IceFlix.Media()
        medio.mediaId = medio_aux["id"]
        medio.provider = IceFlix.FileServicePrx.uncheckedCast(
            server_catalog.communicator().stringToProxy(medio_aux["provider"]))
        medio.info = medio_info
        return medio

    def getTilesByName(self, name, exact, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve una lista con los identificadores según el título de los medios."
        result = []
        media = self.db_controller.media
        for video in media["medios"]:
            if exact:
                if video["info"]["name"] == name:
                    result.append(video["id"])
            else:
                if name in video["info"]["name"]:
                    result.append(video["id"])

        return result

    def getTilesByTags(self, tags, includeAllTags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve una lista con los identificadores según los tags de los medios."
        # Comprobamos que el usuario está autorizado
        self.authorized(userToken)

        # obtener los resultados
        result = []
        media = self.db_controller.media
        for video in media["medios"]:
            if includeAllTags:
                # si falta algún tag en la lista de tags del video, no se añade
                response = any(
                    tag not in video["info"]["tags"] for tag in tags)
                if not response:
                    result.append(video["id"])
            else:
                # si algun tag está en la lista de tags del video, se añade
                response = any(el in tags for el in video["info"]["tags"])
                if response:
                    result.append(video["id"])

        return result

    def renameTile(self,  mediaId, name, adminToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "el admin lo utiliza para renombrar medios."
        #print("get Authenticator\n")
        main = server_catalog.server_main()

        try:
            result = main.getAuthenticator()
            es_admin = IceFlix.AuthenticatorPrx.checkedCast(
                result).isAdmin(adminToken)
        except IceFlix.TemporaryUnavailable as exc:
            raise IceFlix.TemporaryUnavailable() from exc

        if not es_admin:
            raise IceFlix.Unauthorized()

        # Comprobamos que el mediaId exista en la base de datos
        medio_aux = self.get_media_db(mediaId)

        # Renombramos el medio
        medio_aux["info"]["name"] = name

        # Guardamos los cambios
        self.db_controller.actualizar_medio(medio_aux)

        # propagar el evento
        server_catalog.catalog_publisher.renameTile(
            mediaId, name, server_catalog.id_service)

    def addTags(self,  mediaId, tags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "permite añadir una lista de tags a un medio concreto."
        # Comprobamos que el usuario está autorizado
        self.authorized(userToken)

        # Comprobamos que el mediaId exista en la base de datos
        medio_aux = self.get_media_db(mediaId)

        # Añadimos los tags
        lista_nueva = medio_aux["info"]["tags"] + tags
        medio_aux["info"]["tags"] = list(set(lista_nueva))

        # Guardamos los cambios
        self.db_controller.actualizar_medio(medio_aux)

        # propagar el evento
        server_catalog.catalog_publisher.addTags(
            mediaId, userToken, tags, server_catalog.id_service)

    def removeTags(self,  mediaId, tags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "permite eliminar una lista de tags de un medio concreto."
        # Comprobamos que el usuario está autorizado
        self.authorized(userToken)

        # Comprobamos que el mediaId exista en la base de datos
        medio_aux = self.get_media_db(mediaId)

        # Eliminar los tags
        lista_nueva = self.remove_tag(tags, medio_aux["info"]["tags"])
        medio_aux["info"]["tags"] = lista_nueva

        # Guardamos los cambios
        self.db_controller.actualizar_medio(medio_aux)

        # propagar el evento
        server_catalog.catalog_publisher.removeTags(
            mediaId, userToken, tags, server_catalog.id_service)

    def getAllDeltas(self, current=None):  # pylint:disable=invalid-name, unused-argument
        "Envía la información de renombrado de archivo y de tags."
        for video in self.db_controller.media["medios"]:
            server_catalog.catalog_publisher.renameTile(
                video["id"], video["info"]["name"], server_catalog.id_service)
            server_catalog.catalog_publisher.addTags(
                video["id"], "user", video["info"]["tags"], server_catalog.id_service)


########################################################################################
################################# Server Catalog #######################################

class CatalogServer(Ice.Application): # pylint:disable=too-many-instance-attributes
    """Example Ice.Application for a catalog service."""

    def __init__(self):
        """ Inicializador del servicio. """
        super().__init__()
        self.id_service = str(uuid.uuid4())
        self.servant = Catalog()
        self.proxy = None
        self.adapter = None
        self.media = DBController()
        self.media.cargar_media()
        self.fin = True
        self.idx = 0
        self.no_main = False
        self.no_service = False
        self.interfaz_anuncios = None

        # variables TopicManager
        self.topic_manager = None

        # variables topics
        self.topic_announce_str = "Announcements"
        self.topic_catalog_udt_str = "CatalogUpdates"
        self.topic_files_str = "FileAvailabilityAnnounce"
        self.topic_announce = None
        self.topic_catalog_udt = None
        self.topic_files = None
        self.anuncios_subscriber_proxy = None
        self.catalog_udt_subscriber_proxy = None
        self.files_subscriber_proxy = None
        self.anuncios_publisher = None
        self.catalog_publisher = None

    def server_main(self):
        """ método que devuelve la referencia al objeto main """
        # if len(self.interfaz_anuncios.mains) < 1:
        # raise IceFlix.TemporaryUnavailable()

        self.idx += 1

        if self.idx > len(self.interfaz_anuncios.mains) - 1:
            self.idx = 0

        #print("Main type: ", type(list(self.interfaz_anuncios.mains.values())[self.idx]))
        proxy = list(self.interfaz_anuncios.mains.values())[self.idx]
        main = IceFlix.MainPrx.uncheckedCast(proxy)
        return main

    def anunciar_servicio(self):
        """ Anunciar el servicio al main. """
        while self.fin:
            self.anuncios_publisher.announce(self.proxy, self.id_service)
            logging.info(" Servicio anunciado\n")
            time.sleep(10)

    def servicios_caidos(self):
        """ Método que se encarga de eliminar los servicios caídos. """
        while self.fin:
            for idx in self.interfaz_anuncios.tiempos_anuncios.copy(): # pylint:disable=consider-using-dict-items
                if time.time() - self.interfaz_anuncios.tiempos_anuncios[idx] > 12:
                    self.interfaz_anuncios.eliminar_servicio(idx)
                    logging.info(" Servicio eliminado: %s\n", idx)
            time.sleep(1)
            if len(self.interfaz_anuncios.mains) == 0:
                self.fin = False
                print("No hay servicios main disponibles")
                os.kill(os.getpid(), signal.SIGINT)

    def recuperar_topic(self, topic_name):
        ''' Recuperar un topic del topic manager. '''
        try:
            topic = self.topic_manager.create(topic_name)
        except IceStorm.TopicExists: # pylint:disable=no-member
            topic = self.topic_manager.retrieve(topic_name)
        return topic

    def desuscribir_topics(self):
        ''' Desuscribirse de los topics. '''
        self.topic_announce.unsubscribe(self.anuncios_subscriber_proxy)
        self.topic_catalog_udt.unsubscribe(self.catalog_udt_subscriber_proxy)
        self.topic_files.unsubscribe(self.files_subscriber_proxy)

    def arranque_sincronizacion(self):
        """ Método que se encarga de indicar la existencia de otros servicios. """
        time.sleep(12)
        if len(self.interfaz_anuncios.mains) == 0:
            self.no_main = True
            return

        if len(self.interfaz_anuncios.catalogs) == 0:
            self.no_service = True

    def run(self, args):
        """ Run the application, adding the needed objects to the adapter. """
        logging.info(" Running MediaCatalog application\n")
        broker = self.communicator()

        self.adapter = broker.createObjectAdapter("MediaCatalogAdapter")

        self.proxy = self.adapter.addWithUUID(self.servant)

        logging.info(" ServiceID del servicio MediaCatalog: %s\n", self.id_service)
        self.adapter.activate()

        # conectarse al topic manager
        self.topic_manager = IceStorm.TopicManagerPrx.checkedCast( # pylint:disable=no-member
            self.communicator().propertyToProxy("IceStorm.TopicManager")
        )

        if not self.topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        # interfaces de los topics
        self.interfaz_anuncios = Announces()
        interfaz_catalog_udt = CatalogUpdates(self.interfaz_anuncios)
        interfaz_files = FilesAnnounce(self.interfaz_anuncios)

        # establecer los topic
        self.topic_announce = self.recuperar_topic(self.topic_announce_str)
        self.topic_catalog_udt = self.recuperar_topic(
            self.topic_catalog_udt_str)
        self.topic_files = self.recuperar_topic(self.topic_files_str)

        # definir los subscriptores y publicadores

        # subscriptor announcement
        self.anuncios_subscriber_proxy = self.adapter.addWithUUID(
            self.interfaz_anuncios)
        self.topic_announce.subscribeAndGetPublisher(
            {}, self.anuncios_subscriber_proxy)
        # subscriptor catalogUpdates
        self.catalog_udt_subscriber_proxy = self.adapter.addWithUUID(
            interfaz_catalog_udt)
        self.topic_catalog_udt.subscribeAndGetPublisher(
            {}, self.catalog_udt_subscriber_proxy)
        # subscriptor fileAvailabilityAnnounce
        self.files_subscriber_proxy = self.adapter.addWithUUID(interfaz_files)
        self.topic_files.subscribeAndGetPublisher(
            {}, self.files_subscriber_proxy)

        self.arranque_sincronizacion()
        if self.no_main:
            logging.info(" No hay ningún main disponible")
        else:
            if self.no_service:
                logging.info(" Primero en arrancar")
            else:
                logging.info(" No es el primero en arrancar")
                IceFlix.MediaCatalogPrx.uncheckedCast(
                    list(self.interfaz_anuncios.catalogs.values())[0]).getAllDeltas()

            # publicador announcement
            anuncios_publisher_proxy = self.topic_announce.getPublisher()
            self.anuncios_publisher = IceFlix.AnnouncementPrx.uncheckedCast(
                anuncios_publisher_proxy)
            # publicador catalogUpdates
            catalog_udt_publisher_proxy = self.topic_catalog_udt.getPublisher()
            self.catalog_publisher = IceFlix.CatalogUpdatePrx.uncheckedCast(
                catalog_udt_publisher_proxy)

            # Anunciamos el servicio al topic
            hilo_aux = threading.Thread(target=self.anunciar_servicio)
            hilo_aux.start()

            # controlar los servicios caídos
            hilo_aux_caidos = threading.Thread(target=self.servicios_caidos)
            hilo_aux_caidos.start()

            self.shutdownOnInterrupt()
            broker.waitForShutdown()
            self.fin = False

        # Desuscribirse de los topics
        self.desuscribir_topics()

        return 0


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    server_catalog = CatalogServer()
    sys.exit(server_catalog.main(sys.argv))
