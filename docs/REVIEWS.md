# Revisioni degli strumenti esterni

GitHub è stato usato per repository/rami e lettura del codice. Nessun Actions è
stato avviato, nessun repository o blob pubblicato. FreeLLMAPI è stato usato nel
pool dichiarato gratuito, con output limitato e senza attivare abbonamenti o
cambiare la strategia globale. Le quote di diversi provider non erano riportate:
non si dichiara un saldo residuo esatto o che le chiamate esterne azzerino il
consumo della chat.

Quattro revisioni: GPT-OSS120B/Groq, Qwen2.5Coder32B/Cloudflare,
Nemotron3Ultra/NVIDIA, Qwen3.8/Groq. Una revisione separata6.1Sol ha esaminato il
kernel e riprodotto due errori del parser. Questo non indica cambio modello chat.

| Rilievo | Decisione verificata |
|---|---|
| Obbligo immediato kernel4.9/4.14 o bootheader v2/v3 | Respinto: non dimostrato per port legacy |
| Usare Mali-G71 | Respinto: il sorgente seleziona Midgard |
| Mancano getrandom/memfd | Respinto: implementazioni e syscall già presenti |
| Seccomp richiede per forza eBPF | Respinto: sottosistemi confusi |
| BOARD_SEPOLICY_VERS30 cambia formato binario | Respinto: non è POLICYVERS; Q usa già POLICYVERS30 |
| Disattivare neverallow o ELF checks | Respinto: nasconde problemi |
| Usare ldd sui blob ARM | Respinto: analisi statica senza eseguire ELF |
| Hash sezioni perde nomi duplicati | Corretto dopo riproduzione, test dedicato |
| Indirizzo simbolo esportato non verificato | Corretto dopo riproduzione6.1, test dedicato |
| Symlink destinazione può scrivere nello stock | Corretto risolvendo percorso, test dedicato |

Le risposte dei modelli sono ipotesi di revisione. Sorgenti, build e test sono
le evidenze decisive; le indicazioni errate non sono state applicate.
