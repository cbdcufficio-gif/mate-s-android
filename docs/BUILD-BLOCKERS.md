# Distanza dalla ROM completa — aggiornamento 23 ottobre

## Ultima verifica remota — 23 ottobre 2026, 12:20 UTC

Il run [39949624600](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39949624600) ha superato la compilazione del ramdisk Carrera e il parser init Q: 802.915 byte, 510,5 secondi, 47.370.498.048 byte liberi. Il job ha concluso in errore solo al momento della prerelease: il commit del run era indietro rispetto a main su .github/workflows/android-carrera-system.yml; l'API Release ha restituito 403 perché in questa situazione richiede Workflows: write. Il GITHUB_TOKEN non può ricevere tale permesso. Il retry del run è stato richiesto in cancellazione. Il run 39951112143, sul commit 65a89717, è in coda. Il successivo commit b27ae260 aggiorna solo rapporti e checksum; i workflow sono invariati. Questa prova non crea una boot image né verifica il telefono.


## Risultati attuali

Kernel ARM64 con controllo firmware touch compilato e conservato nella
prerelease hi3635-development-kernels-39937087192. Moduli grafici Q con patch
callback compilati ARM32/ARM64 nel run39933540063. Ramdisk pubblico Carrera
compilato e verificato nel run39937831656. Sonda ARM64 realmente eseguita
in TWRP: protocollo Binder8 e framebuffer confermati. Dettagli e hash nei
rapporti accanto a questo file.74 test locali:73 passati,1 skip.

La build generica 39927971028 e stata fermata dal guard interno della fase
system dopo 7201 secondi (`TIME_BUDGET_REACHED`); restavano 25,8 GB liberi.
La build specifica Carrera 39942073472 era ancora in corso alla verifica delle
11:50 UTC. Il prossimo run Carrera estende il limite della fase a 10800 secondi
e conserva la riserva disco di 8 GiB. La suite locale corrente e 76 test:75
passano e uno e saltato per cross compiler opzionale. Il probe del prodotto
richiede anche `root/vendor -> /system/vendor` nel root generato.

Il sistema generico sta ancora compilando; predisposta anche una build
del sistema del vero prodotto lineage_carrera_public, senza blob Huawei.
Entrambi sono basi di sviluppo. Nessuna ROM completa o boot Android10 provato.

## Blocchi da risolvere

| Blocco | Stato e lavoro richiesto |
|---|---|
| Kernel sul telefono | Il nuovo kernel non e stato eseguito: il bootloader unlocked riceve il candidato in RAM ma rifiuta fastboot boot con Command not allowed. Rientro TWRP originale verificato. Non ripetere lo stesso test o usare comandi OEM casuali. |
| Sistema Carrera | Completare e controllare la build pubblica specifica; verificare moduli, link `/vendor` e limiti partizione. L'ispezione indipendente del filesystem ext4 e il caricamento hardware restano aperti. Il sistema generico non va rinominato in ROM Mate S. |
| Boot e mount | Il rootdir Carrera monta system/cache con `--early` e userdata a `late-fs` tramite `latemount`, secondo il flusso Q. `first_stage_mount` resta assente: il prodotto usa `/system` separata e non system-as-root. Decisione verificata staticamente; bootloader/DT, policy e mount reali restano da provare. `TARGET_NO_KERNEL=true` esclude ancora la boot image. |
| Packaging Huawei | Boot stock ha coda36864 byte non classificata; dtimage separato HSDT con entry Carrera identificata. Il repack di TWRP e verificato bit-identico soltanto per il suo formato, non risolve il packaging ROM. |
| Grafica reale | Caricamento e risoluzione delle dipendenze Q, namespace, strutture Huawei, allocazione buffer, fence e composizione non provati sul telefono. La sonda apre Mali/ION ma non esegue i loro ioctl o il composer. |
| Altri HAL | Audio, radio, camera, Wi-Fi, Bluetooth, GNSS, sensori, keystore e impronta non sono integrati nel prodotto Q. Servono contratti e servizi reali, non stub che simulino successo. |
| SELinux e stabilita | Kernel supporta formato policy fino30, ma compatibilita con le capability/policy Q non dimostrata. Servono policy coerente/enforcing e prove della matrice hardware. |
| Consegna | Assemblaggio locale con i soli blob Huawei necessari, firmware e dati personali esclusi da GitHub. Nessun download locale dell'intero Android e nessun servizio a pagamento. |

## Vincoli pratici

Il telefono e tornato in TWRP2.8.7.0/kernel3.10.74-gfa6dc6d dopo la prova RAM.
Nessun flash, erase o unlock eseguito. La recovery corrisponde esattamente
all'immagine ufficiale2.8.7.0; non risulta una versione ufficiale piu recente
nel catalogo Carrera. L'utente autorizza un aggiornamento TWRP se necessario,
ma aggiornarla non abilita il comando RAM del bootloader. Prima di un test
persistente occorrono immagini complete, geometria e recupero verificabili.

Usare runner GitHub standard pubblici e release dei soli output pubblici.
I dump boot/recovery/DTB e i blob Huawei restano locali. Non disabilitare
controlli VINTF, hash o policy soltanto per ottenere un risultato verde.
Un esito di compilazione o il vecchio TWRP operativo non certifica Android10.
