# ADR 0006 — Curaduría por Queen y laboratorio de proveedores

- **Estado:** aceptado como dirección de trabajo; implementación incremental
- **Fecha:** 2026-08-15
- **Decisor:** owner de RiotQueens.ai

## Contexto

El producto debe escalar varias Queens con modismos y personalidad propios. NotebookLM sirve para generar informes de autodescripción a partir de fuentes curadas; los modelos de runtime pueden confundir bardeo local con contenido inseguro. Qwen dejó además una dirección visual y estructural valiosa, pero su HTML contiene copy y roster que ya no gobiernan el producto.

## Decisión

Cada Queen tendrá un paquete independiente de identidad, voz, glosario, límites y evaluación. La esencia compartida no reemplaza esas diferencias. El benchmark de cada Queen decide si una configuración de modelo puede ser usada con ella. Google AI Studio/Gemma/Ollama se prueban en un laboratorio desacoplado; ninguna integración de laboratorio se publica automáticamente.

Las fuentes creativas se registran por hash y clasificación. Las fuentes madre pueden orientar derivaciones, pero no se convierten literalmente en prompt, asset público o claim sin revisión.

## Consecuencias

- aumenta la trazabilidad y evita que el modelo principal homogenice a todas las Queens;
- exige una batería y un registro por Queen;
- permite comparar OpenRouter, Hugging Face, Google AI Studio y Gemma sin cambiar el dominio;
- mantiene fuera del repo secretos, masters privados y exports autenticados no autorizados;
- requiere completar cuatro paquetes de voz antes de habilitar esas Queens en runtime.
