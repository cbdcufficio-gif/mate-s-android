# Contratto dei backport SELinux Carrera

Questo documento progetta interventi; non applica patch e non certifica enforcement.
Il probe configurazione conserva .config generata, policy G0 effettiva, classi,
policycaps e digest del codice Huawei. Una capability enumerata non dimostra
l'hook o l'applicazione del permesso; la differenza di classmap non prova un
rifiuto automatico del caricamento.

## Sorgenti di confronto precise

- Huawei: hi3635-dev/android_kernel_huawei_liszt,
  3fe1625bed89c034996842c1af696ba9bc50d8a9, security/selinux/include/security.h,
  ss/services.c, hooks.c, include/classmap.h, selinuxfs.c.
- Socket class: upstream Linux da69a5306ab92e07224da54aafee8b1dccf024f6,
  "selinux: support distinctions among all network address families":
  https://github.com/torvalds/linux/commit/da69a5306ab92e07224da54aafee8b1dccf024f6
- NNP/nosuid: upstream Linux af63f4193f9fbbbac50fc766417d74735afd87ef,
  "selinux: Generalize support for NNP/nosuid SELinux domain transitions":
  https://github.com/torvalds/linux/commit/af63f4193f9fbbbac50fc766417d74735afd87ef

I diff upstream sono riferimenti semantici, non cherry-pick dichiarati compatibili
con Huawei3.10. NNP dipende dal controllo bounded-transition preesistente e dalle
API credential/mount effettive: ricostruire l'intera catena prima della patch.

## Insiemi indivisibili da progettare

1. extended_socket_class: enum policycap, caricamento bit, esposizione selinuxfs,
   classmap e selezione classe per ciascuna famiglia socket interessata.
2. nnp_nosuid_transition: enum/bit e attivazione, classe process2 e permessi
   nnp_transition/nosuid_transition, controlli exec e bounded transitions,
   propagazione errore e aggiornamento policy capabilities esposte.

Conservare gli INDICI dei bit ABI upstream: extended_socket_class è indice2;
nnp_nosuid_transition è indice5. Le posizioni intermedie always_check_network
(indice3) e cgroup_seclabel(indice4) non possono essere eliminate rinumerando
NNP. Riservare correttamente i bit non supportati senza dichiararne enforcement.
Non aggiungere solo una stringa in services.c o alzare POLICYVERS.

## Test richiesti prima dell'accettazione

- Fixture host con corpi upstream/Huawei fissati e dipendenze esplicite:
  bit2/bit5 distinti, reload policy, capability assente e attiva.
- Socket: famiglia presente autorizzata, stessa famiglia negata con AVC;
  confrontare famiglie che prima condividevano socket generico; mantenere
  controlli file/socket esistenti e test delle famiglie non interessate.
- Exec: no_new_privs/nosuid separati e combinati; dominio invariato;
  transizione autorizzata e negata; bounded SID consentito; preservare EPERM
  per NNP ed EACCES per nosuid dove il contratto upstream lo prevede.
- Policy originale senza nuove capability non deve acquisire permessi impliciti.
  Policy Q reale deve conservare neverallow e capability, senza permissive.
- Compilazione del kernel candidato solo dopo progettazione completa e fixture.
  Prove positive/negative e AVC sul vero kernel Carrera enforcing restano G3:
  runner Linux o TWRP permissive non sostituiscono queste prove.

Non è autorizzato da questo documento alcun flash o riavvio del telefono.
