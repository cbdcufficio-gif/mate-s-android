DEVICE_PATH := device/huawei/carrera
# API 23 is inherited once from product_launched_with_m.mk in the product.
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := xxhdpi

# The explicitly named CI product tests public source inputs only.
# The normal Carrera product still requires verified local Huawei prebuilts.
ifneq ($(TARGET_PRODUCT),lineage_carrera_public)
$(call inherit-product, vendor/huawei/carrera-graphics/carrera-graphics.mk)
endif

# These module names were verified in LineageOS lineage-17.1 source.
# HWC2On1Adapter is used by the 2.1 implementation's loader when appropriate.
PRODUCT_PACKAGES += \
    android.hardware.graphics.allocator@2.0-impl \
    android.hardware.graphics.allocator@2.0-service \
    android.hardware.graphics.mapper@2.0-impl \
    android.hardware.graphics.composer@2.1-impl \
    android.hardware.graphics.composer@2.1-service

PRODUCT_PROPERTY_OVERRIDES += \
    ro.hardware.egl=mali \
    ro.hardware.gralloc=hi3635 \
    ro.hardware.hwcomposer=hi3635

# Minimal rootdir candidate derived from the acquired Carrera partition map.
# This does not include stock proprietary services or a complete SELinux policy.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/rootdir/fstab.hi3635:root/fstab.hi3635 \
    $(DEVICE_PATH)/rootdir/init.hi3635.rc:root/init.hi3635.rc \
    $(DEVICE_PATH)/rootdir/ueventd.hi3635.rc:root/ueventd.hi3635.rc

# Leave ADB authentication enabled. No insecure ro.adb.secure=0 override.
