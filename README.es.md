# 2EZConfig_Re — Guía en español

[![CI de Windows](https://github.com/ECas95/2EZConfig_Re/actions/workflows/ci.yml/badge.svg)](https://github.com/ECas95/2EZConfig_Re/actions/workflows/ci.yml)

[English (README principal)](README.md) | **Español**

**2EZConfig_Re** es un fork comunitario de [2EZConfig V2](https://github.com/ben-rnd/2EZConfig-V2), una herramienta para configurar controles, E/S y parches de compatibilidad de juegos arcade de las familias **EZ2DJ / EZ2AC**, **EZ2Dancer** y **Sabin Sound Star: Renascence Burst**.

> [!IMPORTANT]
> Este proyecto **no distribuye juegos ni archivos de los juegos**. Utilízalo únicamente con software e instalaciones que tengas autorización de usar. Conservamos la atribución y licencias del proyecto original.

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
| [Scores locales](documentation/SCORES_API.md) | SQLite, carga manual de scores y rankings | Los scores son **no verificados**; falta capturarlos desde el juego |
| [Salas multijugador](documentation/MULTIPLAYER.md) | Crear sala, unirse, listo, inicio y resultados para 2–4 participantes | No sincroniza partidas reales |
| [SDK de eventos](documentation/EXTENSION_EVENTS.md) | Guardar eventos de hooks autorizados en JSONL sin networking en la DLL | Requiere adaptadores específicos para canciones y resultados |

Ejecuta el servidor complementario en tu PC moderna:

~~~powershell
python tools/companion_server.py --host 127.0.0.1 --port 8765
~~~

Prueba el endpoint http://127.0.0.1:8765/health. El prototipo solo escucha conexiones locales por defecto; **no lo expongas a Internet como servidor público de rankings**.

## Nuevos hooks: canciones custom, scores online y multijugador

**Ya implementado:** API exportada `EZ2_PublishEvent`, evento `runtime.ready`, archivo local `2ez-events.jsonl` desactivado por defecto, herramienta de reenvío manual, servidor complementario y validación de archivos.

**Pendiente:** un loader real de canciones para cada versión del juego, hooks confiables de selección de canciones/resultados, verificación anti-cheat y sincronización multijugador en tiempo real. Los ejemplos de desarrollo no equivalen a estas funciones dentro del arcade.

Consulta la [guía de nuevos hooks](documentation/NEW_HOOKS.md), [canciones personalizadas](documentation/CUSTOM_SONGS.md), [scores](documentation/SCORES_API.md), [multijugador](documentation/MULTIPLAYER.md) y [SDK de eventos](documentation/EXTENSION_EVENTS.md). Trabaja únicamente con canciones y recursos propios o autorizados.

## Dónde se guardan las configuraciones

| Archivo | Ubicación | Uso |
| --- | --- | --- |
| `game-settings.json` | Carpeta del juego | Juego, opciones y estado de parches |
| `global-settings.json` | `%APPDATA%\2ezconfig\` | Configuración global y controles compartidos |
| `patches.json` | `%APPDATA%\2ezconfig\` | Biblioteca de parches incluida en el programa |
| `user-patches.json` | Carpeta del juego, opcional | Parches propios |
| `2ez-logs.txt` | Carpeta del juego, si activas logging | Registros para diagnóstico |

Si `game-settings.json` o `global-settings.json` están dañados, la nueva implementación intenta **conservar el archivo corrupto**, recuperar la copia `.bak` válida o usar valores predeterminados, mostrando una advertencia. Esta protección no reemplaza un respaldo completo de tu cabinet.

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
