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

Ice.loadSlice("iceflix.ice")
import IceFlix # pylint: disable=import-error, wrong-import-position

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


class Catalog(IceFlix.MediaCatalog):
    """Servant for the IceFlix.MediaCatalog interface."""

    # metodos auxiliares
    def __init__(self):
        """ Inicializador del catálogo. """
        self.db_controller = DBController()

    def autenticate(self, user_token):
        '''Autentica al usuario'''
        main = CatalogServer().server_main()
        try:
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

    def newMedia(self,  mediaId, provider, current=None):  # pylint:disable=invalid-name, unused-argument
        "el FileService informa que hay medios disponibles."
        try:
            self.get_media_db(mediaId)
        except IceFlix.WrongMediaId:
            str_provider = server_catalog.communicator().proxyToString(provider)
            json_media = {"id": mediaId, "provider": str_provider,
                         "info": {"name": mediaId, "tags": []}}
            self.db_controller.aniadir_medio(json_media)

    def removeMedia(self,  mediaId, provider, current=None):  # pylint:disable=invalid-name, unused-argument
        "el FileService informa que un fichero ya no está disponible."
        self.db_controller.eliminar_medio(mediaId)

    def renameTile(self,  mediaId, name, adminToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "el admin lo utiliza para renombrar medios."
        print("get Authenticator\n")
        main = CatalogServer().server_main()

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
        self.db_controller.guardar_media()

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
        self.db_controller.guardar_media()

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
        self.db_controller.guardar_media()


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

        with open('../configs/main_proxy.proxy', 'r', encoding='utf-8') as file:
            self.str_proxy_main = file.readline()

    def server_main(self):
        """ método que devuelve la referencia al objeto main """
        proxy = self.communicator().stringToProxy(self.str_proxy_main)
        main = IceFlix.MainPrx.uncheckedCast(proxy)
        return main

    def anunciar_servicio(self):
        """ Anunciar el servicio al main. """
        while self.fin:
            self.server_main().announce(self.proxy, self.id_service)
            print("Servicio anunciado\n")
            time.sleep(25)

    def run(self, args):
        """ Run the application, adding the needed objects to the adapter. """
        logging.info("Running Main application\n")
        broker = self.communicator()

        self.adapter = broker.createObjectAdapter("MediaCatalogAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)

        print("Servicio creado\n")
        self.server_main().newService(self.proxy, self.id_service)

        hilo_aux = threading.Thread(target=self.anunciar_servicio)
        hilo_aux.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        self.fin = False

        return 0


if __name__ == '__main__':
    server_catalog = CatalogServer()
    sys.exit(server_catalog.main(sys.argv))

# void newMedia(string mediaId, FileService* provider);
# void removeMedia(string mediaId, FileService* provider);
