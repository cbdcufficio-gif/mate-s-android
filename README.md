# Huawei Mate S CRR-L09 / Carrera — porting Android 10+

Obiettivo: una ROM nativa con le funzioni hardware e le app richieste realmente
provate. La direzione corrente è in [PORTING-DIRECTION](docs/PORTING-DIRECTION.md),
lo snapshot dei gate in [PORTING-STATE.json](docs/PORTING-STATE.json), le evidenze
cronologiche in [STATUS](docs/STATUS.md) e i blocchi prioritari in
[BUILD-BLOCKERS](docs/BUILD-BLOCKERS.md). Gli agenti leggono prima [AGENTS.md](AGENTS.md).

La prima architettura da dimostrare combina kernel Huawei ricompilato con driver
Carrera conservati, backport mirati, sistema Q coerente e HAL legacy adattati.
Il run pubblico system/ramdisk è una base di sviluppo senza HAL Huawei, kernel o
DTB inclusi: anche un esito verde non è una ROM avviabile.

Il kernel diagnostico, gli adattatori grafici Q e il ramdisk sono stati compilati.
Il nuovo kernel e Android Q non sono stati avviati sul telefono. Le prove TWRP
riguardano la recovery esistente. Non manca soltanto confezionare uno ZIP.

## Proseguimento

1. Finire e verificare il run pubblico corrente, senza build duplicate.
2. Verificare configurazione finale, ABI/linker/APEX/policy e correggere l'API di
   lancio nella prossima revisione deliberata; la patch è in
   [docs/deferred](docs/deferred/carrera-launch-api22.patch).
3. Chiarire packaging boot/DT e recupero, poi primo avvio kernel/init/ADB Q.
4. Grafica e input, hardware/telefonia/sicurezza, infine stabilità e consegna.

Geometria osservata, limiti e prove sono in [BOOT-RESULT](docs/BOOT-RESULT.md),
[DTIMAGE-RESULT](docs/DTIMAGE-RESULT.md), [CARRERA-ROOTDIR](docs/CARRERA-ROOTDIR.md)
e [HARDWARE-MATRIX](docs/HARDWARE-MATRIX.md). Sorgenti e toolchain sono fissati in
[sources.lock.json](sources.lock.json); per Android serve anche il manifest
risolto di ciascuna build.

## Risorse e vincoli

Solo runner standard pubblici gratuiti per il grande albero Android; niente sync
completo sul PC. Blob, dump, firmware e dati privati restano locali. I candidati
grafici già acquisiti non devono essere inviati di nuovo. La configurazione
stock Android6/API23 non è l'API originaria del modello, Android5.1/API22.

Nessuno script deve installare immagini o riavviare il telefono automaticamente.
Preservare recovery, DT Carrera, cifratura, guardie SELinux/vendor/ELF e protezione
firmware touch. Non usare immagini/DT di Liszt, GRACE o di un altro Kirin.

## Test degli strumenti

```sh
python3 -m unittest discover tests
```

Questa suite verifica strumenti e contratti documentati, non la matrice hardware
Q. Dichiarare separatamente test passati e skip per toolchain opzionali.
