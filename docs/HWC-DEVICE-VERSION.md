# Versione del dispositivo HWC Huawei: analisi statica ARM64

Il percorso `open` del composer ARM64 inizializza `hw_device_t.version` a
`0x01040001`, ossia **HWC 1.4, header 1** secondo gli header Android verificati.
Questo identifica la versione dichiarata dal codice; non dimostra che il
dispositivo si apra o funzioni con Android 10.

## Identita e catena delle evidenze

File locale analizzato: `generated/graphics-01/proprietary/lib64/hw/hwcomposer.hi3635.so`.
SHA-256: `46287c2a098505b26fd2d25873eeab11762c632be7caebedf72f0328a0340591`.
Gli indirizzi seguenti sono indirizzi virtuali ELF prima della base di caricamento.

1. Il simbolo esportato `HMI` vale `0x5c010`. Il campo `hw_module_t.methods`,
   a offset `0x20` nel layout ARM64, ha una rilocazione `R_AARCH64_RELATIVE`
   a `0x5c030`, addendo `0x5c008`.
2. La prima voce della struttura methods a `0x5c008` ha una rilocazione relativa
   con addendo `0x149b8`: questo e il puntatore `open`.
3. A `0x149d0` il terzo argomento, puntatore di uscita, viene salvato in `x21`.
   A `0x14a14` viene confrontato il nome richiesto con la stringa `composer`
   a `0x3a0d8`. Il ramo di costruzione segue il confronto uguale.
4. `malloc(0x2f8)` a `0x14a24` produce il puntatore salvato in `x19` a
   `0x14a28`; un controllo scarta il puntatore nullo. La memoria viene azzerata.
5. A `0x14a74` viene costruito il valore iniziale 1 in `w10`; a `0x14a7c`
   viene inserito `0x0104` nei 16 bit superiori. A `0x14ac4` il valore
   `0x01040001` viene scritto a `[x19 + 4]`, campo `hw_device_t.version`.
   Il tag dispositivo `0x48574454` viene scritto a `[x19]` a `0x14abc`.
6. Sul percorso di successo, a `0x14bd8` lo stesso puntatore `x19` viene scritto
   in `[x21]` e viene restituito zero. Il percorso normale passa inoltre per
   creazione del thread, che puo fallire; configurazione e display possono
   fallire prima di arrivare alla restituzione.

La funzione non esporta un proprio simbolo: l'etichetta vicina proposta dal
disassemblatore non ne identifica il nome. L'identificazione qui deriva dal
puntatore `HMI.methods->open`.

## Decodifica verificata sulle fonti

- [hardware.h](https://github.com/LineageOS/android_hardware_libhardware/blob/lineage-17.1/include/hardware/hardware.h),
  blob `bf076f6c34cddcd352c241c93147d56604f4a581`:
  `HARDWARE_MAKE_API_VERSION_2(major, minor, header)` colloca major nei bit
  24-31, minor nei bit 16-23 e header nei bit 0-15.
- [hwcomposer_defs.h](https://github.com/LineageOS/android_hardware_libhardware/blob/lineage-17.1/include/hardware/hwcomposer_defs.h),
  blob `9f22f862b17861f0b0f669932f25a93140ed1f6e`:
  `HWC_HEADER_VERSION` vale 1; `HWC_DEVICE_API_VERSION_1_4` usa i valori (1,4,1).

FreeLLMAPI, esecuzione `a6ebb2ce-b753-4456-95ea-3addb15c42c6`, modello
`gemini-3.5-flash-lite`, ha confermato il valore grezzo ma proposto una decodifica
errata (major 260): tale interpretazione e stata scartata confrontando gli header.

## Riproduzione e limiti

Usati `llvm-readelf-19 --relocations` e `llvm-objdump-19 -d` senza eseguire il
blob. Le rilocazioni Android compresse vengono decodificate da LLVM; il tool
segnala errori per altre voci simboliche perche `sh_link` della sezione punta a
zero. Le due voci relative qui usate non richiedono una tabella dei simboli e
sono presenti nell'output. GNU readelf non le aveva stampate.

Output locali: `out/hwc-device-version/arm64-relocations.txt`,
`arm64-relocations-warnings.txt` e `arm64-open.txt`. Solo questo rapporto di
metadati e destinato alla pubblicazione, non i blob o il disassemblato.

La variante ARM32 non e stata analizzata qui. Restano da verificare il
caricamento delle dipendenze, la selezione dell'adattatore Android, il layout
delle strutture Huawei, il kernel, i dispositivi e le operazioni effettive.
Nessuna esecuzione sul telefono, nessun flash e nessuna compatibilita grafica
completa dichiarata.

## Gate di versione nel caricatore Android 10

Verificato anche [HwcLoader.h](https://github.com/LineageOS/android_hardware_interfaces/blob/02951860e9c95f19384fa07522925537d8c17a18/graphics/composer/2.1/utils/passthrough/include/composer-passthrough/2.1/HwcLoader.h):
se open riesce, major diverso da 2 conduce ad adaptHwc1Device; questo rifiuta
minor inferiore a 1. Il valore ARM64 osservato produce major1/minor4 e supera
quel solo controllo, portando a HWC2On1Adapter. Non dimostra che open riesca,
che i layout siano compatibili o che le callback operino correttamente.
