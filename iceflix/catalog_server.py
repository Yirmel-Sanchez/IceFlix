'''Service for the IceFlix.MediaCatalog interface.'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import uuid
import threading
import json

import logging
import sys
import Ice
import IceStorm

Ice.loadSlice("iceflix.ice")
import IceFlix # pylint: disable=import-error, wrong-import-position

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
        except: # pylint: disable=bare-except
            logging.error("Error al cargar la base de datos")
            return json.loads('{"medios":[]}')

    def guardar_media(self):
        '''Guarda la base de datos en disco'''
        try:
            with open(self.db_name, 'w', encoding='utf-8') as file:
                json.dump(self.media, file, indent=4)
            return True
        except: # pylint: disable=bare-except
            logging.error("Error al guardar la base de datos")
            return False

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

class Announces(IceFlix.Announcement):
    '''Servant for the IceFlix.Announcement interface.'''
    def __init__(self):
        self.mains = {}
        self.authenticators = {}
        self.catalogs = {}
        self.files = {}
        self.service_id = server_catalog.id_service

    def announce(self, service, serviceId, current=None):  # pylint: disable=unused-argument
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
            print("new Main service: ", serviceId)
        elif service.ice_isA("::IceFlix::Authenticator"):
            self.authenticators.update({serviceId: service})
            print("new Authenticator service: ", serviceId)
        elif service.ice_isA("::IceFlix::MediaCatalog"):
            self.catalogs.update({serviceId: service})
            print("new MediaCatalog service: ", serviceId)
        elif service.ice_isA("::IceFlix::FileService"):
            self.files.update({serviceId: service})
            print("new FileService service: ", serviceId)

########################################################################################
############################## Topic Catalog Update ####################################

class CatalogUpdates(IceFlix.CatalogUpdate):
    '''Servant for the IceFlix.CatalogUpdate interface.'''
    def __init__(self, anuncios):
        '''Inicializador de la clase'''
        self.interfaz_anuncios = anuncios
        self.mediaCatalog = server_catalog.servant
    
    def renameTile(self, mediaId, newName, serviceId, current=None):
        '''captura evento de cambio de nombre'''
        if serviceId == self.interfaz_anuncios.service_id:
            return
        
        if serviceId in self.interfaz_anuncios.catalogs:
            try:
                # Comprobamos que el mediaId exista en la base de datos
                medio_aux = self.mediaCatalog.get_media_db(mediaId)

                # Renombramos el medio
                medio_aux["info"]["name"] = newName

                # Guardamos los cambios
                self.mediaCatalog.db_controller.actualizar_medio(medio_aux)
            except: # pylint: disable=bare-except
                json_media = {"id": mediaId, "provider": "None",
                    "info": {"name": newName, "tags": []}}
                self.mediaCatalog.db_controller.aniadir_medio(json_media)

    def addTags(self, mediaId, user, tags, serviceId, current=None):
        '''captura evento de añadir etiquetas'''
        if serviceId == self.interfaz_anuncios.service_id:
            return
        
        if serviceId in self.interfaz_anuncios.catalogs:
            try:
                # Comprobamos que el mediaId exista en la base de datos
                medio_aux = self.mediaCatalog.get_media_db(mediaId)

                # Añadimos los tags
                lista_nueva = medio_aux["info"]["tags"] + tags
                medio_aux["info"]["tags"] = list(set(lista_nueva))

                # Guardamos los cambios
                self.mediaCatalog.db_controller.actualizar_medio(medio_aux)
            except: # pylint: disable=bare-except
                json_media = {"id": mediaId, "provider": "None",
                    "info": {"name": mediaId, "tags": list(tags)}}
                self.mediaCatalog.db_controller.aniadir_medio(json_media)

    def removeTags(self, mediaId, user, tags, serviceId, current=None):
        '''captura evento de eliminar etiquetas'''
        if serviceId == self.interfaz_anuncios.service_id:
            return
        
        if serviceId in self.interfaz_anuncios.catalogs:
            try:
                # Comprobamos que el mediaId exista en la base de datos
                medio_aux = self.mediaCatalog.get_media_db(mediaId)

                # Eliminar los tags
                lista_nueva = self.mediaCatalog.remove_tag(tags, medio_aux["info"]["tags"])
                medio_aux["info"]["tags"] = lista_nueva

                # Guardamos los cambios
                self.mediaCatalog.db_controller.actualizar_medio(medio_aux)
            except: # pylint: disable=bare-except
                json_media = {"id": mediaId, "provider": "None",
                    "info": {"name": mediaId, "tags": []}}
                self.mediaCatalog.db_controller.aniadir_medio(json_media)

########################################################################################
######################## Topic File Availability Announce ##############################

class FilesAnnounce(IceFlix.FileAvailabilityAnnounce):
    '''servant para la interfaz IceFlix.FileAvailabilityAnnounce'''
    def __init__(self, anuncios):
        '''Inicializador de la clase'''
        self.interfaz_anuncios = anuncios
        self.mediaCatalog = server_catalog.servant
    
    def announceFiles(self, mediaIds, serviceId, current=None):
        '''captura evento de anuncio de ficheros'''
        if serviceId in self.interfaz_anuncios.files:
            str_provider = self.interfaz_anuncios.files[serviceId]

            for id in mediaIds:
                try:
                    medio = self.mediaCatalog.get_media_db(id)

                    json_media = {"id": id, "provider": str_provider,
                        "info": {"name": medio["info"]["name"], "tags": medio["info"]["tags"]}}
                    self.mediaCatalog.db_controller.actualizar_medio(json_media)
                except IceFlix.WrongMediaId:
                    # si no existe en la base de datos, se crea
                    json_media = {"id": id, "provider": str_provider,
                        "info": {"name": id, "tags": []}}
                    self.mediaCatalog.db_controller.aniadir_medio(json_media)

########################################################################################
############################## Servant MediaCatalog ####################################

class Catalog(IceFlix.MediaCatalog):
    """Servant for the IceFlix.MediaCatalog interface."""

    # metodos auxiliares
    def __init__(self):
        """ Inicializador del catálogo. """
        self.db_controller = DBController()

    def autenticate(self, user_token):
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

    def remove_tag(self, tags_rem, list_tags):
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
            print(result)
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

        #propagar el evento
        server_catalog.catalog_publisher.renamedTile(mediaId, name)

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

        #propagar el evento
        server_catalog.catalog_publisher.addTags(mediaId, tags)

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

        #propagar el evento
        server_catalog.catalog_publisher.removeTags(mediaId, tags)

    def getAllDeltas(self): # pylint:disable=invalid-name
        "Envía la información de renombrado de archivo y de tags."
        for video in self.db_controller.media["medios"]:
            server_catalog.catalog_publisher.renamedTile(
                video["id"], video["info"]["name"])
            server_catalog.catalog_publisher.addTags(
                video["id"], video["info"]["tags"])
        

########################################################################################
################################# Server Catalog #######################################

class CatalogServer(Ice.Application):
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
        self.noMain = False
        self.noService = False

        # variables TopicManager
        self.topic_manager_str_prx = "IceStorm/TopicManager -t:tcp -h localhost -p 10000"
        self.topic_manager = None

        #variables topics
        self.topic_announce_str = "Announcement"
        self.topic_catalog_udt_str = "CatalogUpdates"
        self.topic_files_str = "FileAvailabilityAnnounce"

    def server_main(self):
        """ método que devuelve la referencia al objeto main """
        if len(self.interfaz_anuncios.mains) < 1:
            raise IceFlix.TemporaryUnavailable()

        self.idx += 1

        if self.idx > len(self.interfaz_anuncios.mains) - 1:
            self.idx = 0
            
        proxy = self.communicator().stringToProxy(
            list(self.interfaz_anuncios.mains.values())[self.idx])
        main = IceFlix.MainPrx.uncheckedCast(proxy)
        return main
            
    def anunciar_servicio(self):
        """ Anunciar el servicio al main. """
        while self.fin:
            self.anuncios_publisher.announce(self.proxy, self.id_service)
            print("Servicio anunciado\n")
            time.sleep(10)
    
    def recuperarTopic(self, topic_name):
        ''' Recuperar un topic del topic manager. '''
        try:
            topic = self.topic_manager.create(topic_name)
        except IceStorm.TopicExists:
            topic = self.topic_manager.retrieve(topic_name)
        return topic

    def arranque_sincronizacion(self):
        time.sleep(12)
        if len(self.interfaz_anuncios.mains) == 0:
            self.noMain = True
            return
        
        if len(self.interfaz_anuncios.catalogs) == 0:
            self.noService = True

    def run(self, args):
        """ Run the application, adding the needed objects to the adapter. """
        logging.info("Running Main application\n")
        broker = self.communicator()

        self.adapter = broker.createObjectAdapter("MediaCatalogAdapter")

        self.proxy = self.adapter.addWithUUID(self.servant)

        print("Servicio creado\n")
        print(self.proxy, "\n", flush=True)
        self.adapter.activate()
        
        # conectarse al topic manager
        self.topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            broker.stringToProxy(self.topic_manager_str_prx),
        )

        if not self.topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        # interfaces de los topics
        self.interfaz_anuncios = Announces()
        interfaz_catalog_udt = CatalogUpdates(self.interfaz_anuncios)
        interfaz_files = FilesAnnounce(self.interfaz_anuncios)

        # establecer los topic
        self.topic_announce = self.recuperarTopic(self.topic_announce_str)
        self.topic_catalog_udt = self.recuperarTopic(self.topic_catalog_udt_str)
        self.topic_files = self.recuperarTopic(self.topic_files_str)

        # definir los subscriptores y publicadores

        ## subscriptor announcement
        self.anuncios_subscriber_proxy = self.adapter.addWithUUID(self.interfaz_anuncios)
        self.topic_announce.subscribeAndGetPublisher({}, self.anuncios_subscriber_proxy)
        ## subscriptor catalogUpdates
        self.catalog_udt_subscriber_proxy = self.adapter.addWithUUID(interfaz_catalog_udt)
        self.topic_catalog_udt.subscribeAndGetPublisher({}, self.catalog_udt_subscriber_proxy)
        ## subscriptor fileAvailabilityAnnounce
        self.files_subscriber_proxy = self.adapter.addWithUUID(interfaz_files)
        self.topic_files.subscribeAndGetPublisher({}, self.files_subscriber_proxy)

        self.arranque_sincronizacion()
        if self.noMain:
            print("No hay ningún main disponible")
        else:
            if self.noService:
                print("primero en arrancar")
            else:
                print("no es el primero en arrancar")
                IceFlix.MediaCatalogPrx.uncheckedCast(
                    list(self.interfaz_anuncios.catalogs.values())[0]).getAllDeltas()

            ## publicador announcement
            anuncios_publisher_proxy = self.topic_announce.getPublisher()
            self.anuncios_publisher = IceFlix.AnnouncementPrx.uncheckedCast(anuncios_publisher_proxy)
            ## publicador catalogUpdates
            catalog_udt_publisher_proxy = self.topic_catalog_udt.getPublisher()
            self.catalog_publisher = IceFlix.CatalogUpdatePrx.uncheckedCast(catalog_udt_publisher_proxy)

            # Anunciamos el servicio al topic
            hilo_aux = threading.Thread(target=self.anunciar_servicio)
            hilo_aux.start()

            self.shutdownOnInterrupt()
            broker.waitForShutdown()
            self.fin = False

        # Desuscribirse de los topics
        self.topic_announce.unsubscribe(self.anuncios_subscriber_proxy)
        self.topic_catalog_udt.unsubscribe(self.catalog_udt_subscriber_proxy)
        self.topic_files.unsubscribe(self.files_subscriber_proxy)

        return 0


if __name__ == '__main__':
    server_catalog = CatalogServer()
    sys.exit(server_catalog.main(sys.argv))
