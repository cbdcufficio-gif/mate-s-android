# Build Android Q dei moduli pubblici

Il grafo Android generico e stato realmente generato nel run
[39873522042](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39873522042)
con lineage_arm64-userdebug. Il precedente aosp_arm64-userdebug falliva per
PATH_OVERRIDE_SOONG, gia corretto sul repository pubblico.

Il nuovo [workflow](../.github/workflows/android-modules.yml) sincronizza i
sorgenti sul runner standard pubblico, genera il grafo e compila con m -j2:
libutilscallstack, libhwc2on1adapter, libhwc2onfbadapter, allocator2.0 impl e
servizio, mapper2.0 impl, composer2.1 impl e servizio. Sono i moduli originali
Android Q: nessuna libreria sperimentale libmates o HAL fittizio e sostituito.
Non include o trasferisce file Huawei.

Il controllo finale richiede i file ELF installati con i nomi attesi, legge
architettura, DT_NEEDED, SONAME, SHA256 e gli export CallStack richiesti da Mali.
La compilazione riuscita e distinta dal caricamento dei blob sul Mate S.
Il prodotto e lineage_arm64 generico, non Carrera. Il report mantiene
carrera_built=false, rom_built=false e hardware_tested=false.

Limiti: sync20min, grafo10min, moduli45min; il workflow ha95min complessivi.
Il watchdog interrompe la build se lo spazio libero scende sotto12GiB.
I sorgenti Android non vengono scaricati sul PC. Non sono abilitate cache,
Packages o archiviazione Actions di output. Il solo percorso di build locale
esistente richiede ancora un albero Android e i candidati Huawei locali.

Il [kernel run39924712678](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39924712678)
corregge il fallimento del run39880505130: git -C cambiava la directory di
risoluzione della patch, ora indicata con percorso assoluto del workspace
remoto. Il precedente errore avveniva prima della compilazione del kernel.

Questa fase misura la compilazione reale; non produce da sola un system.img
Carrera o un archivio installabile. Il passo successivo resta l'integrazione
Carrera con init, policy, vendor e gli altri HAL, poi assemblaggio e test.

## Revisione e verifiche locali

Suite corrente:48 test eseguiti,47 passati,1 saltato per cross compiler opzionale.
I tre nuovi test verificano il rifiuto del download locale, degli output
mancanti e dei symlink usati come falso risultato della build.

Il connettore FreeLLMAPI rispondeva sessione terminata; usato il gateway locale
gia configurato per Continue, senza modificare configurazione o credenziali.
Revisione sorgente eseguita con dots-studio/dots-3-note-preview:free:
2919 token dichiarati, costo dichiarato0. La risposta era prolissa e troncata;
non e stata trattata come prova di correttezza. Risposta conservata localmente
in out/freellmapi/modules-review.json. Altri modelli hanno restituito429/502:
nessun passaggio a servizi a pagamento e nessuna promessa di disponibilita.

Fonti costi/limiti verificate il23 ottobre2026:
[runner standard pubblico gratuito](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)
e [fatturazione Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## Seguito automatico: immagine generica

Il workflow android-system.yml si attiva sul completamento riuscito della
build moduli sul ramo main dello stesso repository. Ripete le verifiche e
tenta m -j2 systemimage, massimo120min e riserva8GiB. Il timeout complessivo
e230min, entro il limite del job standard. Il codice non accetta input Huawei.

Solo se compilazione e controlli riescono, conserva system.img compresso,
i soli moduli grafici pubblici verificati, manifest sorgenti risolto, report e checksum in una prerelease chiaramente
marcata Generic Android Q development base — DO NOT FLASH. Nessuna cache,
artifact storage Actions, Packages o LFS. Ogni asset deve essere sotto2GiB.
La configurazione Carrera, il boot e i blob Huawei non sono inclusi. Il report
indica se la dimensione sparsa espansa supera la partizione system Carrera.
L'immagine non diventa compatibile col telefono perche entra nella partizione.

Le [Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
hanno limite2GiB per file e nessun limite totale o di banda indicato dalla
documentazione. I binari pubblici compilati sono allegati separati: non vengono
commessi nel repository dei sorgenti. Il workflow non pubblica nulla se la build
fallisce. Il token di scrittura e fornito soltanto al passo di pubblicazione.
