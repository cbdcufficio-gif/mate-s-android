# Dipendenze Q: 16 compilazioni riuscite

Prova: https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39847284731

Region, VectorImpl, SharedBuffer, String8, Rect, String16, Unicode e stringprintf
originali compilano per ARM32/ARM64 con header libc++ di piattaforma.
Anche i due collegamenti relocatable intermedi riescono. I riferimenti a Rect,
String16, conversioni Unicode e StringAppendF sono ora risolti fra questi oggetti.

Correzione rispetto al report precedente: graphics-base.h, graphics-base-v1.0.h,
graphics-base-v1.1.h e graphics-base-v1.2.h sono già conservati nel commit
6d27634866be5b646a8cea1f9abeae902fd831e5 di LineageOS/android_system_core,
directory libsystem/include/system. Il recupero automatico ignorava gli include
relativi: non occorre rigenerarli con HIDL per questa prova.
La ricerca nel pacchetto VNDK non è stata necessaria alla soluzione.

Restano indefiniti i provider libc++, liblog, libc e il runtime del compilatore,
inclusi helper atomici ARM64. Il collegamento -r ammette tali riferimenti:
non equivale al collegamento completo di una libreria condivisa.
Non sono stati prodotti boot.img, system.img o una ROM, né eseguito codice sul telefono.

Prossimo passo: usare provider Q verificati per ciascuna architettura e richiedere
assenza di simboli irrisolti al collegamento condiviso. Nessun simbolo fittizio
o rinomina di namespace per superare il controllo. Il moderno compilatore NDK
resta una limitazione dell'esperimento rispetto alla toolchain Q originale.

Il report completo della prova è nei log GitHub; la copia locale si trova in
out/layout-review/rect-success.json. FreeLLMAPI è stato consultato per la ricerca
degli header; la soluzione è stata verificata direttamente nel sorgente e compilata.
