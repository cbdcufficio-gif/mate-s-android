# Collegamento condiviso ARM32/ARM64 riuscito

Run: https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39850823370

Prodotti sul runner due libmates_graphics_probe.so, una per architettura,
collegate con -shared -z defs. Contengono gli otto sorgenti Q già verificati;
il nome non è libui o libutils e non sono sostituti installabili di queste librerie.

Provider C++: libc++.so originale VNDK29 dal repository ufficiale AOSP,
commit 2e659f04a7cde964415c82dd7507610769165408, con verifica del Git blob
e SHA256. Logging: liblog.so compilata dai 17 sorgenti target Android del
commit system_core già fissato, senza logger fittizio host, con version script
originale. Totale 34 compilazioni logging riuscite oltre alle 16 della grafica.

La prima prova con stub NDK liblog mancava di __android_log_error_write.
Compilando l'implementazione Q completa il problema è stato risolto.
Il recupero della sorgente usa un checkout shallow, blob-filtered e sparse
sul runner; il primo tentativo di archivio completo è stato interrotto al
limite di download. Un header FastStrcmp mancante è stato aggiunto dagli
stessi sorgenti originali.

Un controllo negativo con una funzione deliberatamente inesistente deve
fallire prima del collegamento reale: è fallito come previsto per entrambi i target.
Metadati dinamici, versioni dei simboli, comandi e hash sono nel report JSON.
Le librerie condivise conservano normali import dinamici soddisfatti dai provider:
-z defs non significa che la tabella degli import sia vuota.

Limiti: compilatore e libc/libm/libdl di collegamento derivano dal NDK r27/API29,
mentre header libc++ e sorgenti sono Q e libc++ è un precompilato VNDK29.
Non è ancora una build Soong della piattaforma né prova di caricamento, namespace,
ownership, rendering, compatibilità dei blob Huawei o funzionamento sul telefono.
Il collegamento non dimostra la chiusura transitiva a runtime dei provider.
Gli oggetti binari della prova restano effimeri nel runner; il workflow è
riproducibile e i report sono pubblici. Nessuna ROM, boot.img o system.img prodotta.

Prossimo lavoro: costruire CallStack/libbacktrace e poi i moduli/adattatori
grafici reali di piattaforma, mantenendo distinti prova sperimentale e componenti
destinati alla ROM. Nessuna libreria proprietaria pubblicata e nessun flash.
