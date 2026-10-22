# Grafica B321 → Q: confronto statico, 22 ottobre 2026

Aggiornamento: [esperimento compilato ARM32/ARM64](HEADER-EXPERIMENT.md).
Dimensioni e allineamenti dei sette tipi di riferimento coincidono; quattro
implementazioni Q compilano e coprono i 54 import selezionati Region/VectorImpl.
Il punto 1 sotto è completato per i riferimenti e la toolchain documentati,
ma non certifica gli header effettivi Huawei B321.

Gli otto candidati grafici presenti localmente sono stati ricontrollati contro
gli hash stock, le dipendenze previste e i payload originali. Il risultato è
strutturale: non è una prova del linker Android né di rendering sul telefono.

## Region e CallStack

Il Mali ARM32 importa `Region::getArray(unsigned int*)`; ARM64 usa
`Region::getArray(unsigned long*)`. Il riferimento Q dichiara `getArray(size_t*)`.
Questa differenza nei nomi mangled è coerente con size_t nelle due ABI; non
giustifica una rinomina tra i due simboli e non consente di mescolare librerie
ARM32 e ARM64.

I riferimenti Region di CM13 e Lineage17.1 hanno entrambi un membro
`Vector<Rect> mStorage` e una base `LightFlattenable<Region>`. Le dichiarazioni
dei metodi effettivamente importati da Mali/HWC sono presenti nel riferimento Q.
La variante dump con String8 è diventata std::string e getSharedBuffer è stato
rimosso; questi nomi non compaiono fra gli import dei candidati esaminati.

CallStack dei riferimenti M e Q mantiene `Vector<String8> mFrameLines` e le
firme del costruttore/distruttore importati da Mali. Q aggiunge helper statici
weak e un deleter. Le aggiunte statiche non dimostrano una variazione del layout
di istanza. L'implementazione Q è in libutilscallstack: la dipendenza aggiunta al
candidato Mali resta da compilare e verificare nel namespace effettivo.

Non sostituire Region/CallStack con classi finte o semplici malloc/free.
La presenza dei nomi non dimostra dimensione degli oggetti, offset, ownership,
allocator, vtable, chiamate di ritorno per valore o comportamento dei metodi.
CM13/AOSP sono riferimenti; non sono necessariamente gli header esatti Huawei B321.

## Verifiche che mancano

1. Vector, VectorImpl, SharedBuffer, String8, Rect/Point e LightFlattenable nei due
   alberi; confrontare sizeof, alignof e offset con toolchain ARM32/ARM64 corrette.
2. Disassemblato dei callsite nei blob reali: spazio riservato agli oggetti,
   costruzione/distruzione, ownership, passaggio per valore e accessi inlined.
3. Export e versioni delle librerie Q effettivamente compilate, chiusura
   DT_NEEDED e namespace di ciascun servizio. Non mescolare provider stock e Q
   per ottenere artificialmente copertura di simboli.
4. Contratti gralloc/native_handle, formati/stride, ION ioctl Huawei, cache e fence.
   Un'eventuale libreria privata libion deve conservare i contratti reali;
   il nuovo SONAME da solo non isola l'interposizione dei simboli.
5. Test di caricamento e rendering soltanto dopo build e packaging verificati.

## Riferimenti sorgente verificati

| File | Riferimento | Git blob SHA |
|---|---|---|
| Region M | LineageOS/android_frameworks_native, cm-13.0, include/ui/Region.h | 2a1491837dc78e2f9fa60c267dd394e6c8bb6792 |
| Region Q | LineageOS/android_frameworks_native, lineage-17.1, libs/ui/include/ui/Region.h | 79642ae03249f69200b6e6ac703d343a47c8962c |
| Region.cpp Q | stesso repository/ramo, libs/ui/Region.cpp | 55e3b99aa17d64f0108d8d08e69763da97d18e24 |
| CallStack M | aosp-mirror/platform_system_core, android-6.0.0_r1, include/utils/CallStack.h | 27e89f4622c8dc827205f9fcbcf53744ace7c882 |
| CallStack Q | LineageOS/android_system_core, commit 6d27634866be5b646a8cea1f9abeae902fd831e5 | 7a4a345d05a609da72ca62d18108d15ef7febd47 |

Le copie di consultazione e i report dettagliati rimangono negli output locali;
i blob proprietari non sono stati pubblicati. I rami sono mobili: i blob SHA
identificano il contenuto letto, senza certificare un albero Android completo.
