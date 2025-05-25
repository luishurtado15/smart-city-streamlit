# city-ia-streamlit
city-ia-streamlit

2. Instalación en un entorno virtual (recomendado)
Para evitar conflictos con otras bibliotecas y mantener tu proyecto aislado:

Abre la Terminal
Crea y navega a la carpeta de tu proyecto:
bashmkdir mi_proyecto_streamlit
cd mi_proyecto_streamlit

Crea un entorno virtual:
bashpython -m venv venv
o
bashpython3 -m venv venv

Activa el entorno virtual:
bashsource venv/bin/activate
(Verás que el prompt de la terminal cambia, indicando que el entorno está activo)
Instala Streamlit en el entorno virtual:
bashpip install streamlit

Verifica la instalación:
bashstreamlit --version


Creando tu primera aplicación Streamlit

Crea un archivo Python, por ejemplo app.py:
bashtouch app.py

streamlit run app.py


pip freeze > requirements.txt

