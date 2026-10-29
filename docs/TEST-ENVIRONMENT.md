# Test pubblici completi

I 14 skip locali del 29 ottobre non erano 14 errori di prodotto:
- 10 test ext4: mke2fs/debugfs presenti in /usr/sbin, ma directory assente da PATH.
- 3 test sparse: img2simg/simg2img non disponibili.
- 1 fixture multilib: compiler ARM32/ARM64 non configurati nelle variabili del test.

Con PATH corretto: 131 eseguiti, 127 passati, 4 saltati. Questo dimostra la
causa dei dieci skip ext4. Nessun privilegio root richiesto per queste fixture.

Il workflow manuale complete-public-tests.yml installa su runner pubblico
standard e monouso e2fsprogs, android-sdk-libsparse-utils, patchelf e compiler
cross GNU. scripts/run_complete_tests.py configura PATH e variabili compiler,
richiede tutte le dipendenze e fallisce anche se unittest termina con skip o
expected failure. Nessun albero Android, blob privato o immagine del telefono;
solo piccoli ELF sintetici e filesystem temporanei. Nessun artifact a pagamento.
Il risultato è riportato nei log, non è una prova hardware del port.
