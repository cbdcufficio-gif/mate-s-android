#pragma once
// Experimental orchestration only. No syscall adapter or product integration.
// Operations own verified handles and return false on any validation/error.
enum class CarreraUsbPreparation {
    target_failed, mount_failed, verification_failed, alias_failed,
    alias_verification_failed, start_failed, started
};
template<class Operations>
CarreraUsbPreparation PrepareCarreraUsb(Operations& operations) {
    if (!operations.prepare_target()) return CarreraUsbPreparation::target_failed;
    if (!operations.mount_functionfs()) return CarreraUsbPreparation::mount_failed;
    if (!operations.verify_mount()) return CarreraUsbPreparation::verification_failed;
    if (!operations.write_alias()) return CarreraUsbPreparation::alias_failed;
    if (!operations.verify_alias()) return CarreraUsbPreparation::alias_verification_failed;
    if (!operations.start_adbd()) return CarreraUsbPreparation::start_failed;
    return CarreraUsbPreparation::started;
}
