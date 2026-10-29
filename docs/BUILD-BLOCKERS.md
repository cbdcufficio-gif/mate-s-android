# Blocchi prioritari verso la ROM Carrera

Direzione vigente: [PORTING-DIRECTION.md](PORTING-DIRECTION.md).
Revisione e priorità aggiornate: [REVIEW-2026-10-29.md](REVIEW-2026-10-29.md).
Stato dei gate: [PORTING-STATE.json](PORTING-STATE.json).
La cronologia delle prove precedenti è in [STATUS.md](STATUS.md).

| Priorità | Blocco | Prossima prova che riduce l'incertezza |
|---|---|---|
| G0 | Chiuso: base pubblica verificata sui byte, non ROM | Sistema40696459171; review40724596747; CARRERA-SYSTEM-RESULT.json |
| G1 | Cache directory corretta nei sorgenti ma non ricompilata; capability SELinux, bootstrap/APEX runtime e ordine USB autenticato restano aperti | REVIEW-2026-10-29.md: fixture first-stage passata; nuovi contratti da provare prima del rebuild deliberato |
| G2 | Nessuna boot Q Carrera verificata | Formato v0, coda stock, DT handoff, dimensioni intere e percorso di recupero |
| G3 | Kernel diagnostico e init Q mai avviati | Nuovo kernel identificato, policy/mount/Binder e ADB autenticato con log |
| G4 | Buffer/ION/fence, ABI C++, EGL/HWC, display e touch non provati in Q | Prove incrementali di caricamento, allocazione, rendering e resume |
| G5 | Radio, audio, camera, rete, TEE e periferiche non integrati completamente | Una closure/servizio e un test funzionale per volta; camera/radio/TEE hanno alta incertezza |
| G5/G6 | Alimentazione, termica, cifratura, stabilità e app | Protezioni preservate, policy enforcing, dati recuperabili e matrice hardware/utente registrata |
| G6 | Consegna installabile e rollback non provati | Pacchetto corrispondente al candidato testato e procedura di recupero documentata |

## Errori concettuali da non ripetere

- La build pubblica esclude i blob Huawei: non diventa ROM completa aggiungendo
  un nome versione o confezionando kernel e system senza integrazione.
- I moduli sono controllati dentro ext4; `/vendor` è controllato separatamente
  nello staging root. Non attribuire al controllo ext4 una prova del link
  runtime o dell'intero primo stadio che lo script non esegue.
- Il kernel TWRP 3.10.74 non è il kernel stock 3.10.86 né il nuovo diagnostico.
  Le sue syscall assenti non dimostrano che manchino nel sorgente candidato.
- Il numero 3.10 non impone da solo gralloc4, kernel4.14, eBPF o una nuova
  partizione vendor. Usare le capacità e i contratti effettivi.
- Uguale POLICYVERS=30 non certifica capability/classi SELinux. Uguali nomi di
  simboli non certificano C++ ABI, ownership o semantica dei buffer.
- Conservare firmware/driver e isolare componenti legacy è una strada ibrida
  ragionata; copiare ART/bionic/libbinder Android6 sopra Q non lo è.

## Gate boot specifici

Stock usa pagina 2048, second_size=0 e dtimage HSDT separato. Il helper locale
non tracciato che mette un DTB in second non è un packager Carrera valido.
Il candidato TWRP per prova RAM da 26003456 byte supera boot da 25165824 byte:
non usarlo come immagine boot persistente. Il ramdisk Q è un componente distinto.
La coda stock da 36864 byte non è classificata; la corrispondenza DTB statica non
certifica la selezione del bootloader. Vedere BOOT-RESULT.md e DTIMAGE-RESULT.md.

Fastboot boot è già stato rifiutato con Command not allowed: non ripetere lo
stesso tentativo o comandi OEM casuali. Recovery ufficiale identificata e rientro
in TWRP non provano ancora il rollback completo dopo una ROM fallita.

Le guardie firmware touch testate coprono i percorsi modificati, non ogni
possibile scrittura firmware del sistema. Nessun flash/erase/format/restore o
riavvio automatico, nessuna rimozione dei controlli per un risultato verde.
