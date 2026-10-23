# Clepium – stories automáticas

Publica todos los días a las 12:00 (Buenos Aires) una tanda de stories en la página de Facebook y en Instagram de Clepium.

## Cómo funciona

- Las imágenes van en `stories/` con el formato `storyNN-M.png` (NN = tanda, M = orden).
- Cada día publica la tanda siguiente; después de la última vuelve a la primera.
- Para sumar tandas, subí `story13-1.png`, `story13-2.png`, etc. a `stories/` y entran solas al loop.
- `convert.py` pasa los PNG a JPG (Instagram solo acepta JPEG) y se corre solo en cada ejecución.
- `state.json` guarda qué tanda salió por última vez. Si querés reiniciar el ciclo, borralo.

## Puesta en marcha (una sola vez)

1. Creá un repo **público** en GitHub (por ejemplo `clepium-stories`) y subí todo este contenido.
2. Subí los PNG a la carpeta `stories/` (desde la web: entrás a `stories/` → *Add file* → *Upload files*).
3. En el repo: *Settings* → *Secrets and variables* → *Actions* → *New repository secret*:
   - Nombre: `META_TOKEN`
   - Valor: el token del usuario del sistema (con `pages_manage_posts`, `instagram_basic` e `instagram_content_publish`).

## Probar o publicar a mano

*Actions* → *Publicar stories* → *Run workflow*:

- `dry_run = 1`: simula, no publica nada.
- `tanda`: fuerza una tanda puntual (dejalo vacío para la que toca).
- `targets`: `fb,ig`, `fb` o `ig`.

## Notas

- GitHub puede demorar el disparo programado entre unos minutos y media hora en horas pico.
- Si una imagen falla, sigue con el resto y la ejecución queda marcada en rojo con el detalle del error.
