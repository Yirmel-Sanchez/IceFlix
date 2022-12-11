#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import Ice
import json
import sys
Ice.loadSlice("../iceflix/iceflix.ice")
import IceFlix


class Test():
    def __init__(self):
        self.newMedia_vacio = False
        self.newMedia_noVacio = False

        self.removedMedia_existe = False
        self.removedMedia_noExiste = False
        
        self.renameTile_unauthorized = False
        self.renameTile_wrongMediaId = False
        self.renameTile_correcto = False

        self.addTags_unauthorized = False
        self.addTags_wrongMediaId = False
        self.addTags_correcto = False
        self.addTags_repetido = False

        self.removeTags_unauthorized = False
        self.removeTags_wrongMediaId = False
        self.removeTags_correcto = False

        self.getTile_unauthorized = False
        self.getTile_wrongMediaId = False
        self.getTile_correcto = False

        self.getTilesByName_exact = False
        self.getTilesByName_noExact = False

        self.getTilesByTags_unauthorized = False
        self.getTilesByTags_any = False
        self.getTilesByTags_all = False

    def showResults(self):
        logging.info("\tTest 01 - newMedia_vacio: %s\n", self.newMedia_vacio)
        logging.info("\tTest 02 - newMedia_noVacio: %s\n", self.newMedia_noVacio)
        logging.info("\tTest 03 - renameTile_unauthorized: %s\n", self.renameTile_unauthorized)
        logging.info("\tTest 04 - renameTile_wrongMediaId: %s\n", self.renameTile_wrongMediaId)
        logging.info("\tTest 05 - renameTile_correcto: %s\n", self.renameTile_correcto)
        logging.info("\tTest 06 - addTags_unauthorized: %s\n", self.addTags_unauthorized)
        logging.info("\tTest 07 - addTags_wrongMediaId: %s\n", self.addTags_wrongMediaId)
        logging.info("\tTest 08 - addTags_correcto: %s\n", self.addTags_correcto)
        logging.info("\tTest 09 - addTags_repetido: %s\n", self.addTags_repetido)
        logging.info("\tTest 10 - removeTags_unauthorized: %s\n", self.removeTags_unauthorized)
        logging.info("\tTest 11 - removeTags_wrongMediaId: %s\n", self.removeTags_wrongMediaId)
        logging.info("\tTest 12 - removeTags_correcto: %s\n", self.removeTags_correcto)
        logging.info("\tTest 13 - getTile_unauthorized: %s\n", self.getTile_unauthorized)
        logging.info("\tTest 14 - getTile_wrongMediaId: %s\n", self.getTile_wrongMediaId)
        logging.info("\tTest 15 - getTile_correcto: %s\n", self.getTile_correcto)
        logging.info("\tTest 16 - getTilesByName_exact: %s\n", self.getTilesByName_exact)
        logging.info("\tTest 11 - getTilesByName_noExact: %s\n", self.getTilesByName_noExact)
        logging.info("\tTest 18 - getTilesByTags_unauthorized: %s\n", self.getTilesByTags_unauthorized)
        logging.info("\tTest 19 - getTilesByTags_any: %s\n", self.getTilesByTags_any)
        logging.info("\tTest 20 - getTilesByTags_all: %s\n", self.getTilesByTags_all)
        logging.info("\tTest 21 - removedMedia_noExiste: %s\n", self.removedMedia_noExiste)
        logging.info("\tTest 22 - removedMedia_existe: %s\n", self.removedMedia_existe)
        

    def run_tests(self):
        catalogService = IceFlix.MediaCatalogPrx.uncheckedCast(server.proxy_service)
        fileService = IceFlix.FileServicePrx.uncheckedCast(server.proxy_file)
        
        logging.info("\t\t--- TESTS ---")


        # newMedia_vacio
        catalogService.newMedia("Test1", fileService)

        # newMedia_noVacio
        catalogService.newMedia("Test2", fileService)

        # renameTile_unauthorized
        try:
            catalogService.renameTile("Test1", "Nombre prueba 1", "user01")
            logging.info("llamada rename")
        except IceFlix.Unauthorized:
            self.renameTile_unauthorized = True

        # renameTile_wrongMediaId
        try:
            catalogService.renameTile("Test15", "Nombre prueba 1", "admin01")
        except IceFlix.WrongMediaId:
            self.renameTile_wrongMediaId = True
        
        # renameTile_correcto
        catalogService.renameTile("Test1", "Nombre prueba 1", "admin01")
        catalogService.renameTile("Test2", "Nombre prueba 2", "admin01")

        # addTags_unauthorized
        try:
            catalogService.addTags("Test1", ["nada","aqui"], "user02")
        except IceFlix.Unauthorized:
            self.addTags_unauthorized = True

        # addTags_wrongMediaId
        try:
            catalogService.addTags("Test15", ["nada","aqui"], "user01")
        except IceFlix.WrongMediaId:
            self.addTags_wrongMediaId = True

        # addTags_correcto
        catalogService.addTags("Test1", ["Test","Prueba","quitar"], "user01")

        # addTags_repetido
        catalogService.addTags("Test2", ["Test","Test"], "user01")

        # removeTags_unauthorized
        try:
            catalogService.removeTags("Test1", ["quitar"], "user02")
        except IceFlix.Unauthorized:
            self.removeTags_unauthorized = True
        
        # removeTags_wrongMediaId
        try:
            catalogService.removeTags("Test15", ["quitar"], "user01")
        except IceFlix.WrongMediaId:
            self.removeTags_wrongMediaId = True
        
        # removeTags_correcto
        catalogService.removeTags("Test1", ["quitar"], "user01")

        # getTile_unauthorized
        try:
            catalogService.getTile("Test1", "user02")
        except IceFlix.Unauthorized:
            self.getTile_unauthorized = True
        
        # getTile_wrongMediaId
        try:
            catalogService.getTile("Test15", "user01")
        except IceFlix.WrongMediaId:
            self.getTile_wrongMediaId = True
        
        # getTile_correcto
        media_Test1 = catalogService.getTile("Test1", "user01")
        media_Test2 = catalogService.getTile("Test2", "user01")

        if media_Test1.info.name == "Nombre prueba 1":
            self.newMedia_vacio = True
            self.renameTile_correcto = True
            self.getTile_correcto = True

        if media_Test2.info.name == "Nombre prueba 2":
            self.newMedia_noVacio = True
        
        if media_Test1.info.tags == ["Test","Prueba"]:
            self.addTags_correcto = True
            self.removeTags_correcto = True

        if media_Test2.info.tags == ["Test"]:
            self.addTags_repetido = True
        
        # getTilesByName_exact
        result = catalogService.getTilesByName("Nombre prueba 1", True)
        if len(result) == 1 and result[0] == "Test1":
            self.getTilesByName_exact = True

        # getTilesByName_noExact
        result = catalogService.getTilesByName("Nombre prueba", False)
        if len(result) == 2 and result[0] == "Test1" and result[1] == "Test2":
            self.getTilesByName_noExact = True

        # getTilesByTags_unauthorized
        try:
            catalogService.getTilesByTags(["Test"], False, "user02")
        except IceFlix.Unauthorized:
            self.getTilesByTags_unauthorized = True

        # getTilesByTags_any
        result = catalogService.getTilesByTags(["Test","Prueba"], False, "user01")
        if len(result) > 1:
            self.getTilesByTags_any = True

        # getTilesByTags_all
        result = catalogService.getTilesByTags(["Test","Prueba"], True, "user01")
        if len(result) == 1:
            self.getTilesByTags_all = True

        # removedMedia_noExiste
        catalogService.removeMedia("Test15", fileService)
        result = catalogService.getTilesByTags(["Test"], False, "user01")
        if len(result) > 1:
            self.removedMedia_noExiste = True

        # removedMedia_existe
        catalogService.removeMedia("Test1", fileService)
        result = catalogService.getTilesByTags(["Test"], False, "user01")
        if len(result) == 1:
            self.removedMedia_existe = True
        
        # eliminar todos los medios de prueba
        catalogService.removeMedia("Test2", fileService)
        result = catalogService.getTilesByTags(["Test"], False, "user01")
        #print(result)

        # mostrar resultados
        self.showResults()


class FileTester(IceFlix.FileService):
    pass

class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servantFile = FileTester()
        self.tester = Test()
        self.proxy_file = None
        self.proxy_service = None
        self.str_proxy_service = ""
        self.adapter_file = None
        

    def run(self, args):
        """Run the application, adding the needed objects to the adapter."""
        logging.info("Running Tester application\n")
        comm = self.communicator()

        # FileService
        self.adapter_file = comm.createObjectAdapter("TestFileAdapter")
        self.adapter_file.activate()

        self.proxy_file = self.adapter_file.add(self.servantFile, comm.stringToIdentity("FileTester"))
        logging.info("Proxy FileTester: %s\n", self.proxy_file)

        with open("../configs/catalog_proxy.proxy", "r") as f:
            self.str_proxy_service = f.readline()
        self.proxy_service = comm.stringToProxy(self.str_proxy_service)

        self.tester.run_tests()

        #self.shutdownOnInterrupt()
        #comm.waitForShutdown()
        return 0

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = MainApp()
    sys.exit(server.main(sys.argv))