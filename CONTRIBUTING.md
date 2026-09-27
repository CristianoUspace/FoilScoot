# Contributing

Describe your ESP32 carrier, MPU6050 breakout, toolchain versions, wiring and mounting when reporting results. Include steps to reproduce and a minimal anonymized CSV where useful. Do not commit personal recordings or credentials.

Keep baseline imports traceable. Identify behavior changes separately from documentation and packaging. Preserve third-party copyright notices. Run `python -m unittest discover -s tests -v` for Python changes; firmware changes also need compilation and relevant bench tests.

Proposed pumping metrics should document units, assumptions, filtering, timing quality and validation against real recordings before being presented as training measures.
