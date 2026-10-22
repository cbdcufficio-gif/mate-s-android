# Politica linker Q per Carrera: condizione ancora da verificare

Verificati nel commit system_core 6d27634866be5b646a8cea1f9abeae902fd831e5:

- rootdir/Android.mk, blob 24b39991aa6923e45ed0a2f37270f34234eeebfa.
- rootdir/etc/ld.config.legacy.txt, blob 5aac61bb96c671217444468107500b46d4a56e4e.

BOARD_VNDK_VERSION definito e BOARD_VNDK_RUNTIME_DISABLE diverso da true
seleziona il ramo VNDK enforced. Senza enforcement, la coppia
PRODUCT_TREBLE_LINKER_NAMESPACES=true e SANITIZE_TARGET vuoto seleziona
VNDK lite. Solo il ramo rimanente usa ld.config.legacy.txt.
Quindi BOARD_VNDK_VERSION vuoto, da solo, non dimostra la selezione legacy.

Il riferimento legacy usa namespace.default.isolated=false e cerca
/system, /product, /vendor e /odm per lib/lib64; mantiene namespace APEX
separati. Consente in linea di principio ai processi mappati al default legacy
di cercare provider di piattaforma come libui/libutils/libutilscallstack.
Non è una prova del caricamento del Mali/HWC né del namespace scelto da un
servizio HAL o dal caricatore EGL.

La configurazione Carrera attuale non definisce BOARD_VNDK_VERSION e installa
vendor sotto system/vendor. Prima di integrare i blob occorre conservare:
valori finali delle variabili linker, ld.config effettivamente prodotto,
mount/symlink /vendor e percorsi/namespace dei processi HAL.
Il nuovo check_legacy_linker.py controlla il file fornito, richiedendo il ramo
legacy atteso e i percorsi system/vendor; non modifica configurazioni.
Se non coincidono, richiede revisione invece di disabilitare l'isolamento.

Il controllo è passato sul riferimento originale; una variante di controllo
con default isolato è stata rifiutata. Il file generato dalla futura build
Carrera non esiste ancora: la politica finale resta non verificata.
Revisione FreeLLMAPI Qwen2.5 Coder 32B, confrontata con le condizioni Make reali.
