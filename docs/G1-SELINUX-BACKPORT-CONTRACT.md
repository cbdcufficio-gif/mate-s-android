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

## Inventario effettivo dopo il probe

Review40871087407:97classi policy,50entryclassmapkernel;5classi userspace
separate,44classi policy restanti senza mappingkernel. Commons policy e macro
classmap espansi prima del confronto. Nei mapping esistenti emergono anche
map,watch*,audit_read,getrlimit,module_load,validate_trans e altri permessi.
Il report esatto è G1-CAPTURED-REVIEW-RESULT.json. Questi sono nomi dichiarati,
non prova che ogni permesso o classe sia esercitato nel primo boot.
Prima di estendere il backport, ricondurre ciascuna differenza a feature
configurata, hook e regole policy effettivamente usate: priorità a file mmap
e transizioni/init. Verificare handling di unknown classes/permissions senza
cambiarlo per aggirare i controlli. Non importare ciecamente44classi o tutti
i watch hook moderni; non trattare le5classi userspace come hook mancanti.

## Fixture exec riproducibile — 29 ottobre 2026

`tests/test_selinux_exec_contract.py` compila il corpo **invariato** di
`check_nnp_nosuid` da af63f419, conservato con attribuzione GPL in
`tests/fixtures/selinux_nnp_nosuid.c`. I digest dei sei sorgenti letti e del
corpo sono in `G1-SELINUX-EXEC-SOURCES.json`. La fixture non entra nel kernel.

Sono esercitate 128 combinazioni: NNP, nosuid, SID uguale/diverso, capability
assente/presente, quattro maschere di autorizzazione e bounded SID sì/no.
Si verificano risultato, maschera richiesta, numero di chiamate AVC/bounded e
precedenza degli errno. Con entrambe le restrizioni occorrono entrambi i
permessi process2; un solo permesso non basta, salvo il fallback bounded.
La capability assente non consulta process2, ma conserva il fallback bounded.
Una negazione AVC non implica necessariamente il rifiuto finale: la verifica
bounded può consentire la transizione. SID invariato evita entrambi i controlli.

**Differenza Huawei verificata nel sorgente fissato:** in
`selinux_bprm_set_creds`, exec_sid esplicito con NNP viene rifiutato subito;
negli altri casi NNP o MNT_NOSUID ripristinano il SID precedente. La funzione
`security_bounded_transition` esiste già in Huawei services.c, ma quel percorso
exec non la chiama. Non occorre quindi inventare un parser bounded nuovo:
va verificato e collegato il servizio esistente con i contratti appropriati.

Nel chiamante upstream, un errore del controllo per exec_sid esplicito termina
exec; per una transizione automatica ripristina il vecchio SID e prosegue con
FILE__EXECUTE_NO_TRANS. Poi rimangono TRANSITION, ENTRYPOINT e gli altri controlli.
La fixture attuale prova solo il helper; il chiamante completo, i suoi errori e
questi permessi restano da esercitare prima di una patch Huawei.

**Limite e prossima prova:** AVC, bounded SID e mount sono interfacce simulate;
nessuna policy è caricata né alcun AVC reale prodotto. In particolare
`mnt_may_suid()` upstream non va sostituito automaticamente dal solo bit
MNT_NOSUID Huawei: verificare le restrizioni di mount/user namespace nel codice
fissato e nella configurazione generata. Servono inoltre caricamento/reload del
bit5, mapping process2 e fixture del chiamante esplicito/automatico. La patch
kernel e una nuova compilazione Android restano non applicate.

## Prerequisito mount verificato — 29 ottobre, controllo autonomo

Il corpo upstream mnt_may_suid() richiede insieme: assenza di MNT_NOSUID,
mount appartenente al mount namespace corrente e current_in_userns() rispetto
al superblock. Il solo bit MNT_NOSUID non è un equivalente generale: mount
estranei o un controllo user namespace negativo devono restare restrittivi.
La nuova fixture compila il corpo invariato e verifica tutte le otto
combinazioni, con check_mnt/current_in_userns simulati e digest fissato.

Huawei possiede check_mnt() in fs/namespace.c (confronta mnt_ns corrente), ma
non mnt_may_suid() nei file mount/namespace acquisiti. CONFIG_NAMESPACES=n
nella configurazione generata non autorizza a eliminare il controllo mount:
il supporto interno ai mount namespace è già stato osservato nel codice.
Resta da derivare la variante sicura Huawei dalle sue API userns/superblock,
poi provare il chiamante exec completo. Nessun helper kernel è stato aggiunto.

## Chiamante exec upstream provato — 29 ottobre

La fixture conserva il corpo invariato selinux_bprm_set_creds e il helper già
verificato. Esercita 32 combinazioni di exec_sid esplicito/automatico,
NNP/nosuid, autorizzazione process2 e bounded fallback; altri sette casi
verificano EXECUTE_NO_TRANS, TRANSITION, ENTRYPOINT, SHARE, PTRACE, errore
security_transition_sid e cred_prepared. Controlla SID risultante, reset dei
SID di creazione, percorso dei permessi e per_clear solo in transizione.
Le interfacce policy/credential/inode/mount sono simulate; non è enforcement.

Il rifiuto del helper ferma exec esplicito; nel caso automatico conserva il
vecchio SID ma deve comunque passare EXECUTE_NO_TRANS. Anche una transizione
NNP ammessa deve ancora passare TRANSITION/ENTRYPOINT e SHARE/PTRACE.
Questi ultimi rifiuti conservano EPERM dove previsto dal chiamante.

**Prerequisito Huawei da preservare:** il suo selinux_bprm_set_creds chiama
cap_bprm_set_creds prima di cred_prepared; il corpo upstream acquisito non lo
chiama. Sostituire l'intera funzione Huawei col corpo upstream perderebbe
quell'integrazione. Il backport dovrà mantenere il controllo capability e i
suoi errori, l'accesso inode/audit della versione Huawei e l'ordine del reset.
Nessuna patch kernel applicata. Prossimo: fixture del percorso Huawei
capability/exec e adattamento mount, poi policycap caricamento/reload/process2.

## Loader capability e reload — 29 ottobre

Acquisiti e compilati invariati gli enum e security_load_policycaps() Huawei
ed upstream, con digest nel registro sorgenti. La fixture esegue per ciascun
loader tutte le 65.536 coppie before/after di un bitmap sintetico a8bit.
Verifica indici0/1 Huawei, indici0..5 upstream, azzeramento delle capability
rimosse e assenza di alias tra bit2/bit5 e posizioni intermedie. I bit6/7 non
modificano i valori noti. Le interfacce ebitmap/logging sono simulate; questo
non esercita parsing del formato binario, sincronizzazione, AVC o selinuxfs.

Il sorgente Huawei già invoca il loader sia nel caricamento iniziale (prima
di ss_initialized) sia nel reload, dopo installazione di newpolicydb sotto
policy_rwlock. L'adattamento deve conservare entrambi i punti e assegnare i
nuovi flag a ogni caricamento, incluso il valore zero. Non aggiungere loader
paralleli o state sticky. Il loader upstream importa anche alwaysnetwork e
cgroupseclabel: la fixture ne controlla gli indici, non autorizza a dichiararne
gli hook supportati nel backport Huawei.

Rimangono: bit parser/selinuxfs effettivi, mapping process2 e permessi numerici,
integrazione exec con cap_bprm_set_creds preservato, mount helper compatibile
e poi socket classes. Nessuna patch kernel produttiva ancora applicata.

## process2: evidenza classmap — 29 ottobre

La policy G0 estratta contiene process2 con nnp_transition e
nosuid_transition (policy-classes.txt, run40870457480). Il classmap upstream
fissato af63f419 dichiara process2 con entrambe le stringhe nello stesso
ordine; il classmap Huawei fissato 3fe1625 non contiene process2. Fonti:
https://github.com/torvalds/linux/blob/af63f4193f9fbbbac50fc766417d74735afd87ef/security/selinux/include/classmap.h
https://github.com/hi3635-dev/android_kernel_huawei_liszt/blob/3fe1625bed89c034996842c1af696ba9bc50d8a9/security/selinux/include/classmap.h

Questo conferma una differenza concreta nella mappatura; non prova da solo
rifiuto della policy o che aggiungere due nomi produca enforcement. Occorre
verificare generazione flask/av_perm_to_string, selinux_set_mapping, unknown
permissions, ordine di classmap e corrispondenza degli access vector numerici,
con policy reali e permessi avc, preservando controlli capability esistenti.
Le stringhe del report seinfo non stabiliscono da sole l'ordine dei bit.

## Mapping process2 Huawei con policy sintetica — 29 ottobre

Fixture compilata con selinux_set_mapping e map_decision Huawei invariati.
Il classmap sintetico contiene process2 con nnp_transition e nosuid_transition;
le lookup policy sono stub e restituiscono valori volutamente differenti e in
ordine diverso (class42, maschere8 e2). Il mapping li traduce nei bit kernel1
e2, inclusi auditallow/auditdeny. Sono verificati anche classe e permesso
mancanti con reject_unknown, allow_unknown/deny_unknown e classe vuota/null.
Questa prova dimostra la traduzione sui valori sintetici, non identifica gli
ID numerici nella policy G0 né prova il parsing o l'enforcement sul telefono.
In particolare la classe G0 ha entrambi i permessi, ma il codice Huawei senza
una voce process2 non li collega agli hook. Non applicare una patch fino alla
verifica dei generatori di costanti e integrazione nel percorso exec.
