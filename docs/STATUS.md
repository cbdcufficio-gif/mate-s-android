Stato corrente — 23 ottobre, consegna tecnica:

Aggiornamento operativo, 23 ottobre — mount Carrera e build:

- Il rootdir Q monta system/cache con `mount_all --early` e ritarda userdata a
  `late-fs` con `latemount`, preservando `encryptable=footer`. La scelta dello
  staging separato di `/system` e stata verificata sul sorgente Q; il boot sul
  telefono resta da provare.
- La build generica 39927971028 ha esaurito il limite interno di 7200 secondi,
  non il disco: `TIME_BUDGET_REACHED`, 25,8 GB liberi. La build Carrera
  39942073472 era ancora in corso alle 11:50 UTC e usa ancora il limite
  precedente. Il prossimo run Carrera avra 10800 secondi e la stessa riserva
  disco di 8 GiB.
- Suite locale aggiornata:75 test,74 passati,1 skip per cross compiler
  opzionale. Nessuna immagine Q installabile o boot Android prodotto.

- Kernel con controllo firmware touch: run39937087192 riuscito; prerelease con Image pubbliche/config/report. DiagnosticoSHA3ec66f2b1a20270b101d72374b697dbfb1c178b749781e5580c356b7429b3bb9.
- Moduli grafici Q corretti: run39933540063 riuscito ARM32/ARM64,14 ELF installati; ANDROID-MODULE-PATCHED-RESULT.json.
- Ramdisk Carrera: run39937831656 riuscito,802884 byte, tre file verificati nel cpio; CARRERA-RAMDISK-RESULT.json.
- Sonda ARM64 eseguita in RAM di TWRP: Binder8, display1080x1920x32, ION/Mali aperti; getrandom/memfd assenti nel vecchio kernel.
- Un solo fastboot boot diagnostico: trasferimento OKAY, avvio rifiutato Command not allowed. Nessun flash. Rientro in TWRP2.8.7.0/kernel3.10.74 verificato. RAM-KERNEL-TEST.md.
-75 test:74 passati,1 skip opzionale. Il run generico e fallito per limite interno della fase system; la build specifica Carrera e ancora in corso.
- ROM completa NON pronta: vedere BUILD-BLOCKERS.md per integrazione primo stadio, HAL, policy e boot residui. Non manca soltanto il confezionamento di uno zip.

Aggiornamento successivo 23 ottobre — ramdisk compilato, verifica staging corretta:

Run39934489950: lunch/API23, parser init nativo e compilazione ramdisk riusciti; build507,5s. Il controllo finale ha fermato la pubblicazione: i tre file erano destinati a root mentre Q impacchetta lo staging ramdisk separato. Aggiunte copie esplicite in TARGET_COPY_OUT_RAMDISK e acquisizione del TARGET_RAMDISK_OUT effettivo nel probe. Nuovo tentativo richiesto; nessun artefatto incompleto pubblicato. Il confronto SHA256 del dump recovery identifica esattamente il prefisso ufficiale TWRP2.8.7.0 (25040896 byte). Nessun aggiornamento recovery necessario per l'acquisizione attuale.

Aggiornamento successivo 23 ottobre — hardware collegato e controllo firmware touch:

Acquisizione attuale in sola lettura: TWRP CRR-L09/carrera, kernel3.10.74-gfa6dc6d, GPU/ION/framebuffer e input presenti; hwbinder/vndbinder assenti nella recovery. Questo kernel non e quello stock3.10.86 ne il nuovo diagnostico. Nessuna prova Q attribuita a TWRP.

Nuova patch kernel introduce CONFIG_HUAWEI_TS_FW_UPDATE: resta y nel confronto stock, e n nel profilo Android10 diagnostico. Impedisce l'aggiornamento automatico dal framework e rifiuta i suoi callback boot/SD. Tre corpi reali provati con flag acceso/spento, zero chiamate a driver/coda da spento. Nuova build ARM64 richiesta; limiti in TOUCHSCREEN-FW-GUARD.md. Suite locale69 test:68 passati,1 skip. Nessuna scrittura sul telefono o riavvio. Il catalogo TWRP ufficiale Carrera elenca solo2.8.7.0; nessun aggiornamento ufficiale disponibile li.

Aggiornamento successivo 23 ottobre — primo errore Carrera risolto nei sorgenti:

Il run39930952198 ha superato sync e grafo generico, poi il prodotto Carrera e fallito prima della compilazione per PRODUCT_SHIPPING_API_LEVEL duplicato:23 23. Rimosso il valore ridondante da device.mk; il prodotto eredita gia API23 da product_launched_with_m.mk. Aggiunto controllo del valore risolto nel probe. Nuovo tentativo necessario; nessun ramdisk prodotto dal run fallito. Moduli Q con correzione HWC in compilazione nel run39933540063; immagine generica ancora in corso nel run39927971028.

Aggiornamento successivo 23 ottobre — callback HWC Q:

Corrette nel sorgente pubblico Q le chiamate a setActiveConfig e setCursorPositionAsync quando il vecchio HAL omette le callback. Il cursore passa alla composizione client; i cambi di modalita mancanti sono rifiutati senza simulare successo. Applicazione vincolata agli hash, prova comportamentale su cinque corpi di funzione reali con ASan/UBSan passata. Dettagli in HWC-CALLBACKS.md. Non e una prova di ABI o rendering Huawei.

Nuova compilazione moduli predisposta con patch e prova nativa del codice pubblico. Il workflow dell'immagine accoda le nuove build senza interrompere quella gia in corso. Suite locale:64 test,63 passati,1 skip. Le build system e ramdisk sono ancora in corso; nessuna ROM installabile prodotta.

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
