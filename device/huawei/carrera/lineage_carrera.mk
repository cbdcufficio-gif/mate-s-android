# Experimental Android 10 userspace product. Hardware boot not established.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/product_launched_with_m.mk)
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)
$(call inherit-product, device/huawei/carrera/device.mk)

PRODUCT_DEVICE := carrera
PRODUCT_NAME := lineage_carrera
PRODUCT_BRAND := Huawei
PRODUCT_MANUFACTURER := Huawei
PRODUCT_MODEL := Mate S CRR-L09 experimental
PRODUCT_CHARACTERISTICS := default
# Do not spoof a stock fingerprint or a newer vendor security patch level.
