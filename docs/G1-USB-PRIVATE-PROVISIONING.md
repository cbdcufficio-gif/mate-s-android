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

## Divergenza osservata nel fallback generico Q

Il file init.usb.rc Q fissato abilita android_usb prima di start adbd e non
attende sys.usb.ffs.ready nell'azione adb/configfs=0. La fixture cattura questo
ordine reale; il candidato Carrera deve attendere mount/alias e readiness,
senza assumere che il fallback generico lo faccia già. L'override specifico
non è installato e rimane un blocco prima del candidato hardware.

## Fonte del segnale ready — verifica statica 30 ottobre

Nel `open_functionfs` Q fissato, `sys.usb.ffs.ready=1` viene impostato dopo
la scrittura di descrittori e stringhe, ma **prima** dell'apertura degli
endpoint bulk OUT e IN. Il segnale è emesso solo nel ramo che reinizializza
il controllo. Una successiva apertura bulk può fallire: ready da solo non
certifica endpoint aperti, trasporto funzionante o autenticazione.

Correzione della precedente ipotesi di reset: init.rc Q importa anche
init.usb.configfs.rc, dove l'azione `init.svc.adbd=stopped` azzera ready senza
condizione configfs. Non assumere assenza di reset nel caso legacy; l'azione
legacy `sys.usb.config=none` non lo azzera direttamente. Servono comunque
verifiche su import effettivo, ordine di scheduling, errore/fine servizio e
cambi configurazione sul candidato. Non aggiungere reset concorrenti basandosi
soltanto sull'assenza nella singola azione legacy.

I quattro sorgenti e digest sono in G1-USB-Q-SOURCE-LOCK.json; la fixture
controlla ordine sorgente, import e trigger, non esegue il motore init. Il
futuro percorso USB deve mantenere ready come segnale di descrittori e
verificare separatamente endpoint, connessione e autenticazione ADB. Nessuna
proprietà, patch al prodotto o chiave personale è stata applicata.

## Azioni init non si sostituiscono automaticamente — 30 ottobre

ActionManager Q scorre tutte le azioni e accoda ogni azione che corrisponde
all'evento; non sostituisce la prima con una successiva avente proprietà simili.
Una fixture compila il corpo Q invariato `Action::CheckPropertyTriggers` e
mostra che, con config=adb, configfs=0 e ready=0, l'azione generica corrisponde
anche se esiste un'azione aggiuntiva condizionata a ready=1. Quest'ultima non
impedisce quindi al fallback generico di abilitare il gadget prima di adbd.
La scansione del gestore e l'estrazione della funzione usano sorgenti fissati,
ma non simulano il motore init completo o il kernel.

Per correggere l'ordine occorre intervenire anche sull'azione generica o sulla
sua selezione effettiva; l'aggiunta isolata di init.hi3635.rc non basta.
Va progettata una sostituzione circoscritta che non alteri altri stati USB e
che non consideri ready=1 una prova di endpoint bulk o autenticazione. Non è
ancora stata applicata alcuna modifica USB al prodotto.

## Candidato sperimentale dell'azione legacy — 30 ottobre

La patch di studio `patches/experimental/lineage-q-usb-ready-candidate.patch`
si applica a init.usb.rc Q fissato. Modifica soltanto l'azione generica adb:
configura il gadget disabilitato e avvia adbd; un'azione distinta, condizionata
anche a ready=1, abilita il gadget e registra lo stato. Le altre azioni USB e
la definizione del servizio adbd restano invariate. La verifica applica il
diff a una copia temporanea del sorgente e rifiuta variazioni a stati non
interessati. Non cambia la root di sistema né è integrata nella build.

È un candidato, non una soluzione runtime: ready segnala solo descrittori,
non endpoint bulk; vanno studiati valori ready obsoleti e scheduling di
stop/restart, montaggio/alias FunctionFS, permessi/label e chiave pubblica
nella root effettiva. Se l'azione genericamente pronta può attivarsi con un
ready vecchio, occorre un controllo esplicito senza creare gare tra trigger.
Non attivare proprietà né autenticazione insicura per aggirare questi blocchi.

## Evento ready accodato — 30 ottobre

Il gestore Q memorizza nome e valore dell’evento. Una fixture del matcher Q invariato mostra un caso condizionale: un evento ready=1 accodato può corrispondere anche quando il valore corrente è già 0, purché le altre proprietà corrispondano. La scansione verifica anche la memorizzazione della coppia nella coda. Non è una prova che tale interleaving sia raggiungibile sul dispositivo né che il gadget si abiliti: occorre verificare scheduling e sincronizzazione effettivi. Un semplice reset della proprietà non dimostra che gli eventi già accodati siano eliminati. La patch resta sperimentale.
