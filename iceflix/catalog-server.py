import logging
import Ice
import sys
import IceFlix  # pylint:disable=import-error
import json
import threading
import uuid

class DB_controller():
    def __init__(self, pathDB):
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

class Catalog(IceFlix.MediaCatalog):
    """Servant for the IceFlix.MediaCatalog interface."""
    
    # metodos auxiliares
    def __init__(self):
        """ Inicializador del catálogo. """
        self.dbController = DB_controller()
    
    def autenticate(self, userToken):
        "Indica si el usuario especificado está autorizado."
        main = CatalogServer().serverMain()
        try:
            return main.getAutenticator().isAuthorized(userToken)
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
        medio.provider = medioAux["provider"]
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
        # TODO: implement
        return None
    
    def removeMedia(self,  mediaId, provider, current=None):  # pylint:disable=invalid-name, unused-argument
        "el FileService informa que un fichero ya no está disponible."
        # TODO: implement
        return None
    
    def renameTile(self,  mediaId, name, adminToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "el admin lo utiliza para renombrar medios."
        main = CatalogServer().serverMain()
        try:
            esAdmin = main.getAutenticator().isAdmin(adminToken)
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

    def serverMain(self):
        """ método que devuelve la referencia al objeto main """
        proxy = self.communicator().stringToProxy(sys.argv[1])
        Main = IceFlix.MainPrx.checkedCast(proxy)
        return Main
    
    def anunciarServicio(self):
        """ Anunciar el servicio al main. """
        self.serverMain().announce(self.proxy, self.idService)

    def run(self, args):
        """ Run the application, adding the needed objects to the adapter. """
        logging.info("Running Main application")
        broker = self.communicator()

        self.adapter = broker.createObjectAdapter("MediaCatalogAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)

        self.serverMain().newService(self.proxy, self.idService)

        hiloAux = t = threading.Timer(25, self.anunciarServicio)
        hiloAux.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        hiloAux.join()

        return 0

if __name__ == '__main__':
    server_catalog = CatalogServer()
    sys.exit(server_catalog.main(sys.argv))

# void newMedia(string mediaId, FileService* provider);
# void removeMedia(string mediaId, FileService* provider);
