# 2EZConfig_Re — Guía en español

[![CI de Windows](https://github.com/ECas95/2EZConfig_Re/actions/workflows/ci.yml/badge.svg)](https://github.com/ECas95/2EZConfig_Re/actions/workflows/ci.yml)

[English (README principal)](README.md) | **Español**

**2EZConfig_Re** es un fork comunitario de [2EZConfig V2](https://github.com/ben-rnd/2EZConfig-V2), una herramienta para configurar controles, E/S y parches de compatibilidad de juegos arcade de las familias **EZ2DJ / EZ2AC**, **EZ2Dancer** y **Sabin Sound Star: Renascence Burst**.

> [!IMPORTANT]
> Este proyecto **no distribuye juegos ni archivos de los juegos**. Utilízalo únicamente con software e instalaciones que tengas autorización de usar. Conservamos la atribución y licencias del proyecto original.

## Enfoque principal: compatibilidad y servicios para jugadores

**2EZConfig_Re** debe funcionar como una plataforma de compatibilidad y utilidades para EZ2DJ/EZ2AC, no como otro creador de canciones o un motor de charts. Las prioridades pasan a ser Windows modernos, estabilidad de lanzamiento, controles/audio/pantalla y un **sistema de scores con opción de rankings globales**.

**Disponible ahora:** un botón **Check launcher files** en Diagnostics y [Compatibility Doctor](documentation/COMPATIBILITY_DOCTOR.md) de solo lectura, mejoras de seguridad contra duplicados en scores locales, rankings de **récord personal** y estadísticas locales desde el dashboard. Todas las puntuaciones siguen siendo **no verificadas**.

**Pendiente:** hooks de resultados finales comprobados en una versión exacta del juego, perfiles de compatibilidad medidos en Windows 10/11, autenticación y servidor global real. La ingeniería inversa se usa como referencia, sin copiar códigos propietarios al fork.

Ver [estrategia de modernización](documentation/MODERNIZATION_STRATEGY.md) y [arquitectura de rankings globales](documentation/GLOBAL_RANKINGS.md).

## Funcionalidades disponibles

- **Controles:** botones HID/teclado, ejes y turntables mediante dispositivos compatibles, entradas de mouse y salidas de iluminación HID.
- **Detección de juegos:** identificación por hashes MD5 de ejecutables conocidos y selección manual en caso de no encontrarse coincidencias.
- **Parches:** biblioteca JSON integrada, parches personalizados `user-patches.json`, direcciones RVA, patrones de búsqueda y diferentes momentos de aplicación.
- **Compatibilidad:** ajustes DirectDraw, opciones de solicitud de 60 Hz y audio WASAPI para Windows Vista o posterior.
- **Lanzador:** carga de `2EZ.dll`, DLL adicionales opcionales, arranque sin interfaz y comportamiento especial de 6th Trax / Remember 1st.
- **Protección de configuraciones:** guardado mediante archivo temporal, última copia válida `.bak`, preservación de JSON corruptos como `.corrupt` e intento de recuperación automática.
- **Desarrollo:** compilación CMake/MinGW de 32 bits, verificación SHA-256 del compilador, dependencias fijadas y pruebas automatizadas en GitHub Actions.
- **Diagnóstico HID:** pestaña Diagnostics con botones, ejes y dispositivos conectados en tiempo real.
- **Extensiones opcionales:** eventos JSONL desde `2EZ.dll` con API C, perfiles de cabinets, validador de packs de canciones, API local de scores y salas multijugador experimentales en Python 3.10+.

**Limitaciones:** la iluminación de sensores/pads de EZ2Dancer no está terminada. La compatibilidad con **Windows XP SP3** es un objetivo de compilación; no hay una verificación independiente de este fork en XP ni en cabinets originales. No todos los parches funcionan con todas las revisiones de cada juego.

## Instalación rápida

1. Crea un **respaldo** del juego y de tus configuraciones actuales.
2. Descarga una compilación confiable o compila el proyecto.
3. Coloca **`2EZConfig.exe`** y **`2EZ.dll`** junto al ejecutable principal del juego.
4. Ejecuta `2EZConfig.exe` con la **carpeta del juego como directorio de trabajo**.
5. Si el juego no se detecta automáticamente, selecciona la familia y versión correctas y modifica **Exe Name Override** si es necesario.
6. Configura las pestañas **Settings**, **Buttons**, **Analogs** (EZ2DJ/AC), **Lights** y **Patches**.
7. Prueba primero el juego con los parches opcionales desactivados y actívalos progresivamente.

Para arrancar sin mostrar el configurador, utiliza `2EZConfig.exe -skip-config` después de confirmar que tu configuración funciona.

## Diagnóstico de hardware y herramientas nuevas

La nueva pestaña **Diagnostics** muestra dispositivos HID, botones presionados y ejes analógicos. Es **solo lectura**; los pulsos de luces siguen en la pestaña Lights.

Las herramientas complementarias son opcionales y funcionan en una computadora moderna con **Python 3.10+**. No hacen falta para jugar ni deben ejecutarse en Windows XP:

| Herramienta | Funcionalidad real | Limitación |
| --- | --- | --- |
| [Perfiles de cabinet](documentation/CABINET_PROFILES.md) | Exportar, comparar y restaurar JSON con respaldos | Aún sin selector visual en el configurador |
| [Canciones personalizadas](documentation/CUSTOM_SONGS.md) | Validar manifests y archivos originales o licenciados | **Todavía no instala canciones en EZ2DJ/EZ2AC** |
| [Scores locales](documentation/SCORES_API.md) | SQLite, carga manual y **dashboard local** para scores y rankings | Los scores son **no verificados**; falta capturarlos desde el juego |
| [Salas multijugador](documentation/MULTIPLAYER.md) | Crear sala, unirse, listo, inicio y resultados para 2–4 participantes | No sincroniza partidas reales |
| [SDK de eventos](documentation/EXTENSION_EVENTS.md) | Guardar eventos de hooks autorizados en JSONL sin networking en la DLL | Requiere adaptadores específicos para canciones y resultados |

Ejecuta el servidor complementario en tu PC moderna:

~~~powershell
python tools/companion_server.py --host 127.0.0.1 --port 8765
~~~

Abre el **panel web local** en http://127.0.0.1:8765/dashboard para experimentar con scores, rankings, salas y eventos. El endpoint de salud es http://127.0.0.1:8765/health. El prototipo solo escucha conexiones locales por defecto; **no lo expongas a Internet como servidor público de rankings**.

## Nuevos hooks: canciones custom, scores online y multijugador

**Ya implementado:** API exportada `EZ2_PublishEvent`, evento `runtime.ready`, archivo local `2ez-events.jsonl` desactivado por defecto, herramienta de reenvío manual, servidor complementario y validación de archivos.

**Pendiente:** un loader real de canciones para cada versión del juego, hooks confiables de selección de canciones/resultados, verificación anti-cheat y sincronización multijugador en tiempo real. Los ejemplos de desarrollo no equivalen a estas funciones dentro del arcade.

Consulta la [guía de nuevos hooks](documentation/NEW_HOOKS.md), [canciones personalizadas](documentation/CUSTOM_SONGS.md), [scores](documentation/SCORES_API.md), [multijugador](documentation/MULTIPLAYER.md) y [SDK de eventos](documentation/EXTENSION_EVENTS.md). Trabaja únicamente con canciones y recursos propios o autorizados.

## Investigación de EZ2AC Final:EX

Analicé un paquete privado de ingeniería inversa del juego que describe el catálogo de canciones, los archivos de configuración de modos, el orden de carriles, el sistema de juicio y los rankings. Este fork utiliza **conclusiones técnicas y herramientas propias**; no publica el código reconstruido del juego, archivos comerciales, dumps o claves privadas del material de referencia.

Se agregaron tres herramientas Python **de solo lectura**, útiles para documentación y pruebas:

| Herramienta | Qué hace | Limitación |
| --- | --- | --- |
| [Inspector y mapa SVG de GDS](documentation/fnex/FORMATS.md) | Lee `.gds`, verifica carriles y genera diagramas SVG de teclas y tracks | No modifica archivos del juego ni convierte charts |
| [Inspector de rankings](documentation/fnex/FORMATS.md) | Interpreta posibles formatos de top 5 o top 99 de archivos locales, ocultando los nombres por defecto | No certifica scores ni los sube a Internet |
| [Comprobador de compatibilidad](documentation/fnex/COMPATIBILITY.md) | Calcula SHA-256 del ejecutable local y compara manifests de adaptadores | No instala hooks; el hash de una imagen desempaquetada no equivale al del archivo original |

Prueba el inspector con un archivo **sintético propio del repositorio**:

~~~powershell
python tools/gds_inspector.py examples/fnex/synthetic_mode.gds --json
python tools/gds_visualizer.py examples/fnex/synthetic_mode.gds --output mapa_carriles.svg
~~~

El juego existente se identifica como `ez2ac_fn_ex` en 2EZConfig_Re. Para un futuro hook real aún se necesita verificar **la versión exacta del ejecutable**, las instrucciones esperadas, la compatibilidad de memoria y el funcionamiento en hardware arcade.

Documentación ampliada: [análisis de Final:EX](documentation/fnex/README.md), [formatos y archivos](documentation/fnex/FORMATS.md), [diseño de hooks](documentation/fnex/HOOK_DESIGN.md), [compatibilidad](documentation/fnex/COMPATIBILITY.md) y [plan de implementación](documentation/fnex/INTEGRATION_PLAN.md).

**Todavía no están implementados** un loader real de canciones para Final:EX, un hook de resultados verificados ni el multijugador sincronizado dentro del juego. La nueva infraestructura ayuda a desarrollarlos sin depender de offsets de memoria supuestos.

## Observatorio pasivo de Final:EX

Se incorporaron herramientas de investigación **sin modificar el juego**: un inventario de modos `.gds`, un simulador de eventos para probar las transiciones de selección de canción y resultados, y una comparación de rankings locales que oculta los nombres de jugadores.

~~~powershell
python tools/fnex_mode_inventory.py examples/fnex --json
python tools/fnex_trace_replay.py --input examples/fnex/synthetic_observations.jsonl --output eventos_sinteticos.jsonl --json
python tools/event_bridge.py --file eventos_sinteticos.jsonl
~~~

El segundo comando usa **datos sintéticos**: no detecta canciones reales, no accede a la memoria del arcade y no envía puntuaciones al servidor. Los eventos indican `synthetic=true` y `verified=false`. El último comando es una vista previa local sin transferencia de red.

Guía detallada: [Final:EX Passive Observatory](documentation/fnex/PASSIVE_OBSERVATORY.md). La captura auténtica de resultados y canciones sigue pendiente de un adaptador probado para una versión exacta de Final:EX.

## Compatibilidad con EZ2CustomMod (proyecto externo)

Los nuevos archivos entregados contienen un **mod desarrollado por separado** para Final:EX: lector de canciones BMS, AutoChart, categorías, previews y rankings locales. El proyecto externo describe pruebas con más de 23 mil canciones, pero esa validación **no se ha reproducido en este fork**. No copiamos su código decompilado ni distribuimos su DLL o recursos de juego.

En 2EZConfig_Re ahora hay advertencias de compatibilidad junto a **Settings → Extra DLLs**, además de herramientas Python para revisar la instalación, comprobar la estructura de BMSData y resumir logs de rendimiento en XP sin exponer títulos de canciones o nombres de jugadores.

**Atención:** el ejecutable predeterminado en este fork para Final:EX es `EZ2AC.exe`, pero la guía externa de EZ2CustomMod utiliza `EZ2B.exe`. Verifica cuál está presente en tu instalación y configura **Exe Name Override** manualmente si corresponde.

~~~powershell
python tools/fnex_custommod_preflight.py --game-dir "D:\Arcade\FNEX" --json
python tools/fnex_bms_library_check.py "D:\Arcade\FNEX\BMSData" --check-assets --json
python tools/fnex_custommod_log_report.py "D:\Arcade\FNEX\logs\EZ2CustomMod.log" --json
~~~

Guía técnica: [integración con EZ2CustomMod](documentation/fnex/CUSTOMMOD_INTEROP.md) y [auditoría de sus fuentes privadas](documentation/fnex/CUSTOMMOD_SOURCE_AUDIT.md). Los hooks reales de resultados y los scores online verificados **siguen pendientes**.

## Dónde se guardan las configuraciones

| Archivo | Ubicación | Uso |
| --- | --- | --- |
| `game-settings.json` | Carpeta del juego | Juego, opciones y estado de parches |
| `global-settings.json` | `%APPDATA%\2ezconfig\` | Configuración global y controles compartidos |
| `patches.json` | `%APPDATA%\2ezconfig\` | Biblioteca de parches incluida en el programa |
| `user-patches.json` | Carpeta del juego, opcional | Parches propios |
| `2ez-logs.txt` | Carpeta del juego, si activas logging | Registros para diagnóstico |

Si `game-settings.json` o `global-settings.json` están dañados, la nueva implementación intenta **conservar el archivo corrupto**, recuperar la copia `.bak` válida o usar valores predeterminados, mostrando una advertencia. Esta protección no reemplaza un respaldo completo de tu cabinet.

## Modos de pantalla, escalado y 60/120 Hz

**Corrección de seguridad:** una prueba real de Final:EX produjo un cierre inesperado en Windowed. Hemos bloqueado Windowed, Borderless y Draggable hasta demostrar compatibilidad real con el renderer nativo. Las opciones antiguas guardadas se ignoran automáticamente al arrancar.

En **Display → Native DirectX** puedes probar el motor DirectX 7 original *sin los hooks gráficos DirectDraw de 2EZ*, manteniendo el soporte de IO y otras funciones. No utiliza dgVoodoo, pero tampoco convierte Direct3D7 a OpenGL ni garantiza ventana. [Diagnóstico y procedimiento de recuperación](documentation/NATIVE_DIRECTX_RECOVERY.md).


La pestaña **Display** conserva esas opciones como referencia, pero solo **Original** está habilitado para versiones no certificadas. El ejecutable auxiliar de Windowed/Borderless no se inicia automáticamente mientras no exista una implementación nativa segura. Esto evita repetir el cierre observado.

Ahora es posible solicitar **60 Hz o 120 Hz** en los títulos con soporte DirectDraw4/7. El ajuste 120 Hz es experimental y solo se intenta cuando Windows anuncia ese modo de pantalla. **120 Hz de monitor no significa 120 FPS reales**; los tiempos internos del juego y el scoring no se modifican.

Se conserva el filtrado POINT para píxeles nítidos. Los **shaders CRT, FSR, Anime4K y otros upscalers** necesitarán un backend validado; por ahora recomendamos investigar herramientas externas como Magpie en Windows 10/11, sin instalarlas automáticamente. Consulta la [guía completa de Display](documentation/PRESENTATION_MODES.md).

## Diagnóstico de compatibilidad (Windows modernos)

En una PC con Python 3.10 o superior, analiza tu instalación sin arrancar ni modificar el juego:

~~~powershell
python tools/compatibility_doctor.py --game-dir "D:\Arcade\EZ2" --json
~~~

El reporte inspecciona cabeceras PE, concordancia x86 entre el ejecutable y 2EZ.dll, configuración de audio y opciones de 60 Hz. No mide directamente la GPU, DPI ni latencia real; eso requiere pruebas del sistema. [Guía completa](documentation/COMPATIBILITY_DOCTOR.md).

## Compilar en Windows

Requiere **CMake 3.20+**, Git, herramientas compatibles con MinGW Makefiles, conexión a Internet para las dependencias y, si hace falta, 7-Zip.

```powershell
git clone https://github.com/ECas95/2EZConfig_Re.git
cd 2EZConfig_Re
cmake --preset release
cmake --build --preset release
ctest --test-dir build/release --output-on-failure
```

Los binarios esperados están en `build/release/bin/`. El compilador GCC 12.2 de 32 bits se descarga automáticamente con verificación SHA-256, si no está disponible previamente. GitHub Actions comprueba la compilación en Windows y ejecuta pruebas de recuperación de configuraciones. Esto **no** reemplaza ensayos en Windows XP, CRT y hardware arcade físico.

Las releases se generan únicamente desde etiquetas de versión `vX.Y.Z` e incluyen los archivos de licencia y checksums.

## Diagnóstico GPU universal (Intel, NVIDIA, AMD)

2EZConfig_Re no debe exigir una GPU específica. Añadimos acceso a las preferencias gráficas de Windows desde Diagnostics y un inventario local de adaptadores/controladores, independiente de la marca y de solo lectura.

En un portátil híbrido, una GPU NVIDIA disponible no garantiza que el juego DirectDraw/Direct3D7 utilice esa GPU. Prueba Alto rendimiento sobre el ejecutable real del juego, por ejemplo EZ2AC.exe, no solamente el launcher; compara los errores registrados.

Comando: .\tools\gpu_compatibility_report.ps1

El JSON incluye GPU y versiones de driver, pero no IDs de dispositivo, rutas ni datos personales. No fuerza ni cambia GPU. [Guía de compatibilidad por capacidades](documentation/VENDOR_NEUTRAL_GPU.md).

## Diagnóstico de crashes Intel sin wrappers

Un registro real de Final:EX con **Native DirectX activado** identificó `igc32.dll` (controlador Intel 32.0.101.7088), excepción `0xC0000005`, desplazamiento `0x00E44C06`. Los tres fallos registrados repiten la misma firma; la causa raíz aún necesita aislarse con pruebas del driver/GPU. El diagnóstico **no justifica instalar dgVoodoo u otros wrappers**.

Para analizar eventos exportados de Windows de forma local y sin mostrar rutas privadas:

~~~powershell
.\tools\windows_crash_report.ps1 -EvtxPath 'C:\Logs\ez21.evtx','C:\Logs\ez22.evtx'
~~~

Consulta la [guía de análisis de Intel Graphics](documentation/INTEL_DRIVER_CRASH.md). La herramienta no modifica controladores ni el juego y evita contar dos veces EVTX idénticos.

## Compatibilidad y resolución de problemas

- En Windows moderno, [DDrawCompat](https://github.com/narzoul/DDrawCompat) es una herramienta externa opcional; pruébala por separado.
- Los parches de 60 Hz solicitan un modo de pantalla; debes verificar la frecuencia real del monitor/driver.
- Las funciones basadas en WASAPI requieren Windows Vista o posterior.
- Algunos juegos antiguos no interpretan correctamente carpetas que contienen puntos en el nombre.
- Ante fallas, desactiva DLLs y parches personalizados, habilita logging y revisa los archivos JSON antes de modificar la instalación.
- Windows XP no debería conectarse directamente a redes no confiables.

## Documentación y próximos pasos

La [documentación técnica en inglés](README.md#project-documentation-and-contributing) incluye instalación, compilación, arquitectura, ejemplos JSON, diagnóstico, contribuciones y el [roadmap](documentation/ROADMAP.md). También se incluyen una [guía para desarrolladores](documentation/DEVELOPER_GUIDE.md), [changelog](CHANGELOG.md) y [política de seguridad](SECURITY.md).

El **diagnóstico HID en vivo** ya está integrado y hay un administrador de perfiles mediante comandos. Siguen pendientes la selección visual de perfiles, mapeo gráfico de E/S, inspección de compatibilidad de parches, hooks reales para canciones/scores y protección avanzada de las escrituras de memoria.

**Créditos:** fork de [ben-rnd/2EZConfig-V2](https://github.com/ben-rnd/2EZConfig-V2), basado en [2EZConfig original](https://github.com/ben-rnd/2EZConfig). Consulta [LICENSE](LICENSE) y [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) antes de redistribuir.
