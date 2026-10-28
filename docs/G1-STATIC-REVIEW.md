# G1: configurazione pubblica effettiva — 28 ottobre 2026

Prove: [review 40724596747](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/40724596747),
sorgente d5f708441acc8587670aa47ba047fd772318ad4c; dati completi in
[G1-PUBLIC-CONFIG-RESULT.json](G1-PUBLIC-CONFIG-RESULT.json).
Sono letture statiche dei byte della release G0, non prove di runtime.
Nessuna configurazione del prodotto è stata cambiata per questa analisi.

## Contratti osservati

| Area | Prova effettiva | Limite |
|---|---|---|
| Identità | API29/Android10; API di lancio22 in /system/vendor/build.prop; ABI arm64-v8a,armeabi-v7a,armeabi | Non prova la compatibilità degli HAL Huawei |
| Linker | /system/etc/ld.config.txt è il ramo legacy: namespace.default.isolated=false; ricerca system/product/vendor/odm; namespace APEX separati | Non prova closure, simboli C++, ownership, ioctl o caricamento Mali |
| APEX | Sei directory sotto /system/apex: conscrypt, media, media.swcodec, resolv, runtime.release, tzdata | Struttura flattened osservata; attivazione, bind mount e namespace kernel non provati |
| Ramdisk | init da1863008byte; fstab.hi3635, init.hi3635.rc, ueventd.hi3635.rc; nessun init.rc nel cpio | È un primo stadio, non un root completo per init Q |
| Immagine | Layout q-root-with-system; init.rc e sepolicy nella radice ext4, librerie sotto /system | Non è coerente con un semplice mount legacy della partizione su /system |
| Fstab | Riga system su /system con solo wait; userdata latemount,encryptable=footer conservati | Nessun first_stage_mount per system; nessuna prova boot o decrittazione |
| Policy/kernel | Policy pubblica generata presente nella root ext4; kernel diagnostico compilato separatamente | Formato e presenza non provano capability/classi/permessi o enforcing Carrera |

Il digest del linker estratto è
281c997610443078b3d266e6e87207d457e08652053e6f93db56827dd5988a7d.
Il default legacy non elimina l'isolamento dei namespace runtime/conscrypt/media/resolv.
Il nome runtime.release sul disco non dimostra da solo il mount operativo
/apex/com.android.runtime richiesto da bionic.

## Prima correzione da progettare, non ancora applicata

Il [builder Q fissato](https://github.com/LineageOS/android_build/blob/71a47798ac090b81c6b7db0b5c470f1fa3e604cd/tools/releasetools/build_image.py)
in SetUpInDirAndFsConfig combina root e system anche con il flag storico
system_root_image=false. Lo confermano la fixture precedente e l'immagine reale.

Il [first-stage Q fissato](https://github.com/LineageOS/android_system_core/blob/6d27634866be5b646a8cea1f9abeae902fd831e5/init/first_stage_mount.cpp)
filtra il fstab file per first_stage_mount e, se mantiene system, monta
temporaneamente /system e chiama SwitchRoot("/system").
L'attuale fstab non seleziona system nel primo stadio. Un successivo mount
legacy collocherebbe le librerie in /system/system; inoltre il ramdisk non
contiene init.rc. Sono incoerenze statiche, non un punto di arresto misurato sul telefono.

Prossimo esperimento pubblico delimitato:

1. Fixture con il layout reale e i testi init/fstab catturati; controllare il
   comportamento del filtro Q e la transizione alla root dell'immagine.
2. Valutare first_stage_mount per la sola system nella fixture, verificare
   risoluzione by-name/uevent e assenza di un secondo mount errato nel trigger fs.
   Non copiare un fstab moderno né attivare AVB/formattazione.
3. Provare import init, posizione policy e percorsi linker/APEX dopo lo switch;
   confrontare capability necessarie con la configurazione diagnostica effettiva.
4. Solo dopo prove circoscritte applicare una modifica minima al prodotto,
   suite completa/checksum su runner e un build deliberato se necessario.

Non si modifica il formato dell'immagine per far coincidere un vecchio presupposto.
system_image_rootdir_contents_verified=false resta invariato: alcune letture
statiche non certificano tutta la rootdir né il symlink vendor a runtime.

## G2 e confine delle prove

Boot Huawei v0, dtimage e coda stock restano un gate distinto. I metadati pubblici
indicano boot25165824byte, pagina2048, second_size0 e coda36864byte non classificata.
I byte privati non sono disponibili ai runner e non vanno pubblicati: i digest
non permettono di classificare la coda o provare il bootloader.
L'esperimento G1 sopra può continuare pubblicamente; una futura verifica G2
sui contenuti stock richiederà l'ambiente privato autorizzato del proprietario.

G0 è chiuso; G1 e G2 sono aperti. Nessuna boot Q prodotta o ROM funzionante attestata.
