# CallStack Q: collegamento ARM32/ARM64 riuscito

Run: https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39851862379

CallStack.cpp e Printer.cpp originali del commit Q system_core
6d27634866be5b646a8cea1f9abeae902fd831e5 compilano per ARM32 e ARM64.
Le due libmates_callstack_probe.so sono collegate con -z defs, contro il
precedente helper grafico, liblog Q compilata e libc++/libbacktrace autentiche
del VNDK29 ufficiale, commit 2e659f04a7cde964415c82dd7507610769165408.

Nessun unwinder fittizio: libbacktrace è un precompilato, non è stata ricostruita
in questa prova. I Git blob e SHA256 dei provider sono verificati e registrati
nel JSON. Anche le prove precedenti vengono ricompilate nello stesso workflow.

Entrambe le librerie esportano i due simboli realmente importati dai candidati
Mali locali: _ZN7android9CallStackC1EPKci e _ZN7android9CallStackD1Ev.
Questo copre 4 riferimenti (costruttore e distruttore per architettura).
È una verifica di presenza dei simboli, non di comportamento/ownership.

La compilazione usa -fno-rtti come negli esperimenti precedenti; la presenza
di metodi virtuali non richiede automaticamente RTTI. I flag aggiuntivi
frtti/fvirtual-function-descriptors proposti da FreeLLMAPI non sono stati usati.
La revisione del modello non costituisce prova di correttezza ABI.

Limiti: nessuna chiamata a update/Unwind eseguita; la chiusura transitiva
libbacktrace/libunwindstack/libbase e i namespace Android restano da verificare.
Il compilatore/runtime C di collegamento è ancora il moderno NDK API29;
libmates_callstack_probe non è il modulo Soong libutilscallstack e non va
installata come suo sostituto. Non sono stati prodotti ROM o immagini flashabili.

Prossimo passo: verificare la chiusura dei provider e il caricamento nel
contesto Android Q, poi costruire i veri moduli/adattatori grafici di piattaforma.
Le librerie sperimentali restano effimere nel runner; report e ricetta sono pubblici.
