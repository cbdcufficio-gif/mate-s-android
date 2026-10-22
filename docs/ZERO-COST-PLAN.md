# Mate S Android 10+ — lavoro concreto e vincoli

Obiettivo finale: ROM Android 10 o superiore avviabile sul CRR-L09, con grafica,
touch, telefonia, dati, audio, Wi-Fi, Bluetooth, fotocamere, sensori, GPS,
ricarica e sospensione verificati. Una Image compilata, un system.img generico,
una schermata di avvio o un numero versione modificato non soddisfano l'obiettivo.

## Scelta tecnica iniziale

| Metodo | Decisione e prova necessaria |
|---|---|
| LineageOS 17.1 legacy con kernel Huawei 3.10 | Prima strada da verificare: conserva i driver del SoC. Servono build nativa Android 10, init/policy e adattatori HAL provati. Nessun successo hardware ancora dimostrato. |
| Port Android 7/8/9 intermedio | Esperimento diagnostico solo se chiarisce una regressione specifica; non sostituisce Android 10. Evitare più checkout completi. |
| Userspace ARM32 | Alternativa condizionata alla disponibilità di tutti i blob necessari. ARM64+ARM32 resta il candidato attuale; la presenza di un GPS soltanto ARM64 nell'estrazione impedisce di assumere equivalenza. |
| Backport mirati da altri kernel | Possibili solo con revisione delle dipendenze, delle syscall/ioctl e test. Tenere il driver Huawei originale quando la sua ABI è necessaria. Mai unire immagini/DTB di telefoni diversi. |
| Rebase/mainline/Panfrost | Progetto alternativo molto più ampio: boot, clock, storage, display, radio e gestione energia richiedono supporto specifico. Non una scorciatoia già disponibile. |
| Reverse engineering e shim | Analisi statica di import/export, disassemblato, layout C++, ioctl e formati buffer; implementare solo traduzioni con contratto documentato. Un simbolo con stesso nome non prova compatibilità. |
| GSI/Treble retrofit | Stock Android 6 non offre l'interfaccia vendor moderna richiesta. Una GSI scaricata non è una ROM Carrera; un retrofit richiede prima HAL, mount, VINTF e policy coerenti. Nessuna nuova partizione prevista. |
| Aggiornare solo framework/app | Utile soltanto per app compatibili con il vecchio sistema; non costituisce Android 10 e non cambia la sua API nativa reale. |

Il sorgente Q contiene `HWC2On1Adapter` e mapper 2.0. Non è giustificato dichiarare
obbligatori gralloc4, Mali Bifrost, dmabufheap o kernel 4.14 per qualsiasi port
legacy Q. La possibilità specifica sul Mate S resta da dimostrare.

## Calcolo remoto senza spesa

- GitHub: repository pubblico dei soli sorgenti originali, riferimenti e ricette.
  Niente librerie proprietarie, dump, backup, identificativi del telefono o chiavi.
- Primo workflow: runner standard `ubuntu-22.04`, massimo 10 minuti, lettura del
  manifest fissato a commit, misura di disco/RAM, risultati nei log e nel riepilogo.
  Niente cache, artifact storage, Packages, LFS, Codespaces o larger runner.
- La documentazione pubblica indica 4 CPU, 16 GB RAM e 14 GB SSD per il runner
  Linux pubblico standard; lo spazio realmente disponibile va misurato.
  Il limite documentato del singolo job ospitato è 6 ore.
- La soglia iniziale di 160 GiB liberi è una stima prudenziale di pianificazione,
  non una misura del fabbisogno LineageOS 17.1. Il preflight non autorizza mai un
  sync completo. RAM cgroup e memoria host sono registrate separatamente.
- Prossimo esperimento remoto: build dei soli componenti con dipendenze note,
  dopo aver verificato sorgenti, toolchain e budget. Spezzare system/vendor non
  elimina automaticamente il grafo Soong e le dipendenze condivise.
- Pulizia dei tool preinstallati e filesystem compressi sono ipotesi da misurare
  sul runner effimero, non spazio garantito. Nessuna pulizia del PC.
- Codespaces ha quote di tempo e storage, non è una macchina gratuita illimitata.
  Nessuna attivazione senza prova di blocco delle spese e risorse sufficienti.
- Azure escluso. Oracle, trial con carta, crediti promozionali e istanze pagabili
  non sono soluzioni attivate. Un laboratorio universitario/donatore sarebbe
  utilizzabile solo con accesso autorizzato, spazio adeguato e nessun costo.

FreeLLMAPI svolge ricerca ragionata, generazione e revisione di codice; i suoi
endpoint disponibili restituiscono testo e non offrono un filesystem/runner Android.
Le chiamate non azzerano l'uso ChatGPT necessario a coordinare e verificare.
Nessuna strategia globale, abbonamento o quota a pagamento è stata attivata.

## Evidenze locali di questa sessione

- Otto candidati grafici reali: hash stock confrontati con il lock B321 e patch
  ricontrollate con `verify_patch`, inclusi segmenti, simboli/versioni e payload.
- Inventario statico: 880 librerie lette e 73 file HAL/RIL. La ricerca per SONAME
  ignora deliberatamente namespace e ordine del linker: non è un test di caricamento.
- `lib64/hw/camera.hi3635.so` è escluso dal parser per allineamento PT_LOAD.
  `readelf` conferma un primo LOAD a VA 0x4000/offset 0 e un secondo con differenza
  VA-offset 0x14000 ma p_align 0x10000. Indagare provenienza e loader effettivo;
  non modificare l'header e non concludere che il firmware originale sia rotto.
- Manifest completo letto: 794 progetti; 792 revisioni non fissate a SHA.
  I tag sono riferimenti di release, ma non equivalgono a un lock di tutti i commit.
- Test attuali: 21 eseguiti, uno saltato perché mancano cross compiler configurati.
  Il precedente risultato di 19 senza skip appartiene all'altro ambiente.

## Passaggi che determinano il progresso

1. Risolvere l'accesso GitHub di scrittura e pubblicare solo l'allowlist revisionata.
2. Eseguire il preflight remoto e registrare URL del run e risorse effettive.
3. Confrontare Region/Vector/CallStack e simboli reali con Q; compilare gli
   adattatori grafici con controlli ELF attivi. Nessuna shim che restituisce successo
   senza implementare allocazione, fence e formati buffer corretti.
4. Integrare init/fstab/ueventd, HAL rimanenti e policy enforcing; produrre immagini
   solo dopo build riuscita. Preservare il DTB Carrera e revisionare l'aggiornamento
   automatico firmware touchscreen presente nel kernel.
5. Verificare packaging Huawei, dimensioni e recupero prima della prova hardware.
   Nessuno script di questo progetto scrive partizioni o riavvia il dispositivo.
6. Completare la matrice hardware. Android 11+ resta una valutazione successiva;
   non promettere una versione massima senza prove.

## Fonti primarie consultate il 22 ottobre 2026

- [Runner standard](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)
- [Costi Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Limiti Actions](https://docs.github.com/en/actions/reference/limits)
- [Quote Codespaces](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage)
- [GSI e interfacce Treble](https://source.android.com/docs/core/tests/vts/gsi)
- [Wrapper per HAL legacy](https://source.android.com/docs/core/architecture/hidl)
- [HwcLoader Q](https://github.com/LineageOS/android_hardware_interfaces/blob/02951860e9c95f19384fa07522925537d8c17a18/graphics/composer/2.1/utils/passthrough/include/composer-passthrough/2.1/HwcLoader.h)
- [Mapper 2.0 Q](https://github.com/LineageOS/android_hardware_interfaces/blob/02951860e9c95f19384fa07522925537d8c17a18/graphics/mapper/2.0/default/Android.bp)

Le risposte dei modelli sono suggerimenti sottoposti a verifica, non fonti primarie.
