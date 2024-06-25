# Herramienta para el análisis comparativo de medidas móviles
# Contexto
Las metodologías para medir el rendimiento de la red han evolucionado significativamente. Las técnicas tradicionales incluyen mediciones in situ y pruebas de campo, pero el avance de la tecnología ha permitido el desarrollo de nuevas metodologías basadas en el uso de datos crowdsourced y herramientas de monitoreo remoto. Debido a esto, surge la necesidad de desarrollar una herramienta que permita combinar ambas metodologías con el fin de realizar un estudio en una misma área.

Este repositório pretende explicar brevemente el funcionamiento de la herramienta desarrollada y como se podría utilizar. La herramienta se basa en un preprocesado y procesado automático de los datos, y los resultados a los que se llegarán usando ésta serán unos histogramas agrupados por RSRP o RSRQ y la metodología utilizada.

![image](https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/ae555120-bcbd-443a-b0f7-9555f491ba0b)

# Tabla de Contenidos
```
Herramienta
|__ Notebooks
|   |__ Preprocessing.ipynb
|   |__ Processing.ipynb
|   |__ Graphs.ipynb
|   |__ Main.ipynb
|__ Datos
|   |__ Drive Test
|   |   |__ 
|   |__ Crowdsourced
|   |   |__
|   |__ Celdas
|   |   |__ 
|   |__ Polígono.wkt (opcional)
|__ Interfaz
|   |__ Herramienta.py
|   |__ requirements.txt
|__ README.txt
```
# Breve explicación del preprocesado y procesado
Más adelante se explican las funciones que se han creado para desarrollar la herramienta. Con el fin de entender que operaciones realizan cada una de esas funciones, se explica a continuación brevemente los pasos que se realizan en cada uno de los apartados.
## Preprocesado
### Drive Test
1. Corregir geolocalización
2. Delimitar el alcance geográfico de los datos
3. Calcular un identificador único de las medidas
4. Asignar la banda de frecuencia correspondiente a cada medida
5. Asignar franja horaria y día de la semana a cada medida
6. Calcular geohash de la medida
### Crowdsourced
1. Calcular un identificador único de las medidas
2. Delimitar el alcance geográfico de los datos
3. Filtrar los datos para hacerlos lo más semejantes a los del drive test
4. Asignar franja horaria y día de la semana a cada medida
5. Calcular geohash de la medida
## Procesado
En este caso, el procesado de los datos que realizamos para ambos casos (drive test y crowdsourced) es el mismo:
1. Crear DataFrame de geohashes únicos
2. Asignar bandas de frecuencia y CGI (identificador único) a cada geohash
3. Crear una copia del DataFrame para la RSRP y otra para la RSRQ
4. Asignar franja horaria en el DataFrame de la RSRQ
5. Calcular la RSRP y RSRQ media buscando coincidencias en el DataFrame de las medidas en bruto
6. Homogeneizar DataFrames filtrando el de una metodología con el otro y viceversa
# Funciones creadas
Una vez conocidas las operaciones que realizamos en el preprocesado y procesado de los datos, se definen brevemente todas las funciones desarrolladas para llevarlas a cabo de forma automática.
## Preprocessing.ipynb
**Preprocess_dataframe_celdas:** se trata de la función encargada de realizar el preprocesado de los datos que contienen las celdas. En cuanto a los argumentos de dicha función cuenta con:  
- df (pandas.DataFrame): el DataFrame inicial con las celdas.  
- poligono (str): ruta al archivo .wkt que contiene el polígono (opcional).
- operador (str): operador con el que se desea filtrar las celdas (opcional).

Dicha función nos devuelve el DataFrame preprocesado que contiene las celdas.

**Preprocess_dataframe_ drive_test:** se trata de la función encargada de realizar el preprocesado de los datos que contienen las medidas del drive test. En cuanto a los argumentos de dicha función tenemos:  
- df (pandas.DataFrame): el DataFrame inicial con las medidas del drive test.  
- df_celdas (pandas.DataFrame): el DataFrame preprocesado que contiene las celdas.  
- poligono (str): ruta al archivo .wkt que contiene el polígono (opcional).

Dicha función nos devuelve el DataFrame preprocesado de las medidas del drive test.

**Preprocess_dataframe_crowdsourced:** se trata de la función encargada de realizar el preprocesado de los datos que contienen las medidas crowdsourced. En cuanto a los argumentos de dicha función tenemos:  
- df (pandas.DataFrame): el DataFrame inicial con las medidas del drive test.  
- df_drive_test (pandas.DataFrame): el DataFrame preprocesado que contiene las medidas del drive test.  
- poligono (str): ruta al archivo .wkt que contiene el polígono (opcional).  
- Operador (str): operador con el que se desea filtrar las celdas (opcional).

Dicha función nos devuelve el DataFrame preprocesado de las medidas crowdsourced.

## Processing.ipynb
**Process_dataframe:** se trata de la función encargada de realizar el procesado de los datos. En cuanto a los argumentos de dicha función tenemos:  
- df (pandas.DataFrame): el DataFrame preprocesado que contiene las medidas del drive test o las medidas crowdsourced (ya que el procesado es igual para ambos DataFrames).
 
Dicha función nos devuelve el DataFrame procesado, ya sea el del drive test o el de las medidas crowdsourced.

**Process_dataframe_rsrp_rsrq:** como se explicó en uno de los apartados del punto 2.3.2 necesitaríamos dividir nuestros Dataframes procesados en dos, uno para la RSRP y otro para la RSRQ. Seguido de esto se calcularía la media de la RSRP y para la RSRQ se asignaría la ‘Franja_horaria’ y a continuación se calcularía la media. Esta función es la que se encarga de realizar todo lo mencionado y sus argumentos necesarios son:  
- df_copia (pandas.DataFrame): El DataFrame que se va a copiar para la RSRP y la RSRQ, ya sea el de las medidas del drive test o el de las medidas crowdsourced.  
- df_valores (pandas.DataFrame): El DataFrame inicial del cual se extraen los valores para calcular las medias de RSRP y RSRQ. Si se pasó como argumento anterior el DataFrame procesado del drive test, se pasará como argumento el DataFrame inicial del drive test y de la misma forma con los DataFrames de las medidas crowdsourced.
 
Dicha función nos devuelve los DataFrames con la RSRP y la RSRQ medias calculadas.

**Filtrar_coincidencias:** se trata de la función encargada de realizar la comparación de los datos procesados de ambas metodologías. En cuanto a los argumentos de dicha función tenemos:  
- df1 (pandas.DataFrame): el DataFrame procesado que contiene los datos de RSRP para las medidas del drive test.  
- df2 (pandas.DataFrame): el DataFrame procesado que contiene los datos de RSRP para las medidas crowdsourced.  
- df3 (pandas.DataFrame): el DataFrame procesado que contiene los datos de RSRQ para las medidas del drive test.  
- df4 (pandas.DataFrame): el DataFrame procesado que contiene los datos de RSRQ para las medidas crowdsourced.

Dicha función nos devuelve cuatro DataFrames:  
- filtered_df1 (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRP para las medidas del drive test que estén presentes en el conjunto de datos crowdsourced.  
- filtered_df2 (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRP para las medidas crowdsourced que estén presentes en el conjunto de datos del drive test.  
- filtered_df3 (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas del drive test que estén presentes en el conjunto de datos crowdsourced.  
- filtered_df4 (pandas.DataFrame): el DataFrame procesado que contiene los datos de RSRQ para las medidas crowdsourced que estén presentes en el conjunto de datos del drive test.  

## Graphs.ipynb
**Plot_rsrp:** esta función grafica la comparación de los histogramas de RSRP para la metodología drive test y crowdsourced. Los argumentos de esta función son los siguientes:  
- rsrp_drive_test (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRP para las medidas del drive test presentes en el conjunto de datos crowdsourced.  
- rsrp_crowdsourced (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRP para las medidas crowdsourced presentes en el conjunto de datos del drive test.  

**Plot_rsrq:** esta función grafica la comparación de los histogramas de RSRQ para la metodología drive test y crowdsourced. Los argumentos de esta función son los siguientes:  
- rsrq_drive_test (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas del drive test presentes en el conjunto de datos crowdsourced.  
- rsrq_crowdsourced (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas crowdsourced presentes en el conjunto de datos del drive test.  

**Plot_rsrp_band_freq:** esta función grafica la comparación de los histogramas de RSRP para la metodología drive test y crowdsourced en función de la banda de frecuencia seleccionada en el widget presente en el propio gráfico. Los argumentos de esta función son los siguientes:  
- rsrp_drive_test (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRP para las medidas del drive test presentes en el conjunto de datos crowdsourced.  
- rsrp_crowdsourced (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRP para las medidas crowdsourced presentes en el conjunto de datos del drive test.  

**Plot_rsrq_band_freq:** esta función grafica la comparación de los histogramas de RSRQ para la metodología drive test y crowdsourced en función de la banda de frecuencia seleccionada en el widget presente en el propio gráfico. Los argumentos de esta función son los siguientes:  
- rsrq_drive_test (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas del drive test presentes en el conjunto de datos crowdsourced.  
- rsrq_crowdsourced (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas crowdsourced presentes en el conjunto de datos del drive test.  

**Plot_rsrq_boxplot_by_hour:** esta función grafica la comparación de los boxplots de RSRQ para la metodología drive test y crowdsourced en función de la franja horaria . Los argumentos de esta función son los siguientes:  
- rsrq_drive_test (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas del drive test presentes en el conjunto de datos crowdsourced.  
- rsrq_crowdsourced (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas crowdsourced presentes en el conjunto de datos del drive test.  

**Plot_rsrq_std_by_hour:** esta función presenta la comparación de las gráficas de barras de la desviación estándar de la RSRQ para la metodología drive test y crowdsourced en función de la franja horaria . Los argumentos de esta función son los siguientes:  
- rsrq_drive_test (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas del drive test presentes en el conjunto de datos crowdsourced.  
- rsrq_crowdsourced (pandas.DataFrame): el DataFrame filtrado que contiene los datos de RSRQ para las medidas crowdsourced presentes en el conjunto de datos del drive test.  

# Instalación
A continuación se explican los pasos para realizar la instalación completa de la herramienta.  
1. Desde la terminal de anaconda, crear un nuevo entorno y activarlo
```
conda create --name herramienta python=3.10
conda activate herramienta
```
2. Clonar este repositorio
```
git clone https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles.git
```
3. Descargar todas las dependencias necesarias, para ello una vez en el fichero que acabamos de clonar ejecutamos la siguiente línea
```
cd /Interfaz
pip install -r requirements.txt
```
4. Una vez instaladas todas las dependencias tenemos dos opciones para hacer uso de la herramienta, directamente a través de los notebooks o utilizando la interfaz desarrollada.

## Notebooks
Para acceder desde el notebook, los pasos a seguir son:
1. Accedemos al directorio donde tenemos los notebooks
```
cd Notebooks
```
2. Una vez dentro, ejecutamos el notebook llamado Main.ipynb, el cual ya tiene todos los demás módulos importados, para ello ejecutamos:
```
jupyter notebook Main.ipynb
```
3. Si todo ha ido bien, se nos debería abrir el notebook y ver una interfaz similar a la siguiente:
<p align="center">
  <img src="https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/370d36f3-8c06-432c-8aa5-1f8ec0fc2810" width="750" alt="Imagen 6">
</p>
4. Una vez ahí, introducimos el nombre de los archivos que hemos tenido que añadir en las respectivas carpetas, Drive Test, Crowdsourced y Celdas. Por último, añadimos el nombre del polígono y del operador en caso de que querramos filtrar los datos por esos valores. Una vez hecho ejecutamos el resto de celdas hasta llegar a la parte de resultados.

## Interfaz
Utilizar la herramienta desde la interfaz es mucho más sencillo.
1. Accedemos al directorio donde tenemos el archivo Herramienta.py, para ello ejecutamos:
```
cd Interfaz
python Herramienta.py
```
2. Se nos abrirá una interfaz como la siguiente:
<p align="center">
  <img src="https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/a01384d8-17a9-47da-81f5-1dce0de625d2" width="400" alt="Imagen 1">
</p>
3. Una vez dentro, cargamos todos los archivos que se nos pide, seleccionamos el operador que queramos y le damos al botón naranja 'Procesar Datos'. Si todo ha funcionado deberíamos ver como la barra de abajo comienza a cargar.
<p align="center">
  <img src="https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/a180e27d-6f21-407b-b1df-3062e97d714d" width="400" alt="Imagen 2">
</p>
4. Una vez termine la barra, se nos abrirá otra pestaña como la siguiente, en la cual simplemente seleccionamos el gráfico o el resultado que queramos y se nos mostrará por pantalla.
<p align="center">
  <img src="https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/e631e3db-c309-4f6f-913d-27dc124a4fb9" width="400" alt="Imagen 3">
</p>
<p align="center">
  <img src="https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/234e20cc-d9a0-4829-a611-278a7d3ee009" width="400" alt="Imagen 4">
</p>
