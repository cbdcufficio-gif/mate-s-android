# Espansione delle dipendenze Q

Aggiornamento: [Rect e le 16 compilazioni ora passano](RECT-RESULT.md).
La necessità di generare nuovi header indicata sotto era una diagnosi errata:
i file originali erano già conservati nel commit e mancava il recupero
degli include relativi nel nostro script.

Run: https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39846595995

Aggiunti String16.cpp, Unicode.cpp, stringprintf.cpp e Rect.cpp originali.
14 compilazioni su 16 riuscite: i tre primi sorgenti compilano su ARM32/ARM64;
Rect.cpp si ferma per graphics-base.h, header generato HIDL richiesto da
system/graphics.h. Non è stata inserita una definizione fittizia per superarlo.

Il collegamento relocatable parziale non certifica la chiusura: mancano Rect
e i provider runtime. Il job termina correttamente con errore se una delle
16 compilazioni fallisce. Il precedente risultato di 8 oggetti rimane valido.

Prossimo requisito concreto: generare gli header grafici con gli strumenti
HIDL della piattaforma Q, oppure recuperarli da una build Q riproducibile
verificandone provenienza e versione. Poi ripetere Rect e controllare tutti
i simboli ancora indefiniti. Nessuna libreria condivisa o ROM prodotta.
