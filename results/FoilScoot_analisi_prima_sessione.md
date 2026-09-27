# FoilScoot — prima sessione sulla tavola

Fonti: `FoilScoot_20260927_161600_154430_e1f2d3.csv` e `pump foil first session.mp4`, forniti dall'utente. Analisi del 27 settembre 2026. Nessuna modifica ai sorgenti, al firmware o alle registrazioni originali.

## Risultato principale

La tendenza iniziale verso il rollio sinistro è coerente con i dati. Nel seguito la distribuzione del rollio si sposta verso destra, lontano dal fine corsa sinistro dimostrato, mentre aumenta l'intensità delle rotazioni. Questa sessione mostra dunque un cambiamento di strategia durante l'esercizio; non basta a dimostrare un miglioramento di abilità, perché cambiano anche appoggio alla sedia, movimenti volontari e fatica.

Il piede posteriore vicino al pallone può avere poca leva sul **beccheggio**, ma non diventa per questo neutro per il carico, per il rollio o per il lavoro muscolare. Nell'audio viene segnalata fatica alla gamba posteriore già prima dell'annuncio dei tentativi di pump.

## Sincronizzazione e sequenza

Trascrizione automatica locale dell'audio italiano, confrontata con fotogrammi del video e andamento IMU. Non è una trascrizione integralmente verificata a orecchio. Il “GO” è collocato dal riconoscimento vocale a 16,96–17,16 s. Allineamento operativo adottato:

**tempo video ≈ tempo CSV + 17 s.**

È un allineamento provvisorio per riconoscere le fasi, non una sincronizzazione al fotogramma. L'intervallo fra comando START e parola GO resta sconosciuto; non è stato validato il pattern LED nel video. Gli annunci dei fine corsa coincidono con i corrispondenti plateau entro la precisione necessaria a questa lettura. Non è stata stimata una deriva fra i due orologi.

| Video, circa | CSV, circa | Riscontro |
|---|---:|---|
| 0:00–0:06 | prima della registrazione | Annuncio della calibrazione con tavola a terra |
| 0:17 | 0 s | GO |
| 0:19–0:27 | 2–10 s | Spostamento sul pallone; primo grande movimento di pitch |
| 0:29–0:36 | 12–19 s | Salita sulla tavola, con appoggio alla sedia |
| 0:39–0:47 | 22–30 s | Annuncio di tavola circa orizzontale |
| 0:52–0:55 | 35–38 s | Dimostrazione pitch down |
| 0:56–0:59 | 39–42 s | Dimostrazione pitch up |
| 1:00–1:02 | 43–45 s | Dimostrazione roll sinistro |
| 1:04–1:06 | 47–49 s | Dimostrazione roll destro |
| 1:07–1:21 | 50–64 s | Ricerca dell'equilibrio e annuncio di rilascio della sedia |
| 1:30–1:42 | 73–85 s | Descrizione della tendenza sui talloni |
| 1:43–1:50 | 86–93 s | Commento sul guardare avanti |
| 1:59–2:07 | 102–110 s | Fatica alla gamba posteriore, prima del pump dichiarato |
| 2:10–2:20 | 113–123 s | Annuncio dei tentativi di pump |
| 2:20–2:44 | 123–147 s | Ulteriore commento sulla fatica del quadricipite posteriore |
| 2:45–2:53 | 148–156 s | Commento su tavola circa orizzontale e appoggi occasionali ai fermi |
| 3:01–3:06 | 164–169 s | Annuncio dello stop |
| 3:06–3:07 | 169,04–170,32 s | Sequenza STOP elettronica e fine CSV, secondo l'offset provvisorio |

Il video dura 204,50 s, il CSV 170,32 s. Nel CSV non ci sono MARK intermedi: le voci della tabella sono annotazioni ricostruite, non eventi elettronici registrati. La coda della trascrizione ripete una frase di stop: non è usata come ancoraggio indipendente.

## Qualità della registrazione

- 17.014 campioni IMU, 164 letture batteria e 17 righe evento; un'unica sessione e chiusura COMPLETED.
- Sequenza campioni consecutiva: 13426–30439; nessun buco nella sequenza ricevuta.
- Contatore acquisizioni saltate: da 6 a 25, incremento 19. Questo misura slot saltati dal dispositivo, non pacchetti persi in rete.
- Intervallo mediano 10 ms; massimo 62,102 ms. Sette intervalli superano 20 ms. Frequenza media circa 99,9 campioni/s.
- Giroscopio lontano dal range ±500 °/s: massimo assoluto circa 113 °/s.
- Accelerazioni per asse fino a 1,919 g su Y e 1,955 g su Z: poco margine rispetto a ±2 g. Il CSV filtrato non dimostra se ci sia stata saturazione dei campioni grezzi.
- Norma delle accelerazioni 0,371–2,362 g. Una norma sopra 2 g non prova saturazione: il limite è per singolo asse.
- Batteria riportata 8,047–8,094 V, media 8,071 V. Nessuna deduzione di percentuale di carica.

Nota di riproducibilità: lo sketch attualmente presente nel percorso indicato contiene monitor batteria disabilitato e resistenza superiore 27 kΩ. Non coincide quindi con la configurazione descritta dall'utente e con la presenza di misure batteria nel CSV. Non è stato modificato e non viene assunto come copia esatta del firmware usato nel test.

## Angoli: cosa si può leggere

Le inclinazioni mostrate sono stime dall'accelerometro, dopo media mobile centrata di 51 campioni (circa 0,51 s):

`pitch = atan2(ax, sqrt(ay² + az²))`

`roll = atan2(ay, az)`

Segni: pitch positivo = prua alta; roll positivo = bordo destro basso. Zero IMU conservato. Nessuna calibrazione accelerometrica o compensazione dell'allineamento deck-sensore aggiunta.

Nei primi due secondi il sensore è fermo e restituisce circa pitch −5,1°, roll −7,9°, norma 1,036 g. Questa posa non permette di separare inclinazione del terreno, montaggio e offset del sensore. “Calibrato” qui significa soprattutto bias gyro corretto; non certifica il piano geometrico della tavola.

Scegliendo brevi tratti sui plateau associati agli annunci:

| Posizione | Finestra CSV | Stima indicativa |
|---|---|---:|
| Pitch down | 37,5–38,5 s | −15,8° |
| Pitch up | 40,5–41,5 s | +6,6° |
| Roll sinistro | 43,5–44,5 s | −15,4° |
| Roll destro | 46,5–47,5 s | +9,2° |

Sono mediane delle finestre, non estremi meccanici certificati. L'escursione dimostrata è circa 22° in pitch e 25° in roll. La deformazione del pallone e il carico possono cambiare il limite effettivo. Il punto medio dei fermi non equivale necessariamente all'orizzontale.

Durante pump e urti, accelerazione traslazionale e gravità si sovrappongono: non va interpretato ogni picco accelerometrico come inclinazione. Il limite è descritto anche nella [nota Analog Devices AN-1057](https://www.analog.com/en/resources/app-notes/an-1057.html). Per misure dinamiche migliori serve una stima combinata gyro/accelerometro e la verifica dello zero sul deck.

## Equilibrio e deduzioni

**1. La preferenza iniziale per il lato sinistro è visibile.** Nella finestra CSV 55–75 s (video circa 1:12–1:32), il roll apparente mediano è −8,8°, con il 90% dei valori fra −12,9° e −2,3°. È spostato verso il fine corsa sinistro dimostrato. Questo sostiene la tua osservazione; non misura direttamente il peso sui talloni.

**2. Il seguito cambia, ma resta movimentato.** Fra CSV 120–150 s (video 2:17–2:47), il roll mediano è +0,6°, con il 90% dei valori fra −6,0° e +6,2°. La distribuzione si allontana dal fine corsa sinistro. Nelle finestre di confronto più ampie, equilibrio CSV 55–110 s e tentativi di pump 113–155 s, l'RMS del gyro di roll aumenta da 17,5 a 24,0 °/s, circa +37%. È una misura di intensità delle rotazioni, non di frequenza né un punteggio di abilità. La fase finale contiene anche movimenti volontari.

**3. Il piede posteriore non è neutro in tutti i sensi.** Se la linea della forza del piede passa vicino al centro d'appoggio, la leva longitudinale sul pitch è piccola. Può però sostenere molto peso. Lo spostamento della pressione fra tallone e avampiede può ancora produrre un momento di rollio. La fatica riferita è compatibile con un sostegno prolungato; non prova da sola quale percentuale del peso porti quel piede.

**4. La sedia è una parte della meccanica dell'esercizio.** Nei fotogrammi ci sono fasi con mano alla sedia e fasi con braccia libere. L'appoggio può fornire sia forza sia momento stabilizzante. Non si può attribuire ogni cambiamento soltanto alla postura dei piedi. Il video grandangolare consente di identificare gesti e contatti visibili, ma non di misurare con precisione angoli articolari e distribuzione dei carichi.

**5. Stai esercitando equilibrio e controllo su un appoggio deformabile.** Il pallone bloccato permette di isolare alcuni problemi, ma non riproduce le forze idrodinamiche del foil in avanzamento. La sessione non consente di valutare l'efficienza propulsiva del pump. L'IMU da sola non separa in modo univoco flessione delle ginocchia, compressione del pallone, contatto con i fermi e sostegno della sedia.

## Prossimo confronto utile

Una prova breve a condizioni ripetibili chiarirebbe l'effetto della stance: stessa posizione del pallone, stesso uso della sedia e stessa durata; piede posteriore prima sopra l'appoggio e poi leggermente arretrato, mantenendo il sostegno fra i piedi. Segnare posizione dei piedi, annunciare la variante e mantenere per qualche secondo ciascun fine corsa. Prima, verificare un riferimento orizzontale del deck con una misura indipendente.

Il confronto dovrebbe distinguere: posizione media del rollio, ampiezza delle oscillazioni, velocità delle correzioni e tempo con mano alla sedia. Nessuna modifica al firmware è necessaria per iniziare questo confronto.
