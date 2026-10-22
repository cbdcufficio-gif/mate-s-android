Aggiornamento 23 ottobre: acquisizione boot/DTB e prova grafo Android; vedere BOOT-RESULT.md e BUILD-BLOCKERS.md.

Aggiornamento 22 ottobre: [compilazione ARM32/ARM64 degli header e di quattro implementazioni Q](HEADER-EXPERIMENT.md), con 54 import selezionati coperti. Nessuna ROM installabile ancora prodotta.

# Stato verificato — 22 ottobre 2026

## Prosecuzione desktop

Ora i candidati grafici reali sono presenti e tutti e otto sono stati verificati
strutturalmente contro il lock B321. Non occorre reinviare l'archivio richiesto
nella sezione storica più sotto. Nuove evidenze e metodi: ZERO-COST-PLAN.md,
ABI-REVIEW.md e SESSION-20261022.json.

Repository pubblico creato: https://github.com/cbdcufficio-gif/mate-s-android.
Due workflow remoti riusciti: 4 CPU, circa 16 GB RAM e 105,1 GiB liberi dopo
pulizia SDK della VM e installazione cross compiler. Tutti i 21 test passano nel
runner con zero skip. Localmente: 20 passati e uno saltato per cross compiler.
Nessuna build Android completa/moduli Q, boot.img, ROM installabile o prova hardware.

## Risultati precedenti

## Compilato e testato

Kernel Huawei/Hi3635 3.10.86, commit
`3fe1625bed89c034996842c1af696ba9bc50d8a9`, con correzione locale
dell'include Immersion. Due compilazioni complete ARM64 riuscite:

| Profilo | SHA256 della Image |
|---|---|
| Config stock | `7448449bc64a44902c4ab7cb6b4ee279237acd6b3e0c3e25b5e95fa7c75345ce` |
| android10-diagnostic | `46e884abb2959be92238f09611f8d512b9ef405be4bbd6ba453c23a10a91458f` |

La seconda Image misura 21.369.416 byte. La configurazione effettiva ha SHA256
`2d8f144062b9b44b00762ae6d6274e1e7753bc9208d9ab74b3687e0a2e3a65c2`.
Comandi, sorgente e compilatore sono registrati in kernel-build-report.json.
Il sorgente pubblico non è dimostrato identico alla release B321 installata.

19 test automatici riusciti senza skip: parser ELF, GNU symbol versions,
alterazioni di codice/indirizzi, risoluzione dipendenze, controllo symlink/hash,
preparazione grafica sintetica ARM32+ARM64 e audit kernel. Anche 46 librerie
ARM32 reali della recovery sono state lette dal parser. Queste prove non
dimostrano caricabilità dei blob grafici B321 in Android 10.

## Ancora da dimostrare

- Build dei moduli grafici e dell'intero Android; nessun system.img prodotto.
- Loader, namespace, ABI C++, GPU, HWC e ioctl con i blob reali.
- Init, servizi, politica SELinux e VINTF completi di Carrera.
- Packaging Huawei della boot image, coda/firme e selezione del DTB stock.
- Percorso di recupero provato, avvio hardware e tutti i componenti della matrice.
- Supporto fastboot boot: non verificato; nessuna sonda viene proposta.

Il sorgente include un percorso di aggiornamento firmware touchscreen al boot:
va revisionato prima di avviare un nuovo kernel. L'archivio kernel è materiale
di sviluppo, NON un pacchetto installabile. Non flashare le Image fornite.

## Prossimi passaggi

Boot, dtimage e recovery acquisiti in sola lettura dal CRR-L09 il 23 ottobre.
Vedere BOOT-RESULT.md e DTIMAGE-RESULT.md; non occorre richiedere nuovamente
i candidati grafici o il dump boot. Avviato esperimento remoto di sync sorgenti
e grafo Android reale, con limiti di spazio e tempo. Non equivale a una build ROM.

Android 10 è un primo candidato tecnico. Non si promettono una data di rilascio,
un tetto massimo Android o una ROM completa senza build e prove sul dispositivo.
