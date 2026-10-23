# CI-only source build. Proprietary Huawei modules are deliberately absent.
# Produces development inputs, never an installable Carrera ROM.
$(call inherit-product, device/huawei/carrera/lineage_carrera.mk)
PRODUCT_NAME := lineage_carrera_public
PRODUCT_MODEL := Mate S CRR-L09 public source probe
