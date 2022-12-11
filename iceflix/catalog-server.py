import logging
import Ice
import sys
Ice.loadSlice("iceflix.ice")
import IceFlix  # pylint:disable=import-error
import json
import threading
import uuid
import time

class DB_controller():
    def __init__(self):
        self.db_name = '../DB/media.json'
        self.media = self.cargarMedia()

    def cargarMedia(self):
        try:
            with open(self.db_name, 'r') as f:
                return json.load(f)
        except:
            logging.error("Error al cargar la base de datos")

    def guardarMedia(self):
        try:
            with open(self.db_name, 'w') as f:
                json.dump(self.media, f, indent=4)
                return True
        except:
            logging.error("Error al guardar la base de datos")
            return False
    
    def actualizarMedio(self, medioJson):
        for video in self.media["medios"]:
            if video["id"] == medioJson["id"]:
                video["provider"] = medioJson["provider"]
                video["info"] = medioJson["info"]
        return self.guardarMedia()
    
    def eliminarMedio(self, mediaId):
        for video in self.media["medios"]:
            if video["id"] == mediaId:
                self.media["medios"].remove(video)
        return self.guardarMedia()
    
    def aniadirMedio(self, medioJson):
        self.media["medios"].append(medioJson)
        return self.guardarMedia()

class Catalog(IceFlix.MediaCatalog):
    """Servant for the IceFlix.MediaCatalog interface."""
    
    # metodos auxiliares
    def __init__(self):
        """ Inicializador del catálogo. """
        self.dbController = DB_controller()
    
    def autenticate(self, userToken):
        print("Autenticando usuario...")
        "Indica si el usuario especificado está autorizado."
        main = CatalogServer().serverMain()
        try:
            return main.getAuthenticator().isAuthorized(userToken)
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable()

    def authorized(self, userToken):
        "Lanza una excepción si el usuario no está autorizado."
        authorized = self.autenticate(userToken)
        if not authorized:
            raise IceFlix.Unauthorized()

    def getMediaDB(self, mediaId):
        "Devuelve el medio cuyo identificador sea igual a mediaId si está en la BD."
        media = self.dbController.media
        for video in media["medios"]:
            if video["id"] == mediaId:
                return video
        raise IceFlix.WrongMediaId()

    def removeTag(self, tagsRem, listTags):
        "Elimina los tags de la lista listTags."
        for tag in tagsRem:
            if tag in listTags:
                listTags.remove(tag)
        return listTags
    
    # metodos de la interfaz
    def getTile(self, mediaId, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve el medio cuyo identificador sea igual a mediaId."
        self.authorized(userToken) # Comprobamos que el usuario está autorizado
        
        # Comprobamos que el mediaId exista en la base de datos
        medioAux = self.getMediaDB(mediaId)
        
        # Creamos el medio
        medioInfo = IceFlix.MediaInfo()
        medioInfo.name = medioAux["info"]["name"]
        medioInfo.tags = medioAux["info"]["tags"]

        medio = IceFlix.Media()
        medio.mediaId = medioAux["id"]
        medio.provider = IceFlix.FileServicePrx.uncheckedCast(server_catalog.communicator().stringToProxy(medioAux["provider"]))
        medio.info = medioInfo
        return medio
        
    def getTilesByName(self, name, exact, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve una lista con los identificadores según el título de los medios."
        result = []
        media = self.dbController.media
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
        self.authorized(userToken) # Comprobamos que el usuario está autorizado
        
        # obtener los resultados
        result = []
        media = self.dbController.media
        for video in media["medios"]:
            if includeAllTags:
                # si falta algún tag en la lista de tags del video, no se añade
                response = any (tag not in video["info"]["tags"] for tag in tags)
                if not response:
                    result.append(video["id"])
            else:
                # si algun tag está en la lista de tags del video, se añade
                response = any (el in tags for el in video["info"]["tags"])
                if response:
                    result.append(video["id"])
        
        return result

    def newMedia(self,  mediaId, provider, current=None):  # pylint:disable=invalid-name, unused-argument
        "el FileService informa que hay medios disponibles."
        try:
            result = self.getMediaDB(mediaId)
        except IceFlix.WrongMediaId:
            str_provider = server_catalog.communicator().proxyToString(provider)
            jsonMedia = {"id": mediaId, "provider": str_provider, "info": {"name": mediaId, "tags": []}}
            self.dbController.aniadirMedio(jsonMedia)
    
    def removeMedia(self,  mediaId, provider, current=None):  # pylint:disable=invalid-name, unused-argument
        "el FileService informa que un fichero ya no está disponible."
        self.dbController.eliminarMedio(mediaId)
    
    def renameTile(self,  mediaId, name, adminToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "el admin lo utiliza para renombrar medios."
        print("get Authenticator\n")
        main = CatalogServer().serverMain()
        
        try:
            result = main.getAuthenticator()
            print(result)
            esAdmin = IceFlix.AuthenticatorPrx.checkedCast(result).isAdmin(adminToken)
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable()
        
        if not esAdmin:
            raise IceFlix.Unauthorized()
        
        # Comprobamos que el mediaId exista en la base de datos
        medioAux = self.getMediaDB(mediaId)

        # Renombramos el medio
        medioAux["info"]["name"] = name

        # Guardamos los cambios
        self.dbController.actualizarMedio(medioAux)
        self.dbController.guardarMedia()
    
    def addTags(self,  mediaId, tags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "permite añadir una lista de tags a un medio concreto."
        self.authorized(userToken) # Comprobamos que el usuario está autorizado

        # Comprobamos que el mediaId exista en la base de datos
        medioAux = self.getMediaDB(mediaId)

        # Añadimos los tags
        listaNueva = medioAux["info"]["tags"] + tags
        medioAux["info"]["tags"] = list(set(listaNueva))
        
        # Guardamos los cambios
        self.dbController.actualizarMedio(medioAux)
        self.dbController.guardarMedia()
    
    def removeTags(self,  mediaId, tags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "permite eliminar una lista de tags de un medio concreto."
        self.authorized(userToken) # Comprobamos que el usuario está autorizado

        # Comprobamos que el mediaId exista en la base de datos
        medioAux = self.getMediaDB(mediaId)

        # Eliminar los tags
        listaNueva = self.removeTag(tags, medioAux["info"]["tags"])
        medioAux["info"]["tags"] = listaNueva
        
        # Guardamos los cambios
        self.dbController.actualizarMedio(medioAux)
        self.dbController.guardarMedia()

class CatalogServer(Ice.Application):
    """Example Ice.Application for a catalog service."""

    def __init__(self):
        """ Inicializador del servicio. """
        super().__init__()
        self.idService = str(uuid.uuid4())
        self.servant = Catalog()
        self.proxy = None
        self.adapter = None
        self.media = DB_controller()
        self.media.cargarMedia()
        self.fin = True
        with open('../configs/main_proxy.proxy', 'r') as f:
            self.str_proxy_main = f.readline()

    def serverMain(self):
        """ método que devuelve la referencia al objeto main """
        proxy = self.communicator().stringToProxy(self.str_proxy_main)
        Main = IceFlix.MainPrx.uncheckedCast(proxy)
        return Main
    
    def anunciarServicio(self):
        """ Anunciar el servicio al main. """
        while self.fin:
            self.serverMain().announce(self.proxy, self.idService)
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
        self.serverMain().newService(self.proxy, self.idService)  

        hiloAux = t = threading.Thread(target=self.anunciarServicio)
        hiloAux.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        self.fin = False

        return 0

if __name__ == '__main__':
    server_catalog = CatalogServer()
    sys.exit(server_catalog.main(sys.argv))

# void newMedia(string mediaId, FileService* provider);
# void removeMedia(string mediaId, FileService* provider);
