# Kernel: nuova compilazione remota riuscita

[Run39924712678](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39924712678),
23 ottobre2026: entrambi i comandi build_kernel.py sono terminati con successo,
con marker IMAGE_COMPILED_OFFLINE e creazione delle Image ARM64.

| Profilo | SHA256 Image riportato nel log |
|---|---|
| stock | 51490e439a2abfd0545c2f815bbe81df00c3ff05f061ec0498108651bf0fcd04 |
| android10-diagnostic | 53cb735c13afadf852df72d42788f51170c5ec73e0693d5b02a9fa40d715b56f |

Sorgente e compilatore sono quelli fissati in sources.lock.json. Lo script
verifica la patch, il compilatore e i valori di configurazione richiesti.
Questi hash appartengono a questo ambiente di compilazione: non sono stati
assunti uguali a quelli delle compilazioni precedenti.

Corretto il percorso della patch nel workflow: git -C risolveva il vecchio
percorso relativo nella cartella kernel. Il nuovo percorso parte dal workspace
remoto. Il nuovo run supera sia fetch/patch sia compilazione.

I log mostrano anche un export OM_Printf duplicato e8 section mismatch.
Non sono errori fatali della compilazione, ma non costituiscono prove di
correttezza runtime. Nessun kernel e stato avviato sul Mate S.

Il workflow conserva log/riepilogo, non gli eseguibili della VM effimera.
Non e stata creata una boot.img; nessun file di questo run e installabile
sul telefono come ROM Android10. Recupero e compatibilita hardware restano
quelli descritti in BOOT-RESULT.md e HARDWARE-MATRIX.md.
