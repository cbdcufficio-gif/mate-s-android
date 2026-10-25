# Direzione operativa del port Carrera

Decisione: 25 ottobre 2026. Si applica alle fasi successive al run
[40231781220](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40231781220),
commit `2ed1f61`. Il run mantiene i propri input e non viene interrotto o
duplicato per applicare questa revisione documentale.

## Scelta architetturale

La prima strada è **kernel Huawei ricompilato con driver Carrera conservati,
backport strettamente necessari, sistema Q coerente e HAL legacy adattati per
singolo processo**. È già un'architettura ibrida: non serve rimpiazzare l'intero
kernel per cambiare la versione Android. Non è ancora dimostrata sul telefono.

Il sistema Q deve mantenere coerenti framework, ART, bionic e librerie di
piattaforma. Si conservano selettivamente driver, firmware e componenti vendor
legacy; non si sovrappongono le librerie Android6 a quelle Q per far coincidere
nomi di simboli. Un namespace privato non corregge automaticamente layout C++,
ownership, ioctl o due runtime libc incompatibili nello stesso processo.
Quando il contratto non è conciliabile, valutare un processo legacy separato
con bridge IPC esplicito oppure una reimplementazione sorgente delimitata.

ARM64 kernel e userspace multilib restano il candidato: camera ARM32 e candidati
GNSS ARM64 non sono intercambiabili. Il controllo è per servizio, non per slogan
“tutto 32 bit è più semplice”.

## Primo compito quando termina la build

### Se riesce

1. Conservare identità del run/commit e manifest risolto; verificare la release
   `carrera-public-system-40231781220` e i quattro asset richiesti: system gzip,
   ramdisk, archivio moduli e report. Confrontare digest dell'asset, SHA256SUMS e
   campi del report, dichiarando se la verifica è sui byte o su metadati server.
   Non scaricare grandi immagini sul PC se il controllo può avvenire sul runner.
2. Richiedere `PUBLIC_CARRERA_SYSTEM_AND_RAMDISK_BUILT`; controllare limite
   sparse espanso di 2684354560 byte, hash dei moduli estratti dall'ext4 e hash
   ramdisk verificato nel cpio. Aggiornare il risultato con le prove effettive.
3. Mantenere distinti: file `/vendor/...` nella radice del filesystem system
   (montato in `/system`), symlink `/vendor -> /system/vendor` nella root e
   ordine delle azioni init. Il verificatore attuale certifica i moduli in ext4,
   ma il symlink solo in `product/root`. Il campo
   `system_image_rootdir_contents_verified=false` è un limite dichiarato,
   non va trasformato in true né trattato come guasto senza leggerne il motivo.
4. Il risultato chiude soltanto la base pubblica. Procedere a G1 sotto:
   ispezione configurazioni effettive, packaging e protocollo del primo boot.
   Non iniziare un altro ciclo completo di build generiche o integrazione
   simultanea di tutti gli HAL.

### Se fallisce

Classificare il primo errore causale, separando compilazione, verifica e
pubblicazione. Tempo, disco e compiler/linker richiedono risposte diverse.

- Il precedente 40212475462 ha raggiunto 64967/80500 target prima del limite
  di 10800 s, con 18130833408 byte liberi. Quel numero Ninja non è una
  percentuale di completamento della ROM e non rende lineare il tempo residuo.
- Il run corrente usa 19200 s per la fase e timeout workflow 350 minuti.
  Se raggiunge ancora il limite, misurare fase critica e costi prima di
  ottimizzare pacchetti/sync o progettare checkpoint con manifest identico.
  Non estendere oltre i limiti della piattaforma né disattivare il guard.
- Se manca disco, misurare anche picco unpack ext4, compressione e overlay
  vendor futuro; preservare riserva 8 GiB. Pulire solo il runner monouso.
- Se compilazione/ABI/verifica fallisce, correzione minima e test pertinenti,
  poi un solo run deliberato. Una mancata release dopo build riuscita è
  un problema di pubblicazione, non una compilazione fallita.

## Correzione concettuale: API di lancio

Il run archiviato 40231781220 ereditava `product_launched_with_m.mk`/23.
Dopo il suo arresto per disco, il target è stato corretto a L MR1/API22. Il firmware B321
acquisito è Android6, ma il [modello Huawei nasce con Android5.1](https://consumer.huawei.com/no/phones/mate-s/specs/).
Il [makefile Q L MR1](https://github.com/LineageOS/android_build/blob/71a47798ac090b81c6b7db0b5c470f1fa3e604cd/target/product/product_launched_with_l_mr1.mk)
definisce proprio il primo livello di lancio, 22.

La patch [deferred/carrera-launch-api22.patch](deferred/carrera-launch-api22.patch)
corregge insieme ereditarietà, commento device, guard del probe e checksum.
È stata applicata e provata su una copia isolata del commit 2ed1f61:
**76 test tracciati, 75 passati, 1 skip opzionale**. Non comprende file locali
non tracciati. Ora è applicata al prodotto; il file patch resta storico.
La prossima build deve verificare API22; non riapplicare la patch storica.
Non modificare retroattivamente i rapporti del run API23. Non usare una variante
di API/FCM per aggirare controlli senza motivazione.

## Gate e prove richieste

| Gate | Consegna minima | Condizione per il successivo |
|---|---|---|
| G0 Base pubblica | Report/manifest/asset autentici del run, ext4 e ramdisk controllati | Input di sviluppo verificati, non ROM |
| G1 Configurazione finale coerente | API di lancio corretta nella prossima revisione; ld.config generato e namespace; modalità APEX; policy/capability kernel; overlay vendor minimo e budget system finale | Ogni componente indispensabile al primo avvio ha origine e contratto chiari |
| G2 Boot e recupero | Boot Huawei v0 specifica; dtimage Carrera conservato; coda stock classificata; intero contenitore entro boot; percorso recovery disponibile e documentato | Candidato corretto e prova recuperabile prima di operazioni persistenti |
| G3 Primo avvio Q | Identità kernel nuovo, init Q, caricamento policy, mount, Binder/HIDL e ADB autenticato | Log ripetibili; TWRP e un logo non soddisfano il gate |
| G4 UI/input e sicurezza operativa | Buffer/ION/fence, EGL/HWC/SF, touch/backlight; ricarica e protezioni termiche preservate | Interazione ripetibile e test sonno/risveglio |
| G5 Funzioni telefono | Audio, radio, dati/Wi-Fi/VPN, camera/media, GNSS, sensori, TEE/cifratura e periferiche richieste | Matrice hardware e app verificata, policy enforcing |
| G6 Consegna | Stress/memoria/autonomia, APK scelti, installer e recupero, checksum e limiti dichiarati | Pacchetto corrispondente al candidato realmente provato |

G1 può essere studiato mentre G0 compila, ma un guasto ignoto non va presentato
come errore hardware accertato. Le aree radio/camera/TEE restano ad alta
incertezza; hanno priorità diagnostica dopo il primo boot, senza promettere
una “piccola rifinitura finale”.

## Decisioni tecniche da usare come esperimenti

- **Kernel**: verificare syscall/Binder/seccomp/config effettive, non aggiungere
  backport solo dal numero 3.10. Il recovery kernel è diverso dalla Image
  diagnostica. EXT/SID Binder mancanti vanno studiati considerando il fallback
  Q; protocollo 8 e SG da soli non provano ogni transazione.
- **APEX e memoria/rete**: valutare flattened APEX, LMK e xt_qtaguid nei percorsi
  supportati da Q, prima di importare tutti i requisiti dei nuovi lanci.
  CONFIG_NAMESPACES=n non prova mount namespace assente: serve la prova
  effettiva su un processo diagnostico e l'ispezione di init.
- **SELinux**: formato 30 uguale non dimostra capability/classi/permessi uguali.
  Integrare policy minima enforcing; non ignorare neverallow o falsificare SPL.
- **Boot**: il helper locale che mette un DTB in legacy second non è il
  packager Carrera. Il candidato TWRP da 26003456 byte supera la partizione
  boot da 25165824; non trasferirlo da prova RAM a flash boot. Il ramdisk Q
  più piccolo è un componente distinto. Il fastboot boot già rifiutato non
  viene ripetuto senza una nuova ragione verificabile.
- **Grafica**: callback HWC protette e build dei wrapper sono progressi reali,
  ma restano layout C++, private handle, stride, ioctl ION, cache e fence.
  Rendering software può isolare un guasto, non certifica il funzionamento GPU.
- **Audio**: flag XML chiude il vecchio errore compiler; XML/route e HAL restano
  da integrare. Analisi ABI private, come eventuali dipendenze ICU legacy,
  restano locali; scegliere librerie private o bridge solo con contratto provato.
- **Dati e TEE**: FDE è una strada per dispositivi aggiornati a Q; non significa
  che la partizione stock sarà direttamente decifrabile. Conservare footer,
  keymaster e recupero; nessuna formattazione implicita.

## Alternative e criterio per cambiare strada

Spostare il kernel intero a 4.x/5.x/mainline solo dopo identificazione di una
capacità impossibile o troppo costosa da retroportare e di un BSP Carrera
concreto. Le immagini di Liszt/GRACE/altro Kirin non sono sostituti.
GSI/retrofit Treble è un possibile obiettivo dopo aver costruito interfacce
vendor coerenti; non risolve gli HAL mancanti e non richiede per magia una
nuova partizione fisica.

Android7/8/9 intermedio solo come esperimento con domanda/criterio di uscita
precisi. App/web engine compatibili sullo stock possono soddisfare funzioni
parziali, ma non trasformano Android6 in API29. Chroot/container condividono
il kernel e richiedono bridge hardware: non sono una ROM nativa pronta.

Android11+ resta aperto dopo Q: valutare nuovi contratti per versione, incluso
il venir meno dell'FDE upstream da Android13. Non promettere un massimo Android
né introdurre oggi un port parallelo completo.
Fonti: [HIDL legacy](https://source.android.com/docs/core/architecture/hidl),
[APEX flattened](https://source.android.com/docs/core/ota/apex),
[FDE](https://source.android.com/docs/security/features/encryption/full-disk),
[accounting legacy](https://source.android.com/docs/core/data/ebpf-traffic-monitor).

## Stato, coordinamento e costo

`PORTING-STATE.json` è lo snapshot strutturato dei gate; `STATUS.md` conserva
la cronologia, `BUILD-BLOCKERS.md` la lista corta corrente. Ogni avanzamento
registra commit, run, hash/prova e limite residuo. Gli agenti devono leggere
questi file prima di riprendere e verificare il live state.

Il monitor Codex e quello Antigravity non devono entrambi correggere lo stesso
run: prima cercare commit/run successori e proprietario attivo. Un solo writer;
audit in parallelo sono ammessi su copie indipendenti. Non cancellare file
non tracciati. Le modifiche documentali non devono avviare build Android:
controllare i path filter prima del push.

Nessun albero Android completo locale, larger runner, trial o servizio pagabile.
Sorgenti/output pubblici solo sui runner standard; vendor privato assemblato
localmente con strumenti piccoli o risorsa gratuita autorizzata. FreeLLMAPI
serve per analisi e revisione di input pubblici: risposte da verificare,
quota non riportata non significa disponibilità illimitata. Se non risponde,
continuare con fonti e test senza cambiare piano o attivare fallback a pagamento.

