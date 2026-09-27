# Recording and calibration

Use Python 3.10+; only the standard library is needed. The Windows launcher tries `py`, then `python`, then an optional local Codex runtime. The portable command is `python desktop/client.py`. Options include `--host`, `--port`, `--web-port`, `--output`, `--no-browser`, and `--debug`.

Keep the sensor still during calibration. Startup gyro bias is corrected; accelerometer offsets are not calibrated and gravity is retained. The v1.5 implementation allows a stationary tilted pose. Calibration checks variability, gyro bias and acceleration norm; passing is not proof of perfect calibration. `Ricalibra IMU` recalibrates outside recording.

Start video before recording and include the external GPIO23 LED in frame. Start, mark and stop produce two short flashes and one long flash, with corresponding CSV events. Align a visible edge with its matching event; start and end references help estimate clock drift. Alignment is manual and limited by frame timing and firmware execution.

| Control | Meaning |
|---|---|
| Avvia registrazione | Create a new CSV and request START |
| Segna evento / LED | Mark and flash without stopping acquisition |
| Stop e salva | Record the final LED pattern, then close the CSV |
| Ricalibra IMU | Recalibrate while not recording |
| Chiudi FoilScoot | Shut down after recording and pending commands finish |

Wait for command acknowledgement before the next action. Closing the browser does not stop recording. Wait for `COMPLETED`, then close via the page or Ctrl+C. A disconnection, reboot or IMU error interrupts the session; reconnection restores preview but does not resume that CSV. Start a new session explicitly.

The preview holds about ten seconds; the CSV retains received session samples. Files flush periodically and synchronize on normal close; sudden shutdown can lose recent writes. Sampling is nominally 100 Hz, not hard real time. The missed-slot counter and device timestamp intervals help assess timing.

Battery monitoring is enabled in the latest owner-supplied sketch with a 22 kΩ / 10 kΩ divider. Enabled measurements average 32 readings spaced at least 32 ms apart; the timestamp marks completion of the average. The UI hides stale voltage after four seconds or disconnection. Invalid readings have no CSV voltage. Disabled messages in the original firmware carry no session ID and therefore are not logged as session battery rows.

The original notes report AccX positive with bow up, AccY positive with right edge down and GyroZ positive counterclockwise viewed from above. Verify these conventions for your mounting; no mounting geometry is bundled.
