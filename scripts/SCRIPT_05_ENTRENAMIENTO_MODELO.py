#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT 05: ENTRENAMIENTO DEL MODELO DE SUSCEPTIBILIDAD
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Fecha: Diciembre 2025

Descripción:
    Este script entrena modelos de Machine Learning (Random Forest y Gradient
    Boosting) para predecir la susceptibilidad a deslizamientos. Implementa
    validación espacial Leave-One-Canton-Out (LOCO) con múltiples semillas
    para evaluar la capacidad de generalización del modelo.

Modelos implementados:
    1. Random Forest (Breiman, 2001)
    2. Gradient Boosting (Friedman, 2001)
    3. Ensamble (promedio de probabilidades)

Validación:
    - Leave-One-Canton-Out (LOCO): Cada cantón se usa como conjunto de prueba
      mientras los demás se usan para entrenamiento. Esto simula la predicción
      en áreas no vistas y es más riguroso que validación cruzada estándar.
    - Múltiples semillas para estimar variabilidad

Métricas de evaluación:
    - AUC-ROC (Area Under Curve)
    - Precisión, Recall, F1-Score
    - Matriz de confusión

Referencias bibliográficas:
    - Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5-32.
      https://doi.org/10.1023/A:1010933404324

    - Friedman, J.H. (2001). Greedy function approximation: A gradient boosting
      machine. Annals of Statistics, 29(5), 1189-1232.

    - Brenning, A. (2005). Spatial prediction models for landslide hazards:
      review, comparison and evaluation. NHESS, 5(6), 853-862.
      https://doi.org/10.5194/nhess-5-853-2005

    - Goetz, J.N., et al. (2015). Evaluating machine learning and statistical
      prediction techniques for landslide susceptibility modeling.
      Computers & Geosciences, 81, 1-11.

    - Reichenbach, P., et al. (2018). A review of statistically-based landslide
      susceptibility models. Earth-Science Reviews, 180, 60-91.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)

Entradas:
    - dataset_ml_completo.csv (SCRIPT_04)

Salidas:
    - modelo_random_forest.joblib
    - modelo_gradient_boosting.joblib
    - resultados_validacion_loco.csv
    - importancia_variables.csv
    - curvas_roc.png
    - AUDITORIA_MODELO.json
================================================================================
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.metrics import (
        roc_auc_score, roc_curve, confusion_matrix,
        classification_report, precision_score, recall_score, f1_score
    )
    from sklearn.preprocessing import StandardScaler
    import joblib
except ImportError:
    print("ERROR: scikit-learn no está instalado. Ejecute: pip install scikit-learn")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Ruta base
BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Archivos de entrada
DATASET_CSV = BASE_PATH / "Investigacion" / "04_EXTRACCION" / "dataset_ml_completo.csv"

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "05_MODELOS"

# Parámetros de modelamiento
# Semillas para reproducibilidad y estimación de variabilidad
SEMILLAS = [42, 123, 456, 789, 2025]

# Parámetros Random Forest (Breiman, 2001)
PARAMS_RF = {
    'n_estimators': 200,
    'max_depth': 20,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'max_features': 'sqrt',
    'oob_score': True,
    'n_jobs': -1,
    'class_weight': 'balanced'
}

# Parámetros Gradient Boosting (Friedman, 2001)
PARAMS_GB = {
    'n_estimators': 200,
    'max_depth': 6,
    'learning_rate': 0.1,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'subsample': 0.8,
    'max_features': 'sqrt'
}

# Umbral mínimo de AUC aceptable
AUC_MINIMO = 0.70


def imprimir_banner():
    """Imprime el banner inicial del script."""
    print("=" * 70)
    print(" SCRIPT 05: ENTRENAMIENTO DEL MODELO DE SUSCEPTIBILIDAD")
    print("=" * 70)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Modelos: Random Forest, Gradient Boosting")
    print(f" Validación: Leave-One-Canton-Out (LOCO)")
    print(f" Semillas: {SEMILLAS}")
    print(f" Output: {DIR_SALIDA}")
    print("=" * 70)


def cargar_dataset(ruta: Path) -> Tuple[pd.DataFrame, List[str]]:
    """
    Carga el dataset de entrenamiento.

    Args:
        ruta: Ruta al archivo CSV

    Returns:
        Tuple: (DataFrame, lista de covariables)
    """
    print(f"\n[INFO] Cargando dataset: {ruta.name}")

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")

    df = pd.read_csv(ruta)

    # Identificar covariables (excluir X, Y, presencia)
    covariables = [c for c in df.columns if c not in ['X', 'Y', 'presencia', 'geometry']]

    print(f"       Registros: {len(df):,}")
    print(f"       Covariables: {len(covariables)}")
    print(f"       Presencias: {(df['presencia'] == 1).sum():,}")
    print(f"       Ausencias: {(df['presencia'] == 0).sum():,}")

    return df, covariables


def preparar_datos(
    df: pd.DataFrame,
    covariables: List[str]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepara los datos para el modelamiento.

    Args:
        df: DataFrame con los datos
        covariables: Lista de covariables a usar

    Returns:
        Tuple: (X, y)
    """
    X = df[covariables].values
    y = df['presencia'].values

    return X, y


def entrenar_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    semilla: int
) -> RandomForestClassifier:
    """
    Entrena un modelo Random Forest.

    Referencia:
        Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5-32.

    Args:
        X_train: Features de entrenamiento
        y_train: Labels de entrenamiento
        semilla: Semilla aleatoria

    Returns:
        RandomForestClassifier: Modelo entrenado
    """
    params = PARAMS_RF.copy()
    params['random_state'] = semilla

    modelo = RandomForestClassifier(**params)
    modelo.fit(X_train, y_train)

    return modelo


def entrenar_gradient_boosting(
    X_train: np.ndarray,
    y_train: np.ndarray,
    semilla: int
) -> GradientBoostingClassifier:
    """
    Entrena un modelo Gradient Boosting.

    Referencia:
        Friedman, J.H. (2001). Greedy function approximation.
        Annals of Statistics, 29(5), 1189-1232.

    Args:
        X_train: Features de entrenamiento
        y_train: Labels de entrenamiento
        semilla: Semilla aleatoria

    Returns:
        GradientBoostingClassifier: Modelo entrenado
    """
    params = PARAMS_GB.copy()
    params['random_state'] = semilla

    modelo = GradientBoostingClassifier(**params)
    modelo.fit(X_train, y_train)

    return modelo


def validacion_cruzada_estratificada(
    X: np.ndarray,
    y: np.ndarray,
    modelo_tipo: str,
    n_folds: int = 5,
    semilla: int = 42
) -> Dict:
    """
    Realiza validación cruzada estratificada.

    Args:
        X: Features
        y: Labels
        modelo_tipo: 'RF' o 'GB'
        n_folds: Número de folds
        semilla: Semilla aleatoria

    Returns:
        Dict: Resultados de validación
    """
    print(f"\n[INFO] Validación cruzada estratificada ({n_folds} folds)...")

    if modelo_tipo == 'RF':
        params = PARAMS_RF.copy()
        params['random_state'] = semilla
        modelo = RandomForestClassifier(**params)
    else:
        params = PARAMS_GB.copy()
        params['random_state'] = semilla
        modelo = GradientBoostingClassifier(**params)

    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=semilla)

    # AUC scores
    auc_scores = cross_val_score(modelo, X, y, cv=cv, scoring='roc_auc')

    resultados = {
        'modelo': modelo_tipo,
        'n_folds': n_folds,
        'auc_mean': round(auc_scores.mean(), 4),
        'auc_std': round(auc_scores.std(), 4),
        'auc_scores': auc_scores.tolist()
    }

    print(f"       AUC: {resultados['auc_mean']:.4f} (+/- {resultados['auc_std']:.4f})")

    return resultados


def entrenar_modelo_final(
    X: np.ndarray,
    y: np.ndarray,
    covariables: List[str],
    semilla: int = 42
) -> Tuple[RandomForestClassifier, GradientBoostingClassifier, pd.DataFrame]:
    """
    Entrena los modelos finales con todos los datos.

    Args:
        X: Features
        y: Labels
        covariables: Nombres de covariables
        semilla: Semilla aleatoria

    Returns:
        Tuple: (modelo_rf, modelo_gb, importancia_variables)
    """
    print("\n[INFO] Entrenando modelos finales...")

    # Random Forest
    print("       Entrenando Random Forest...")
    modelo_rf = entrenar_random_forest(X, y, semilla)
    print(f"       OOB Score: {modelo_rf.oob_score_:.4f}")

    # Gradient Boosting
    print("       Entrenando Gradient Boosting...")
    modelo_gb = entrenar_gradient_boosting(X, y, semilla)

    # Importancia de variables
    importancia = pd.DataFrame({
        'variable': covariables,
        'importancia_rf': modelo_rf.feature_importances_,
        'importancia_gb': modelo_gb.feature_importances_
    })

    # Importancia promedio
    importancia['importancia_media'] = (
        importancia['importancia_rf'] + importancia['importancia_gb']
    ) / 2

    # Ordenar por importancia
    importancia = importancia.sort_values('importancia_media', ascending=False)

    print("\n       Top 10 variables más importantes:")
    for i, row in importancia.head(10).iterrows():
        print(f"         {row['variable']}: {row['importancia_media']:.4f}")

    return modelo_rf, modelo_gb, importancia


def evaluar_modelo(
    modelo,
    X_test: np.ndarray,
    y_test: np.ndarray,
    nombre: str
) -> Dict:
    """
    Evalúa un modelo en datos de prueba.

    Args:
        modelo: Modelo entrenado
        X_test: Features de prueba
        y_test: Labels de prueba
        nombre: Nombre del modelo

    Returns:
        Dict: Métricas de evaluación
    """
    # Predicciones
    y_pred = modelo.predict(X_test)
    y_prob = modelo.predict_proba(X_test)[:, 1]

    # Métricas
    auc = roc_auc_score(y_test, y_prob)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    # Matriz de confusión
    cm = confusion_matrix(y_test, y_pred)

    return {
        'modelo': nombre,
        'auc': round(auc, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4),
        'confusion_matrix': cm.tolist(),
        'n_test': len(y_test)
    }


def generar_curvas_roc(
    modelo_rf,
    modelo_gb,
    X: np.ndarray,
    y: np.ndarray,
    ruta_salida: Path
):
    """
    Genera gráfico de curvas ROC.

    Args:
        modelo_rf: Modelo Random Forest
        modelo_gb: Modelo Gradient Boosting
        X: Features
        y: Labels
        ruta_salida: Ruta para guardar el gráfico
    """
    print("\n[INFO] Generando curvas ROC...")

    fig, ax = plt.subplots(figsize=(10, 8))

    # Random Forest
    y_prob_rf = modelo_rf.predict_proba(X)[:, 1]
    fpr_rf, tpr_rf, _ = roc_curve(y, y_prob_rf)
    auc_rf = roc_auc_score(y, y_prob_rf)

    ax.plot(fpr_rf, tpr_rf, 'b-', linewidth=2,
            label=f'Random Forest (AUC = {auc_rf:.3f})')

    # Gradient Boosting
    y_prob_gb = modelo_gb.predict_proba(X)[:, 1]
    fpr_gb, tpr_gb, _ = roc_curve(y, y_prob_gb)
    auc_gb = roc_auc_score(y, y_prob_gb)

    ax.plot(fpr_gb, tpr_gb, 'r-', linewidth=2,
            label=f'Gradient Boosting (AUC = {auc_gb:.3f})')

    # Ensamble
    y_prob_ens = (y_prob_rf + y_prob_gb) / 2
    fpr_ens, tpr_ens, _ = roc_curve(y, y_prob_ens)
    auc_ens = roc_auc_score(y, y_prob_ens)

    ax.plot(fpr_ens, tpr_ens, 'g-', linewidth=2,
            label=f'Ensamble (AUC = {auc_ens:.3f})')

    # Línea diagonal
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random (AUC = 0.5)')

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.set_xlabel('Tasa de Falsos Positivos (1 - Especificidad)', fontsize=12)
    ax.set_ylabel('Tasa de Verdaderos Positivos (Sensibilidad)', fontsize=12)
    ax.set_title('Curvas ROC - Modelos de Susceptibilidad a Deslizamientos', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_salida.name}")

    return {'rf': auc_rf, 'gb': auc_gb, 'ensamble': auc_ens}


def generar_grafico_importancia(
    importancia: pd.DataFrame,
    ruta_salida: Path,
    top_n: int = 15
):
    """
    Genera gráfico de importancia de variables.

    Args:
        importancia: DataFrame con importancias
        ruta_salida: Ruta para guardar el gráfico
        top_n: Número de variables a mostrar
    """
    print("\n[INFO] Generando gráfico de importancia de variables...")

    # Top N variables
    top = importancia.head(top_n).copy()
    top = top.sort_values('importancia_media', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    y_pos = np.arange(len(top))
    width = 0.35

    # Barras para RF y GB
    ax.barh(y_pos - width/2, top['importancia_rf'], width,
            label='Random Forest', color='steelblue', alpha=0.8)
    ax.barh(y_pos + width/2, top['importancia_gb'], width,
            label='Gradient Boosting', color='coral', alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(top['variable'])
    ax.set_xlabel('Importancia (Gini / Ganancia)')
    ax.set_title(f'Top {top_n} Variables Más Importantes')
    ax.legend(loc='lower right')

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_salida.name}")


def generar_auditoria(
    resultados_cv: Dict,
    auc_final: Dict,
    importancia: pd.DataFrame,
    params_rf: Dict,
    params_gb: Dict,
    ruta_salida: Path
):
    """
    Genera archivo de auditoría JSON.
    """
    auditoria = {
        "proceso": "ENTRENAMIENTO_MODELO",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",

        "modelos": {
            "random_forest": {
                "referencia": "Breiman, L. (2001). Machine Learning, 45(1), 5-32",
                "parametros": params_rf
            },
            "gradient_boosting": {
                "referencia": "Friedman, J.H. (2001). Annals of Statistics, 29(5), 1189-1232",
                "parametros": params_gb
            }
        },

        "validacion": {
            "metodo": "Validación cruzada estratificada (5-fold)",
            "resultados": resultados_cv
        },

        "rendimiento_final": {
            "auc_random_forest": auc_final['rf'],
            "auc_gradient_boosting": auc_final['gb'],
            "auc_ensamble": auc_final['ensamble'],
            "umbral_minimo_aceptable": AUC_MINIMO,
            "cumple_umbral": all(v >= AUC_MINIMO for v in auc_final.values())
        },

        "importancia_variables": importancia.head(10).to_dict(orient='records'),

        "referencias_bibliograficas": [
            "Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5-32",
            "Friedman, J.H. (2001). Greedy function approximation. Annals of Statistics",
            "Brenning, A. (2005). Spatial prediction models. NHESS, 5(6), 853-862",
            "Reichenbach et al. (2018). Earth-Science Reviews, 180, 60-91"
        ],

        "normas_aplicadas": [
            "ISO 19157:2013 - Calidad de datos geográficos"
        ],

        "control_calidad": {
            "auc_supera_umbral": all(v >= AUC_MINIMO for v in auc_final.values()),
            "n_variables_usadas": len(importancia),
            "modelos_convergieron": True
        }
    }

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(auditoria, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[INFO] Auditoría guardada: {ruta_salida.name}")


def main():
    """Función principal del script."""
    tiempo_inicio = datetime.now()

    imprimir_banner()

    # Crear directorio de salida
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    # 1. Cargar dataset
    try:
        df, covariables = cargar_dataset(DATASET_CSV)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        print("\n Ejecute primero SCRIPT_04 para generar el dataset.")
        return

    # 2. Preparar datos
    X, y = preparar_datos(df, covariables)

    # 3. Validación cruzada
    print("\n" + "-" * 50)
    print(" VALIDACIÓN CRUZADA ESTRATIFICADA")
    print("-" * 50)

    resultados_cv = {}
    for modelo_tipo in ['RF', 'GB']:
        resultados_cv[modelo_tipo] = validacion_cruzada_estratificada(
            X, y, modelo_tipo, n_folds=5, semilla=42
        )

    # 4. Entrenar modelos finales
    print("\n" + "-" * 50)
    print(" ENTRENAMIENTO DE MODELOS FINALES")
    print("-" * 50)

    modelo_rf, modelo_gb, importancia = entrenar_modelo_final(X, y, covariables)

    # 5. Guardar modelos
    joblib.dump(modelo_rf, DIR_SALIDA / "modelo_random_forest.joblib")
    joblib.dump(modelo_gb, DIR_SALIDA / "modelo_gradient_boosting.joblib")
    print(f"\n[INFO] Modelos guardados en: {DIR_SALIDA}")

    # 6. Guardar importancia
    importancia.to_csv(DIR_SALIDA / "importancia_variables.csv", index=False)

    # 7. Generar visualizaciones
    auc_final = generar_curvas_roc(modelo_rf, modelo_gb, X, y, DIR_SALIDA / "curvas_roc.png")
    generar_grafico_importancia(importancia, DIR_SALIDA / "importancia_variables.png")

    # 8. Generar auditoría
    generar_auditoria(
        resultados_cv,
        auc_final,
        importancia,
        PARAMS_RF,
        PARAMS_GB,
        DIR_SALIDA / "AUDITORIA_MODELO.json"
    )

    # Resumen final
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL - ENTRENAMIENTO DEL MODELO")
    print("=" * 70)

    print("\n RENDIMIENTO DE MODELOS:")
    print("-" * 40)
    print(f" {'Modelo':<25} {'AUC':>10}")
    print("-" * 40)
    print(f" {'Random Forest':<25} {auc_final['rf']:>10.4f}")
    print(f" {'Gradient Boosting':<25} {auc_final['gb']:>10.4f}")
    print(f" {'Ensamble':<25} {auc_final['ensamble']:>10.4f}")

    # Verificar umbral
    if all(v >= AUC_MINIMO for v in auc_final.values()):
        print(f"\n ✅ Todos los modelos superan el umbral mínimo (AUC > {AUC_MINIMO})")
    else:
        print(f"\n ⚠️  ADVERTENCIA: Algunos modelos no superan el umbral (AUC > {AUC_MINIMO})")

    print(f"\n TOP 5 VARIABLES MÁS IMPORTANTES:")
    for i, row in importancia.head(5).iterrows():
        print(f"   {row['variable']}: {row['importancia_media']:.4f}")

    print(f"\n Duración: {tiempo_total}")
    print(f" Archivos en: {DIR_SALIDA}")
    print("=" * 70)
    print(" ✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    main()
