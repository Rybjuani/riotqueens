# Evaluación de La Bardera

**Estado:** VERIFICADO / en calibración real.

La batería ejecutable es [`scripts/eval_modismos.py`](../../../scripts/eval_modismos.py) y el contrato está en [`scripts/modismo_battery.md`](../../../scripts/modismo_battery.md). Debe separar `PASS`, `HARD_FAIL`, `CAPABILITY_BOUNDARY` e `INFRA_FAILURE`.

`glosariomodismos.md` es la batería normativa de voz de La Bardera. La batería soft sólo sirve como diagnóstico rápido y no puede producir un `PASS`. La evidencia recuperada de la sesión viva de Grok demostró que Llama 3.3 podía pasar el soft y fallar el glosario real, incluso después de inoculación y few-shot.

Un proveedor/configuración pasa cuando completa el glosario sin bloqueos indebidos de voz, sin fuga de identidad, sin truncación y con límites preservados. Mientras el runtime no acepte adjuntos, pedir o prometer ver/recibir PDFs, fotos o archivos también es un fallo: la Queen puede responder con su voz, pero no inventar capacidad. El resultado debe registrar modelo, proveedor, parámetros, commit, fecha y muestra de salida sanitizada. Este resultado sólo habilita a Bardera.
