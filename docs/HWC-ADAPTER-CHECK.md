# Verifica HWC2On1Adapter

Fonte verificata: https://github.com/LineageOS/android_hardware_interfaces/blob/02951860e9c95f19384fa07522925537d8c17a18/graphics/composer/2.1/utils/hwc2on1adapter/HWC2On1Adapter.cpp

Le righe 38-42 leggono device->common.version; il costruttore alle righe 93-96 usa quel valore. Non leggono HMI.module_api_version. Il valore modulo Huawei 0.1 non permette di dedurre HWC 1.1 o le funzionalita disponibili.

Il codice contiene percorsi distinti per versioni minori: display virtuali da 3, doze e setPowerMode da 4, surface damage da 5. Questi rami non provano da soli che un dispositivo sia accettato o funzioni.

Prossimo controllo: individuare staticamente il puntatore methods->open del modulo Huawei, seguire la costruzione del dispositivo e identificare la scrittura di common.version; verificare inoltre il chiamante Android che seleziona l'adattatore. Gestire rilocazioni e codice ARM/Thumb. Una costante trovata senza collegamento al dispositivo restituito non e prova sufficiente. Nessuna esecuzione del blob necessaria per questa analisi.

Revisione FreeLLMAPI: qwen2.5-coder-32b, execution f01d8649-74f7-415b-86c7-06f97b3134ee. La risposta confondeva versione modulo e dispositivo: conclusione rifiutata confrontandola con il sorgente. Nessuna compatibilita o funzione del telefono dichiarata verificata.
