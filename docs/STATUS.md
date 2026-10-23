Aggiornamento successivo 23 ottobre — rootdir Carrera:

Aggiunti fstab.hi3635, init.hi3635.rc e ueventd.hi3635.rc derivati dai metadati acquisiti, con copia nel ramdisk del prodotto Carrera. Nessuna formattazione o cifratura forzata introdotta. Dettagli e limiti in CARRERA-ROOTDIR.md.

Predisposto android-carrera.yml: target esplicito lineage_carrera_public-userdebug, senza prebuilts Huawei, per compilare il ramdisk e verificarlo tramite gli strumenti nativi Q. Il prodotto normale continua a richiedere i blob locali. Esito della nuova prova non ancora verificato; nessuna boot.img o ROM completa prodotta. Suite locale61 test:60 passati,1 skip.

Aggiornamento 23 ottobre — build effettive e seguito automatico:

- Kernel stock e android10-diagnostic compilati con successo nel run39924712678; hash e limiti in KERNEL-REMOTE-RESULT.md.
- Gralloc ARM64 dichiara modulo0.3 dopo il costruttore, percorso Gralloc0Hal verificato; dettagli in GRALLOC-INITIALIZATION.md.
- Build moduli Q reali riuscita nel run39924712682:14 ELF installati verificati, librerie ARM32/ARM64 e servizi ARM64; export Mali CallStack presenti su entrambe le architetture. Nessuna compatibilita hardware dichiarata.
- Il workflow android-system.yml e partito automaticamente nel run39927971028, ripete i controlli e tenta una system.img generica. Conserva esclusivamente output pubblici in una prerelease esplicitamente non installabile sul Mate S. Nessun blob Huawei e incluso.
- La suite locale ha53 test:52 passati,1 saltato. Nessuna ROM Carrera completa, integrazione hardware completa o prova di avvio Android10.

Aggiornamento 23 ottobre: acquisizione boot/DTB e prova grafo Android; vedere BOOT-RESULT.md e BUILD-BLOCKERS.md.

Aggiornamento 23 ottobre, run Actions 39873522042, commit `277d150a16f391b9964783fcdf922e1fdba0fc5c`:
corretto il target del probe da `aosp_arm64-userdebug` a
`lineage_arm64-userdebug`, che carica il prodotto LineageOS registrato. Il
workflow ha sincronizzato il manifest Android Q fissato a
`c7b3d4b65b79e2e0d6a891547ad138e1fcdafb56` e completato `m -j2 nothing` con
`GENERIC_BUILD_GRAPH_PASSED`. Tempi: sync 516,5 s; grafo 135,1 s. Spazio libero
misurato: 113.009.008.640 byte all'avvio del probe, 51.345.686.528 dopo il sync,
48.843.919.360 dopo il grafo. Log e manifest risolto sono nel run Actions:
https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39873522042.
Il risultato è un grafo Android generico, non il prodotto Carrera: nessun
`systemimage`, `boot.img`, ROM o test hardware è stato eseguito. I 48,8 GB
rimanenti non dimostrano spazio sufficiente per una build completa.
Il run precedente [39865914932](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39865914932)
falliva in `vendor/lineage/build/soong/Android.bp:30` con
`unknown variable '$(PATH_OVERRIDE_SOONG)'`: usava `aosp_arm64-userdebug`, che
non caricava la configurazione del prodotto LineageOS. La sostituzione con il
target LineageOS registrato ha eliminato quell'errore nel run successivo.

Aggiornamento 22 ottobre: [compilazione ARM32/ARM64 degli header e di quattro implementazioni Q](HEADER-EXPERIMENT.md), con 54 import selezionati coperti. Nessuna ROM installabile ancora prodotta.

# Stato verificato — 22 ottobre 2026

## Prosecuzione desktop

Ora i candidati grafici reali sono presenti e tutti e otto sono stati verificati
strutturalmente contro il lock B321. Non occorre reinviare l'archivio richiesto
nella sezione storica più sotto. Nuove evidenze e metodi: ZERO-COST-PLAN.md,
ABI-REVIEW.md e SESSION-20261022.json.

Repository pubblico creato: https://github.com/cbdcufficio-gif/mate-s-android.
Due workflow remoti riusciti: 4 CPU, circa 16 GB RAM e 105,1 GiB liberi dopo
pulizia SDK della VM e installazione cross compiler. Tutti i 21 test passano nel
runner con zero skip. Localmente: 20 passati e uno saltato per cross compiler.
Nessuna build Android completa/moduli Q, boot.img, ROM installabile o prova hardware.

## Risultati precedenti

## Compilato e testato

Kernel Huawei/Hi3635 3.10.86, commit
`3fe1625bed89c034996842c1af696ba9bc50d8a9`, con correzione locale
dell'include Immersion. Due compilazioni complete ARM64 riuscite:

| Profilo | SHA256 della Image |
|---|---|
| Config stock | `7448449bc64a44902c4ab7cb6b4ee279237acd6b3e0c3e25b5e95fa7c75345ce` |
| android10-diagnostic | `46e884abb2959be92238f09611f8d512b9ef405be4bbd6ba453c23a10a91458f` |

La seconda Image misura 21.369.416 byte. La configurazione effettiva ha SHA256
`2d8f144062b9b44b00762ae6d6274e1e7753bc9208d9ab74b3687e0a2e3a65c2`.
Comandi, sorgente e compilatore sono registrati in kernel-build-report.json.
Il sorgente pubblico non è dimostrato identico alla release B321 installata.

19 test automatici riusciti senza skip: parser ELF, GNU symbol versions,
alterazioni di codice/indirizzi, risoluzione dipendenze, controllo symlink/hash,
preparazione grafica sintetica ARM32+ARM64 e audit kernel. Anche 46 librerie
ARM32 reali della recovery sono state lette dal parser. Queste prove non
dimostrano caricabilità dei blob grafici B321 in Android 10.

## Ancora da dimostrare

- Build dei moduli grafici e dell'intero Android; nessun system.img prodotto.
- Loader, namespace, ABI C++, GPU, HWC e ioctl con i blob reali.
- Init, servizi, politica SELinux e VINTF completi di Carrera.
- Packaging Huawei della boot image, coda/firme e selezione del DTB stock.
- Percorso di recupero provato, avvio hardware e tutti i componenti della matrice.
- Supporto fastboot boot: non verificato; nessuna sonda viene proposta.

Il sorgente include un percorso di aggiornamento firmware touchscreen al boot:
va revisionato prima di avviare un nuovo kernel. L'archivio kernel è materiale
di sviluppo, NON un pacchetto installabile. Non flashare le Image fornite.

## Prossimi passaggi

Boot, dtimage e recovery acquisiti in sola lettura dal CRR-L09 il 23 ottobre.
Vedere BOOT-RESULT.md e DTIMAGE-RESULT.md; non occorre richiedere nuovamente
i candidati grafici o il dump boot. Il probe remoto di sync e grafo Android Q
generico è riuscito, con limiti di spazio e tempo misurati. Non equivale a una
build del prodotto Carrera o a una build ROM. La suite locale corrente conta
41 test passati e uno saltato per cross-compiler opzionale.

Android 10 è un primo candidato tecnico. Non si promettono una data di rilascio,
un tetto massimo Android o una ROM completa senza build e prove sul dispositivo.
