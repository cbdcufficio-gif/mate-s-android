# Correzione dei target della build grafica

build_graphics.py richiedeva esplicitamente i quattro prebuilt Huawei e il
composer, ma ometteva allocator e mapper già dichiarati in device.mk.
Ora richiede anche allocator 2.0 implementazione/servizio, mapper 2.0 e
libutilscallstack reale. Nessuna libreria sperimentale libmates viene usata.

I nomi allocator sono stati ricontrollati in hardware/interfaces, commit
02951860e9c95f19384fa07522925537d8c17a18, graphics/allocator/2.0/default/Android.bp,
blob 9980ae0f2f73ac16e61159fd0c23a59471ab3b94.

Verificati sintassi shell e presenza dei cinque target PRODUCT_PACKAGES
grafici nella richiesta di compilazione. Revisione breve FreeLLMAPI.
I controlli ELF Soong restano attivi. Non è stata eseguita una nuova build
Android: serve ancora l'albero di piattaforma completo o una chiusura di
sorgenti sufficiente, con overlay vendor locale e configurazione finale verificata.
