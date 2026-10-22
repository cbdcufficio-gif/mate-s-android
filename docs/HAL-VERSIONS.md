# Versioni statiche dei moduli Huawei

Analizzati gli otto candidati grafici locali senza eseguirli.
hwcomposer.hi3635.so ARM32/ARM64 espone un HMI file-backed con tag HWMT,
module_api_version=0x0001 e hal_api_version=0x0000.
La versione modulo è quindi 0.1, non la versione del dispositivo HWC
restituito da open: non dimostra l'accettazione da parte di HWC2On1Adapter.

Per gralloc.hi3635.so ARM32/ARM64 l'HMI esportato non è interamente contenuto
nei primi 8 byte di una regione PT_LOAD file-backed: la versione non è
determinabile con questa lettura. Non sono stati interpretati zeri come
una versione valida. Il prossimo controllo richiede analisi dell'inizializzazione.

Il layout dei primi campi è verificato contro hardware.h di Lineage17.1,
blob bf076f6c34cddcd352c241c93147d56604f4a581:
uint32 tag, uint16 module_api_version, uint16 hal_api_version.
FreeLLMAPI è stato consultato per i limiti della lettura statica.

Script riproducibile: scripts/hal_version_probe.py, con --graphics e --out.
Il JSON pubblicato contiene soltanto metadati e hash, nessun binario Huawei.
Nessun HAL aperto, nessuna ROM o immagine prodotta e nessuna operazione sul telefono.
