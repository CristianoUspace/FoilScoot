# FoilScoot v1.3 — IMU via Wi-Fi e registrazione sul laptop

Questa versione crea una rete autonoma sulla ESP-WROOM-32 e registra sul laptop. La pagina web, i grafici e il client funzionano senza Internet. Radio, servi e motori restano esclusi.

## 1. Caricare lo sketch

1. Aprire `FoilScoot_WiFi/FoilScoot_WiFi.ino` con Arduino IDE.
2. Copiare **la cartella `src` completa del progetto funzionante** nella cartella `FoilScoot_WiFi`, accanto al file `.ino`. Non è inclusa in questo pacchetto perché nel materiale fornito c'era soltanto lo sketch. È la stessa dipendenza della versione IMU + LED già provata.
3. Selezionare la stessa scheda e porta usate nel test precedente e caricare.
4. Accendere con IMU ferma e in piano, Z verso l'alto. Dopo 3 secondi di attesa iniziano circa 3–6 secondi di assestamento e calibrazione.

Pin mantenuti: LED warning esterno GPIO 23, LED integrato GPIO 2; `Wire.begin()` conserva i pin predefiniti della board selezionata. Modulo MPU6050 all'indirizzo `0x68`. Range invariati: ±2 g e ±500 °/s. La frequenza I2C passa da 1 MHz a 400 kHz; lettura e invio sono ora a 100 Hz nominali. I coefficienti dei filtri vengono calcolati dal tempo reale trascorso, usando le costanti di tempo dei filtri originali a 2 kHz. Questo non rende equivalenti le prestazioni di campionamento: la nuova acquisizione va verificata sulla tavola.

## 2. Collegare il laptop

- Rete: **FoilScoot-IMU**
- Password: **FoilScoot32**
- Indirizzo scheda: **192.168.4.1**
- Se Windows segnala “nessun Internet”, restare collegati: è previsto.

È consentito un dispositivo Wi-Fi alla volta. Il programma Python comunica in TCP sulla porta 8765. Non occorre un router.

## 3. Avviare il client

Aprire `FoilScoot_Laptop/Avvia_FoilScoot.cmd`. Si apre il browser su **http://127.0.0.1:8080**. Tenere aperta la finestra del programma.

Il client richiede Python 3.10 o successivo, senza pacchetti aggiuntivi. Il launcher prova il comando `py`, poi `python`, poi il runtime Python incluso in questa installazione di Codex, se disponibile. In alternativa, da una console nella cartella del client: `python client.py`.

Il client si riconnette automaticamente alla scheda. I grafici mostrano gli ultimi 10 secondi anche prima di registrare; la visualizzazione si aggiorna circa 5 volte al secondo, mentre il CSV conserva tutti i campioni ricevuti della sessione. Nulla viene caricato online.

- **Avvia registrazione**: crea un file, richiede l'avvio alla scheda e attende conferma. Il LED esegue la sequenza di sincronizzazione.
- **Segna evento / LED**: salva un marcatore e ripete la sequenza, senza interrompere l'acquisizione.
- **Stop e salva**: acquisisce anche la sequenza LED finale, poi chiude il CSV. Attendere “COMPLETED” nel registro.
- **Ricalibra IMU**: disponibile fuori registrazione; appoggiare il sensore in piano e lasciarlo fermo. La finestra richiede conferma per evitare di ricalibrare involontariamente.

Durante un comando/sequenza i pulsanti attendono la conferma. Chiudere la pagina non interrompe la registrazione. Per terminare normalmente: Stop e salva, poi Ctrl+C nella finestra Python. Una chiusura improvvisa o un'interruzione di alimentazione può perdere le ultime scritture; il file viene scaricato dal buffer circa ogni secondo, e sincronizzato su disco alla chiusura normale.

## Codici LED

Il warning è il LED esterno su GPIO 23, attivo alto come nello sketch originale.

| Sequenza | Significato |
|---|---|
| Acceso durante calibrazione | Lasciare IMU ferma e in piano |
| 2 flash brevi, ripetuti con pausa | Creazione rete fallita: leggere seriale e riavviare |
| 3 flash brevi, ripetuti con pausa | IMU assente, errore di lettura o calibrazione non accettata |
| 2 flash lunghi da 500 ms, una volta | Client Python collegato e handshake ricevuto |
| 2 flash da 120 ms + 1 da 500 ms | Sincronizzazione video di START, MARK o STOP |
| Spento | Nessun pattern in corso; controllare HMI per lo stato registrazione |

Il LED integrato continua a dare un breve impulso ogni 2 secondi. Gli errori hanno priorità sul pattern di connessione; in caso di errore rete e IMU insieme il warning mostra l'errore rete. Il collegamento Wi-Fi di Windows da solo non fa partire la sequenza “client collegato”: deve essere attivo il programma Python. Per registrare il video inquadrare il LED esterno, non il LED verde di alimentazione del modulo MPU6050.

La calibrazione verifica la connessione, il completamento delle letture, la variabilità di accelerometro/giroscopio e la plausibilità della posizione. Soglie iniziali: deviazione standard per asse ≤0,025 g e ≤0,8 °/s; media gyro entro ±5 °/s; norma del vettore accelerometrico medio tra 0,75 e 1,25 g, senza vincolo sui singoli assi. Sono controlli euristici, non una certificazione della calibrazione: movimenti molto lenti o accelerazioni costanti possono non essere riconosciuti. I codici `CAL_MOVING`, `CAL_ACCEL_NORM`, `CAL_GYRO_BIAS`, `IMU_NOT_FOUND` e `I2C_READ_FAILED` compaiono nell'HMI. Correggere posizione/collegamenti e premere Ricalibra.

## CSV e timestamp

I file sono salvati in `FoilScoot_Laptop/registrazioni`, con nome del tipo `FoilScoot_20260927_103000_123456_ab12cd.csv`. Il suffisso evita collisioni. Ogni nuova registrazione crea un nuovo file.

Il CSV usa virgola come separatore, punto decimale e codifica UTF-8; in Excel italiano importarlo scegliendo il separatore virgola.

| Campi | Significato |
|---|---|
| `row_type` | `data` per campioni, `event` per marcatori e fine sessione |
| `session_id`, `boot_id` | Identificativo registrazione e avvio della scheda |
| `device_us` | Tempo monotono ESP32 a 64 bit, dall'avvio; campioni marcati all'inizio della lettura I2C |
| `session_s` | Secondi dal comando START accettato dalla scheda |
| `received_utc`, `received_local` | Data/ora di ricezione sul laptop, con fuso esplicito |
| `received_monotonic_ns` | Orologio monotono del laptop, indipendente dalle correzioni dell'ora civile |
| `sequence` | Progressivo dei campioni dall'avvio scheda; include anche l'anteprima |
| `missed_slots_total` | Scadenze di acquisizione saltate dall'avvio scheda, non soltanto dalla sessione |
| `acc_x_g`, `acc_y_g`, `acc_z_g` | Accelerazioni filtrate in g, inclusa la gravità; offset accelerometrici non corretti |
| `gyro_x_dps`, `gyro_y_dps`, `gyro_z_dps` | Velocità angolari calibrate e filtrate in gradi/s |
| `event`, `led` | Nome evento e stato LED 0/1, se comunicato dalla scheda |

Le righe aggiunte dal laptop, come `COMPLETED` o `INTERRUPTED_CONNECTION_OR_IO`, non inventano un timestamp ESP32: `device_us` e `session_s` rimangono vuoti. Il timestamp di ricezione è assegnato alla decodifica della riga, quindi comprende ritardi di Wi-Fi, buffer e programma. Non è una misura del momento fisico di acquisizione e non sincronizza gli orologi tra laptop ed ESP32.

## Video

Avviare prima il video. Inquadrare il warning mentre si preme Avvia registrazione; riprenderlo anche durante Stop e salva. Nel CSV le righe `START_LED_ON/OFF`, `MARK_LED_ON/OFF` e `STOP_LED_ON/OFF` contengono il tempo ESP32 rilevato subito dopo la scrittura del GPIO, prima dell'invio di rete. `START_SYNC_DONE`, `MARK_SYNC_DONE` e `STOP_SYNC_DONE` delimitano il completamento dei pattern.

Associare un fronte acceso nel video al corrispondente evento per allineare le due timeline. Un riferimento a inizio e fine consente di stimare lo scostamento progressivo tra gli orologi. La precisione resta limitata dai fotogrammi, dall'esposizione video e dai tempi di esecuzione del firmware; non è una sincronizzazione hardware. Il programma fornisce i marcatori, non esegue ancora l'allineamento automatico del video.

## Interruzioni e qualità della registrazione

La sessione viene chiusa e segnalata come interrotta se cade la connessione, la scheda si riavvia, arriva un errore IMU o si verifica un errore di scrittura. La riconnessione serve l'anteprima: **non riprende automaticamente la vecchia registrazione**. Riavviare esplicitamente una nuova sessione.

TCP mantiene ordinati i messaggi, ma può bloccare temporaneamente l'invio. Non c'è memoria di registrazione a bordo e non si recuperano misure durante una disconnessione. La scheda sorveglia i messaggi del client e lo scollega dopo 8 secondi di silenzio; il laptop rileva 6 secondi senza messaggi (15 durante la ricalibrazione). Il contatore “slot saltati” segnala parte dei ritardi di campionamento; per valutarli usare anche le differenze tra `device_us` successivi, attese intorno a 10000 µs. I 100 Hz sono un obiettivo nominale.

Segni confermati sulla tavola: AccX positivo a prua alta; AccY positivo con bordo destro basso; GyroZ positivo per rotazione antioraria vista dall'alto. Questa versione non calcola ancora rollio, beccheggio e imbardata in gradi.

## Verifiche eseguite e prova sulla scheda

Client verificato con un simulatore TCP: messaggi frammentati, avvio, marcatore, stop, calibrazione, CSV, disconnessione, controllo sequenze ed errore IMU. Verificati anche gli endpoint web e il blocco delle richieste di controllo prive del token della pagina. La verifica software non sostituisce la prova del collegamento reale.

Il firmware non è stato compilato né caricato da questa sessione: la libreria locale originale non è allegata e la cartella degli strumenti Arduino installati non è accessibile. Sul dispositivo verificare per prima cosa connessione, pattern LED, 30 secondi di registrazione a tavola ferma, poi rollio/beccheggio, Stop e presenza degli eventi nel CSV. Verificare la perdita della connessione in una sessione separata.

Riferimenti tecnici: [API Wi-Fi Espressif](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html), [mappa registri MPU6050 di TDK/InvenSense](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map.pdf).


## Correzione v1.1 — calibrazione

Non si richiede più X/Y quasi a zero: una IMU ferma ma inclinata può essere accettata. La procedura corregge soltanto lo zero del giroscopio. L'accelerometro conserva il vettore di gravità effettivamente misurato; non viene forzato a (0,0,1) dalla posa di avvio. Una calibrazione degli offset accelerometrici richiederà una procedura separata con più orientamenti. Questo può cambiare i valori a riposo rispetto al primo sketch, che sottraeva gli offset in una sola posa.

Dopo un secondo di assestamento vengono raccolti 400 campioni. Le soglie di stabilità restano 0,025 g e 0,8 °/s di deviazione standard: non sono state allargate alla cieca. La seriale stampa sei righe `CAL AccX/.../GyroZ` con media, deviazione standard, soglia e indicazione `INSTABILE`, poi norma accelerometrica ed esito. Se compare ancora CAL_MOVING, inviare tutte queste righe dopo una prova su un piano rigido, con cavi fermi. Il solo codice CAL_MOVING non dimostra che il sensore sia stato mosso: può indicare anche rumore o vibrazioni.

Il client attende fino a 15 secondi per la conferma dei comandi. Start si abilita dopo calibrazione riuscita; Stop solo durante una registrazione attiva. Aggiornare anche client.py e riavviare il programma Python.

Questa revisione è stata verificata con i test del client simulato; la nuova calibrazione non è ancora stata provata sulla scheda fisica né compilata in questa sessione.


## Correzione v1.2 — pulsanti web

Eliminati i gestori onclick inline e il nome command: i pulsanti ora usano addEventListener e sendControlCommand, evitando conflitti di nomi nel contesto degli elementi HTML. Verificati i quattro pulsanti con test JavaScript e ripetuti i test TCP/CSV del client. Rispetto alla v1.1 basta sostituire FoilScoot_Laptop/index.html e ricaricare la pagina con Ctrl+F5; firmware e client.py non cambiano.


## Client v1.3 — console diagnostica

La console mostra automaticamente ora e livello dei messaggi: tentativi di connessione, handshake, cambi di stato IMU, comandi ricevuti dalla pagina e inviati alla ESP, eventi LED, apertura e chiusura CSV con percorso e numero di campioni, errori e riconnessioni. Ogni 5 secondi, durante il collegamento, una riga VIVO riporta frequenza di ricezione sul laptop, eta dell’ultimo campione e contatori della sessione. La frequenza di ricezione include gli effetti dei buffer e non misura direttamente la frequenza di acquisizione ESP. I contatori CSV restano quelli dell’ultima sessione anche in anteprima. Nessuna stampa per singolo campione o per aggiornamento periodico della pagina. Per PING e stack trace degli errori avviare `python client.py --debug`. Basta aggiornare client.py e riavviare il programma; firmware invariato.
