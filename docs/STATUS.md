Probe recupero misurato: [40599220835](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40599220835), sorgente`ef950f8`, nessuna compilazione.

# Capacità misurata e recupero ospiti circoscritto — 28 ottobre 2026

Probe40595739296 riuscito. Workspace,/mnt,/tmp,/opt hanno stesso device2049:
nessun filesystem disco aggiuntivo utilizzabile. Dopo pulizia esistente:
128109096960byte liberi su155897610240. Non usare tmpfs RAM per fingere
capacità disco gratuita: ridurrebbe la memoria disponibile alla compilazione.

Payload ospiti nuovi misurati: Julia,Miniconda,AzureCLI,AWSCLI,AWSSAM,
PowerShell,Gradle,sbt,kotlinc: somma3858657280byte (du, recupero df da verificare).
ToolcachePython1620873216byte preservato con Python/Node e runtime runner.
Nuovo probe di solo recupero rimuove esclusivamente i nove strumenti ospiti
misurati sul runner monouso, poi verifica python3/git/gzip/tar e delta df.
Nessun sorgente,Git,intermedio,cachebuild o telefono modificato.
Il recupero non prova che tutto il picco finale rientri: riserva8GiB e verifiche
ext4/compressione restano obbligatorie. Nessun sistema completo rilanciato.

Probe capacità: [40595739296](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40595739296), sorgente`6c0d9e0`, nessuna compilazione.

# Tentativo caldo: cache efficace, arresto disco — 27 ottobre 2026

40541710584 job122321530088, sorgente0f0789d: DISK_RESERVE_REACHED dopo7330,7s,
79972/80491target,8553492480byte liberi; successivo df8534372352.
Nessun errore compiler trovato nei log completi, nessun ext4/system/release
verificato. Non è timeout. Cache:34965hit/42813 (81,67%),7848miss,
78uncacheable,2,68GB readonly. Revisioni778selezionate confermate contro lock.
Non confrontare i tempi come benchmark controllato col cold: vecchio manifest
non recuperato, sorgenti non provati identici.

Diagnostica release carrera-build-diagnostics-40541710584 scaricata e verificata
su byte con SHA256SUMS: log sistema9939000byte e Ninja23458909byte non troncati.
Ninja130199righe output: più output possono condividere lo stesso comando,
non sommare durate senza deduplicare; niente critical path provato senza grafo.
.repo17061343232byte; out53997498368byte. Restano misurati Julia1095401472,
Miniconda1027280896,AzureCLI611782656byte e altri payload ospiti; toolcachePython
1620873216 preservato finché la dipendenza runtime non è chiarita.
Non rimuovere source/Git/intermedi né ridurre riserva8GiB.

Prossimo passo: probe android-storage-headroom.yml replica soltanto pulizia
ospiti già autorizzata, misura df/findmnt/deviceid e payload opzionali SENZA
rimuoverli, senza sync né compilazione. Valutare margine effettivo e picco
ext4/compressione prima di autorizzare altro sistema completo. Nessun retry
completo lanciato. Log gh run view vuoti: API actions/jobs/ID/logs ha restituito
correttamente104309byte; non interpretare vista vuota come log assenti.

Unico tentativo caldo: [40541710584](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40541710584), sorgente `0f0789d`, workflow sistema pubblico. Nessun retry automatico dopo questo tentativo.

# Sync bloccato verificato; unico tentativo caldo — 27 ottobre 2026

40537259220 riuscito: sync465,5s,66874654720byte liberi. Verificati tutti i778
progetti selezionati da default,-darwin contro lock794, più nomi, gruppi come
insiemi e copyfile/linkfile. Report PINNED_ANDROID_SYNC_PASSED e
SYNCED_REVISIONS_MATCH_LOCK. Non è prova di compilazione.

Preparata diagnostica pubblica allowlist: report,manifest,log e due possibili
.ninja_log; massimo32MiB per input (testa/coda se eccede),16MiB output compresso.
SHA256SUMS e inventory dichiarano troncamenti. Piccole release dedicate,
escluse dallo storage artifact Actions; pulizia solo release prerelease marcate
MATES_PUBLIC_DIAGNOSTICS_V1 dopo7giorni alla pubblicazione successiva.
Se nessun run successivo parte la pulizia non è automatica: il monitor deve
rimuovere quelle scadute. Nessuna immagine/albero sorgenti incluso.
Diagnostica best-effort non impedisce pubblicazione sistema riuscito.

Ccache: azzera contatori dopo restore, registra versione/config e statistiche
verbose prima della cancellazione. Il prossimo sistema richiede cache-hit
esatto, altrimenti si ferma prima di compilare. Cache remota confermata1voce,
2558560049byte. Cache calda sola lettura; un solo tentativo deliberato,
non ulteriore cold build implicita. Revisioni fissate nuove rispetto al run
freddo non ricostruibile; ccache verifica compiler/input, hit non garantiti.
88test eseguiti:87passati,1skip; YAML e shell syntax verificati.

Sync senza compilazione: [40537259220](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40537259220), sorgente `75d7d9f`.

# Manifest verificato e sync separato — 27 ottobre 2026

Probe40532026808 riuscito; asset piccoli verificati sui byte con SHA256SUMS.
Manifest b30f6d479b321cab00305b1c9a31450d0a8940138996e7e25cf27f7a0146f845:
794 progetti con SHA40, include espansi,1copyfile e37linkfile.
Installato come configs/android-resolved-manifest.xml e verificato per digest
prima del sync. repo sync --no-manifest-update impedisce aggiornamento del
manifest; repo manifest -r successivo confronta ogni progetto selezionato con
la revisione fissata. La selezione default,-darwin resta invariata.
Nuovo workflow manuale android-pinned-sync.yml si ferma dopo sync, senza graph
o compilazione. Cache remota verificata:1voce,2558560049byte.
87test eseguiti:86passati,1skip. Prima della build calda restano diagnostica
Ninja/log limitata e statistiche cache prima della cancellazione.

Probe successore: [40532026808](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40532026808), sorgente `8516226`.

# Corretto URL relativo del probe manifest — 27 ottobre 2026

40527024053 è fallito prima di scaricare sorgenti: project_count794,
URL errato github.com/LineageOS/LineageOS/android_build. Il resolver usava
la directory del manifest invece dell'URL repository come base relativa.
Correzione project_url con test per fetch relativo e assoluto;
84 test eseguiti,83 passati,1 skip. Nessuna build completa avviata.

Run probe manifest: [40527024053](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40527024053), sorgente `49ddd88`. Nessuna build completa avviata.

# Probe manifest senza compilazione — 27 ottobre 2026

Nuovo workflow manuale android-manifest-lock.yml: risolve i riferimenti pubblici
con quattro processi Git concorrenti, senza clonare sorgenti né compilare.
Conserva manifest completo con SHA per progetto, report e digest in una release
pubblica piccola (massimo 5 MiB). Un report PUBLIC_MANIFEST_REFS_LOCKED prova
solo la risoluzione dei riferimenti nell'intervallo del probe; non prova sync,
compilazione, disponibilità futura o snapshot atomico upstream.
I tre workflow grafo, ramdisk e sistema ora partono solo con workflow_dispatch,
per evitare duplicati e build complete implicite durante le correzioni.
83 test eseguiti: 82 passati, 1 skip. Prima di una build calda restano da
integrare consumo del manifest bloccato e diagnostica limitata con dati Ninja.

# Cache fredda salvata; riproducibilità prima del retry — 27 ottobre 2026

Run 40474812777, job 122090305948, sorgente faf4d7c73c0b34fad83167935cf585928a0da508,
fallito per TIME_BUDGET_REACHED dopo 18000,7 s: 78981/80491 target,
15484002304 byte liberi. Nessun sistema/ext4/release verificato.
Ccache: 8555 hit, 34258 miss, 78 chiamate non cacheabili, 24 cleanup;
dimensione riportata 2,68 GB. Salvataggio confermato della chiave
mates-q-carrera-public-ccache-v1, archivio 2558560049 byte.
I contatori primary-storage sono accessi interni e non compilazioni aggiuntive.

Non è stato lanciato un retry: il manifest risolto completo non è conservato
nei log disponibili. Il commit del repository manifest usa default revision
refs/heads/lineage-17.1; il solo commit del progetto non fissa tutti i sorgenti.
Prossimo passo: piccolo probe che acquisisce e blocca revisioni complete,
diagnostica limitata e deduplicazione trigger prima della build deliberata.
La cache esistente è un'ottimizzazione candidata, non un checkpoint Ninja.
Vedere [revisione operativa](REVIEW-2026-10-27.md). G1/G2 precedono gli altri HAL.

# Successore con cache limitata — 27 ottobre 2026

Run [40474812777](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40474812777),
job `122090305948`, commit `faf4d7c73c0b34fad83167935cf585928a0da508`.
Release attesa solo se riesce: `carrera-public-system-40474812777`.
Annullato il grafo generico duplicato `40474812631`: il workflow completo lo
comprende già. Stato e monitor ora seguono questo run e l'esito della cache.

# Limite tempo confermato; riuso compilazione — 27 ottobre 2026

Run [40405482104](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40405482104),
commit `4691cf4`, fermato da TIME_BUDGET_REACHED a 18000,4 s; 79285/80491 target,
15311339520 byte liberi. Risorse misurate: 4 CPU, RAM 16765411328 byte,
3 processi. WebView/ramdisk precedenti al sistema riusciti; nessun sistema/ext4/release.
Il solo incremento 2 -> 3 processi non ha chiuso il limite; non si rialza il budget.

Nuova correzione: ccache C/C++ da massimo 3 GB, un'unica chiave immutabile
`mates-q-carrera-public-ccache-v1`, restore/save ufficiali fissati a commit.
Soong usa CC_WRAPPER; Make usa USE_CCACHE/CCACHE_EXEC. Opt-in soltanto su runner
pubblico monouso. Input/compiler restano parte delle chiavi interne di ccache;
non si riusano direttamente immagini o output Android non verificati.
Un primo tentativo freddo potrebbe ancora esaurire il tempo, ma conserva lavoro
per un solo successore caldo, da autorizzare operativamente solo dopo aver
verificato salvataggio, dimensioni e statistiche. Un hit usa cache in sola lettura
per evitare espulsioni a catena durante i miss. Nessuna garanzia sul guadagno.

[Quota GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching):
10 GB cache gratuiti per repository, separati dagli artefatti. Al controllo:
0 cache/0 byte. Non modificati limite o fatturazione. Prima di salvare: dimensione
locale <=3300000000 byte e totale remoto <=6000000000 byte; una sola chiave,
nessun artefatto Android grande. Su build riuscita la cache locale viene eliminata
prima dell'espansione ext4, preservando la riserva 8 GiB. Su build fallita viene
salvata esplicitamente se entro i limiti; niente salvataggio automatico success-only.

Test locali: 81 eseguiti, 80 passati, 1 skip; opt-in cache coperto.
Sintassi workflow e checksum verificati prima del push. Main `6e1cd70`, nessun
successore concorrente rilevato. G0 resta aperto; nessuna operazione sul telefono.

# Successore con budget corretto — 26 ottobre 2026

Run [40405482104](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40405482104),
job `121862019582`, commit `4691cf465ff85d7bb86211371bd78cb120437009`.
Release attesa soltanto se riesce: `carrera-public-system-40405482104`.
Un solo run avviato; nessun ramdisk duplicato. Monitor aggiornato.
80 test eseguiti: 79 passati, 1 skip; checksum e diff verificati.

# Timeout complessivo; WebView verificato — 26 ottobre 2026

Run [40346676795](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40346676795),
commit `20cd98e`, annullato. Annotazione GitHub: `The job has exceeded the maximum
execution time of 5h50m0s`. La build era a 78895/80491 target; nessun errore
compiler osservato nella coda. Al cancel: 17515741184 byte liberi; `.repo`
17066266624 byte, `out` 47774572544 byte. Nessun sistema/ext4/release verificato.

**WebView risolto come input**: ARM e ARM64 scaricati via LFS in 6 e 9 s,
dimensioni e SHA256 del puntatore verificati, manifest presente e CRC ZIP validi.
ARM SHA256 `0dc261c3f37e9ac16a4f593ef316a097fc59815bb2082a8e38c519647bbcb3cc`;
ARM64 SHA256 `1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a`.
Ramdisk API22 compilato, SHA256
`6379c931e66f326acfa4fdea4d8388aa7da9bf62895aba755b4fdddb62cf6a4a`.
Queste prove non attestano installazione WebView né avvio hardware.

Il budget sistema 320 minuti sommato alla preparazione/sync/grafo/ramdisk
(~36 minuti nel run) eccede il timeout complessivo di 350 minuti prima ancora
di ext4/compressione/pubblicazione. Correzione: budget sistema 300 minuti,
timeout job invariato; parallelismo sistema 3 solo con >=4 CPU e >=12 GiB RAM,
altrimenti 2. Risorse e numero di job vengono registrati prima di compilare,
così restano anche in un cancel. Nessuna estensione oltre limiti piattaforma;
riserva disco 8 GiB, output, policy e controlli ext4 invariati.
Il tempo effettivo va misurato: la nuova scelta non garantisce completamento.

Validazione: 80 test eseguiti, 79 passati, 1 skip opzionale, compresi limiti
CPU/RAM della selezione del parallelismo. Main `f021427`, nessun successore o
intervento concorrente al controllo. G0 resta aperto; seguono G1 e G2.

# Successore con preflight WebView — 26 ottobre 2026

Run [40346676795](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40346676795),
job `121655330530`, commit `20cd98e368a192e45bfa20c2f1cb4afe5b15ce39`.
Release attesa solo se riesce: `carrera-public-system-40346676795`.
Annullato il ramdisk duplicato `40346676667` generato dal push: il workflow
completo include già quella compilazione e il medesimo preflight WebView.
Monitor e stato ora seguono questo run; non riprocessare il guasto 40300253229.

# Errore input WebView — 26 ottobre 2026

Run [40300253229](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40300253229),
commit `85a4484`: fase sistema terminata dopo 17705,5 s, returncode 1,
stop_reason null, 13238657024 byte liberi. Nessun arresto per tempo/disco.
Primo errore causale osservato: target `webview_intermediates/package.apk`,
`failed opening zip: Invalid file`, poi veridex `Expected valid zip or dex file`.
Il log termina a 79889/80491 target; sistema/ext4 e release restano non verificati.

Il manifest bloccato seleziona repository WebView separati per architettura.
Il [repository ARM64 pubblico](https://github.com/LineageOS/android_external_chromium-webview_prebuilt_arm64)
usa `*.apk filter=lfs`; il blob Git osservato è un puntatore di 134 byte,
non l'APK. L'ipotesi causale è mancata idratazione LFS, coerente con l'assenza
di un passaggio LFS nel probe; il vecchio log non conserva i byte del file
invalido, quindi non dimostra direttamente che fosse proprio quel puntatore.

Correzione: dopo sync/grafo e prima della costosa compilazione Carrera,
recuperare solo `webview.apk` ARM/ARM64 con `git lfs pull`; leggere oid SHA256
e dimensione dal puntatore del commit risolto; verificare byte, hash, manifest
APK e CRC ZIP. Download limitato a runner pubblico monouso, guardia 20 GiB
in questa fase e timeout 300 s per architettura. Nessuna rimozione di WebView
o aggiramento di veridex; nessun download globale LFS per tutte le architetture.
I report conservano commit, digest, dimensioni e verifica; un input ancora
invalido arresta subito il probe. Log LFS inclusi nella diagnostica sistema.

Validazione: 79 test eseguiti, 78 passati, 1 skip; nuovi test su puntatore,
hash/dimensione/ZIP e rifiuto download locale. Nessuna compilazione Android locale.
G0 resta aperto; API22 e guardie /vendor, SELinux, firmware touch invariate.
Nessun run successore o correzione concorrente rilevato su main `49f75ce`.

# Successore in corso — 26 ottobre 2026

Run [40300253229](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40300253229),
job `121496077489`, commit `85a448452d6029aa9491873470a272d66dbc5b33`.
Avviato dal push della correzione; nessun run ramdisk duplicato generato.
Release attesa soltanto in caso di successo: `carrera-public-system-40300253229`.
Validazione locale: 76 test eseguiti, 75 passati, 1 skip opzionale;
sintassi YAML/bash e checksum verificati. Non è una build Android locale.
Monitor e stato seguono questo successore, senza riprocessare 40245174034.

# Nuovo arresto disco API22 — 26 ottobre 2026

Il run [40245174034](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40245174034),
commit `1d932d2`, si è fermato per **DISK_RESERVE_REACHED** a 18011,8 s,
ultimo target 79885/80491, 8547528704 byte liberi. Ramdisk API22 compilato;
sistema non completato/verificato, nessuna release della coppia.
La pulizia precedente ha portato lo spazio iniziale da 112694460416 a
122925395968 byte (runner diversi: incremento osservato, non misura isolata).
Diagnostica finale: `.repo` 16707293184 byte; `out` 52677238784 byte.
Il conteggio Ninja non è una percentuale della ROM né una stima lineare del tempo.

Nessun successore o intervento concorrente rilevato su main `6340864`.
Seconda correzione circoscritta: SDK Go preinstallato, JDK ospite, moduli Node
globali e browser di test non usati da questa build; prune delle sole immagini
Docker inutilizzate. Nessuna cancellazione di container/volumi, sorgenti Git o
intermedi. Python/Node runtime conservati. Il workflow rifiuta un override Java
esterno: [Soong Q](https://github.com/LineageOS/android_build_soong/blob/lineage-17.1/ui/build/config.go)
seleziona `prebuilts/jdk/jdk9` in assenza di override; envsetup esporta quel JAVA_HOME.
La riserva resta 8 GiB; budget 19200 s e timeout 350 minuti invariati.
Il nuovo run misurerà lo spazio realmente recuperato: completamento non garantito.

G0 resta aperto; API22 resta applicata; ordine G1 configurazione/ABI e G2
boot/recupero invariato. Nessuna operazione sul telefono.

# Run successore seguito — 26 ottobre 2026

Avviato [40245174034](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40245174034),
job `121325107274`, commit `1d932d277dc1339f10e1acb5423f4e57a666a2ac`:
API22 e pulizia mirata del runner; setup in corso al controllo iniziale.
Release attesa solo se riesce: `carrera-public-system-40245174034`.
Annullato il run ramdisk ridondante `40245174036` generato dallo stesso push:
il workflow completo include già la medesima fase. Nessun secondo sistema avviato.
Il monitor segue questo successore; non riprocessare il fallimento 40231781220.

# Aggiornamento operativo — 26 ottobre 2026

Il run [40231781220](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40231781220),
commit `2ed1f61` con API23, è terminato il 25 ottobre alle 23:27 UTC per
**DISK_RESERVE_REACHED**, dopo 8909,7 s della fase sistema. Restavano
8531783680 byte liberi; ultimo target osservato 69330/80491. SIGTERM/143
è la conseguenza della guardia, non un errore compiler. Il ramdisk era riuscito;
il sistema/ext4 non è stato completato o verificato e nessuna release della
coppia è stata pubblicata. G0 resta aperto.

Prima dell'intervento: main `0ab5767`, nessun run successore rilevato.
Correzione circoscritta: rimuovere ulteriori SDK preinstallati non usati soltanto
sul runner pubblico monouso, con elenco esplicito e dimensioni prima/dopo.
Non si eliminano metadati Git dei sorgenti, intermedi Android o output; restano
riserva 8 GiB, verifica ext4, SELinux e guardie hardware. Il recupero effettivo
di spazio sarà misurato dal nuovo run: non è una garanzia di completamento.

La patch API22 preparata è ora applicata a ereditarietà prodotto, commento e
guard del probe per la prossima build deliberata. Il risultato storico API23
resta tale; il file deferred è conservato come traccia, non va riapplicato.
Validazione locale sui soli file tracciati: 76 test eseguiti, 75 passati,
1 skip opzionale. Non equivale a compilazione Android o avvio hardware.
Ordine successivo invariato: G0 -> G1 configurazione/ABI -> G2 boot/recupero.

---

# Stato corrente — direzione aggiornata il 25 ottobre 2026

La fonte operativa per le prossime fasi è [PORTING-DIRECTION.md](PORTING-DIRECTION.md)
e lo snapshot strutturato è [PORTING-STATE.json](PORTING-STATE.json).
Il seguito automatico deve leggerli prima di elaborare il risultato della build.

- Run seguito: [40231781220](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40231781220),
  commit `2ed1f61`, in compilazione all'aggiornamento di direzione: verificare lo
  stato live. Budget fase 19200 s, timeout workflow 350 minuti, riserva 8 GiB.
- Il precedente 40212475462 è terminato per limite 10800 s a 64967/80500 target,
  non per un errore compiler osservato in quel punto. Il conteggio Ninja non
  misura la percentuale di completamento della ROM.
- Base pubblica, prodotto finale con vendor, boot corretto e prove hardware sono
  gate distinti. Il primo esito verde non abilita automaticamente un flash.
- API22 di lancio: correzione preparata e testata in
  [deferred/carrera-launch-api22.patch](deferred/carrera-launch-api22.patch),
  da applicare prima della prossima build deliberata dopo archiviazione del run
  API23 corrente. Nessun input del run in corso modificato da questa revisione.
- La nuova direzione preserva kernel/driver Carrera, backport misurati e sistema
  Q coerente; esclude sostituzioni casuali del framework o di librerie stock.
- Validazione della patch API22 su copia isolata dei soli file tracciati:
  76 test eseguiti, 75 passati, 1 skip opzionale. Non è una build Android completa.

Il controllo dei checksum pubblici ha inoltre rilevato una voce storica errata
per `.github/workflows/platform-cxx.yml`: il contenuto tracciato coincide con il
blob GitHub `770dbd1860b0ebfc3f3925c6e37ff2e9b242e0d3`, SHA256
`abc9e35f9f592edcf568b12ae244a0a6a5d9fae38364cbe5a2a4e5d4ca34b823`.
Corretta soltanto la voce in SHA256SUMS; il workflow non è stato modificato.

## Cronologia: ogni esito si riferisce al proprio commit

Le descrizioni in corso/in coda e i conteggi test nelle sezioni seguenti sono
snapshot storici. Non sovrascrivono lo stato operativo sopra.

Stato corrente — 25 ottobre:

Aggiornamento operativo, 25 ottobre, 19:56 UTC — build sistema pubblico Carrera:

- Il run [40212475462](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40212475462) sul commit `88f9e9b` ha superato con successo setup, sync, verifica grafo generico e compilazione del ramdisk Carrera.
- La compilazione del sistema `lineage_carrera_public-userdebug` (`m -j2 ... systemimage simg2img`) è avanzata senza errori di codice, arrivando a 64.967 su 80.500 target Ninja (80,7%).
- Al secondo 10.801,6 il guard interno della sonda ha arrestato il processo (`TIME_BUDGET_REACHED`, exit 143/SIGTERM) per raggiungimento del limite temporale di 10.800 s (3 ore). Restavano 18.130.833.408 byte liberi (~18,1 GB), ben oltre la riserva minima di 8 GiB.
- Intervento applicato: esteso il timeout della fase build in `android_carrera_system_probe.py` a 19.200 s (320 minuti / 5h 20m) e il `timeout-minutes` del workflow GitHub adiacente a 350 m. Aggiunta pulizia di `/usr/local/share/boost` nel runner monouso per preservare ulteriore spazio disco.
- Suite locale: 77 test passati (1 skip opzionale).

Aggiornamento operativo, 23 ottobre, 12:20 UTC — build ramdisk Carrera:

- Il run [39949624600](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39949624600) ha compilato il ramdisk del prodotto pubblico lineage_carrera_public-userdebug in 510,5 secondi. Misura 802.915 byte; parser init Q passato e tre file rootdir verificati nello staging. SHA256 e limiti sono in CARRERA-RAMDISK-RESULT.json e CARRERA-ROOTDIR.md.
- Il job è fallito solo dopo la compilazione, quando la prerelease ha richiesto un permesso Workflows: write non concedibile al GITHUB_TOKEN: il commit puntava a una revisione precedente del workflow rispetto a main. Il run corrente 39951112143 è sul tip di main; il retry del vecchio run è stato richiesto in cancellazione.
- I run 39942073472 (Carrera completo, limite vecchio) e 39937861011 (sistema generico) erano ancora in corso; 39951112143 (Carrera completo, limite 10800 s) era in coda. Non c'è ancora una system image verificata.
- Suite locale: 76 test, 75 passati, 1 skip per cross compiler opzionale. Nessuna boot image, ROM installabile o prova di avvio Android prodotta.


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
- Il prossimo controllo Carrera richiede anche il link generato
  `root/vendor -> /system/vendor` per il copy-out vendor legacy.
- Suite locale aggiornata:76 test,75 passati,1 skip per cross compiler
  opzionale. Nessuna immagine Q installabile o boot Android prodotto.

- Kernel con controllo firmware touch: run39937087192 riuscito; prerelease con Image pubbliche/config/report. DiagnosticoSHA3ec66f2b1a20270b101d72374b697dbfb1c178b749781e5580c356b7429b3bb9.
- Moduli grafici Q corretti: run39933540063 riuscito ARM32/ARM64,14 ELF installati; ANDROID-MODULE-PATCHED-RESULT.json.
- Ramdisk Carrera: run39937831656 riuscito,802884 byte, tre file verificati nel cpio; CARRERA-RAMDISK-RESULT.json.
- Sonda ARM64 eseguita in RAM di TWRP: Binder8, display1080x1920x32, ION/Mali aperti; getrandom/memfd assenti nel vecchio kernel.
- Un solo fastboot boot diagnostico: trasferimento OKAY, avvio rifiutato Command not allowed. Nessun flash. Rientro in TWRP2.8.7.0/kernel3.10.74 verificato. RAM-KERNEL-TEST.md.
-76 test:75 passati,1 skip opzionale. Il run generico e fallito per limite interno della fase system; la build specifica Carrera e ancora in corso.
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
