'''Tester.'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import Ice

Ice.loadSlice("../iceflix/iceflix.ice")
import IceFlix  # pylint: disable=import-error, wrong-import-position


class Test():  # pylint: disable=too-many-instance-attributes
    '''Test class.'''

    def __init__(self):
        self.new_media_vacio = False
        self.new_media_no_vacio = False

        self.removed_media_existe = False
        self.removed_media_no_existe = False

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

    def show_results(self):
        '''Muestra los resultados de los tests.'''
        logging.info("\tTest 01 - newMedia_vacio: %s\n", self.new_media_vacio)
        logging.info("\tTest 02 - newMedia_noVacio: %s\n",
                     self.new_media_no_vacio)
        logging.info("\tTest 03 - renameTile_unauthorized: %s\n",
                     self.rename_tile_unauthorized)
        logging.info("\tTest 04 - renameTile_wrongMediaId: %s\n",
                     self.rename_tile_wrong_media_id)
        logging.info("\tTest 05 - renameTile_correcto: %s\n",
                     self.rename_tile_correcto)
        logging.info("\tTest 06 - addTags_unauthorized: %s\n",
                     self.add_tags_unauthorized)
        logging.info("\tTest 07 - addTags_wrongMediaId: %s\n",
                     self.add_tags_wrong_media_id)
        logging.info("\tTest 08 - addTags_correcto: %s\n",
                     self.add_tags_correcto)
        logging.info("\tTest 09 - addTags_repetido: %s\n",
                     self.add_tags_repetido)
        logging.info("\tTest 10 - removeTags_unauthorized: %s\n",
                     self.remove_tags_unauthorized)
        logging.info("\tTest 11 - removeTags_wrongMediaId: %s\n",
                     self.remove_tags_wrong_media_id)
        logging.info("\tTest 12 - removeTags_correcto: %s\n",
                     self.remove_tags_correcto)
        logging.info("\tTest 13 - getTile_unauthorized: %s\n",
                     self.get_tile_unauthorized)
        logging.info("\tTest 14 - getTile_wrongMediaId: %s\n",
                     self.get_tile_wrong_media_id)
        logging.info("\tTest 15 - getTile_correcto: %s\n",
                     self.get_tile_correcto)
        logging.info("\tTest 16 - getTilesByName_exact: %s\n",
                     self.get_tiles_by_name_exact)
        logging.info("\tTest 11 - getTilesByName_noExact: %s\n",
                     self.get_tiles_by_name_no_exact)
        logging.info("\tTest 18 - getTilesByTags_unauthorized: %s\n",
                     self.get_tiles_by_tags_unauthorized)
        logging.info("\tTest 19 - getTilesByTags_any: %s\n",
                     self.get_tiles_by_tags_any)
        logging.info("\tTest 20 - getTilesByTags_all: %s\n",
                     self.get_tiles_by_tags_all)
        logging.info("\tTest 21 - removedMedia_noExiste: %s\n",
                     self.removed_media_no_existe)
        logging.info("\tTest 22 - removedMedia_existe: %s\n",
                     self.removed_media_existe)

    def run_tests(self):  # pylint: disable=too-many-branches, too-many-statements
        '''Ejecuta los tests.'''
        catalog_service = IceFlix.MediaCatalogPrx.uncheckedCast(
            server.proxy_service)
        file_service = IceFlix.FileServicePrx.uncheckedCast(server.proxy_file)

        logging.info("\t\t--- TESTS ---")

        # newMedia_vacio
        catalog_service.newMedia("Test1", file_service)

        # newMedia_noVacio
        catalog_service.newMedia("Test2", file_service)

        # renameTile_unauthorized
        try:
            catalog_service.renameTile("Test1", "Nombre prueba 1", "user01")
            logging.info("llamada rename")
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
            self.new_media_vacio = True
            self.rename_tile_correcto = True
            self.get_tile_correcto = True

        if media_test2.info.name == "Nombre prueba 2":
            self.new_media_no_vacio = True

        if media_test1.info.tags == ["Test", "Prueba"]:
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

        # removedMedia_noExiste
        catalog_service.removeMedia("Test15", file_service)
        result = catalog_service.getTilesByTags(["Test"], False, "user01")
        if len(result) > 1:
            self.removed_media_no_existe = True

        # removedMedia_existe
        catalog_service.removeMedia("Test1", file_service)
        result = catalog_service.getTilesByTags(["Test"], False, "user01")
        if len(result) == 1:
            self.removed_media_existe = True

        # eliminar todos los medios de prueba
        catalog_service.removeMedia("Test2", file_service)
        result = catalog_service.getTilesByTags(["Test"], False, "user01")
        # print(result)

        # mostrar resultados
        self.show_results()


class FileTester(IceFlix.FileService):  # pylint: disable=too-few-public-methods
    """Example FileService servant."""


class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant_file = FileTester()
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

        self.proxy_file = self.adapter_file.add(
            self.servant_file, comm.stringToIdentity("FileTester"))
        logging.info("Proxy FileTester: %s\n", self.proxy_file)

        with open("../configs/catalog_proxy.proxy", "r", encoding='utf-8') as file:
            self.str_proxy_service = file.readline()
        self.proxy_service = comm.stringToProxy(self.str_proxy_service)

        self.tester.run_tests()

        # self.shutdownOnInterrupt()
        # comm.waitForShutdown()
        return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    server = MainApp()
    sys.exit(server.main(sys.argv))
