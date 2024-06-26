import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QWidget, QLabel, QFileDialog, QComboBox, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
import geohash2
import numpy as np
import seaborn as sns
from PyQt5.QtWidgets import QProgressBar
import os

def preprocess_dataframe_celdas(df, poligono=None, operador=None):
    df = df.rename(columns={'latitude': 'Latitud', 'longitude': 'Longitud'})
    
    if poligono is not None:
        with open(poligono, "r") as f:
            contenido_wkt = f.read()
        poligono_shape = Polygon([(float(x), float(y)) for x, y in [pair.split() for pair in contenido_wkt[10:-2].split(", ")]])
        
        df['Poligono'] = df.apply(lambda row: poligono_shape.contains(Point(row['Longitud'], row['Latitud'])), axis=1)
        df = df[df['Poligono']]
        df.drop(columns=['Poligono'], inplace=True)

    if operador is not None:
        if operador == 'Movistar':
            df = df[df['cell_id_non_encrypted'].str.split('-').str[1] == '7']
        if operador == 'Orange':
            df = df[df['cell_id_non_encrypted'].str.split('-').str[1] == '3']
        if operador == 'Vodafone':
            df = df[df['cell_id_non_encrypted'].str.split('-').str[1] == '1']

    df['CGI'] = df['cell_id_non_encrypted'].str.split('-').apply(lambda x: int(x[2]) * 256 + int(x[3]))
    
    return df

def preprocess_dataframe_drive_test(df, df_celdas, poligono=None):
    df.rename(columns={'Latitud': 'Longitud', 'Longitud': 'Latitud'}, inplace=True)
    
    if poligono is not None:
        with open(poligono, "r") as f:
            contenido_wkt = f.read()
        poligono_shape = Polygon([(float(x), float(y)) for x, y in [pair.split() for pair in contenido_wkt[10:-2].split(", ")]])
        
        df['Poligono'] = df.apply(lambda row: poligono_shape.contains(Point(row['Longitud'], row['Latitud'])), axis=1)
        df = df[df['Poligono']]
        df.drop(columns=['Poligono'], inplace=True)
        
    for index, row in df.iterrows():
        coordenadas_conexion = (row['Latitud'], row['Longitud'])
        celdas_filtradas = df_celdas[(df_celdas['pci'] == row['PCI']) & (df_celdas['earfcn'] == row['EARFCN'])]
        distancias = []
        for _, celda in celdas_filtradas.iterrows():
            coordenadas_celda = (celda['Latitud'], celda['Longitud'])
            distancia = geodesic(coordenadas_conexion, coordenadas_celda).meters
            distancias.append((distancia, celda['CGI']))
        if distancias:
            distancia_minima, eNodeB = min(distancias, key=lambda x: x[0])
            df.at[index, 'CGI'] = eNodeB
        else:
            df.at[index, 'CGI'] = None
            
    df = df.dropna(subset=['CGI'])
    df['CGI'] = df['CGI'].astype(int)
    
    df['BAND_FREQ'] = None
    for index, row in df.iterrows():
        cgi = row['CGI']
        matching_cell = df_celdas[df_celdas['CGI'] == cgi]
        if not matching_cell.empty:
            band_freq = matching_cell.iloc[0]['cell_frequency_band']
            df.at[index, 'BAND_FREQ'] = band_freq
    
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Franja_horaria'] = pd.cut(df['Fecha'].dt.hour, bins=range(0, 25, 1), labels=range(1, 25), right=False)
    
    df['Dia'] = df['Fecha'].dt.dayofweek
    df = df[~df['Fecha'].dt.dayofweek.isin([5, 6])]
    
    df['Geohash'] = df.apply(lambda row: geohash2.encode(row['Latitud'], row['Longitud'], precision=8), axis=1)
            
    return df

def preprocess_dataframe_crowdsourced(df, df_drive_test, poligono=None, operador=None):
    df['CGI'] = df['cell_id_non_encrypted'].str.split('-').apply(lambda x: int(x[2]) * 256 + int(x[3]))
    df.rename(columns={'carrier':'Operador','hour': 'Hora', 'gps_latitude':'Latitud','gps_longitude':'Longitud','cell_frequency_band':'BAND_FREQ','timestamp_local':'Fecha','rsrp':'RSRP','rsrq':'RSRQ'}, inplace=True)
    
    if poligono is not None:
        with open(poligono, "r") as f:
            contenido_wkt = f.read()
        poligono_shape = Polygon([(float(x), float(y)) for x, y in [pair.split() for pair in contenido_wkt[10:-2].split(", ")]])
        
        df['Poligono'] = df.apply(lambda row: poligono_shape.contains(Point(row['Longitud'], row['Latitud'])), axis=1)
        df = df[df['Poligono']]
        df.drop(columns=['Poligono'], inplace=True)
    df = df[df['location_status'] == 'in_vehicle']
    
    if operador is not None:
        if operador == 'Movistar':
            df = df[df['Operador'] == 'MOVISTAR']
        if operador == 'Orange':
            df = df[df['Operador'] == 'ORANGE']
        if operador == 'Vodafone':
            df = df[df['Operador'] == 'VODAFONE']
    
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Franja_horaria'] = pd.cut(df['Fecha'].dt.hour, bins=range(0, 25, 1), labels=range(1, 25), right=False)
    
    franjas_únicas = df_drive_test['Franja_horaria'].unique()
    franjas_únicas = list(franjas_únicas)
    df = df[df['Franja_horaria'].isin(franjas_únicas)]
    
    df['Dia'] = df['Fecha'].dt.dayofweek
    df = df[~df['Fecha'].dt.dayofweek.isin([5, 6])]
    
    df['Geohash'] = df.apply(lambda row: geohash2.encode(row['Latitud'], row['Longitud'], precision=8), axis=1)
    
    return df

def process_dataframe(df):
    columna_geohash = 'Geohash'
    valores_unicos = df[columna_geohash].drop_duplicates()
    geohash_df = pd.DataFrame({'Geohash': valores_unicos})

    geohash_df['geometry'] = geohash_df['Geohash'].apply(lambda x: geohash2.decode_exactly(x)[:2])
    geohash_df[['Latitud', 'Longitud']] = geohash_df['geometry'].apply(lambda x: pd.Series([str(x[0]), str(x[1])]))
    geohash_df.drop('geometry', axis=1, inplace=True)

    geohash_df['BAND_FREQ'] = None
    band_freq_unique = df.groupby('Geohash')['BAND_FREQ'].unique()
    for index, row in geohash_df.iterrows():
        geohash = row['Geohash']
        if geohash in band_freq_unique:
            geohash_df.at[index, 'BAND_FREQ'] = band_freq_unique[geohash].tolist()
    new_rows = []
    
    for index, row in geohash_df.iterrows():
        geohash = row['Geohash']
        latitud = row['Latitud']
        longitud = row['Longitud']
        band_freq_list = row['BAND_FREQ']
        for band_freq in band_freq_list:
            new_rows.append({'Geohash': geohash, 'Latitud': latitud, 'Longitud': longitud, 'BAND_FREQ': band_freq})
    geohash_df = pd.DataFrame(new_rows)
    
    ci_unicos = df.groupby(['Geohash', 'BAND_FREQ'])['CGI'].apply(lambda x: list(set(x)))
    geohash_df['CGI'] = None
    for index, row in geohash_df.iterrows():
        geohash = row['Geohash']
        band_freq = row['BAND_FREQ']
        if (geohash, band_freq) in ci_unicos.index:
            cell_ids = ci_unicos.loc[(geohash, band_freq)]
            geohash_df.at[index, 'CGI'] = cell_ids
            
    new_rows = []
    for index, row in geohash_df.iterrows():
        geohash = row['Geohash']
        latitud = row['Latitud']
        longitud = row['Longitud']
        band_freq = row['BAND_FREQ']
        cgi_list = row['CGI']
        for cgi in cgi_list:
            new_rows.append({'Geohash': geohash, 'Latitud': latitud, 'Longitud': longitud,'BAND_FREQ': band_freq,'CGI': cgi})
    geohash_df = pd.DataFrame(new_rows)

    return geohash_df

def process_dataframe_rsrp_rsrq(df_copia, df_valores):
    rsrp_df = df_copia.copy()
    rsrq_df = df_copia.copy()

    rsrp_df['RSRP_media'] = None
    rsrp_df['eventos'] = None
    for index, row in rsrp_df.iterrows():
        geohash = row['Geohash']
        band_freq = row['BAND_FREQ']
        cgi = row['CGI']
        match_rsrp = df_valores[(df_valores['Geohash'] == geohash) & (df_valores['BAND_FREQ'] == band_freq) & (df_valores['CGI'] == cgi)]
        if not match_rsrp.empty:
            rsrp_df.at[index, 'RSRP_media'] = np.mean(match_rsrp['RSRP'])
            rsrp_df.at[index, 'eventos'] = len(match_rsrp)

    rsrq_df['Franja_horaria'] = None
    for index, row in rsrq_df.iterrows():
        geohash = row['Geohash']
        band_freq = row['BAND_FREQ']
        cgi = row['CGI']
        match_franja = df_valores[(df_valores['Geohash'] == geohash) & (df_valores['BAND_FREQ'] == band_freq) & (df_valores['CGI'] == cgi)]
        if not match_franja.empty:
            franjas = list(set(match_franja['Franja_horaria']))
            rsrq_df.at[index, 'Franja_horaria'] = franjas

    rsrq_df['Franja_horaria'] = rsrq_df['Franja_horaria'].apply(lambda x: [x] if isinstance(x, str) else x)
    rsrq_df = rsrq_df.explode('Franja_horaria')

    rsrq_df['RSRQ_media'] = None
    rsrq_df['eventos'] = None
    for index, row in rsrq_df.iterrows():
        geohash = row['Geohash']
        band_freq = row['BAND_FREQ']
        cgi = row['CGI']
        franja = row['Franja_horaria']
        match_rsrq = df_valores[(df_valores['Geohash'] == geohash) & (df_valores['BAND_FREQ'] == band_freq) & (df_valores['CGI'] == cgi) & (df_valores['Franja_horaria'] == franja)]
        if not match_rsrq.empty:
            rsrq_df.at[index, 'RSRQ_media'] = np.mean(match_rsrq['RSRQ'])
            rsrq_df.at[index, 'eventos'] = len(match_rsrq)

    rsrp_df = rsrp_df[['Geohash', 'Latitud', 'Longitud', 'BAND_FREQ', 'CGI', 'RSRP_media', 'eventos']]
    rsrq_df = rsrq_df[['Geohash', 'Latitud', 'Longitud', 'BAND_FREQ', 'CGI', 'Franja_horaria', 'RSRQ_media', 'eventos']]

    return rsrp_df, rsrq_df

def filtrar_coincidencias(df1, df2, df3, df4, columns_to_match1=None, columns_to_match2=None):
    columns_to_match1 = ['Geohash', 'BAND_FREQ', 'CGI']
    columns_to_match2 = ['Geohash', 'BAND_FREQ', 'CGI', 'Franja_horaria']
    def filtrar(df_a, df_b, cols):
        filtered_a = pd.DataFrame(columns=df_a.columns)
        filtered_b = pd.DataFrame(columns=df_b.columns)
        
        for _, row in df_a.iterrows():
            coincidencia = df_b
            for col in cols:
                coincidencia = coincidencia[coincidencia[col] == row[col]]
            if not coincidencia.empty:
                filtered_a = pd.concat([filtered_a, row.to_frame().T])
        
        for _, row in df_b.iterrows():
            coincidencia = df_a
            for col in cols:
                coincidencia = coincidencia[coincidencia[col] == row[col]]
            if not coincidencia.empty:
                filtered_b = pd.concat([filtered_b, row.to_frame().T])
        
        filtered_a.reset_index(drop=True, inplace=True)
        filtered_b.reset_index(drop=True, inplace=True)
        
        return filtered_a, filtered_b
    
    filtered_df1, filtered_df2 = filtrar(df1, df2, columns_to_match1)
    filtered_df3, filtered_df4 = filtrar(df3, df4, columns_to_match2)
    
    return filtered_df1, filtered_df2, filtered_df3, filtered_df4

palette = [(0.12156862745098039, 0.4666666666666667, 0.7058823529411765), (1.0, 0.4980392156862745, 0.054901960784313725)]

def plot_rsrp(rsrp_drive_test, rsrp_crowdsourced, operador=None):
    plt.figure(figsize=(9, 5))
    
    sns.histplot(data=rsrp_drive_test['RSRP_media'], label='Drive Test', color=palette[0], kde=True, binrange=(-140, -43))
    sns.histplot(data=rsrp_crowdsourced['RSRP_media'], label='Crowdsourced', color=palette[1], kde=True, binrange=(-140, -43))

    title = 'Distribución de RSRP'
    if operador:
        title += f' - Operador: {operador}'

    plt.title(title)
    plt.ylabel('Frecuencia')
    plt.xlabel('RSRP')
    
    plt.legend()
    plt.show()

def plot_rsrq(rsrq_drive_test, rsrq_crowdsourced):
    plt.figure(figsize=(9, 5))
    
    sns.histplot(data=rsrq_drive_test['RSRQ_media'], label='Drive Test', color=palette[0], kde=True, binwidth = 1)
    sns.histplot(data=rsrq_crowdsourced['RSRQ_media'], label='Crowdsourced', color=palette[1], kde=True, binwidth = 1)
    
    plt.title('Distribución de RSRQ')
    plt.ylabel('Frecuencia')
    plt.xlabel('RSRQ')
    
    plt.legend()
    plt.show()

class PlotWindow(QWidget):
    def __init__(self, rsrp_drive_test, rsrp_crowdsourced, rsrq_drive_test, rsrq_crowdsourced, operador=None):
        super().__init__()
        self.operador = operador
        self.setWindowTitle("Generar Histogramas")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label_title = QLabel("Resultados")
        self.label_title.setStyleSheet("font-size: 23px; font-weight: bold;")
        self.layout.addWidget(self.label_title)

        self.label_title = QLabel("Gráficos RSRP")
        self.label_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.layout.addWidget(self.label_title)

        self.btn_plot_rsrp = QPushButton("Generar Histograma de RSRP")
        self.layout.addWidget(self.btn_plot_rsrp)
        self.btn_plot_rsrp.clicked.connect(lambda: self.plot_rsrp(rsrp_drive_test, rsrp_crowdsourced, self.operador))

        self.btn_plot_rsrp_band_freq = QPushButton("Generar Histogramas de RSRP por Banda de Frecuencia")
        self.layout.addWidget(self.btn_plot_rsrp_band_freq)
        self.btn_plot_rsrp_band_freq.clicked.connect(lambda: self.plot_rsrp_band_freq(rsrp_drive_test, rsrp_crowdsourced, self.operador))

        self.label_title = QLabel("Gráficos RSRQ")
        self.label_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.layout.addWidget(self.label_title)

        self.btn_plot_rsrq = QPushButton("Generar Histograma de RSRQ")
        self.layout.addWidget(self.btn_plot_rsrq)
        self.btn_plot_rsrq.clicked.connect(lambda: self.plot_rsrq(rsrq_drive_test, rsrq_crowdsourced,self.operador))

        self.btn_plot_rsrq_band_freq = QPushButton("Generar Histogramas de RSRQ por Banda de Frecuencia")
        self.layout.addWidget(self.btn_plot_rsrq_band_freq)
        self.btn_plot_rsrq_band_freq.clicked.connect(lambda: self.plot_rsrq_band_freq(rsrq_drive_test, rsrq_crowdsourced,self.operador))

        self.btn_plot_rsrq_boxplot_by_hour = QPushButton("Generar BoxPlot de RSRQ por Hora")
        self.layout.addWidget(self.btn_plot_rsrq_boxplot_by_hour)
        self.btn_plot_rsrq_boxplot_by_hour.clicked.connect(lambda: self.plot_rsrq_boxplot_by_hour(rsrq_drive_test, rsrq_crowdsourced,self.operador))

        self.btn_plot_rsrq_std_by_hour = QPushButton("Generar Plot de la desviación RSRQ por Hora")
        self.layout.addWidget(self.btn_plot_rsrq_std_by_hour)
        self.btn_plot_rsrq_std_by_hour.clicked.connect(lambda: self.plot_rsrq_std_by_hour(rsrq_drive_test, rsrq_crowdsourced,self.operador))

        self.label_title = QLabel("Exportar DataFrames")
        self.label_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.layout.addWidget(self.label_title)

        self.btn_export_rsrp = QPushButton("Exportar DataFrames RSRP")
        self.layout.addWidget(self.btn_export_rsrp)
        self.btn_export_rsrp.clicked.connect(lambda: self.export_dataframe(rsrp_drive_test, rsrp_crowdsourced, 'RSRP'))

        self.btn_export_rsrq = QPushButton("Exportar DataFrames RSRQ")
        self.layout.addWidget(self.btn_export_rsrq)
        self.btn_export_rsrq.clicked.connect(lambda: self.export_dataframe(rsrq_drive_test, rsrq_crowdsourced, 'RSRQ'))
    
        self.setStyleSheet("""
            PlotWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #f6a04f;
                border: none;
                color: white;
                padding: 12px;
                text-align: center;
                margin: 10px;
                cursor: pointer;
                min-width: 200px;
                box-shadow: 0 4px #999;
                font-size: 16px;
                font-weight: bold;
                border-radius: 7px;
            }
            QPushButton:hover {
                background-color: #cc7b38;
            }
            QPushButton:pressed {
                background-color: #cc7b38;
                box-shadow: 0 2px #666;
                transform: translateY(2px);
            }
            QLabel {
                font-size: 16px;
                margin-top: 10px;
                color: #333;
            }
        """)

    def plot_rsrp(self, rsrp_drive_test, rsrp_crowdsourced, operador=None):
        plt.figure(figsize=(9, 5))
        sns.histplot(data=rsrp_drive_test['RSRP_media'], label='Drive Test', color='blue', kde=True, binrange=(-140, -43))
        sns.histplot(data=rsrp_crowdsourced['RSRP_media'], label='Crowdsourced', color='red', kde=True, binrange=(-140, -43))
        title = 'Distribución de RSRP'
        if operador == 'Movistar':
            title += ' - Operador 1'
        elif operador == 'Vodafone':
            title += ' - Operador 2'
        elif operador == 'Orange':
            title += ' - Operador 3'
        plt.title(title)
        plt.ylabel('Frecuencia')
        plt.xlabel('RSRP')
        plt.legend()
        plt.show()

    def plot_rsrq(self, rsrq_drive_test, rsrq_crowdsourced, operador=None):
        plt.figure(figsize=(9, 5))
        sns.histplot(data=rsrq_drive_test['RSRQ_media'], label='Drive Test', color='blue', kde=True, binwidth=1)
        sns.histplot(data=rsrq_crowdsourced['RSRQ_media'], label='Crowdsourced', color='red', kde=True, binwidth=1)
        title = 'Distribución de RSRQ'
        if operador == 'Movistar':
            title += ' - Operador 1'
        elif operador == 'Vodafone':
            title += ' - Operador 2'
        elif operador == 'Orange':
            title += ' - Operador 3'
        plt.title(title)
        plt.ylabel('Frecuencia')
        plt.xlabel('RSRQ')
        plt.legend()
        plt.show()
    
    def plot_rsrp_band_freq(self, rsrp_drive_test, rsrp_crowdsourced, operador=None):

        bands_drive_test = rsrp_drive_test['BAND_FREQ'].unique()
        bands_crowdsourced = rsrp_crowdsourced['BAND_FREQ'].unique()

        for band in set(bands_drive_test).union(bands_crowdsourced):
            fig, ax = plt.subplots(figsize=(9, 5))
            
            if band in bands_drive_test:
                data_drive_test = rsrp_drive_test[rsrp_drive_test['BAND_FREQ'] == band]['RSRP_media']
                sns.histplot(data=data_drive_test, label='Drive Test', color='blue', kde=True, binrange=(-140, -43), ax=ax)
            
            if band in bands_crowdsourced:
                data_crowdsourced = rsrp_crowdsourced[rsrp_crowdsourced['BAND_FREQ'] == band]['RSRP_media']
                sns.histplot(data=data_crowdsourced, label='Crowdsourced', color='red', kde=True, binrange=(-140, -43), ax=ax)
            
            title = f'Distribución de RSRP ({band})'
            if operador == 'Movistar':
                title += ' - Operador 1'
            elif operador == 'Vodafone':
                title += ' - Operador 2'
            elif operador == 'Orange':
                title += ' - Operador 3'
            plt.title(title)
            plt.xlabel('RSRP')
            plt.ylabel('Frecuencia')
            plt.legend()
            
            plt.show()

    def plot_rsrq_band_freq(self, rsrq_drive_test, rsrq_crowdsourced, operador=None):
        try:

            bands_drive_test = rsrq_drive_test['BAND_FREQ'].unique()
            bands_crowdsourced = rsrq_crowdsourced['BAND_FREQ'].unique()
            
            for band in set(bands_drive_test).union(bands_crowdsourced):
                fig, ax = plt.subplots(figsize=(9, 5))
                
                if band in bands_drive_test:
                    data_drive_test = rsrq_drive_test[rsrq_drive_test['BAND_FREQ'] == band]['RSRQ_media']
                    if not data_drive_test.empty and len(data_drive_test) > 1:
                        sns.histplot(data=data_drive_test, label='Drive Test', color='blue', kde=True, binwidth=1, ax=ax)
                    else:
                        print(f"No hay suficientes datos de Drive Test para la banda {band}")
                        
                if band in bands_crowdsourced:
                    data_crowdsourced = rsrq_crowdsourced[rsrq_crowdsourced['BAND_FREQ'] == band]['RSRQ_media']
                    if not data_crowdsourced.empty and len(data_crowdsourced) > 1:
                        sns.histplot(data=data_crowdsourced, label='Crowdsourced', color='red', kde=True, binwidth=1, ax=ax)
                    else:
                        print(f"No hay suficientes datos de Crowdsourced para la banda {band}")
                
                title = f'Distribución de RSRQ ({band})'
                if operador == 'Movistar':
                    title += ' - Operador 1'
                elif operador == 'Vodafone':
                    title += ' - Operador 2'
                elif operador == 'Orange':
                    title += ' - Operador 3'
                plt.title(title)
                plt.xlabel('RSRQ')
                plt.ylabel('Frecuencia')
                plt.legend()
                
                plt.show()
        
        except Exception as e:
            print(f"Se ha producido un error: {e}")

    def plot_rsrq_boxplot_by_hour(self, rsrq_drive_test, rsrq_crowdsourced, operador=None):

        rsrq_drive_test['Tipo'] = 'Drive Test'
        rsrq_crowdsourced['Tipo'] = 'Crowdsourced'

        combined_df = pd.concat([rsrq_drive_test, rsrq_crowdsourced], ignore_index=True)

        plt.figure(figsize=(12, 6))
        sns.boxplot(x='Franja_horaria', y='RSRQ_media', hue='Tipo', data=combined_df, palette=palette)
        title = 'Distribución de RSRQ por Franja Horaria'
        if operador == 'Movistar':
            title += ' - Operador 1'
        elif operador == 'Vodafone':
            title += ' - Operador 2'
        elif operador == 'Orange':
            title += ' - Operador 3'
        plt.title(title)
        plt.xlabel('Franja Horaria')
        plt.ylabel('RSRQ')
        plt.legend(title='Tipo')
        plt.show()

    def plot_rsrq_std_by_hour(self, rsrq_drive_test, rsrq_crowdsourced, operador=None):

        rsrq_drive_test['Tipo'] = 'Drive Test'
        rsrq_crowdsourced['Tipo'] = 'Crowdsourced'

        combined_df = pd.concat([rsrq_drive_test, rsrq_crowdsourced], ignore_index=True)

        std_by_hour = combined_df.groupby(['Franja_horaria', 'Tipo'])['RSRQ_media'].std().reset_index()

        plt.figure(figsize=(12, 6))
        sns.barplot(x='Franja_horaria', y='RSRQ_media', hue='Tipo', data=std_by_hour, palette={'Drive Test': palette[0], 'Crowdsourced': palette[1]})
        title = 'Desviación Estándar de RSRQ por Franja Horaria'
        if operador == 'Movistar':
            title += ' - Operador 1'
        elif operador == 'Vodafone':
            title += ' - Operador 2'
        elif operador == 'Orange':
            title += ' - Operador 3'
        plt.title(title)
        plt.xlabel('Franja Horaria')
        plt.ylabel('Desviación Estándar de RSRQ')
        plt.xticks(rotation=45)
        plt.legend(title='Tipo')
        plt.show()
    
    def export_dataframe(self, df_drive_test, df_crowdsourced, tipo):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar DataFrame", "", "Archivos CSV (*.csv)", options=options)
        if filename:
            df_drive_test.to_csv(f"{filename}_drive_test_{tipo}.csv", index=False)
            df_crowdsourced.to_csv(f"{filename}_crowdsourced_{tipo}.csv", index=False)
            QMessageBox.information(self, "Información", f"DataFrames {tipo} exportados correctamente.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Herramienta Comparación Medidas Ad-Hoc v Colaborativas")
        self.setGeometry(100, 100, 1000, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QGridLayout()
        self.central_widget.setLayout(self.layout)

        self.loaded_files = {'celdas': [], 'drive_test': [], 'crowdsourced': [], 'poligono': []}

        self.label_title = QLabel("Herramienta Comparación Medidas Ad-Hoc v Colaborativas")
        self.label_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.label_title, 0, 0, 1, 2, alignment=Qt.AlignCenter)

        self.layout.setVerticalSpacing(20)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 12px;
                text-align: center;
                margin: 10px;
                cursor: pointer;
                min-width: 200px;
                box-shadow: 0 4px #999;
                font-size: 16px;
                font-weight: bold;
                border-radius: 7px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #45a049;
                box-shadow: 0 2px #666;
                transform: translateY(2px);
            }
            QLabel {
                font-size: 16px;
                margin-top: 10px;
                color: #333;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #4CAF50;
                border-radius: 10px;
                font-size: 16px;
                padding: 5px;
                margin-top: 10px;
            }
            QProgressBar {
                border: 1px solid #f6a04f;
                border-radius: 7px;
                background-color: #f0f0f0;
                text-align: center;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #f6a04f;
                width: 20px;
                margin: 1px;
                border-radius: 7px;
            }
            QPushButton#btnProcesar {
                background-color: #f6a04f;
                border-radius: 7px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#btnProcesar:hover {
                background-color: #cc7b38;
            }
            QPushButton#btnProcesar:pressed {
                background-color: #cc7b38;
                box-shadow: 0 2px #666;
                transform: translateY(2px);
            }
            QPushButton#btnEliminar {
                background-color: #FF0000;
                border-radius: 7px;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#btnEliminar:hover {
                background-color: #B22222;
            }
            QPushButton#btnEliminar:pressed {
                background-color: #B22222;
                box-shadow: 0 2px #666;
                transform: translateY(2px);
            }
        
        """)

        self.btn_cargar_celdas = QPushButton("Cargar Archivo de Celdas")
        self.layout.addWidget(self.btn_cargar_celdas, 1, 0)
        self.btn_cargar_celdas.clicked.connect(self.cargar_archivo_celdas)
        self.label_celdas = QLabel("Seleccione el archivo CSV que contiene las celdas.")
        self.label_celdas.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.label_celdas, 1, 1)
        self.celdas_container = QVBoxLayout()
        self.layout.addLayout(self.celdas_container, 2, 0, 1, 2)

        self.btn_cargar_drive_test = QPushButton("Cargar Archivo de Drive Test")
        self.layout.addWidget(self.btn_cargar_drive_test, 3, 0)
        self.btn_cargar_drive_test.clicked.connect(self.cargar_archivo_drive_test)
        self.label_drive_test = QLabel("Seleccione el archivo CSV que contiene los datos de Drive Test.")
        self.label_drive_test.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.label_drive_test, 3, 1)
        self.drive_test_container = QVBoxLayout()
        self.layout.addLayout(self.drive_test_container, 4, 0, 1, 2)

        self.btn_cargar_crowdsourced = QPushButton("Cargar Archivo Crowdsourced")
        self.layout.addWidget(self.btn_cargar_crowdsourced, 5, 0)
        self.btn_cargar_crowdsourced.clicked.connect(self.cargar_archivo_crowdsourced)
        self.label_crowdsourced = QLabel("Seleccione el archivo CSV que contiene los datos Crowdsourced.")
        self.label_crowdsourced.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.label_crowdsourced, 5, 1)
        self.crowdsourced_container = QVBoxLayout()
        self.layout.addLayout(self.crowdsourced_container, 6, 0, 1, 2)

        self.label_poligono = QLabel("Seleccione el archivo WKT que contiene el polígono:")
        self.label_poligono.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.label_poligono, 7, 1)
        self.btn_poligono = QPushButton("Cargar Polígono")
        self.layout.addWidget(self.btn_poligono, 7, 0)
        self.btn_poligono.clicked.connect(self.cargar_poligono)
        self.poligono_container = QVBoxLayout()
        self.layout.addLayout(self.poligono_container, 8, 0, 1, 2)

        self.label_operador = QLabel("Seleccione operador:")
        self.layout.addWidget(self.label_operador, 9, 0)
        self.combo_operador = QComboBox()
        self.combo_operador.addItem(None)
        self.combo_operador.addItem("Movistar")
        self.combo_operador.addItem("Orange")
        self.combo_operador.addItem("Vodafone")
        self.layout.addWidget(self.combo_operador, 9, 1)
        self.operador = None

        self.btn_procesar = QPushButton("Procesar Datos")
        self.btn_procesar.setObjectName("btnProcesar")
        self.layout.addWidget(self.btn_procesar, 10, 0, 1, 2)
        self.btn_procesar.clicked.connect(self.preprocesar_datos)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress_bar, 11, 0, 1, 2)

        self.df_celdas = None
        self.df_drive_test = None
        self.df_crowdsourced = None

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def cargar_archivo_celdas(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Abrir archivo de celdas', '', 'Archivos CSV (*.csv)')
        if filename:
            self.df_celdas = pd.read_csv(filename)
            if len(self.df_celdas.columns) < 2:
                self.df_celdas = pd.read_csv(filename, delimiter=';', decimal=',')
                QMessageBox.information(self, "Información", "Archivo de celdas cargado correctamente con delimitador ';' y separador decimal ','.")
            else:
                QMessageBox.information(self, "Información", "Archivo de celdas cargado correctamente.")
            self.mostrar_archivo_cargado(filename, 'celdas', self.celdas_container)

    def cargar_archivo_drive_test(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Abrir archivo de Drive Test', '', 'Archivos CSV (*.csv)')
        if filename:
            self.df_drive_test = pd.read_csv(filename)
            if len(self.df_drive_test.columns) < 2:
                self.df_drive_test = pd.read_csv(filename, delimiter=';', decimal=',')
                QMessageBox.information(self, "Información", "Archivo de Drive Test cargado correctamente con delimitador ';' y separador decimal ','.")
            else:
                QMessageBox.information(self, "Información", "Archivo de Drive Test cargado correctamente.")
            self.mostrar_archivo_cargado(filename, 'drive_test', self.drive_test_container)

    def cargar_archivo_crowdsourced(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Abrir archivo Crowdsourced', '', 'Archivos CSV (*.csv)')
        if filename:
            self.df_crowdsourced = pd.read_csv(filename)
            if len(self.df_crowdsourced.columns) < 2:
                self.df_crowdsourced = pd.read_csv(filename, delimiter=';', decimal=',')
                QMessageBox.information(self, "Información", "Archivo Crowdsourced cargado correctamente con delimitador ';' y separador decimal ','.")
            else:
                QMessageBox.information(self, "Información", "Archivo Crowdsourced cargado correctamente.")
            self.mostrar_archivo_cargado(filename, 'crowdsourced', self.crowdsourced_container)

    def cargar_poligono(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setNameFilter("Todos los archivos (*.*)")
        if file_dialog.exec_():
            filenames = file_dialog.selectedFiles()
            if filenames and filenames[0].endswith('.wkt'):
                self.poligono = filenames[0]
                QMessageBox.information(self, "Información", "Archivo de polígono cargado correctamente.")
                self.mostrar_archivo_cargado(filenames[0], 'poligono', self.poligono_container)
            else:
                QMessageBox.critical(self, "Error", "Por favor, seleccione un archivo de polígono con extensión .wkt.")

    
    def mostrar_archivo_cargado(self, filename, file_type, container):
        layout = QHBoxLayout()
        label = QLabel(f"Archivo cargado: {os.path.basename(filename)}")
        button = QPushButton("Eliminar")
        button.setObjectName("btnEliminar")
        
        button.clicked.connect(lambda _, filename=filename, container=container: self.eliminar_archivo_cargado(layout, file_type, container))
        
        layout.addWidget(label)
        layout.addWidget(button)
        container.addLayout(layout)

    def eliminar_archivo_cargado(self, layout, file_type, container):
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if file_type == 'celdas':
            self.df_celdas = None
        elif file_type == 'drive_test':
            self.df_drive_test = None
        elif file_type == 'crowdsourced':
            self.df_crowdsourced = None
        elif file_type == 'poligono':
            self.poligono = None

    def preprocesar_datos(self):
        if self.df_celdas is None or self.df_drive_test is None or self.df_crowdsourced is None:
            QMessageBox.critical(self, "Error", "Por favor, cargue todos los archivos necesarios.")
            return

        self.operador = self.combo_operador.currentText()

        df_celdas = preprocess_dataframe_celdas(self.df_celdas, poligono=self.poligono, operador=self.operador)
        self.update_progress_bar(20)

        df_drive_test = preprocess_dataframe_drive_test(self.df_drive_test, df_celdas, poligono=self.poligono)
        self.update_progress_bar(40)

        df_crowdsourced = preprocess_dataframe_crowdsourced(self.df_crowdsourced, df_drive_test, poligono=self.poligono, operador=self.operador)
        self.update_progress_bar(60)

        df_procesado_crowdsourced = process_dataframe(df_crowdsourced)
        df_procesado_drive_test = process_dataframe(df_drive_test)
        self.update_progress_bar(80)

        rsrp_drive_test, rsrq_drive_test = process_dataframe_rsrp_rsrq(df_procesado_drive_test, df_drive_test)
        rsrp_crowdsourced, rsrq_crowdsourced = process_dataframe_rsrp_rsrq(df_procesado_crowdsourced, df_crowdsourced)

        rsrp_drive_test, rsrp_crowdsourced, rsrq_drive_test, rsrq_crowdsourced = filtrar_coincidencias(rsrp_drive_test, rsrp_crowdsourced, rsrq_drive_test, rsrq_crowdsourced)
        self.update_progress_bar(100)
        print(rsrq_drive_test.head())
        print(rsrq_crowdsourced.head())

        self.plot_window = PlotWindow(rsrp_drive_test, rsrp_crowdsourced, rsrq_drive_test, rsrq_crowdsourced, self.operador)
        self.plot_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())