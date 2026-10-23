# Prova hardware e limite del bootloader — 23 ottobre 2026

## Sonda nativa realmente eseguita

native/kernel_readonly_probe.c e stato compilato in un ELF ARM64 statico di
2792 byte, SHA256 2700dca7dfcc5ec70086c97154d01b6a7c20f5556e6da99ec4ebe8c68b100a8d.
Eseguito nella /tmp tmpfs di TWRP; hash confrontati prima dell'esecuzione e
file temporaneo rimosso. Solo query kernel, nessun accesso ai dati personali.

Risultati: kernel 3.10.74-gfa6dc6d, macchina aarch64, Binder protocollo8,
framebuffer 1080x1920 con32bpp. Aperture in lettura di ION e Mali riuscite;
nessun ioctl GPU/ION o lettura di input/framebuffer. Mancano /dev/hwbinder e
/dev/vndbinder (ENOENT), getrandom e memfd_create restituiscono ENOSYS.
Questo riguarda il kernel recovery esistente, non il nuovo diagnostico o Q.
Il precedente uname armv7l proveniva dall'ambiente32bit della recovery.

Compilazione riproducibile: scripts/build_native_probe.py con clang19 e un
linker LLD. E stato scaricato solo il pacchetto Debian lld19 di1374952 byte,
SHA256 756a805e8811d527dd2b5417f016c9342b8631fa9c1ddcd56265c13ae33bf3a4,
estratto in out/tools/lld19 senza installazioni globali. Il builder non accede
al telefono. FreeLLMAPI ha revisionato altri passaggi; due tentativi di
generare la sonda sono falliti per timeout/429, quindi nessun loro codice e
stato eseguito.

## Candidato locale per il solo test del kernel

scripts/prepare_ram_kernel_test.py combina il kernel diagnostico compilato nel
run39937087192 con il ramdisk TWRP ufficiale gia posseduto. Prima verifica:
SHA256 del prefisso recovery ufficiale, ricostruzione originale bit-identica,
offset/flag ARM64 invariati, configurazione diagnostica, controllo firmware
touch disattivato, checksum dei componenti e ID SHA1 boot legacy.

Candidato locale:26003456 byte,
SHA256 2b72f909ffa67f75d6883a533eec47488466b09fb334611f916ce97c424ff27b.
Contiene TWRP e non viene pubblicato nel repository. Il ramdisk e la command
line permissiva sono preservati esclusivamente per il test recovery: non sono
una ricetta Android10. Il builder non avvia e non scrive nulla sul telefono.

## Tentativo RAM e rientro verificato

Con utente presente e VolumeSu coordinato per il rientro, sono stati eseguiti
reboot verso bootloader, query informative e un singolo fastboot boot.
Huawei conferma unlocked e max-download-size471859200. Il trasferimento del
candidato termina OKAY; Booting restituisce FAILED, Command not allowed.
Il nuovo kernel NON e stato eseguito. Non dedurre da questo un'incompatibilita
del kernel: il comando di avvio e stato rifiutato dal bootloader.

Nessun flash, unlock o erase eseguito. Riavvio standard con VolumeSu e rientro
in TWRP2.8.7.0/kernel3.10.74-gfa6dc6d confermati via ADB. La recovery installata
e rimasta quella originale. Non ripetere il test RAM o provare comandi OEM
casuali. Un test persistente richiede un piano separato su immagini complete,
geometria, recupero e verifica dell'integrazione; aggiornare TWRP non abilita
automaticamente il comando fastboot boot del bootloader.

Nota operativa: fastboot devices -l espone un descrittore non standard senza
etichetta fastboot. E stato necessario selezionare il trasporto USB usb:BUS-PORT
ricavato dinamicamente. Non fissare quel valore nei comandi. Le query standard
product/unlocked sono rifiutate; oem get-bootinfo e la query max-download-size
hanno risposto. Non fidarsi del solo exit code di getvar: alcuni FAIL qui
restituivano0. Nessun identificativo individuale e pubblicato.
