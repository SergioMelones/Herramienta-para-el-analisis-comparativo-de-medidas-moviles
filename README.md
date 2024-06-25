# Herramienta para el análisis comparativo de medidas móviles
# Contexto
Las metodologías para medir el rendimiento de la red han evolucionado significativamente. Las técnicas tradicionales incluyen mediciones in situ y pruebas de campo, pero el avance de la tecnología ha permitido el desarrollo de nuevas metodologías basadas en el uso de datos crowdsourced y herramientas de monitoreo remoto. Debido a esto, surge la necesidad de desarrollar una herramienta que permita combinar ambas metodologías con el fin de realizar un estudio en una misma área.

Este repositório pretende explicar brevemente el funcionamiento de la herramienta desarrollada y como se podría utilizar. Los resultados a los que se llegarán usando la herramienta serán unos histogramas agrupados por RSRP o RSRQ y la metodología utilizada.

<p align="center">
  <img src="https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/ca60ebd9-e58f-4524-bc4a-5fa0d5e234d0" alt="Imagen 1" style="display: inline-block;" width="500" height="300">
  <img src="https://github.com/SergioMelones/Herramienta-para-el-analisis-comparativo-de-medidas-moviles/assets/126664020/a3951b8e-47d2-4e84-84cb-46007ee588b3" alt="Imagen 2" style="display: inline-block;" width="500" height="300">
</p>

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
|   |__ Polígono.wkt (opcional)
|__ Interfaz
|   |__ Herramienta.py
|   |__ requirements.txt
|__ README.txt
```
# Funciones creadas
En este apartado se definirán brevemente todas las funciones desarrolladas para la herramienta
## Preprocessing.ipynb
•	Preprocess_dataframe_celdas: se trata de la función encargada de realizar el preprocesado de los datos que contienen las celdas. En cuanto a los argumentos de dicha función cuenta con:  
  o	df (pandas.DataFrame): el DataFrame inicial con las celdas.  
  o	poligono (str): ruta al archivo .wkt que contiene el polígono (opcional).  
  o	operador (str): operador con el que se desea filtrar las celdas (opcional).  
Dicha función nos devuelve el DataFrame preprocesado que contiene las celdas.  
•	Preprocess_dataframe_ drive_test: se trata de la función encargada de realizar el preprocesado de los datos que contienen las medidas del drive test. En cuanto a los argumentos de dicha función tenemos:  
  o	df (pandas.DataFrame): el DataFrame inicial con las medidas del drive test.  
  o	df_celdas (pandas.DataFrame): el DataFrame preprocesado que contiene las celdas.  
  o	poligono (str): ruta al archivo .wkt que contiene el polígono (opcional).  
Dicha función nos devuelve el DataFrame preprocesado de las medidas del drive test.  
•	Preprocess_dataframe_crowdsourced: se trata de la función encargada de realizar el preprocesado de los datos que contienen las medidas crowdsourced. En cuanto a los argumentos de dicha función tenemos:  
  o	df (pandas.DataFrame): el DataFrame inicial con las medidas del drive test.  
  o	df_drive_test (pandas.DataFrame): el DataFrame preprocesado que contiene las medidas del drive test.  
  o	poligono (str): ruta al archivo .wkt que contiene el polígono (opcional).  
  o	Operador (str): operador con el que se desea filtrar las celdas (opcional).  
Dicha función nos devuelve el DataFrame preprocesado de las medidas crowdsourced.
# Instalación
Los pasos para realizar la instalación completa de la herramienta son:  
1. Crear un nuevo entorno y activarlo
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
4. Una vez instaladas todas las dependencias tenemos dos opciones para hacer uso de la herramienta, a continuación se explican por separado cada una de ellas.

# Notebooks
