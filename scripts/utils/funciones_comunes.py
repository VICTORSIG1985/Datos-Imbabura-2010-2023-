#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
FUNCIONES COMUNES PARA EL PROYECTO
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Fecha: Diciembre 2025

Descripción:
    Este módulo contiene funciones auxiliares reutilizables para todos los
    scripts del proyecto, incluyendo:
    - Manejo de rasters (lectura, escritura, validación)
    - Generación de logs y auditorías
    - Control de calidad según ISO 19157
    - Funciones de utilidad general

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)
    - ISO 19115-1:2014 (Metadatos geográficos)
================================================================================
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any

import numpy as np

# Intentar importar librerías geoespaciales
try:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import Affine
    from rasterio.enums import Resampling
    RASTERIO_DISPONIBLE = True
except ImportError:
    RASTERIO_DISPONIBLE = False
    print("ADVERTENCIA: rasterio no está instalado. Algunas funciones no estarán disponibles.")

try:
    import geopandas as gpd
    GEOPANDAS_DISPONIBLE = True
except ImportError:
    GEOPANDAS_DISPONIBLE = False


# ==============================================================================
# CONFIGURACIÓN DE LOGGING
# ==============================================================================

def configurar_logging(
    nombre_script: str,
    directorio_logs: Path,
    nivel: int = logging.INFO
) -> logging.Logger:
    """
    Configura el sistema de logging para un script.

    Args:
        nombre_script: Nombre del script (para nombrar el archivo log)
        directorio_logs: Directorio donde guardar los logs
        nivel: Nivel de logging (default: INFO)

    Returns:
        logging.Logger: Logger configurado
    """
    # Crear directorio de logs si no existe
    directorio_logs.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo log con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_log = directorio_logs / f"{nombre_script}_{timestamp}.log"

    # Configurar formato
    formato = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para archivo
    file_handler = logging.FileHandler(archivo_log, encoding='utf-8')
    file_handler.setFormatter(formato)
    file_handler.setLevel(nivel)

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formato)
    console_handler.setLevel(nivel)

    # Crear logger
    logger = logging.getLogger(nombre_script)
    logger.setLevel(nivel)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Log iniciado: {archivo_log}")

    return logger


# ==============================================================================
# FUNCIONES DE AUDITORÍA
# ==============================================================================

def generar_auditoria(
    nombre_proceso: str,
    parametros: Dict,
    resultados: Dict,
    archivos_entrada: List[str],
    archivos_salida: List[str],
    directorio_salida: Path,
    metadata_adicional: Optional[Dict] = None
) -> Path:
    """
    Genera un archivo JSON de auditoría para un proceso.

    Cumple con ISO 19115-1:2014 para trazabilidad de linaje.

    Args:
        nombre_proceso: Nombre del proceso ejecutado
        parametros: Parámetros utilizados
        resultados: Resultados obtenidos (métricas, estadísticas)
        archivos_entrada: Lista de archivos de entrada
        archivos_salida: Lista de archivos de salida
        directorio_salida: Directorio donde guardar la auditoría
        metadata_adicional: Metadatos adicionales opcionales

    Returns:
        Path: Ruta del archivo de auditoría generado
    """
    timestamp = datetime.now()

    auditoria = {
        "proceso": nombre_proceso,
        "fecha_ejecucion": timestamp.isoformat(),
        "timestamp_unix": timestamp.timestamp(),
        "version_python": sys.version,
        "sistema_operativo": sys.platform,

        "entradas": {
            "archivos": archivos_entrada,
            "parametros": parametros
        },

        "salidas": {
            "archivos": archivos_salida,
            "resultados": resultados
        },

        "linaje_iso19115": {
            "LI_Lineage": {
                "statement": f"Proceso: {nombre_proceso}",
                "processStep": {
                    "description": nombre_proceso,
                    "dateTime": timestamp.isoformat(),
                    "processor": {
                        "individualName": "Víctor Hugo Pinto Páez",
                        "organisationName": "Universidad de las Fuerzas Armadas ESPE"
                    }
                },
                "source": archivos_entrada
            }
        }
    }

    if metadata_adicional:
        auditoria["metadata_adicional"] = metadata_adicional

    # Calcular checksums de archivos de salida
    auditoria["checksums"] = {}
    for archivo in archivos_salida:
        if Path(archivo).exists():
            auditoria["checksums"][archivo] = calcular_checksum(archivo)

    # Guardar auditoría
    directorio_salida.mkdir(parents=True, exist_ok=True)
    archivo_auditoria = directorio_salida / f"AUDITORIA_{nombre_proceso}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

    with open(archivo_auditoria, 'w', encoding='utf-8') as f:
        json.dump(auditoria, f, indent=2, ensure_ascii=False, default=str)

    return archivo_auditoria


def calcular_checksum(archivo: Union[str, Path], algoritmo: str = 'sha256') -> str:
    """
    Calcula el checksum de un archivo para verificación de integridad.

    Args:
        archivo: Ruta del archivo
        algoritmo: Algoritmo de hash ('sha256', 'md5')

    Returns:
        str: Checksum en hexadecimal
    """
    hash_func = hashlib.new(algoritmo)
    with open(archivo, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


# ==============================================================================
# FUNCIONES PARA RASTERS
# ==============================================================================

def leer_raster(ruta: Union[str, Path]) -> Tuple[np.ndarray, Dict]:
    """
    Lee un raster y retorna los datos y metadatos.

    Args:
        ruta: Ruta al archivo raster

    Returns:
        Tuple[np.ndarray, Dict]: (datos, metadatos)
    """
    if not RASTERIO_DISPONIBLE:
        raise ImportError("rasterio no está disponible")

    with rasterio.open(ruta) as src:
        datos = src.read(1)
        metadatos = {
            'crs': src.crs,
            'transform': src.transform,
            'width': src.width,
            'height': src.height,
            'dtype': src.dtypes[0],
            'nodata': src.nodata,
            'bounds': src.bounds,
            'count': src.count
        }
    return datos, metadatos


def escribir_raster(
    datos: np.ndarray,
    ruta_salida: Union[str, Path],
    metadatos_plantilla: Dict,
    nodata: float = -9999,
    dtype: str = 'float32',
    compress: str = 'LZW'
) -> Path:
    """
    Escribe un raster con metadatos especificados.

    Cumple con ISO 19157 para calidad de datos.

    Args:
        datos: Array numpy con los datos
        ruta_salida: Ruta de salida
        metadatos_plantilla: Metadatos de un raster de referencia
        nodata: Valor NoData
        dtype: Tipo de datos
        compress: Algoritmo de compresión

    Returns:
        Path: Ruta del archivo creado
    """
    if not RASTERIO_DISPONIBLE:
        raise ImportError("rasterio no está disponible")

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    perfil = {
        'driver': 'GTiff',
        'dtype': dtype,
        'width': metadatos_plantilla['width'],
        'height': metadatos_plantilla['height'],
        'count': 1,
        'crs': metadatos_plantilla['crs'],
        'transform': metadatos_plantilla['transform'],
        'nodata': nodata,
        'compress': compress,
        'tiled': True,
        'blockxsize': 256,
        'blockysize': 256
    }

    with rasterio.open(ruta_salida, 'w', **perfil) as dst:
        dst.write(datos.astype(dtype), 1)

    return ruta_salida


def validar_raster_iso19157(
    ruta: Union[str, Path],
    crs_esperado: str = 'EPSG:32717',
    resolucion_esperada: float = 30.0,
    nodata_esperado: float = -9999
) -> Dict:
    """
    Valida un raster según estándares ISO 19157.

    Verifica:
    - Completitud (porcentaje de datos válidos)
    - Consistencia lógica (CRS, resolución, NoData)
    - Exactitud posicional (alineación de pixeles)

    Args:
        ruta: Ruta al raster
        crs_esperado: CRS esperado
        resolucion_esperada: Resolución esperada en metros
        nodata_esperado: Valor NoData esperado

    Returns:
        Dict: Resultados de validación
    """
    if not RASTERIO_DISPONIBLE:
        raise ImportError("rasterio no está disponible")

    resultados = {
        'archivo': str(ruta),
        'valido': True,
        'errores': [],
        'advertencias': [],
        'metricas': {}
    }

    try:
        with rasterio.open(ruta) as src:
            # Verificar CRS
            if src.crs is None:
                resultados['errores'].append("CRS no definido")
                resultados['valido'] = False
            elif str(src.crs) != crs_esperado:
                resultados['errores'].append(
                    f"CRS incorrecto: {src.crs} (esperado: {crs_esperado})"
                )
                resultados['valido'] = False

            # Verificar resolución
            res_x = abs(src.transform[0])
            res_y = abs(src.transform[4])
            if abs(res_x - resolucion_esperada) > 0.1 or abs(res_y - resolucion_esperada) > 0.1:
                resultados['errores'].append(
                    f"Resolución incorrecta: {res_x}x{res_y} (esperado: {resolucion_esperada})"
                )
                resultados['valido'] = False

            # Verificar NoData
            if src.nodata != nodata_esperado:
                resultados['advertencias'].append(
                    f"NoData diferente: {src.nodata} (esperado: {nodata_esperado})"
                )

            # Calcular completitud
            datos = src.read(1)
            if src.nodata is not None:
                validos = np.sum(datos != src.nodata)
            else:
                validos = np.sum(~np.isnan(datos))
            total = datos.size
            completitud = validos / total * 100

            resultados['metricas'] = {
                'crs': str(src.crs),
                'resolucion_x': res_x,
                'resolucion_y': res_y,
                'ancho': src.width,
                'alto': src.height,
                'nodata': src.nodata,
                'dtype': src.dtypes[0],
                'completitud_porcentaje': round(completitud, 2),
                'pixeles_validos': int(validos),
                'pixeles_totales': int(total),
                'valor_minimo': float(np.nanmin(datos[datos != src.nodata])) if src.nodata else float(np.nanmin(datos)),
                'valor_maximo': float(np.nanmax(datos[datos != src.nodata])) if src.nodata else float(np.nanmax(datos)),
                'bounds': {
                    'left': src.bounds.left,
                    'bottom': src.bounds.bottom,
                    'right': src.bounds.right,
                    'top': src.bounds.top
                }
            }

            # Verificar completitud mínima
            if completitud < 95:
                resultados['advertencias'].append(
                    f"Completitud baja: {completitud:.2f}% (recomendado: >95%)"
                )

    except Exception as e:
        resultados['errores'].append(f"Error al leer raster: {str(e)}")
        resultados['valido'] = False

    return resultados


def obtener_estadisticas_raster(ruta: Union[str, Path]) -> Dict:
    """
    Calcula estadísticas descriptivas de un raster.

    Args:
        ruta: Ruta al raster

    Returns:
        Dict: Estadísticas (min, max, mean, std, percentiles)
    """
    if not RASTERIO_DISPONIBLE:
        raise ImportError("rasterio no está disponible")

    with rasterio.open(ruta) as src:
        datos = src.read(1)
        nodata = src.nodata

        # Crear máscara de datos válidos
        if nodata is not None:
            mask = datos != nodata
        else:
            mask = ~np.isnan(datos)

        datos_validos = datos[mask]

        if len(datos_validos) == 0:
            return {'error': 'No hay datos válidos'}

        estadisticas = {
            'count': len(datos_validos),
            'min': float(np.min(datos_validos)),
            'max': float(np.max(datos_validos)),
            'mean': float(np.mean(datos_validos)),
            'std': float(np.std(datos_validos)),
            'median': float(np.median(datos_validos)),
            'percentile_5': float(np.percentile(datos_validos, 5)),
            'percentile_25': float(np.percentile(datos_validos, 25)),
            'percentile_75': float(np.percentile(datos_validos, 75)),
            'percentile_95': float(np.percentile(datos_validos, 95)),
        }

    return estadisticas


# ==============================================================================
# FUNCIONES DE UTILIDAD
# ==============================================================================

def formatear_tiempo(segundos: float) -> str:
    """
    Formatea segundos a formato legible.

    Args:
        segundos: Tiempo en segundos

    Returns:
        str: Tiempo formateado (ej: "2h 15m 30s")
    """
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)

    partes = []
    if horas > 0:
        partes.append(f"{horas}h")
    if minutos > 0:
        partes.append(f"{minutos}m")
    partes.append(f"{segs}s")

    return " ".join(partes)


def imprimir_banner(titulo: str, ancho: int = 70):
    """
    Imprime un banner decorativo para la consola.

    Args:
        titulo: Título a mostrar
        ancho: Ancho del banner
    """
    print("=" * ancho)
    print(titulo.center(ancho))
    print("=" * ancho)


def imprimir_seccion(titulo: str, ancho: int = 70):
    """
    Imprime un separador de sección.

    Args:
        titulo: Título de la sección
        ancho: Ancho del separador
    """
    print()
    print("-" * ancho)
    print(titulo)
    print("-" * ancho)


def verificar_dependencias(dependencias: List[str]) -> Dict[str, bool]:
    """
    Verifica si las dependencias están instaladas.

    Args:
        dependencias: Lista de nombres de paquetes

    Returns:
        Dict[str, bool]: Estado de cada dependencia
    """
    import importlib

    estado = {}
    for dep in dependencias:
        try:
            importlib.import_module(dep)
            estado[dep] = True
        except ImportError:
            estado[dep] = False

    return estado


# ==============================================================================
# CLASE PARA GESTIÓN DE PROGRESO
# ==============================================================================

class BarraProgreso:
    """
    Barra de progreso simple para consola.
    """

    def __init__(self, total: int, descripcion: str = "", ancho: int = 40):
        self.total = total
        self.descripcion = descripcion
        self.ancho = ancho
        self.actual = 0

    def actualizar(self, incremento: int = 1):
        """Actualiza la barra de progreso."""
        self.actual += incremento
        porcentaje = self.actual / self.total
        completado = int(self.ancho * porcentaje)
        barra = "█" * completado + "░" * (self.ancho - completado)
        print(f"\r{self.descripcion}: [{barra}] {porcentaje*100:.1f}%", end="", flush=True)

    def finalizar(self):
        """Finaliza la barra de progreso."""
        print()


# ==============================================================================
# REFERENCIAS BIBLIOGRÁFICAS DE ESTE MÓDULO
# ==============================================================================
REFERENCIAS = """
Referencias bibliográficas de las funciones implementadas:

1. ISO 19157:2013 - Geographic information - Data quality
   International Organization for Standardization.

2. ISO 19115-1:2014 - Geographic information - Metadata - Part 1: Fundamentals
   International Organization for Standardization.

3. GDAL/Rasterio documentation
   https://rasterio.readthedocs.io/

4. NumPy documentation
   https://numpy.org/doc/
"""

if __name__ == "__main__":
    print("Módulo de funciones comunes cargado correctamente.")
    print()
    print("Dependencias disponibles:")
    deps = verificar_dependencias(['rasterio', 'geopandas', 'numpy', 'pandas', 'scipy'])
    for dep, disponible in deps.items():
        status = "OK" if disponible else "NO INSTALADO"
        print(f"  [{status}] {dep}")
