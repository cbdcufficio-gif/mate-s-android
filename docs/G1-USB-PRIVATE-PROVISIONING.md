# USB diagnostica autenticata: contratto privato

Le fixture verificano i selettori e il fallback Q, non la periferica USB.
Le proprietà candidate restano NON applicate: ro.adb.nonblocking_ffs=false e
sys.usb.ffs.aio_compat=true. Un persist.adb.nonblocking_ffs precedente prevale:
non ignorarlo nella futura diagnosi.

## Sequenza da verificare prima del candidato

1. Root effettiva dopo first_stage_mount/switch-root disponibile; /dev montato.
2. Creazione /dev/usb-ffs/adb con permessi e label adbd definiti dalla policy.
3. Mount FunctionFS, alias f_ffs/aliases=adb, proprietà legacy android_usb coerenti.
4. Avvio adbd autenticato; descrittori registrati e sys.usb.ffs.ready=1.
5. Solo il trigger di ready abilita il gadget; provare arresto/riavvio servizio
   nei futuri test autorizzati, evitando doppio bind e readiness anticipata.

TWRP Carrera ha mostrato in sola lettura FunctionFS, alias adb e gadget
CONFIGURED. Non prova che Q abbia identica sequenza, label o disponibilità AIO.

## Chiave personale, fuori dal repository

La futura preparazione privata deve ricevere esplicitamente la sola chiave
pubblica del proprietario, verificarne il formato e ottenere un'immagine
privata separata. Nessuna chiave di prova/default condivisa nel prodotto.
Il consumer Q legge /adb_keys e /data/misc/adb/adb_keys: senza /data/UI usare
/adb_keys nella ROOT EFFETTIVA dopo switch-root, con file context adb_keys_file
confermato sulla policy candidata e modalità/ownership coerenti col consumer.
Verificare sul contenitore finale percorso, contenuto e label; mettere il file
soltanto nel vecchio ramdisk non soddisfa il contratto. Non scrivere nel device
con gli strumenti di questo progetto. Nessuna chiave privata va letta/coperta.
Conservare ro.adb.secure=1; nessun adbd root/insecure o TCP aperto come scorciatoia.

## Prove future richieste

Chiave autorizzata accettata; chiave differente rifiutata; chiave assente non
apre una shell; indisponibilità di /data non interrompe la diagnostica prevista.
Label/AVC e permessi vanno verificati sul kernel candidato enforcing. USB,
autenticazione e init devono fallire in modo osservabile e senza scrivere dati.
Questi test hardware restano separatamente autorizzati; nessun risultato runtime
è implicato dalle fixture host o dall'attuale TWRP permissive.
