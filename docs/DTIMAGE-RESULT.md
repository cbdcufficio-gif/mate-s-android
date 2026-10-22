# Analisi statica della partizione dtimage — 23 ottobre 2026

L'immagine locale acquisita misura 33.554.432 byte, SHA256
`c89beda2d1f0bcdd54b680f8602ed4d0db5a1819427287f5943b4530364e6bb3`.
Lo script `scripts/dtimage_inspect.py` legge solamente file locali e produce
metadati; non estrae, sceglie, carica o installa un DTB sul telefono.

## Tabella e candidati trovati

Intestazione `HSDT`, versione little-endian 1, conteggio dichiarato 121.
La struttura della tabella è **inferita dai byte**, non da una specifica Huawei:
121 record da 24 byte a partire dall'offset 12.

| Campo relativo al record | Interpretazione verificata |
|---|---|
| 0–3 | Quattro byte coincidenti con le quattro celle big-endian `hisi,boardid` del FDT puntato |
| 4–7 | Significato sconosciuto, conservato nel rapporto |
| 8–11 | Dimensione allocata, uint32 little-endian |
| 12–15 | Offset del FDT nell'immagine, uint32 little-endian |
| 16–23 | Significato sconosciuto, conservato nel rapporto |

Tutti i 121 record puntano a FDT v17 strutturalmente validi, contenuti nelle
rispettive dimensioni allocate; gli intervalli non si sovrappongono e tutti i
boardid coincidono con il record. Il parser verifica header, limiti, reserve
map, blocchi stringhe/struttura, token, proprietà e terminazione.

Una scansione indipendente della partizione trova **127 FDT validi**:
121 referenziati dalla tabella e 6 non referenziati. Questi ultimi possono
essere residui, ma la loro origine non è dimostrata. Gli offset sono
26200064, 26456064, 26716160, 26972160, 27232256, 27488256;
i rispettivi boardid sono [1,8,9,2], [1,8,9,4], [1,8,9,1], [1,8,9,3],
[1,8,9,6], [1,8,9,0]. Non sono promossi a membri della tabella.

## Corrispondenza con il boardid osservato

L'input acquisito da `/proc/device-tree/hisi,boardid` è
`00000001000000040000000700000006`, cioè **[1,4,7,6]**.
Esiste un solo FDT con questo boardid nella scansione:

| Metadato | Valore |
|---|---|
| Record HSDT, indice da zero | 73 |
| Offset nell'immagine | 15808512 |
| Dimensione FDT | 212482 byte |
| Spazio allocato dal record | 212992 byte |
| SHA256 dei soli byte FDT | `0f473f2c633ecfcc621fd311fc5d48a39ca66aa375119f077e901a8dbd1eff6e` |
| model | `hi3635` |
| compatible | `hisilicon,hi3635` |
| Versione FDT / ultima compatibile | 17 / 16 |

È una corrispondenza statica utile per il port Carrera. Non prova l'algoritmo
con cui il bootloader sceglie o modifica il DTB, né l'identità completa con
l'albero attualmente attivo. `model` e `compatible` indicano la famiglia SoC e
non distinguono da soli il Mate S dagli altri dispositivi Hi3635.
I due campi ignoti della tabella restano ignoti. Nessuna immagine viene
preparata per il flash da questo risultato.

## Riproducibilità e limiti

Il rapporto completo rimane locale in
`out/stock-boot-20261023/dtimage-inspection.json`; non contiene payload e non
viene pubblicato automaticamente. Script eseguito sull'immagine reale:
121 record verificati, 127 candidati validi, zero magic FDT rifiutati.
Undici test sintetici passano, inclusi troncamenti, proprietà fuori limite,
blocchi sovrapposti, struttura sbilanciata, tabella incoerente e candidato
non referenziato. Nessun dato Huawei è incluso nei test.

FreeLLMAPI Qwen2.5 Coder 32B ha rivisto il metodo di validazione
(esecuzione `19ac4874-0731-4466-bbdf-a451b99ae67d`, 385 token dichiarati).
Le evidenze derivano dal parser e dai byte locali, non dalla risposta LLM.
