# Revisioni degli strumenti esterni

## Sessione desktop del 22 ottobre, prosecuzione

Sono stati consultati GPT-OSS120B, Nemotron3Ultra, Qwen2.5Coder32B e Llama3.3.
Analisi delle architetture, vincoli di build, HAL, generazione e revisione codice
sono state inviate a FreeLLMAPI. Il gateway non è un server di compilazione.
Gemini2.5Flash risultava nel catalogo ma la chiamata ha restituito model-not-found;
un'ulteriore revisione GPT-OSS è fallita per timeout. Le quote non riportate
restano sconosciute. Non sono stati modificati routing globale o abbonamenti.

Molte risposte richiedevano correzioni: GSI non-Treble pronta, kernel4.14 o
gralloc4 obbligatori per ogni port Q, super partition necessaria e shim gralloc
malloc/free sono stati respinti. La prima bozza Python usava psutil e parametri
XMLParser non presenti nella libreria standard: è stata sostituita e testata.
La revisione che suggeriva di rimuovere il pin a commit o abilitare sovrascritture
non è stata applicata. Anche la proposta finale di classi grafiche finte è respinta.

Le decisioni correnti sono in ZERO-COST-PLAN.md e ABI-REVIEW.md. Il repository
pubblico ora contiene sorgenti e workflow; la dichiarazione storica qui sotto
di nessun repository/Actions avviato descrive la sessione precedente.

## Sessione precedente

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
