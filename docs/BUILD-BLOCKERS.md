# Distanza dalla ROM completa — 23 ottobre 2026

Audit dei file presenti nel progetto, senza scaricare Android né eseguire blob.
Il prodotto attuale è esplicitamente un esperimento di compilazione userspace.
Non esiste ancora evidenza di una build Soong completa o di un system.img Carrera.

## Blocchi osservabili

| Blocco | Evidenza attuale | Risultato necessario |
|---|---|---|
| Sorgenti e build Android | Run Actions [39873522042](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39873522042), commit `277d150a16f391b9964783fcdf922e1fdba0fc5c`: manifest Q fissato a `c7b3d4b65b79e2e0d6a891547ad138e1fcdafb56`, sync riuscito (516,5 s), `lineage_arm64-userdebug` e `m -j2 nothing` riusciti (135,1 s). Il probe ha lasciato 48.843.919.360 byte liberi; non ha costruito il target Carrera né `systemimage`. Le revisioni di ogni progetto risolte sono riportate nel log del run, non sono ancora un lock versionato del prodotto. | Build del prodotto `lineage_carrera` con revisioni sorgente bloccate, misurazione sufficiente di spazio e tempo, `systemimage` reale e log riproducibile. |
| Boot image esclusa | `BoardConfig.mk`: `TARGET_NO_KERNEL := true`, nessun `BOARD_PREBUILT_BOOTIMAGE`, nessuna ricetta Carrera per kernel/ramdisk/DTB. | Parametri estratti dalla boot effettiva, DTB Carrera identificato, integrazione kernel e ramdisk Q, verifica dimensioni e struttura Huawei. La boot stock acquisita non è una boot Android 10. |
| Ramdisk e policy | `device.mk` non copia init/fstab/ueventd; nessun percorso di policy Carrera nel BoardConfig. | Mount corretti, cifratura, permessi nodi, servizi e policy SELinux caricabile/enforcing. Revisionare i comportamenti che possono scrivere firmware al primo avvio. |
| Grafica non caricata da Q | Solo quattro prebuilts Huawei e cinque moduli HIDL; prove precedenti sono compilazioni/link parziali. | Build dei moduli reali con controlli ELF, linker finale, ABI e caricamento dei blob, allocazione buffer/fence, composizione e resume provati. |
| HAL oltre la grafica | Manifest VINTF contiene solo allocator, mapper, composer; il prodotto non integra radio, audio, camera, Wi-Fi, Bluetooth, GNSS, sensori e protezione chiavi. | Servizi e dipendenze effettivi, dichiarazioni VINTF coerenti, init/policy/configurazioni, test della matrice hardware. |
| Risorse e distribuzione | Solo capacità del runner misurata; nessun fabbisogno reale del sync/build. I blob sono locali e il runner pubblico non li possiede. | Misure reali entro budget e un percorso privato per l'assemblaggio locale finale; non pubblicare dump o blob per sbloccare un job. |

## Verifica sul sorgente del sistema di build

Nel [Makefile LineageOS fissato a commit](https://github.com/LineageOS/android_build/blob/71a47798ac090b81c6b7db0b5c470f1fa3e604cd/core/Makefile#L1069)
(blob `f6c24634393f8577d0225e119371335c3e4ed2ef`, righe 1069–1079),
`TARGET_NO_KERNEL=true` senza `BOARD_PREBUILT_BOOTIMAGE` svuota
`INSTALLED_BOOTIMAGE_TARGET`. Aggiungere solamente `BOARD_PREBUILT_BOOTIMAGE`
alla configurazione attuale fallirebbe inoltre sul controllo
`BOARD_BUILD_SYSTEM_ROOT_IMAGE != true`. Non modificare la geometria di boot
per aggirare quel controllo: occorre una vera integrazione Carrera.

`TARGET_NO_BOOTLOADER=true` non implica che al telefono manchi il bootloader:
esclude la sua costruzione. Non occorre svilupparne o sostituirne uno per questo
port. Analogamente `BOARD_VNDK_VERSION` vuoto è una scelta legacy da verificare
contro il linker finale, non un errore da correggere impostando una versione
arbitraria. Vedere `LINKER-POLICY.md`.

## Percorso pratico a costo zero

Usare il repository pubblico e i runner standard già misurati per compilare
sorgenti pubblici e verificare il grafo Android; mantenere stock, blob e
assemblaggio finale sul PC. Il primo lavoro remoto utile è un tentativo
**limitato e misurato** di sincronizzazione superficiale dei progetti necessari,
con interruzione prima di esaurire il disco e registrazione di ogni commit.
Servono poi compilazione della piattaforma e risoluzione dei primi errori Soong.
Le ricette che dichiarano prebuilts Huawei non possono essere eseguite sul
runner pubblico privo di quei file: i relativi controlli finali restano locali.

La misura precedente di 105,1 GiB liberi non prova che Android completo entri
nel runner. Se sorgenti e output non entrano nei limiti gratuiti verificati,
il percorso richiede una macchina già disponibile o concessa gratuitamente con
spazio adeguato; non è corretto promettere che spezzare i job risolva da solo
il grafo o lo storage. Nessun servizio a pagamento, cache o archivio remoto
grande deve essere attivato come soluzione implicita.

Per limitare il disco del PC, trasferire solo gli output pubblici strettamente
necessari all'assemblaggio e conservarne gli hash; la procedura di assemblaggio
e consegna gratuita deve ancora essere implementata e verificata. Non è
attualmente una pipeline capace di produrre la ROM in un comando.

Una build riuscita resta distinta dall'avvio sul Mate S. La ROM completa
richiede il percorso di recupero e le prove elencate in `HARDWARE-MATRIX.md`.

## Revisione delegata

Consultato FreeLLMAPI Qwen2.5 Coder 32B (esecuzione
`4c2cdd30-9876-4591-99d1-575263b86745`, 533 token dichiarati).
Scartate le raccomandazioni di considerare bootloader/recovery mancanti sul
telefono e di impostare VNDK per garantire compatibilità: non seguono dai file.
Nessuna configurazione del prodotto è stata cambiata senza una soluzione provata.
