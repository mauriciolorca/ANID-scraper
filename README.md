# ANID Scraper

Un scraper para extraer información detallada de los concursos publicados en el sitio web de ANID (Agencia Nacional de Investigación y Desarrollo de Chile).

## Características

- Extrae URLs de concursos desde https://anid.cl/concursos/
- Compara con concursos ya registrados para obtener solo los nuevos
- Extrae información detallada de cada concurso, incluyendo:
  - Estado del concurso
  - Fechas (inicio, cierre, fallo)
  - Tipo de concurso
  - Nombre
  - Contenido de todas las pestañas (Presentación, Público Objetivo, etc.)
- Guarda la información en formato CSV
- Manejo robusto de errores y método de respaldo
- Evita bloqueos del sitio web

## Requisitos

- Python 3.8 o superior
- Chrome/Chromium instalado
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/[tu-usuario]/ANID-scraper.git
cd ANID-scraper
```

2. Crear un entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
venv\Scripts\activate     # En Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

Simplemente ejecuta el script:
```bash
python ANID_scraper.py
```

El script:
1. Buscará nuevos concursos en el sitio web de ANID
2. Creará/actualizará `ANID_concursos.csv` con las URLs encontradas
3. Extraerá información detallada de cada concurso
4. Guardará toda la información en `ANID_concursos_detallado.csv`

## Estructura de Archivos

- `ANID_scraper.py`: Script principal
- `requirements.txt`: Lista de dependencias
- `ANID_concursos.csv`: URLs de los concursos
- `ANID_concursos_detallado.csv`: Información detallada de cada concurso

## Notas Técnicas

- Utiliza una combinación de requests/BeautifulSoup4 y Selenium para máxima eficiencia
- Implementa retrasos aleatorios y rotación de User-Agents para evitar bloqueos
- Modo headless para Chrome en la extracción de URLs
- Manejo automático de errores con método de respaldo

## Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Haz fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.
