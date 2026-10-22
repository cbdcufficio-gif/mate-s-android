# Prossimo collegamento: vincolo rilevato

Analisi dei simboli degli otto oggetti della prova precedente: la chiusura
non è completa. Mancano implementazioni Rect, String16, Unicode, logging,
runtime C/C++ e android::base::StringAppendF, oltre ad altri simboli elencati
nel report locale out/layout-review/link-closure.json.

In particolare StringAppendF usa std::__ndk1 negli oggetti NDK. Questo è un
segnale concreto che questi oggetti non vanno distribuiti come librerie di
piattaforma Q: occorre ricompilare con la configurazione libc++ della piattaforma
e verificarne i simboli effettivi. Non rinominare i simboli per aggirare il problema.

Il riferimento verificato system_core/libutils/Android.bp, commit
6d27634866be5b646a8cea1f9abeae902fd831e5, definisce libutilscallstack con
CallStack.cpp e dipendenze libutils/libbacktrace. La sola compilazione dei
quattro sorgenti precedenti non soddisfa questi requisiti.

Prossimo esperimento circoscritto: ricostruire la chiusura minima con toolchain
e libc++ di piattaforma, richiedendo risoluzione completa al collegamento;
poi integrare CallStack e libbacktrace. Nessuna libreria caricabile o ROM
prodotta da questa analisi. Consultazione FreeLLMAPI: Qwen2.5 Coder 32B,
2019 token dichiarati; decisioni basate sui simboli reali e Android.bp.
