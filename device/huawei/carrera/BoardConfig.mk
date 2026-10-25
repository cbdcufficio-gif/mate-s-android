# Carrera values derived from the acquired device, not Liszt partition geometry.
DEVICE_PATH := device/huawei/carrera
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := cortex-a53
TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := cortex-a53
TARGET_USES_64_BIT_BINDER := true
TARGET_BOARD_PLATFORM := hi3635
TARGET_BOOTLOADER_BOARD_NAME := hi3635
USE_XML_AUDIO_POLICY_CONF := 1

# This product is for userspace/module compilation. Boot packaging stays gated.
TARGET_NO_KERNEL := true
TARGET_NO_RECOVERY := true
TARGET_NO_BOOTLOADER := true
TARGET_NO_RADIOIMAGE := true
BOARD_BUILD_SYSTEM_ROOT_IMAGE := false
TARGET_COPY_OUT_VENDOR := system/vendor
# Deliberately leave BOARD_VNDK_VERSION unset: stock is a pre-Treble device.
TARGET_USERIMAGES_USE_EXT4 := true
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 2684354560
BOARD_BOOTIMAGE_PARTITION_SIZE := 25165824
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 33554432

DEVICE_MANIFEST_FILE := $(DEVICE_PATH)/configs/manifest.xml
TARGET_SCREEN_WIDTH := 1080
TARGET_SCREEN_HEIGHT := 1920
# No userdata image geometry, boot offsets, generic DTB, or flash recipe supplied.
