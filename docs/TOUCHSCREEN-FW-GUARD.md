# Controllo degli aggiornamenti firmware touch nel kernel diagnostico

Sorgente pubblico Huawei/Hi3635 fissato a
`3fe1625bed89c034996842c1af696ba9bc50d8a9`. Il framework in
drivers/huawei_platform/touthscreen/huawei_touchscreen.c invoca
try_update_firmware durante ts_init quando il boot non e recovery.
Il comando TS_FW_UPDATE_BOOT chiama chip_fw_update_boot; Synaptics collega
questo callback a synaptics_fw_update_boot, che include il percorso S3718.
Esistono inoltre il comando SD e l'attributo sysfs fw_update_sd.

La patch introduce CONFIG_HUAWEI_TS_FW_UPDATE, bool con default y per mantenere
il comportamento vendor nel profilo stock. Il frammento android10-diagnostic
lo imposta n. Quando e disattivato:

- ts_init non accoda il comando automatico di aggiornamento firmware;
- i callback boot/SD restituiscono EOPNOTSUPP prima di invocare il driver;
- la scrittura all'attributo fw_update_sd viene rifiutata prima di accodarla.

Non vengono disabilitati chip detection, input, IRQ, calibrazione o watchdog.
Questo descrive i percorsi del framework modificati: non e un audit completo
di ogni scrittura possibile nei driver panel, negli strumenti debug o negli
altri servizi. Il funzionamento del touch con la patch richiede prova hardware.

## Prove riproducibili

configs/kernel-touch-update.json fissa gli hash delle due sorgenti risultanti
e della patch. build_kernel.py accetta solo queste modifiche e il precedente
fix Immersion; verifica anche il valore effettivo del nuovo controllo dopo
olddefconfig, y per stock e n per android10-diagnostic.

check_touchscreen_guard.py compila tre corpi di funzione reali del sorgente
corretto con il controllo acceso e spento. I callback con controllo acceso
propagano gli errori del driver; da spento non effettuano chiamate al driver
ne alla coda. Prova host passata con ASan/UBSan, senza eseguire firmware.
Il workflow kernel ripete la prova e compila entrambe le Image ARM64.
La nuova compilazione completa e ancora necessaria prima di usare il kernel.

Revisione FreeLLMAPI via gateway locale: cohere/north-mini-code:free,
2019 token, costo dichiarato 0. Scartati i suggerimenti di riallocare fw_name
senza verificarne il tipo, spostare il controllo recovery gia precedente alla
chiamata e riordinare il watchdog fuori dal contesto: non dimostrati dagli
estratti. Il nuovo controllo e verificato dal codice e dalle prove, non dalle
conclusioni del modello.

## Acquisizione hardware attuale

TWRP risponde come CRR-L09/carrera/hi3635 e usa kernel 3.10.74-gfa6dc6d,
diverso dal kernel stock acquisito 3.10.86 e dalle Image di sviluppo.
Presenti /dev/binder, /dev/ion, /dev/mali0 e fb0/fb1/fb2; hwbinder e vndbinder
assenti nella recovery. Il framebuffer fb0 riporta hisifb0, 1080x3840 virtuali.
Il touch e esposto come huawei,touchscreen, con input event4. Questi sono dati
di TWRP, non prove che Android Q funzioni. Inventario completo locale in out/.

Il catalogo [TWRP ufficiale Carrera](https://dl.twrp.me/carrera/), verificato
il 23 ottobre, elenca solo twrp-2.8.7.0-carrera.img. Non e stato trovato li un
aggiornamento ufficiale; la recovery collegata permette gia l'acquisizione.
Nessuna recovery o partizione e stata modificata.
