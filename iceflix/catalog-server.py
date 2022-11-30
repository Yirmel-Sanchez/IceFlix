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

    def cargarMedia(self):
        try:
            with open(self.db_name, 'r') as f:
                return json.load(f)
        except:
            logging.error("Error al cargar la base de datos")

    def guardarMedia(self, media):
        try:
            with open(self.db_name, 'w') as f:
                json.dump(media, f, indent=4)
                return True
        except:
            logging.error("Error al guardar la base de datos")
            return False

class Catalog(IceFlix.MediaCatalog):
    """Servant for the IceFlix.MediaCatalog interface."""

    def getTile(self, mediaId, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve el medio cuyo identificador sea igual a mediaId."
        # TODO: implement
        return None
    
    def getTilesByName(self, name, exact, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve una lista con los identificadores según el título de los medios."
        # TODO: implement
        return None

    def getTilesByTags(self, tags, includeAllTags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "Devuelve una lista con los identificadores según los tags de los medios."
        # TODO: implement
        return None
    
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
        # TODO: implement
        return None
    
    def addTags(self,  mediaId, tags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "permite añadir una lista de tags a un medio concreto."
        # TODO: implement
        return None
    
    def removeTags(self,  mediaId, tags, userToken, current=None):  # pylint:disable=invalid-name, unused-argument
        "permite eliminar una lista de tags de un medio concreto."
        # TODO: implement
        return None


class CatalogServer(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.idService = str(uuid.uuid4())
        self.servant = Catalog()
        self.proxy = None
        self.adapter = None

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

## Media getTile(string mediaId, string userToken) throws WrongMediaId,     TemporaryUnavailable, Unauthorized;
## StringList getTilesByName(string name, bool exact);
# StringList getTilesByTags(StringList tags, bool includeAllTags, string userToken) throws Unauthorized;
# void newMedia(string mediaId, FileService* provider);
# void removeMedia(string mediaId, FileService* provider);
# void renameTile(string mediaId, string name, string adminToken) throws Unauthorized, WrongMediaId;

# void addTags(string mediaId, StringList tags, string userToken) throws Unauthorized, WrongMediaId;
# void removeTags(string mediaId, StringList tags, string userToken) throws Unauthorized, WrongMediaId;