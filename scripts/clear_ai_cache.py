"""CLI para vaciar la caché del `AIClassifier`.

Nota: ejecutar este script en una sesión separada NO limpiará la caché de procesos del servidor ya en ejecución.
Para limpiar la caché de un servidor en ejecución, reinícialo o añade un endpoint admin que llame `classifier.clear_cache()`.
"""

import sys

try:
    from app.services import ai_classifier
except Exception as exc:
    print("No se pudo importar 'app.services.ai_classifier':", exc)
    print("Asegúrate de ejecutar este script en el entorno del proyecto (PYTHONPATH/venv).")
    sys.exit(2)

# Intentar usar un método público si existe
classifier = getattr(ai_classifier, "classifier", None)
if classifier is None:
    print("No se encontró la instancia 'classifier' en app.services.ai_classifier.")
    sys.exit(1)

# Si el objeto expone clear_cache, usarlo; si no, intentar limpiar el atributo privado.
cleared = None
if hasattr(classifier, "clear_cache") and callable(getattr(classifier, "clear_cache")):
    try:
        cleared = classifier.clear_cache()
    except Exception as exc:
        print("Error llamando classifier.clear_cache():", exc)
        sys.exit(1)
else:
    # acceder a _cache directamente
    cache_attr = getattr(classifier, "_cache", None)
    if cache_attr is None:
        print("La instancia 'classifier' no tiene atributo '_cache' ni método 'clear_cache'.")
        sys.exit(1)
    try:
        n = len(cache_attr)
        cache_attr.clear()
        cleared = n
    except Exception as exc:
        print("Error limpiando classifier._cache:", exc)
        sys.exit(1)

print(f"Cache cleared: {cleared} entries")
sys.exit(0)
