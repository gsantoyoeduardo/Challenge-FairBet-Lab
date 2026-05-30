# Declaración de Uso de IA 

En cumplimiento con la política de evaluación y autoría del reto FairBet Lab, declaro a continuación el uso de herramientas de Inteligencia Artificial Generativa (Gemini) durante la Fase 5 del proyecto:

## 1. Depuración de Errores (Debugging)
* **Contexto:** Durante la ejecución ¿+de las pruebas automatizadas con Docker (`docker-compose exec backend python manage.py test`).
* **Asistencia:** Utilicé la IA para identificar la causa de un `ModuleNotFoundError` relacionado con la librería `hypothesis` y un `TypeError` por la falta de archivos `__init__.py` en las carpetas de testing.
* **Resultado:** Comprendí que el contenedor requería la instalación explícita de la dependencia y que Python necesita los archivos de inicialización para descubrir los tests.

## 2. Generación de Boilerplate y Testing
* **Contexto:** Implementación de *Property-based testing* para validar las invariantes financieras.
* **Asistencia:** Solicité a la IA la estructura básica (boilerplate) de una prueba con `hypothesis` en Django.
* **Resultado:** Adapté el código generado a la Clean Architecture del proyecto, importando correctamente los modelos `Account` y `LedgerEntry`, y asegurando que las aserciones validaran la partida doble estricta. (Commit marcado con `[ai-assisted]`).

## 3. Revisión y Estructuración de Documentación
* **Contexto:** Redacción del documento legal de cumplimiento de la Ley 31557 y generación de esquemas visuales.
* **Asistencia:** Usé la IA para estructurar el documento `compliance_ley31557.md` con un tono formal y autocrítico, y para generar código PlantUML/Mermaid que luego me sirvió de guía para realizar los bocetos a mano exigidos en la carpeta `/sketches/`.
* **Resultado:** Un documento de compliance claro y diagramas conceptualizados correctamente antes de su trazado manual.

**Declaración final:**
Comprendo línea por línea el código y la arquitectura documentada en esta fase, y estoy en plena capacidad de defender, modificar o explicar estas implementaciones sin asistencia de IA.