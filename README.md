# Repositorio para la entrega final del laboratorio de SSDD - IceFlix: diseño de microservicios

## Estructura del repositorio

El repositorio contiene los siguientes archivos y directorios:

* `configs`: directorio que contiene los archivos de configuración de los servicios y tests.
* `DB`: directorio que contiene el fichero que almacena los medios del sistema.
    *  `DB/media.json`: archivo **.json** que sirve como almacenamiento persistente de los medios del servicio de catálogo.
    *  `DB/tmp`: directorio en el que se almacenan los archivos temporales de la conexión de **IceStorm**
* `iceflix`: directorio principal del servicio.
    * `iceflix/catalog_server.py`: implementación del servicio del catálogo.
    * `iceflix/iceflix.ice`: contiene las definiciones de las interfaces Slice sistema.
    * `iceflix/run_icestorm`: script que ejecuta el arranque de Icebox.
    * `iceflix/run_service`: script que ejecuta el servicio del catálogo.
* `tests`: directorio que contiene las pruebas del servicio.
    * `tests/authenticator_tester.py`: servicio que simula el servicio de autenticación implementando solo los métodos que utiliza el catálogo.
    * `tests/main_tester.py`: servicio que simula el servicio de principal implementando solo los métodos que utiliza el catálogo.
    * `tests/test_server.py`: programa que prueba las llamadas del servicio de catálogo, simulando en parte al servicio de ficheros y un servicio de catálogo auxiliar.
    * `tests/run_mainTester`: script que ejecuta los servicios que simulan al Main y al authenticator.
    * `tests/run_tests`: script que ejecuta las pruebas del catálogo.

## Ejecución del Servicio

Para utilizar el servicio del cátalogo de manera distribuida con el resto de servicios del sistema es necesario:
1. Desde el directorio `iceflix/` ejecutar **IceBox** con el comando `./run_icestorm`.
2. Desde el directorio `iceflix/` ejecutar el servicio **Catalog** con el comando `./run_service`.

## Ejecución de las Pruebas

Para la ejecución de las pruebas es necesario:
1. Desde el directorio `iceflix/` ejecutar **IceBox** con el comando `./run_icestorm`.
2. Desde el directorio `tests/` ejecutar los simuladores del **Main** y del **Authenticator** con el comando `./run_mainTester`.
3. Desde el directorio `iceflix/` ejecutar el servicio **Catalog** con el comando `./run_service`.
4. Desde el directorio `tests/` ejecutar las pruebas con el comando `./run_tests`.

## Librerías y paquetes requeridos
Para la correcta ejecución del sistema es necesaria la instalación de la librería `zeroc-ice` en una versión mayor o igual a la **3.7.0**, así como las librerías de `icebox` en una versión mayor o igual a la **3.7.0**.

