# Quiniela Mundial 2026

Dashboard en Streamlit para ranking de quiniela del Mundial.

## Archivos

- `app.py`: aplicación principal.
- `predicciones.csv`: predicciones por participante.
- `resultados_manual.csv`: respaldo para cargar marcadores manualmente si la API no responde.
- `requirements.txt`: dependencias para Streamlit Cloud.

## Regla actual

El archivo original trae predicciones tipo:

- `L`: gana local
- `E`: empate
- `V`: gana visitante

La regla actual es **1 punto por acierto**. Para cambiarlo, edita `PUNTOS_ACIERTO` en `app.py`.

## Publicar en Streamlit Community Cloud

1. Crea un repositorio en GitHub.
2. Sube estos cuatro archivos al repositorio.
3. Entra a Streamlit Community Cloud.
4. Crea una nueva app apuntando al repo y al archivo `app.py`.
5. Comparte la liga generada.

## Ejecutar local

```bash
pip install -r requirements.txt
streamlit run app.py
```
