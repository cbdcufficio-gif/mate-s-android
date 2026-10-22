# Acquisizione avvio CRR-L09 — 23 ottobre 2026

Lettura della boot attualmente installata, della recovery e di dtimage da TWRP,
senza scritture su partizioni, mount aggiuntivi o riavvii. I tre SHA256 calcolati
sul dispositivo coincidono con le copie locali. I binari e gli init proprietari
restano in `out/stock-boot-20261023/`, esclusi dalla pubblicazione.

| Partizione | Byte | SHA256 |
|---|---:|---|
| boot | 25165824 | 8474582f3b093036731ac456e327f53c9da1465e174aa43fe8fec666810175e1 |
| recovery | 33554432 | 4c8534b77d525c04713b2cce7c233fde5cd2c34d58b2b94020a9ae0ac4932845 |
| dtimage | 33554432 | c89beda2d1f0bcdd54b680f8602ed4d0db5a1819427287f5943b4530364e6bb3 |

Boot Android legacy, pagina 2048 byte, kernel 21102856 byte a offset2048,
ramdisk gzip 4021800 byte a offset21106688, nessun secondo stadio.
SHA1 legacy (componenti e dimensioni) corrisponde all'ID nell'header.
Il controllo verifica integrita strutturale, non autenticita firmware.
Il ramdisk dichiara `CRR-C900B321_BOOT`, Android6/MRA58K nella fingerprint;
non dimostra da solo che tutto il sistema installato sia stock C432B321.

La coda dopo le componenti allineate misura 36864 byte, di cui36749 nonzero.
Non e stata classificata come firma o padding: potrebbe anche essere residuo
nella partizione. Non eliminarla o ricopiarla in una nuova boot senza chiarirne
il ruolo. Nessun DTB con magic FDT trovato nel payload kernel; esiste invece
la partizione separata dtimage. Vedere DTIMAGE-RESULT.md.

Il ramdisk scompresso e 8137984 byte. Lo script `boot_inspect.py` controlla
limiti, archive newc, nomi, trailer e gzip singolo; legge i testi selezionati
in un report locale senza estrarre percorsi, creare link o eseguire contenuti.
La configurazione kernel incorporata IKCONFIG e stata recuperata localmente: tutti i valori CONFIG coincidono con configs/stock-b321.config (zero differenze). Questo non prova identita dei sorgenti kernel.

I mount stock includono system p38 in sola lettura e cache p34, mentre fstab
contiene userdata con encryptable=footer e zram. Gli init importano servizi
Huawei e selezionano file tramite ro.boardid.product: il file init.71341.rc
contiene il riferimento CARRERA. Sono dati per l'integrazione Q, non file
compatibili da copiare integralmente: include anche servizi di aggiornamento
recovery, cifratura e programmi proprietari da rivedere.

Fonti del formato: [bootimg.h](https://github.com/LineageOS/android_system_core/blob/6d27634866be5b646a8cea1f9abeae902fd831e5/mkbootimg/include/bootimg/bootimg.h)
e [mkbootimg.py](https://github.com/LineageOS/android_system_core/blob/6d27634866be5b646a8cea1f9abeae902fd831e5/mkbootimg/mkbootimg.py).
Il suggerimento FreeLLMAPI iniziale su offset/header/SHA1 era errato ed e stato
scartato in favore del formato sorgente e del digest effettivamente corrispondente.

Nessuna boot Android10 prodotta. La recovery e accessibile adesso e la sua copia
e verificata; il ripristino completo dopo una ROM fallita non e stato provato.
