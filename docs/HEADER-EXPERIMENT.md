# Header e sorgenti grafici originali: risultato del 22 ottobre 2026

Esperimento remoto riuscito:
https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39844806800

Su runner pubblico standard ubuntu-22.04, NDK r27d (27.3.13750724),
clang C++17, target Android API23 per M e API29 per Q. Sorgenti fissati in
configs/layout-sources.json. Sono stati scaricati 358171 byte di header e
sorgenti originali; nessun checkout Android completo. Nessun blob Huawei
caricato su GitHub, cache o artifact a pagamento, installazione locale o flash.

## Misure effettive

Dimensioni identiche fra i riferimenti CM13 e Lineage17.1:

| Classe | ARM32 byte/allineamento | ARM64 byte/allineamento |
|---|---:|---:|
| Region | 20 / 4 | 40 / 8 |
| CallStack | 20 / 4 | 40 / 8 |
| VectorImpl | 20 / 4 | 40 / 8 |
| SharedBuffer | 16 / 4 | 24 / 8 |
| String8 | 4 / 4 | 8 / 8 |
| Rect | 16 / 4 | 16 / 4 |
| Point | 8 / 4 | 8 / 4 |

Le misure derivano da sizeof/alignof compilati in array e dalle dimensioni dei
simboli ELF, senza eseguire codice ARM. Il dump del compilatore conferma per
VectorImpl vptr all'offset 0 e membri mStorage/mCount/mFlags/mItemSize agli
offset 4/8/12/16 (ARM32), 8/16/24/32 (ARM64), nei due riferimenti.
Region contiene il Vector all'offset 0; CallStack contiene mFrameLines all'offset 0.

## Compilazione delle implementazioni Q

Region.cpp, VectorImpl.cpp, SharedBuffer.cpp e String8.cpp originali compilano
senza modifiche per entrambe le architetture: 8 oggetti relocatable.
Non sono librerie Android collegate, né moduli prodotti da Soong.
CallStack.cpp non è stato compilato: resta da costruire libutilscallstack.

Confrontando gli oggetti con gli 8 candidati grafici locali, tutti i 54 import
selezionati per nome di classe sono presenti: 7 riferimenti di Mali e 20 di HWC
per architettura, relativi a Region/VectorImpl. La selezione cercava anche String8
e SharedBuffer, senza import diretti corrispondenti. Non è una verifica della
tabella dinamica finale, delle versioni dei simboli, della visibilità dopo linking,
dei namespace o della chiusura delle dipendenze. Non giustifica uno shim fittizio.

## Differenze semantiche ancora da verificare

SharedBuffer mantiene gli offset, ma Q usa std::atomic<int> per mRefs e cambia
acquire/release; dealloc passa da ssize_t a void e rimuove il controllo sul
contatore. Q include controlli di overflow in alloc/editResize.
L'assenza di import diretti negli 8 candidati non esclude accessi inlined o
dipendenze indirette. CM13 non è il sorgente Huawei B321; la toolchain moderna
non riproduce automaticamente l'ABI storica del produttore.

## Riproduzione

Il workflow header-layout.yml compila senza collegare né eseguire i risultati.
Il report completo e i dump sono nei log e nel riepilogo del job.
La comparazione locale usa scripts/compare_layout_symbols.py con il report JSON
e la directory dei candidati già presenti sul PC; esporta solo metadati.

Due errori iniziali del recupero header sono stati corretti usando logging e
backtrace della stessa versione, ARect e RegionHelper originali. Una prima prova
delle implementazioni aveva sei successi e due errori: ora il workflow richiede
esplicitamente otto compilazioni riuscite prima di terminare con successo.

## Uso FreeLLMAPI

Sei consultazioni riuscite su Qwen2.5 Coder 32B e GPT-OSS 120B, 13069 token
dichiarati dal gateway in questa prosecuzione. Analisi, confronto dei sorgenti
e revisione; risposte grezze conservate localmente. Sono stati respinti il
programma iostream come metodo di estrazione delle dimensioni, la formula che
ometteva il vptr, modifiche inutili al controllo delle directory e conclusioni
non dimostrate sulla compatibilità Huawei. Il confronto SharedBuffer è stato
integrato con le differenze omesse dal modello.

## Prossime verifiche necessarie

Collegare veri provider Q con dipendenze e simboli corretti; costruire
libutilscallstack e gli adattatori HWC; confrontare il disassemblato Huawei con
i layout misurati; verificare ION, gralloc, fence e namespace. Quindi init,
SELinux, DTB Carrera, packaging e test hardware controllati.
Nessuna boot.img/system.img o ROM installabile prodotta in questo esperimento.
