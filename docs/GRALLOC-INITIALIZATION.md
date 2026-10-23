# Inizializzazione gralloc ARM64 — analisi statica

File candidato ARM64 SHA256: `bd2c5df671541f84231c24c0de565d85e7cbefa00a4659584d5d8fdcc6007d1f`.

Il modulo ARM64 dichiara **gralloc 0.3** dopo la propria inizializzazione.
Il precedente risultato HMI_NOT_UNIQUELY_FILE_BACKED resta corretto per la
sola lettura del file: il simbolo risiede in BSS ed e inizializzato dal codice.
Non bisogna interpretare gli zeri iniziali come versione0.0.

Catena verificata con llvm-readelf-19 e llvm-objdump-19 sui candidati locali:

1. DT_INIT_ARRAY=0x17b18, dimensione8. La rilocazione relativa dell'unica voce
   indica la funzione0x2000; la voce0x17b20 appartiene invece a FINI_ARRAY.
2. La funzione0x2000 carica il GOT a0x17fd8, rilocato GLOB_DAT verso
   HMI=0x18038, e salta al costruttore private_module_tC1Ev.
3. C1 e C2 sono alias esportati a0x2890. Il costruttore salva this in x19.
   A0x28dc scrive il tag HWMT; a0x2900 prepara valore3 e a0x2908 lo scrive
   con strh a[this+4]. A0x2938 scrive zero con strh a[this+6].
4. Secondo hardware.h, questi sono rispettivamente module_api_version e
   hal_api_version. Quindi 0x0003 e versione modulo0.3; hal_api_version=0.
   A0x2904 imposta inoltre il puntatore methods all'indirizzo0x18008,
   che ha una rilocazione relativa alla funzione0x2718.

Nessun blob e stato eseguito. Disassemblato completo e rilocazioni restano
locali in out/gralloc-init, esclusi dalla pubblicazione.

Il [GrallocLoader di Android Q](https://github.com/LineageOS/android_hardware_interfaces/blob/02951860e9c95f19384fa07522925537d8c17a18/graphics/mapper/2.0/utils/passthrough/include/mapper-passthrough/2.0/GrallocLoader.h)
calcola major=(module_api_version>>8)&0xff e seleziona Gralloc0Hal per major0.
Il valore osservato corrisponde quindi al percorso legacy. La versione HIDL
mapper2.0 identifica il servizio esterno e non richiede che il modulo Huawei
sia gralloc2. Nessuna modifica del numero versione del blob e necessaria.

Restano da provare caricamento, callback, layout buffer privati, fence,
formati, allocazione e mapping reali. La variante ARM32 non e stata analizzata
qui. Questo rapporto non prova compatibilita runtime o successo di open.

Il Gralloc0Hal mapper Q usa mMinor=module_api_version&0xff e controlla
la presenza delle callback async prima di usarle con minor>=3. L'allocator
Gralloc0Hal chiama gralloc_open: il solo valore0.3 non ne prova il successo.
Fonti: graphics/mapper/2.0/utils/passthrough/include/mapper-passthrough/2.0/Gralloc0Hal.h
(blob7369ac759322009c5f4ddda4b62d57eba9d8b3f4) e allocator equivalente
(blob6c179be722fd0a0f453479da8440464c952df7a7), hardware/interfaces commit
02951860e9c95f19384fa07522925537d8c17a18.
