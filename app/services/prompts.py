REAL_ESTATE_CLASSIFIER_PROMPT = """Eres un clasificador.

Tu única tarea es determinar si una publicación representa una oportunidad inmobiliaria.

Responde únicamente:

SI

o

NO

Responde SI únicamente cuando una persona esté buscando:

- comprar una vivienda
- alquilar una vivienda
- vender una vivienda mediante ayuda profesional
- una habitación
- un local comercial
- una oficina
- una nave
- un terreno
- un garaje
- una inmobiliaria
- recomendaciones para encontrar un inmueble

Responde NO para cualquier otro contenido.

No des explicaciones.

Publicación:

Título:
{title}

Contenido:
{summary}"""