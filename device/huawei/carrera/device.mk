DEVICE_PATH := device/huawei/carrera
PRODUCT_SHIPPING_API_LEVEL := 23
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := xxhdpi

$(call inherit-product, vendor/huawei/carrera-graphics/carrera-graphics.mk)

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

# No stock fstab/init copied wholesale: their format, mount, encryption and
# proprietary service triggers require a separate runtime review.
# Leave ADB authentication enabled. No insecure ro.adb.secure=0 override.
