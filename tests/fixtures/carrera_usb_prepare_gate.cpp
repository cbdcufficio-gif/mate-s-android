#include <cassert>
#include <vector>
#include "carrera_usb_prepare_gate.h"
struct FaultInjectedOperations {
    unsigned failures;
    int starts=0;
    std::vector<int> calls;
    bool step(int number) {calls.push_back(number);return !(failures&(1u<<number));}
    bool prepare_target() {return step(0);}
    bool mount_functionfs() {return step(1);}
    bool verify_mount() {return step(2);}
    bool write_alias() {return step(3);}
    bool verify_alias() {return step(4);}
    bool start_adbd() {++starts;return step(5);}
};
int main() {
    const CarreraUsbPreparation failure_results[]={
        CarreraUsbPreparation::target_failed,CarreraUsbPreparation::mount_failed,
        CarreraUsbPreparation::verification_failed,CarreraUsbPreparation::alias_failed,
        CarreraUsbPreparation::alias_verification_failed,CarreraUsbPreparation::start_failed};
    // All combinations: first failure must stop side effects and prevent start.
    for(unsigned failures=0;failures<64;++failures) {
        FaultInjectedOperations operations{failures,0,{}};
        auto result=PrepareCarreraUsb(operations);
        int first=0;while(first<6 && !(failures&(1u<<first))) ++first;
        assert(result==(first==6?CarreraUsbPreparation::started:failure_results[first]));
        assert(operations.starts==(first>=5?1:0));
        assert(operations.calls.size()==static_cast<unsigned>(first==6?6:first+1));
        for(unsigned i=0;i<operations.calls.size();++i)assert(operations.calls[i]==static_cast<int>(i));
    }
}
