#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
CONFIGURACIÓN CENTRAL DEL PROYECTO
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Institución: Universidad de las Fuerzas Armadas ESPE
Fecha de creación: Diciembre 2025
Versión: 1.0.0

Descripción:
    Este archivo centraliza todas las rutas, parámetros y configuraciones
    del proyecto para garantizar consistencia y reproducibilidad científica.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)
    - ISO 19115-1:2014 (Metadatos geográficos)
    - ISO 19131:2007 (Especificaciones de productos de datos)

Referencias metodológicas:
    - Varnes, D.J. (1978). Slope movement types and processes.
    - Reichenbach et al. (2018). A review of statistically-based landslide
      susceptibility models. Earth-Science Reviews, 180, 60-91.
================================================================================
"""

import os
from pathlib import Path
from datetime import datetime

# ==============================================================================
# METADATOS DEL PROYECTO
# ==============================================================================
PROYECTO = {
    "nombre": "Susceptibilidad a Deslizamientos - Imbabura",
    "autor": "Víctor Hugo Pinto Páez",
    "institucion": "Universidad de las Fuerzas Armadas ESPE",
    "fecha_inicio": "2025-12-26",
    "version": "1.0.0",
    "area_estudio": "Provincia de Imbabura, Ecuador",
    "periodo_analisis": "2010-2023",
    "crs": "EPSG:32717",
    "crs_nombre": "WGS 84 / UTM zone 17S",
    "resolucion_metros": 30,
    "nodata_value": -9999,
}

# ==============================================================================
# RUTAS BASE (AJUSTAR SEGÚN TU SISTEMA)
# ==============================================================================
# Ruta base del proyecto - MODIFICAR SEGÚN TU CONFIGURACIÓN
BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Directorio de trabajo para investigación
INVESTIGACION_PATH = BASE_PATH / "Investigacion"

# Directorio para scripts
SCRIPTS_PATH = INVESTIGACION_PATH / "SCRIPTS"

# ==============================================================================
# RUTAS DE DATOS DE ENTRADA (FUENTES ORIGINALES CERTIFICADAS)
# ==============================================================================
DATOS_ENTRADA = {
    # A) DEM Original
    "dem_original": BASE_PATH / "DEM_IMBABURA_17_COR.tif",

    # B) Inventario de Deslizamientos
    "inventario_xlsx": BASE_PATH / "DESLIZAMIENTOS_SGNR.xlsx",

    # C) Área de Interés (AOI)
    "aoi_cantones": Path(r"D:\DATA\AOI_IMBABURA_CANTON.gpkg"),

    # D) Variables Categóricas (Shapefiles)
    "geomorfologia": BASE_PATH / "v_ge004_geomorfologia_a",
    "cobertura_vegetal": BASE_PATH / "v_ff010_cobertura_vegetal_2022_a",
    "deforestacion": BASE_PATH / "v_fc010_deforestacion_90_20_a",

    # E) Índices Espectrales Landsat
    "landsat_dir": BASE_PATH / "02_COVARIABLES" / "LANDSAT",

    # F) Variables Bioclimáticas WorldClim
    "worldclim": BASE_PATH / "world_clim" / "WorldClim_v2.1_Baseline_1970-2000_Imbabura_UTM17S.tif",

    # G) Datos Censales
    "censo_dir": BASE_PATH / "02_COVARIABLES" / "CENSO",
}

# ==============================================================================
# RUTAS DE SALIDA (ORGANIZADAS POR PASO)
# ==============================================================================
SALIDAS = {
    # Paso 00A: Derivados Topográficos
    "derivados_topo": INVESTIGACION_PATH / "00_Derivados_Topograficos",

    # Paso 00B: Análisis de Multicolinealidad
    "multicolinealidad": INVESTIGACION_PATH / "00_Analisis_Multicolinealidad",

    # Paso 01: Inventario Procesado
    "inventario": INVESTIGACION_PATH / "01_PROCESSED",

    # Paso 02: Covariables Procesadas
    "covariables": INVESTIGACION_PATH / "02_COVARIABLES",

    # Paso 03: Muestreo de Ausencias
    "muestreo": INVESTIGACION_PATH / "03_MUESTREO",

    # Paso 04: Extracción de Valores
    "extraccion": INVESTIGACION_PATH / "04_EXTRACCION",

    # Paso 05: Modelos Entrenados
    "modelos": INVESTIGACION_PATH / "05_MODELOS",

    # Paso 06: Mapas Finales
    "mapas": INVESTIGACION_PATH / "06_MAPAS",

    # Logs y Auditorías
    "logs": INVESTIGACION_PATH / "LOGS",
    "auditorias": INVESTIGACION_PATH / "AUDITORIAS",
}

# ==============================================================================
# ÍNDICES ESPECTRALES LANDSAT (2010-2023)
# ==============================================================================
INDICES_LANDSAT = {
    "NDVI": {
        "media": "NDVI_media_2010-2023.tif",
        "std": "NDVI_std_2010-2023.tif",
        "descripcion": "Normalized Difference Vegetation Index",
        "formula": "(NIR - RED) / (NIR + RED)",
        "rango": [-1, 1],
        "referencia": "Rouse et al. (1974)"
    },
    "EVI": {
        "media": "EVI_media_2010-2023.tif",
        "std": "EVI_std_2010-2023.tif",
        "descripcion": "Enhanced Vegetation Index",
        "formula": "2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))",
        "rango": [-1, 1],
        "referencia": "Huete et al. (2002)"
    },
    "NDMI": {
        "media": "NDMI_media_2010-2023.tif",
        "std": "NDMI_std_2010-2023.tif",
        "descripcion": "Normalized Difference Moisture Index",
        "formula": "(NIR - SWIR1) / (NIR + SWIR1)",
        "rango": [-1, 1],
        "referencia": "Gao (1996)"
    },
    "LST": {
        "media": "LST_media_2010-2023.tif",
        "std": "LST_std_2010-2023.tif",
        "descripcion": "Land Surface Temperature",
        "unidades": "Kelvin",
        "referencia": "Jiménez-Muñoz et al. (2014)"
    },
    "NDWI": {
        "media": "NDWI_media_2010-2023.tif",
        "std": "NDWI_std_2010-2023.tif",
        "descripcion": "Normalized Difference Water Index",
        "formula": "(GREEN - NIR) / (GREEN + NIR)",
        "rango": [-1, 1],
        "referencia": "McFeeters (1996)"
    },
    "MNDWI": {
        "media": "MNDWI_media_2010-2023.tif",
        "std": "MNDWI_std_2010-2023.tif",
        "descripcion": "Modified Normalized Difference Water Index",
        "formula": "(GREEN - SWIR1) / (GREEN + SWIR1)",
        "rango": [-1, 1],
        "referencia": "Xu (2006)"
    },
    "SAVI": {
        "media": "SAVI_media_2010-2023.tif",
        "std": "SAVI_std_2010-2023.tif",
        "descripcion": "Soil Adjusted Vegetation Index",
        "formula": "((NIR - RED) / (NIR + RED + L)) * (1 + L), L=0.5",
        "rango": [-1, 1],
        "referencia": "Huete (1988)"
    },
    "NBR": {
        "media": "NBR_media_2010-2023.tif",
        "std": "NBR_std_2010-2023.tif",
        "descripcion": "Normalized Burn Ratio",
        "formula": "(NIR - SWIR2) / (NIR + SWIR2)",
        "rango": [-1, 1],
        "referencia": "Key & Benson (2006)"
    },
}

# ==============================================================================
# VARIABLES BIOCLIMÁTICAS WORLDCLIM
# ==============================================================================
BIOCLIMATICAS = {
    "bio1": {
        "banda": 1,
        "nombre": "Temperatura media anual",
        "unidades": "°C × 10",
        "descripcion": "Annual Mean Temperature"
    },
    "bio4": {
        "banda": 2,
        "nombre": "Estacionalidad de temperatura",
        "unidades": "CV",
        "descripcion": "Temperature Seasonality (CV)"
    },
    "bio12": {
        "banda": 3,
        "nombre": "Precipitación anual",
        "unidades": "mm",
        "descripcion": "Annual Precipitation"
    },
    "bio13": {
        "banda": 4,
        "nombre": "Precipitación mes más húmedo",
        "unidades": "mm",
        "descripcion": "Precipitation of Wettest Month"
    },
    "bio14": {
        "banda": 5,
        "nombre": "Precipitación mes más seco",
        "unidades": "mm",
        "descripcion": "Precipitation of Driest Month"
    },
    "bio15": {
        "banda": 6,
        "nombre": "Estacionalidad de precipitación",
        "unidades": "CV",
        "descripcion": "Precipitation Seasonality (CV)"
    },
    "bio16": {
        "banda": 7,
        "nombre": "Precipitación trimestre más húmedo",
        "unidades": "mm",
        "descripcion": "Precipitation of Wettest Quarter"
    },
    "bio17": {
        "banda": 8,
        "nombre": "Precipitación trimestre más seco",
        "unidades": "mm",
        "descripcion": "Precipitation of Driest Quarter"
    },
}

# ==============================================================================
# DERIVADOS TOPOGRÁFICOS A GENERAR
# ==============================================================================
DERIVADOS_TOPOGRAFICOS = {
    "dem": {
        "archivo": "dem.tif",
        "descripcion": "Modelo Digital de Elevación",
        "unidades": "metros",
        "metodo": "Copia del original certificado",
        "referencia": "USGS SRTM / ALOS PALSAR"
    },
    "slope": {
        "archivo": "slope_degrees.tif",
        "descripcion": "Pendiente del terreno",
        "unidades": "grados (0-90)",
        "metodo": "Horn (1981) - gradiente de 3x3",
        "referencia": "Horn, B.K.P. (1981). Hill shading and the reflectance map."
    },
    "aspect": {
        "archivo": "aspect_degrees.tif",
        "descripcion": "Orientación de la pendiente",
        "unidades": "grados (0-360, Norte=0)",
        "metodo": "Horn (1981)",
        "referencia": "Horn, B.K.P. (1981). Hill shading and the reflectance map."
    },
    "curvature": {
        "archivo": "curvatura.tif",
        "descripcion": "Curvatura general del terreno",
        "unidades": "1/m",
        "metodo": "Zevenbergen & Thorne (1987)",
        "referencia": "Zevenbergen, L.W. & Thorne, C.R. (1987). Earth Surface Processes and Landforms."
    },
    "plan_curvature": {
        "archivo": "curvatura_plana.tif",
        "descripcion": "Curvatura en planta (perpendicular a pendiente)",
        "unidades": "1/m",
        "metodo": "Zevenbergen & Thorne (1987)",
        "referencia": "Zevenbergen, L.W. & Thorne, C.R. (1987)"
    },
    "profile_curvature": {
        "archivo": "curvatura_perfil.tif",
        "descripcion": "Curvatura en perfil (dirección de pendiente)",
        "unidades": "1/m",
        "metodo": "Zevenbergen & Thorne (1987)",
        "referencia": "Zevenbergen, L.W. & Thorne, C.R. (1987)"
    },
    "twi": {
        "archivo": "twi.tif",
        "descripcion": "Índice Topográfico de Humedad",
        "unidades": "adimensional",
        "metodo": "ln(a/tan(β)) - Beven & Kirkby (1979)",
        "referencia": "Beven, K.J. & Kirkby, M.J. (1979). Hydrological Sciences Bulletin."
    },
    "tri": {
        "archivo": "tri.tif",
        "descripcion": "Índice de Rugosidad del Terreno",
        "unidades": "metros",
        "metodo": "Riley et al. (1999)",
        "referencia": "Riley, S.J. et al. (1999). Intermountain Journal of Sciences."
    },
    "tpi": {
        "archivo": "tpi.tif",
        "descripcion": "Índice de Posición Topográfica",
        "unidades": "metros",
        "metodo": "Weiss (2001) - ventana 3x3",
        "referencia": "Weiss, A.D. (2001). ESRI User Conference."
    },
    "flow_accumulation": {
        "archivo": "flow_accumulation.tif",
        "descripcion": "Acumulación de flujo",
        "unidades": "número de celdas",
        "metodo": "D8 - O'Callaghan & Mark (1984)",
        "referencia": "O'Callaghan, J.F. & Mark, D.M. (1984). Computer Vision, Graphics, and Image Processing."
    },
    "flow_direction": {
        "archivo": "flow_direction.tif",
        "descripcion": "Dirección de flujo",
        "unidades": "código direccional (1-128)",
        "metodo": "D8 - O'Callaghan & Mark (1984)",
        "referencia": "O'Callaghan, J.F. & Mark, D.M. (1984)"
    },
    "dist_drenajes": {
        "archivo": "dist_drenajes.tif",
        "descripcion": "Distancia a red de drenaje",
        "unidades": "metros",
        "metodo": "Distancia euclidiana a drenajes (threshold=1000 celdas)",
        "referencia": "Calculado a partir de flow accumulation"
    },
    "hillshade": {
        "archivo": "hillshade.tif",
        "descripcion": "Sombreado del terreno",
        "unidades": "0-255",
        "metodo": "Azimut=315°, Altitud=45°",
        "referencia": "Horn, B.K.P. (1981)"
    },
}

# ==============================================================================
# PARÁMETROS DE ANÁLISIS DE MULTICOLINEALIDAD
# ==============================================================================
MULTICOLINEALIDAD = {
    # Umbral de correlación de Pearson
    # Referencia: Dormann et al. (2013). Collinearity: a review of methods to deal with it
    # and a simulation study evaluating their performance. Ecography, 36(1), 27-46.
    "umbral_correlacion": 0.80,

    # Umbral de VIF (Variance Inflation Factor)
    # Referencia: O'Brien, R.M. (2007). A caution regarding rules of thumb for VIF.
    # Quality & Quantity, 41(5), 673-690.
    "umbral_vif": 10.0,

    # Prioridad física de variables (mayor = más importante conservar)
    # Basado en Varnes (1978) y Reichenbach et al. (2018)
    "prioridad_variables": {
        # Topográficas fundamentales (gravitacionales)
        "dem": 10,
        "slope": 9,
        "aspect": 7,
        "curvature": 8,
        "plan_curvature": 7,
        "profile_curvature": 7,
        "twi": 8,
        "tri": 6,
        "tpi": 5,
        "flow_accumulation": 6,
        "dist_drenajes": 7,

        # Índices espectrales (proxies de cobertura/humedad)
        "NDVI_media": 5,
        "NDVI_std": 4,
        "EVI_media": 4,
        "EVI_std": 3,
        "NDMI_media": 5,
        "NDMI_std": 4,
        "LST_media": 3,
        "LST_std": 2,
        "NDWI_media": 4,
        "MNDWI_media": 3,
        "SAVI_media": 4,
        "NBR_media": 4,

        # Bioclimáticas (proxies de condiciones climáticas)
        "bio1": 2,  # Temperatura - proxy del gradiente altitudinal
        "bio4": 3,
        "bio12": 4,  # Precipitación anual - importante
        "bio13": 3,
        "bio14": 3,
        "bio15": 3,
        "bio16": 3,
        "bio17": 3,

        # Categóricas
        "geomorfologia": 8,
        "cobertura": 6,
        "deforestacion": 5,
    },
}

# ==============================================================================
# PARÁMETROS DE MODELAMIENTO
# ==============================================================================
MODELAMIENTO = {
    # Semillas aleatorias para reproducibilidad
    "semillas": [42, 123, 456, 789, 2025],

    # Ratio presencias:ausencias
    "ratio_muestreo": 1.0,

    # Buffer de exclusión para ausencias (metros)
    # Referencia: Steger et al. (2021). The influence of systematically rotated
    # DEM-derived predictors on physically based landslide susceptibility models.
    "buffer_exclusion": 500,

    # Parámetros Random Forest
    # Referencia: Breiman (2001). Random Forests. Machine Learning, 45(1), 5-32.
    "random_forest": {
        "n_estimators": 200,
        "max_depth": 20,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "oob_score": True,
        "n_jobs": -1,
        "random_state": 42,
    },

    # Parámetros Gradient Boosting
    # Referencia: Friedman (2001). Greedy function approximation: a gradient boosting machine.
    "gradient_boosting": {
        "n_estimators": 200,
        "max_depth": 6,
        "learning_rate": 0.1,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "subsample": 0.8,
        "random_state": 42,
    },

    # Validación LOCO (Leave-One-Canton-Out)
    # Referencia: Brenning (2005). Spatial prediction models for landslide hazards.
    "loco_cantones": [
        "ANTONIO ANTE",
        "COTACACHI",
        "IBARRA",
        "OTAVALO",
        "PIMAMPIRO",
        "URCUQUI"
    ],

    # Umbral mínimo de AUC aceptable
    "auc_minimo": 0.70,
}

# ==============================================================================
# PARÁMETROS DE CALIDAD ISO 19157
# ==============================================================================
CALIDAD_ISO = {
    # Completitud
    "completitud_minima": 0.95,  # 95% de datos válidos

    # Consistencia lógica
    "crs_requerido": "EPSG:32717",
    "resolucion_requerida": 30,
    "nodata_requerido": -9999,

    # Exactitud posicional
    "rmse_maximo": 15,  # metros (1/2 pixel)

    # Exactitud temática
    "precision_minima": 0.70,
    "recall_minimo": 0.70,
    "f1_minimo": 0.70,
}

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def crear_estructura_carpetas():
    """
    Crea la estructura de carpetas del proyecto si no existe.

    Cumple con ISO 19115-1:2014 para organización de metadatos.
    """
    carpetas_creadas = []

    for nombre, ruta in SALIDAS.items():
        if not ruta.exists():
            ruta.mkdir(parents=True, exist_ok=True)
            carpetas_creadas.append(str(ruta))

    # Crear carpeta de scripts si no existe
    if not SCRIPTS_PATH.exists():
        SCRIPTS_PATH.mkdir(parents=True, exist_ok=True)
        carpetas_creadas.append(str(SCRIPTS_PATH))

    return carpetas_creadas


def verificar_datos_entrada():
    """
    Verifica la existencia de todos los datos de entrada.

    Returns:
        dict: Estado de cada archivo (existe: True/False)
    """
    estado = {}

    for nombre, ruta in DATOS_ENTRADA.items():
        if isinstance(ruta, Path):
            estado[nombre] = {
                "ruta": str(ruta),
                "existe": ruta.exists(),
                "tipo": "directorio" if ruta.is_dir() else "archivo"
            }

    return estado


def generar_metadatos_iso19115(nombre_dataset, descripcion, fecha_creacion=None):
    """
    Genera metadatos básicos según ISO 19115-1:2014.

    Args:
        nombre_dataset: Nombre del dataset
        descripcion: Descripción del dataset
        fecha_creacion: Fecha de creación (default: ahora)

    Returns:
        dict: Metadatos estructurados
    """
    if fecha_creacion is None:
        fecha_creacion = datetime.now().isoformat()

    return {
        "MD_Metadata": {
            "fileIdentifier": f"{nombre_dataset}_{datetime.now().strftime('%Y%m%d')}",
            "language": "spa",
            "characterSet": "utf8",
            "dateStamp": fecha_creacion,
            "contact": {
                "organisationName": PROYECTO["institucion"],
                "individualName": PROYECTO["autor"],
            },
            "identificationInfo": {
                "citation": {
                    "title": nombre_dataset,
                    "date": fecha_creacion,
                },
                "abstract": descripcion,
                "spatialRepresentationType": "grid",
            },
            "referenceSystemInfo": {
                "code": PROYECTO["crs"],
                "codeSpace": "EPSG",
            },
        }
    }


def obtener_ruta_script(nombre_script):
    """
    Obtiene la ruta completa para guardar un script.

    Args:
        nombre_script: Nombre del script (ej: "SCRIPT_00A_DERIVADOS_TOPOGRAFICOS.py")

    Returns:
        Path: Ruta completa del script
    """
    return SCRIPTS_PATH / nombre_script


# ==============================================================================
# INFORMACIÓN DE EJECUCIÓN
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("CONFIGURACIÓN DEL PROYECTO")
    print("=" * 70)
    print(f"Proyecto: {PROYECTO['nombre']}")
    print(f"Autor: {PROYECTO['autor']}")
    print(f"Versión: {PROYECTO['version']}")
    print(f"CRS: {PROYECTO['crs']}")
    print(f"Resolución: {PROYECTO['resolucion_metros']} metros")
    print()

    print("Verificando estructura de carpetas...")
    carpetas = crear_estructura_carpetas()
    if carpetas:
        print(f"  Carpetas creadas: {len(carpetas)}")
        for c in carpetas:
            print(f"    - {c}")
    else:
        print("  Todas las carpetas ya existen")

    print()
    print("Verificando datos de entrada...")
    estado = verificar_datos_entrada()
    for nombre, info in estado.items():
        status = "OK" if info["existe"] else "NO ENCONTRADO"
        print(f"  [{status}] {nombre}: {info['ruta']}")

    print()
    print("=" * 70)
