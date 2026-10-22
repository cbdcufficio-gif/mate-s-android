# Matrice di accettazione

Stock/TWRP confermato non equivale a funzionamento nel nuovo Android.

| Parte | Evidenza | Prova richiesta nel candidato | Stato |
|---|---|---|---|
| Kernel | Due Image compilate | Boot, log, DTB e alimentazione | Solo offline |
| Init/ADB | TWRP già operativo | Init Android10, ADB autenticato, logcat | Da integrare |
| Binder/HIDL | Multidevice/protocollo8/SG nel sorgente | Servizi e transazioni32/64 | Non provato |
| Display | Samsung S6E3FA3X01 | Accensione, luminosità, rotazione, resume | Non provato |
| GPU/gralloc/HWC | Blob, hash e ricette | Loader, GLES, fence, video, resume | Candidati offline |
| Touch | Synaptics S3718 | Multitouch, IRQ, resume, audit firmware-update | Non provato |
| Storage | Mappa e dump verificati | Mount, cifratura e userdata senza format implicito | Da integrare |
| USB | Bulk recovery→PC | ADB autenticato, stabilità, riconnessioni | Solo recovery |
| Audio | HAL e dipendenze | Speaker, microfoni, cuffie, audio chiamate | Non provato |
| Telefonia | Balong inventariato | SIM, dati, SMS, chiamate, recupero rete | Da portare |
| Wi-Fi | Driver famiglia nei sorgenti | Variante Carrera, DHCP, reconnect | Non provato |
| Bluetooth | HAL da integrare | Pairing, audio, input e reconnect | Non provato |
| GNSS | Componenti legacy | Fix freddo/caldo e resume | Non provato |
| Camera | Driver Carrera e blob | Anteriore/posteriore, foto/video/flash/AF | Non provato |
| Sensori | Sensorhub e HAL | Accelerometro, gyro, prossimità, luce | Non provato |
| Impronta | Config stock conservata | Enroll/unlock, protezione dati | Non provato |
| Vibrazione | Driver compilato dopo fix | Intensità, pattern e I2C | Solo compilazione |
| Batteria/termica | Driver stock conservati | Ricarica, letture e protezioni | Non provato |
| Suspend/resume | Supporto vendor conservato | Consumo, wakeup, rete/touch/audio | Non provato |
| SELinux/keystore | Kernel max30, Q POLICYVERS30 | Policy caricabile/enforcing e chiavi | Non provato |
| Potato/Telegram | Obiettivo utente | APK ufficiali, notifiche, messaggi | Non provato |
| ProtonVPN | Supporto TUN da mantenere | VPN, routing/DNS, reconnect e suspend | Non provato |
| Brave/Tor | Brave richiede Android>=10 | APK ufficiali, rendering/rete/media | Non provato |

Una ROM completa richiede risultati registrati per questa matrice e prove di
stabilità. Una risposta LLM non è una prova hardware. Avanzare oltre Android10
quando i vincoli effettivi della versione successiva sono stati misurati.
