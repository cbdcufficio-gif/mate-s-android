# Prova libc++ di piattaforma riuscita

Run: https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39846064944

182 header originali libc++ Lineage17.1 (4547605 byte), commit
0dfca9975f466d77ebb15f4d3cf4442b15384ae4, usati senza modifiche con
-nostdinc++ al posto degli header C++ NDK. Tutte le otto compilazioni dei
quattro sorgenti Q per ARM32/ARM64 sono riuscite. Il compilatore resta NDK r27d:
questa prova non ricostruisce ancora la toolchain e il runtime completi Q.

Il simbolo StringAppendF ora usa std::__1; nei log degli oggetti non compare
__ndk1. È risolto il problema di namespace dell'esperimento precedente,
non la chiusura di collegamento. Nessuna libreria condivisa collegata, ROM o
prova hardware. Header e oggetti sono stati prodotti sul runner remoto gratuito.

Restano Rect, String16/Unicode, android-base, logging/runtime e successivamente
CallStack/libbacktrace, da collegare con provider effettivi e senza simboli finti.
