# Catena VNDK29: audit statico completato

Run: https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39852629910

Su ARM32 e ARM64, seguendo ricorsivamente DT_NEEDED da libbacktrace.so,
sono stati recuperati libbacktrace, libunwindstack, libbase, libc++ e liblzma
dal commit ufficiale VNDK29 2e659f04a7cde964415c82dd7507610769165408.
Ogni file è stato verificato per Git blob, SHA256, architettura e SONAME.
Totale scaricato sul runner: 2698412 byte, nessun binario eseguito.

Nessuna libreria DT_NEEDED manca nella parte VNDK della catena.
Il confine esplicito non verificato comprende libc.so, libm.so, libdl.so e
liblog.so: la chiusura completa non è certificata.

Per ciascun consumer sono stati confrontati nomi/versioni degli import con
gli export dei soli provider raggiungibili nel grafo. Il report conserva i
conteggi di import forti senza candidato: includono i provider di sistema
esclusi e non dimostrano che le librerie siano difettose.
Gli esempi dettagliati rimangono nei log e nel report locale.

Questa prova completa l'inventario delle dipendenze indirette VNDK richieste
dall'esperimento CallStack. Non verifica namespace, ordine di risoluzione,
interposizione, relocazioni, dipendenze caricate con dlopen o comportamento
di unwinding. Non è stata prodotta né installata una ROM.

Prossimo requisito: fornire e verificare i provider di sistema Q reali e
provare il caricamento in un ambiente Android controllato, poi passare ai
moduli grafici di piattaforma. Ricetta e metadati sono pubblici; i provider
binari restano sul runner. FreeLLMAPI è stato usato per la revisione del metodo.
