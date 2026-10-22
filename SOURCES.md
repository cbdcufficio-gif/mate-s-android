# Fonti primarie — consultazione 22 ottobre 2026

I commit completi dei repository studiati sono in sources.lock.json. Sono
riferimenti verificati per questa ricerca, non un manifest completo Android.

- [Kernel Hi3635, commit compilato](https://github.com/hi3635-dev/android_kernel_huawei_liszt/tree/3fe1625bed89c034996842c1af696ba9bc50d8a9): Makefile 3.10.86, merge_hi3635_defconfig, Binder, syscall e driver. Il nome liszt non certifica compatibilità Carrera; DTS Carrera effettivi mancanti. Percorsi e righe nel report kernel-audit.json.
- [Toolchain GCC ARM64 4.9 usata](https://github.com/LineageOS/android_prebuilts_gcc_linux-x86_aarch64_aarch64-linux-android-4.9/tree/7280ce2399316a5dbd8872e0bfe69435d8719230): compilatore bloccato anche tramite hash binario.
- [Device Liszt](https://github.com/hi3635-dev/android_device_huawei_liszt/tree/f4e36642c2e83d9327ee78e62746b7abb41c1b09): riferimento legacy per studio, non device tree trasferibile integralmente a Carrera.
- [TeamWin Carrera](https://github.com/TeamWin/android_device_huawei_carrera): riferimento recovery specifico, non ROM Android moderna completa.
- [Wiki Hi3635](https://github.com/hi3635-dev/wiki): esperienza downstream Liszt/Mozart; non conferma supporto completo Mate S.
- [Manifest LineageOS 17.1](https://github.com/LineageOS/android/tree/c7b3d4b65b79e2e0d6a891547ad138e1fcdafb56): base Android 10; dopo sync serve repo manifest -r.
- [Build LineageOS 17.1](https://github.com/LineageOS/android_build/tree/71a47798ac090b81c6b7db0b5c470f1fa3e604cd): prodotto e regole build studiate.
- [Hardware interfaces Q](https://github.com/LineageOS/android_hardware_interfaces/tree/02951860e9c95f19384fa07522925537d8c17a18): composer 2.1 e adattatori HWC1; presenza dell'adattatore non prova il funzionamento del composer Huawei.
- [SELinux Q: policy_version.mk](https://github.com/LineageOS/android_system_sepolicy/blob/lineage-17.1/policy_version.mk): POLICYVERS predefinito 30, distinto da BOARD_SEPOLICY_VERS. Non applicare aggiramenti dei controlli.
- [CallStack Q](https://android.googlesource.com/platform/system/core/+/android-10.0.0_r1/libutils/include/utils/CallStack.h) e [Android.bp](https://android.googlesource.com/platform/system/core/+/android-10.0.0_r1/libutils/Android.bp): implementazione libutilscallstack separata; aggiungere DT_NEEDED è soltanto un candidato da provare.
- [Region Android 6](https://android.googlesource.com/platform/frameworks/native/+/android-6.0.0_r1/include/ui/Region.h) e [Region Android 10](https://android.googlesource.com/platform/frameworks/native/+/android-10.0.0_r1/libs/ui/include/ui/Region.h): confronto dichiarazioni/layout di riferimento, non prova ABI dei blob vendor.
- [Brave: requisiti](https://support.brave.com/hc/en-us/articles/360021357112-What-are-the-system-requirements-to-install-Brave): Android 10 o successivo alla consultazione. Compatibilità delle altre app e degli APK specifici ancora da verificare.
- [Requisiti AOSP attuali](https://source.android.com/docs/setup/start/requirements): non sono una misura automatica del checkout LineageOS 17.1.
- [Criteri supporto LineageOS](https://github.com/LineageOS/charter/blob/main/device-support-requirements.md): matrice completa necessaria prima di dichiarare una ROM supportata.
- [patchelf 0.18.0](https://github.com/NixOS/patchelf/tree/99c24238981b7b1084313aca8f5c493bb46f302c): strumento usato nei test offline; nessuna esecuzione dei blob ispezionati.

Dump, configurazione e inventario ELF forniti dall'utente sono evidenze locali
distinte dalle fonti pubbliche. Il cloud non vede USB o filesystem del Dell.
Le risposte FreeLLMAPI sono revisioni, non fonti primarie: decisioni in
docs/REVIEWS.md. Nessuna compatibilità mainline/postmarketOS viene trasferita
automaticamente a questo progetto Android downstream.
