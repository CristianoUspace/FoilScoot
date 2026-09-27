# FoilScoot v1.5 — tensione batteria LiPo 2S

Misura del pacco a monte del convertitore. Progetto per la LiPo 2S da 7,4 V nominali / 8,4 V carica. Non usare questo dimensionamento come autorizzazione per pacchi diversi.

## Componenti e collegamenti

- R1: 27 kΩ, 1%, 1/4 W.
- R2: 10 kΩ, 1%, 1/4 W.
- Consigliato: condensatore ceramico da 100 nF tra GPIO34 e GND, vicino alla ESP32.
- GPIO34 deve essere libero: il vecchio ingresso radio non è usato dal firmware attuale.

```text
LiPo + (dopo interruttore generale, prima del convertitore)
      |
    R1 27 kΩ
      |
      +---------------- GPIO34 ESP32
      |                     |
    R2 10 kΩ              100 nF
      |                     |
LiPo − / GND ---------------+------ GND ESP32
```

Le masse devono essere comuni (convertitore non isolato). Il positivo LiPo NON va direttamente al GPIO. A 8,4 V il nodo del partitore vale circa 2,27 V: Vpin = Vbatteria × 10/37. L'assorbimento del partitore a batteria carica è circa 0,23 mA.

Realizzare i collegamenti a batteria scollegata. Verificare al multimetro la tensione del nodo prima di collegarlo alla ESP. L'interruttore generale deve togliere alimentazione sia al convertitore sia al partitore: evitare di lasciare tensione sul GPIO con ESP32 spenta. Per prove USB, scollegare il ramo di misura dalla LiPo se la relativa sequenza di alimentazione non è gestita. Non alimentare contemporaneamente USB e ingresso esterno senza aver verificato il circuito della propria scheda.

## Attivazione

1. Copiare la cartella src del progetto funzionante accanto a FoilScoot_WiFi.ino: la libreria MPU6050 originale non è inclusa.
2. Dopo aver costruito e verificato il partitore, cambiare nel firmware:
   `constexpr bool BATTERY_MONITOR_ENABLED = false;`
   in:
   `constexpr bool BATTERY_MONITOR_ENABLED = true;`
3. Caricare il firmware. Aggiornare client.py e index.html, riavviare Python e ricaricare la pagina. Il pacchetto mantiene il pulsante Chiudi FoilScoot e il launcher v1.4.
4. Confrontare volt indicati e multimetro durante il funzionamento con Wi-Fi acceso. Se necessario impostare BATTERY_CAL_FACTOR = valore_attuale_del_fattore × V_multimetro / V_client e ricaricare. Controllare l'accordo anche a un'altra tensione: un singolo fattore non elimina la non linearità dell'ADC.

Lettura disattivata per impostazione iniziale: senza cablaggio il client mostra “Lettura disattivata”, non una falsa tensione di batteria. I vecchi firmware senza messaggi batteria continuano a funzionare, mostrando misura non disponibile.

## Client, avvisi e CSV

La pagina mostra la tensione del pacco con due decimali (formato di visualizzazione, non garanzia di precisione). Ogni misura è la media di 32 letture distanziate di almeno 32 ms: circa un aggiornamento al secondo; i ritardi di rete o la calibrazione possono rallentarlo. Il tempo ESP32 assegnato al messaggio è quello di completamento della media, non un singolo istante di campionamento.

Soglie iniziali modificabili all'inizio di client.py:
- BATTERY_LOW_V = 7.2: preavviso giallo.
- BATTERY_CRITICAL_V = 7.0: invito rosso a terminare il test.
- Isteresi 0,1 V per evitare continui cambi di avviso vicino alla soglia.

Sono soglie operative conservative per preparare e terminare i test, NON limiti universali di sicurezza o una stima della percentuale residua. La misura è sul pacco intero: non individua una singola cella troppo scarica o sbilanciata. Non sostituisce un allarme per singola cella/BMS e non scollega la batteria. Verificare i limiti del proprio pacco. Non sono aggiunti pattern al LED di sincronizzazione video.

La console segnala i cambi di stato batteria. Se la misura manca per oltre 4 secondi o cade la connessione, il valore non viene presentato come attuale. Valori fuori dalla finestra plausibile 4,0–8,6 V o fuori dal campo ADC previsto risultano “misura non valida”: controllare subito cablaggio, fattore di calibrazione e batteria. Una lettura plausibile non prova che il cablaggio sia corretto.

Durante una registrazione, i CSV includono righe row_type=battery, con device_us, data/ora di ricezione, battery_v e battery_state. Le righe IMU restano row_type=data e conservano i sei canali originali; i due campi batteria sono aggiunti in fondo alle colonne. Un errore di misura ha tensione vuota e stato invalid. Il valore batteria non viene ripetuto artificialmente in ogni campione IMU.

## Verifiche

Passati i test software per soglie, isteresi, lettura disattivata/non valida/scaduta e scrittura CSV. Ripetuti i test TCP con scheda simulata per avvio/stop, marcatori, calibrazione e disconnessione; controllata la sintassi JavaScript. Firmware non compilato o verificato sull'hardware in questa sessione. Confrontare con multimetro e verificare la frequenza IMU dopo l'attivazione ADC.

GPIO34 appartiene ad ADC1; ADC2 interferisce con il Wi-Fi sull'ESP32 classico. Fonti: [documentazione Espressif ADC](https://docs.espressif.com/projects/esp-idf/en/v4.4/esp32/api-reference/peripherals/adc.html), [API analogReadMilliVolts e attenuazione](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/adc.html).
