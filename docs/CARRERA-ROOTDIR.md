# Integrazione rootdir Carrera

Esito aggiornato: run39937831656 riuscito. Ramdisk802884 byte, staging
out/target/product/carrera/ramdisk; tre file confrontati con le sorgenti e
con il contenuto cpio. Parser init Q passato. Report in
CARRERA-RAMDISK-RESULT.json e prerelease carrera-public-ramdisk-39937831656.
Non e una boot image e non dimostra il montaggio primo stadio o un boot Q.

## Secondo tentativo: compilazione riuscita, staging distinto

Nel run [39934489950](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39934489950)
il prodotto supera lunch/API23 e compila host_init_verifier e ramdisk in
507,5 secondi, con 47370854400 byte liberi. Il parser nativo accetta init.hi3635.rc.
Il controllo successivo fallisce per fstab.hi3635 assente dalla root di output.

Nel build Q fissato, core/envsetup.mk distingue TARGET_ROOT_OUT e
TARGET_RAMDISK_OUT; con BOARD_BUILD_SYSTEM_ROOT_IMAGE=false il secondo usa
TARGET_COPY_OUT_RAMDISK=ramdisk. core/Makefile impacchetta quel solo staging.
Aggiunte quindi destinazioni esplicite $(TARGET_COPY_OUT_RAMDISK) per i tre
file, mantenendo quelle root per l'integrazione del system Carrera.
Il probe acquisisce TARGET_RAMDISK_OUT dal build, verifica il percorso e
confronta i file realmente installati con quelli dentro il cpio.
Non cambia la geometria boot o la configurazione system-root per superare il test.
Questi tre file restano candidati minimi: mount primo stadio Q, policy e
integrazione completa non sono ancora verificati. Occorre un nuovo run.

## Primo tentativo remoto e correzione

Il run [39930952198](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39930952198)
ha sincronizzato i sorgenti e completato il grafo generico. Il prodotto Carrera
si e fermato prima della compilazione: `Multiple words in a single argument: 23 23`,
in core/product_config.mk:381. product_launched_with_m.mk e device.mk
assegnavano entrambi PRODUCT_SHIPPING_API_LEVEL; l'ereditarieta dei prodotti
Q componeva due valori. Rimossa l'assegnazione in device.mk: rimane la sorgente
canonica [product_launched_with_m.mk](https://github.com/LineageOS/android_build/blob/71a47798ac090b81c6b7db0b5c470f1fa3e604cd/target/product/product_launched_with_m.mk).
Il probe ora verifica esplicitamente che il valore risolto sia esattamente 23.
Occorre un nuovo esito remoto: il tentativo fallito non ha prodotto un ramdisk.

Il prodotto sperimentale ora copia nella root del ramdisk tre file originali
del progetto: init.hi3635.rc, fstab.hi3635 e ueventd.hi3635.rc. Il valore
ro.hardware=hi3635 e stato letto dal dispositivo collegato in recovery;
androidboot.hardware=hi3635 e presente nella command line attiva. Non e stata
copiata la command line della recovery, ne le sue opzioni SELinux.

## Evidenze e scelte

Android Q [rootdir/init.rc](https://github.com/LineageOS/android_system_core/blob/6d27634866be5b646a8cea1f9abeae902fd831e5/rootdir/init.rc)
importa /init.${ro.hardware}.rc e invoca il trigger fs. Il nuovo file contiene
unicamente on fs -> mount_all /fstab.hi3635: nessun anticipo del trigger fs,
nessun servizio stock, comando di flash o trigger di aggiornamento firmware.

Q [init/ueventd.cpp](https://github.com/LineageOS/android_system_core/blob/6d27634866be5b646a8cea1f9abeae902fd831e5/init/ueventd.cpp)
legge esplicitamente /ueventd.${ro.hardware}.rc. Il file .carrera.rc.reference
precedente non era caricato automaticamente con hardware=hi3635: resta solo
riferimento storico e non viene copiato nel ramdisk.

System, cache e userdata usano i percorsi by-name del CRR-L09 osservati dal
telefono; nessun indice di un altro dispositivo. System e in sola lettura.
Le opzioni ext4 e encryptable=footer di userdata sono mantenute dalla fstab
acquisita. Cache usa nosuid,nodev,noatime e wait,check. Non sono introdotti
formattable, forceencrypt, fileencryption, resize o creazione di partizioni.
L'esecuzione normale di mount/check puo comunque aggiornare un filesystem:
questi sono input per la futura immagine, non comandi eseguiti sul telefono.

Binder/hwbinder/vndbinder mantengono le consuete autorizzazioni Unix Android.
Ion0664 system:system, Mali00666 system:system e fb20660 system:system derivano
dai metadati ueventd della boot acquisita. Non dimostrano che il kernel o le
regole SELinux Q permettano l'uso effettivo. Il file e intenzionalmente limitato
a questi nodi; radio, camera, audio e altri dispositivi richiedono integrazione.

## Verifica e limiti

Cinque test di contratto controllano mappa by-name, cifratura non forzata,
assenza di autoformattazione, unica azione init, permessi acquisiti e
corrispondenza dei nomi copiati. Suite totale:61 test,60 passati,1 skip.
Non e stato eseguito il verificatore nativo host_init_verifier su questi file,
ne una build completa del prodotto Carrera. Il sorgente Q del verificatore
(blob84077291c979f38670383f3fb53b009fc3363fc9) e stato consultato: usa
host_init_verifier <init rc file> [passwd file], una futura verifica nativa.

Il prodotto mantiene TARGET_NO_KERNEL=true: questa modifica da sola non
costruisce boot.img. Mancano ancora policy enforcing Carrera, configurazione
USB/ADB e gestione energia specifiche, servizi/HAL restanti, revisione del
firmware touchscreen nel kernel e packaging boot. Nessuna prova di boot Q
eseguita e nessuna recovery/partizione modificata.

Il job system generico gia in corso usa lineage_arm64 e non incorpora questa
rootdir Carrera. Non bisogna confondere quella base con il prodotto del telefono.

## Revisione FreeLLMAPI

Gateway locale, modello dots-studio/dots-3-note-preview:free,2871 token dichiarati,
costo dichiarato0. Risposta locale out/freellmapi/runtime-rootdir-review.json.
Scartati suggerimenti incoerenti con dati e fonti: riteneva assenti percorsi e
flag gia forniti, proponeva forcefencrypt e un trigger fs prematuro, servizi
fittizi e destinazioni PRODUCT_COPY_FILES basate sul percorso assoluto
TARGET_ROOT_OUT invece della destinazione relativa root/. Sono confermate
come lavoro ancora necessario l'integrazione HAL e la policy SELinux.

## Prova remota dedicata

Aggiunto il prodotto esplicitamente distinto lineage_carrera_public-userdebug.
Eredita la configurazione Carrera ma omette soltanto i prebuilts Huawei nel
target pubblico; il prodotto normale lineage_carrera continua a richiederli.
Non viene creato alcun HAL fittizio e il target pubblico non e una ROM.
Tre test aggiuntivi controllano questa separazione e il rifiuto del download locale.

android-carrera.yml tenta una build Soong reale di host_init_verifier e ramdisk
con questo prodotto, verifica l'init attraverso il parser nativo Q (le azioni
sono stub nel verificatore, non eseguite), poi confronta hash dei tre file
sorgenti, dei file installati nella root e delle voci nel cpio generato.
Solo in caso di successo conserva una prerelease del ramdisk di sviluppo
pubblico con report e manifest. Nessun kernel, DTB o blob Huawei incluso.
Non e un'immagine di avvio: non deve essere installato o avviato sul telefono.
Timeout lavoro75min, riserva12GiB per la build Carrera, runner standard pubblico.
Il primo sync/grafo generico e riutilizzato solo all'interno della stessa VM.
La prova e appena predisposta: un esito nativo riuscito non e ancora verificato.
