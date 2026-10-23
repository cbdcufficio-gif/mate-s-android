# Callback HWC1 mancanti: correzione pubblica Android Q

Il composer Huawei ARM64 dichiara HWC 1.4 ma il percorso open esaminato
azzera 0x2f8 byte e non assegna direttamente tre callback standard:
getActiveConfig, setActiveConfig e setCursorPositionAsync.
L'assenza di assegnazioni dirette e un'evidenza statica; non dimostra il valore
dei campi dopo tutti gli helper, ne un crash osservato sul dispositivo.

## Contratto verificato

Con hw_device_t ARM64 di 0x78 byte, l'ordine in
[hwcomposer.h](https://github.com/LineageOS/android_hardware_libhardware/blob/lineage-17.1/include/hardware/hwcomposer.h)
(blob 9eb1aafbed0c0cb4dbd5c71613c0dd179b4aead9) colloca le tre voci a
0xc0, 0xc8 e 0xd0. Le assegnazioni osservate arrivano a getDisplayAttributes,
0xb8; le estensioni Huawei iniziano a 0xe0. Non e una verifica completa del
layout di layer, display contents o private handle Huawei.

[HWC2On1Adapter.cpp](https://github.com/LineageOS/android_hardware_interfaces/blob/02951860e9c95f19384fa07522925537d8c17a18/graphics/composer/2.1/utils/hwc2on1adapter/HWC2On1Adapter.cpp)
gestisce gia getActiveConfig nullo, scegliendo la prima configurazione. Le
chiamate alle altre due callback non sono tutte protette. La patch aggiunge:

- BadConfig per un cambio di configurazione privo di callback; selezionare
  quella gia attiva conserva il comportamento precedente.
- Unsupported per un cambio colore senza callback, senza aggiornare lo stato.
- Rifiuto dell'inizializzazione quando il getter segnala nessuna configurazione
  attiva e il setter manca o fallisce.
- Composizione client del cursore quando manca la callback asincrona; una
  chiamata diretta alla posizione senza callback restituisce BadLayer.

I codici rispettano gli errori ammessi da
[hwcomposer2.h](https://github.com/LineageOS/android_hardware_libhardware/blob/lineage-17.1/include/hardware/hwcomposer2.h).
Nessuna versione HWC viene falsificata e nessuna callback simulata restituisce
successo al posto del driver.

## Applicazione e prove

configs/android-patches.json fissa SHA256 di sorgente, patch e risultato.
scripts/android_patches.py prova la patch su una copia temporanea, rifiuta
sorgenti diversi e symlink, verifica il risultato e gestisce la seconda
applicazione senza modifiche. I moduli Q compilati successivamente includono
la patch; i risultati delle build precedenti restano riferiti al codice originale.

scripts/check_hwc_callbacks.py estrae cinque corpi di funzione reali dalla
versione corretta e li esegue con una piccola facciata di test sul computer.
Verifica callback nulle, riuscite e fallite, conservazione dello stato e
fallback del cursore. AddressSanitizer e UndefinedBehaviorSanitizer attivi;
LeakSanitizer escluso per l'incompatibilita con il tracciamento del sandbox.
La prova locale con clang++-19 e passata. Non verifica ABI Android, caricamento
dei blob, comportamento di prepare/set Huawei o rendering sul telefono.
La compilazione completa ARM32/ARM64 viene ripetuta dal workflow dei moduli.

FreeLLMAPI auto ha usato dots-studio/dots-3-note-preview:free: 4854 token,
costo dichiarato 0. I suoi suggerimenti sono stati controllati contro le
fonti: scartati Unsupported per il cursore, l'inesistente NoConfig e la
pretesa di avere provato il comportamento hardware.

Suite locale dopo l'integrazione: 64 test, 63 passati e uno skip per un
cross compiler opzionale. Nessun flash, riavvio o esecuzione del blob.

## Compilazione remota riuscita

Run39933540063, commit770036f35af70d7a2dc867669ffd2171a52b2624: patch
applicata agli hash previsti, prova dei cinque corpi di funzione riuscita,
moduli reali ARM32/ARM64 compilati.14 ELF installati:2 sotto system e12
sotto vendor del prodotto generico. Report in ANDROID-MODULE-PATCHED-RESULT.json.
Build735,7s;47065083904 byte liberi. Il risultato verifica compilazione e
simboli, non l'esecuzione del composer Huawei nel nuovo Android.
