#include <assert.h>
#include <stdint.h>
typedef uint16_t u16;
#define PF_ALG 38
#define PF_APPLETALK 5
#define PF_ATMPVC 8
#define PF_ATMSVC 20
#define PF_AX25 3
#define PF_BLUETOOTH 31
#define PF_BRIDGE 7
#define PF_CAIF 37
#define PF_CAN 29
#define PF_DECnet 12
#define PF_IEEE802154 36
#define PF_INET 2
#define PF_INET6 10
#define PF_IPX 4
#define PF_IRDA 23
#define PF_ISDN 34
#define PF_IUCV 32
#define PF_KEY 15
#define PF_LLC 26
#define PF_NETLINK 16
#define PF_NETROM 6
#define PF_NFC 39
#define PF_PACKET 17
#define PF_PHONET 35
#define PF_PPPOX 24
#define PF_RDS 21
#define PF_ROSE 11
#define PF_RXRPC 33
#define PF_TIPC 30
#define PF_UNIX 1
#define PF_VSOCK 40
#define PF_X25 9
#define PF_MAX 41
#define SECCLASS_ALG_SOCKET 1
#define SECCLASS_APPLETALK_SOCKET 2
#define SECCLASS_ATMPVC_SOCKET 3
#define SECCLASS_ATMSVC_SOCKET 4
#define SECCLASS_AX25_SOCKET 5
#define SECCLASS_BLUETOOTH_SOCKET 6
#define SECCLASS_BRIDGE_SOCKET 7
#define SECCLASS_CAIF_SOCKET 8
#define SECCLASS_CAN_SOCKET 9
#define SECCLASS_DCCP_SOCKET 10
#define SECCLASS_DECNET_SOCKET 11
#define SECCLASS_ICMP_SOCKET 12
#define SECCLASS_IEEE802154_SOCKET 13
#define SECCLASS_IPX_SOCKET 14
#define SECCLASS_IRDA_SOCKET 15
#define SECCLASS_ISDN_SOCKET 16
#define SECCLASS_IUCV_SOCKET 17
#define SECCLASS_KEY_SOCKET 18
#define SECCLASS_LLC_SOCKET 19
#define SECCLASS_NETLINK_AUDIT_SOCKET 20
#define SECCLASS_NETLINK_DNRT_SOCKET 21
#define SECCLASS_NETLINK_FIREWALL_SOCKET 22
#define SECCLASS_NETLINK_IP6FW_SOCKET 23
#define SECCLASS_NETLINK_KOBJECT_UEVENT_SOCKET 24
#define SECCLASS_NETLINK_NFLOG_SOCKET 25
#define SECCLASS_NETLINK_ROUTE_SOCKET 26
#define SECCLASS_NETLINK_SELINUX_SOCKET 27
#define SECCLASS_NETLINK_SOCKET 28
#define SECCLASS_NETLINK_TCPDIAG_SOCKET 29
#define SECCLASS_NETLINK_XFRM_SOCKET 30
#define SECCLASS_NETROM_SOCKET 31
#define SECCLASS_NFC_SOCKET 32
#define SECCLASS_PACKET_SOCKET 33
#define SECCLASS_PHONET_SOCKET 34
#define SECCLASS_PPPOX_SOCKET 35
#define SECCLASS_RAWIP_SOCKET 36
#define SECCLASS_RDS_SOCKET 37
#define SECCLASS_ROSE_SOCKET 38
#define SECCLASS_RXRPC_SOCKET 39
#define SECCLASS_SCTP_SOCKET 40
#define SECCLASS_SOCKET 41
#define SECCLASS_TCP_SOCKET 42
#define SECCLASS_TIPC_SOCKET 43
#define SECCLASS_UDP_SOCKET 44
#define SECCLASS_UNIX_DGRAM_SOCKET 45
#define SECCLASS_UNIX_STREAM_SOCKET 46
#define SECCLASS_VSOCK_SOCKET 47
#define SECCLASS_X25_SOCKET 48
#define NETLINK_AUDIT 1
#define NETLINK_DNRTMSG 2
#define NETLINK_FIREWALL 3
#define NETLINK_IP6_FW 4
#define NETLINK_KOBJECT_UEVENT 5
#define NETLINK_NFLOG 6
#define NETLINK_ROUTE 7
#define NETLINK_SELINUX 8
#define NETLINK_SOCK_DIAG 9
#define NETLINK_XFRM 10
#define SOCK_STREAM 1
#define SOCK_DGRAM 2
#define SOCK_SEQPACKET 5
#define SOCK_DCCP 6
#define IPPROTO_IP 0
#define IPPROTO_ICMP 1
#define IPPROTO_TCP 6
#define IPPROTO_UDP 17
#define IPPROTO_SCTP 132
static int selinux_policycap_extsockclass;
static inline int default_protocol_stream(int protocol)
{
	return (protocol == IPPROTO_IP || protocol == IPPROTO_TCP);
}

static inline int default_protocol_dgram(int protocol)
{
	return (protocol == IPPROTO_IP || protocol == IPPROTO_UDP);
}

static inline u16 socket_type_to_security_class(int family, int type, int protocol)
{
	switch (family) {
	case PF_UNIX:
		switch (type) {
		case SOCK_STREAM:
		case SOCK_SEQPACKET:
			return SECCLASS_UNIX_STREAM_SOCKET;
		case SOCK_DGRAM:
			return SECCLASS_UNIX_DGRAM_SOCKET;
		}
		break;
	case PF_INET:
	case PF_INET6:
		switch (type) {
		case SOCK_STREAM:
		case SOCK_SEQPACKET:
			if (default_protocol_stream(protocol))
				return SECCLASS_TCP_SOCKET;
			else if (selinux_policycap_extsockclass && protocol == IPPROTO_SCTP)
				return SECCLASS_SCTP_SOCKET;
			else
				return SECCLASS_RAWIP_SOCKET;
		case SOCK_DGRAM:
			if (default_protocol_dgram(protocol))
				return SECCLASS_UDP_SOCKET;
			else if (selinux_policycap_extsockclass && protocol == IPPROTO_ICMP)
				return SECCLASS_ICMP_SOCKET;
			else
				return SECCLASS_RAWIP_SOCKET;
		case SOCK_DCCP:
			return SECCLASS_DCCP_SOCKET;
		default:
			return SECCLASS_RAWIP_SOCKET;
		}
		break;
	case PF_NETLINK:
		switch (protocol) {
		case NETLINK_ROUTE:
			return SECCLASS_NETLINK_ROUTE_SOCKET;
		case NETLINK_FIREWALL:
			return SECCLASS_NETLINK_FIREWALL_SOCKET;
		case NETLINK_SOCK_DIAG:
			return SECCLASS_NETLINK_TCPDIAG_SOCKET;
		case NETLINK_NFLOG:
			return SECCLASS_NETLINK_NFLOG_SOCKET;
		case NETLINK_XFRM:
			return SECCLASS_NETLINK_XFRM_SOCKET;
		case NETLINK_SELINUX:
			return SECCLASS_NETLINK_SELINUX_SOCKET;
		case NETLINK_AUDIT:
			return SECCLASS_NETLINK_AUDIT_SOCKET;
		case NETLINK_IP6_FW:
			return SECCLASS_NETLINK_IP6FW_SOCKET;
		case NETLINK_DNRTMSG:
			return SECCLASS_NETLINK_DNRT_SOCKET;
		case NETLINK_KOBJECT_UEVENT:
			return SECCLASS_NETLINK_KOBJECT_UEVENT_SOCKET;
		default:
			return SECCLASS_NETLINK_SOCKET;
		}
	case PF_PACKET:
		return SECCLASS_PACKET_SOCKET;
	case PF_KEY:
		return SECCLASS_KEY_SOCKET;
	case PF_APPLETALK:
		return SECCLASS_APPLETALK_SOCKET;
	}

	if (selinux_policycap_extsockclass) {
		switch (family) {
		case PF_AX25:
			return SECCLASS_AX25_SOCKET;
		case PF_IPX:
			return SECCLASS_IPX_SOCKET;
		case PF_NETROM:
			return SECCLASS_NETROM_SOCKET;
		case PF_BRIDGE:
			return SECCLASS_BRIDGE_SOCKET;
		case PF_ATMPVC:
			return SECCLASS_ATMPVC_SOCKET;
		case PF_X25:
			return SECCLASS_X25_SOCKET;
		case PF_ROSE:
			return SECCLASS_ROSE_SOCKET;
		case PF_DECnet:
			return SECCLASS_DECNET_SOCKET;
		case PF_ATMSVC:
			return SECCLASS_ATMSVC_SOCKET;
		case PF_RDS:
			return SECCLASS_RDS_SOCKET;
		case PF_IRDA:
			return SECCLASS_IRDA_SOCKET;
		case PF_PPPOX:
			return SECCLASS_PPPOX_SOCKET;
		case PF_LLC:
			return SECCLASS_LLC_SOCKET;
		case PF_CAN:
			return SECCLASS_CAN_SOCKET;
		case PF_TIPC:
			return SECCLASS_TIPC_SOCKET;
		case PF_BLUETOOTH:
			return SECCLASS_BLUETOOTH_SOCKET;
		case PF_IUCV:
			return SECCLASS_IUCV_SOCKET;
		case PF_RXRPC:
			return SECCLASS_RXRPC_SOCKET;
		case PF_ISDN:
			return SECCLASS_ISDN_SOCKET;
		case PF_PHONET:
			return SECCLASS_PHONET_SOCKET;
		case PF_IEEE802154:
			return SECCLASS_IEEE802154_SOCKET;
		case PF_CAIF:
			return SECCLASS_CAIF_SOCKET;
		case PF_ALG:
			return SECCLASS_ALG_SOCKET;
		case PF_NFC:
			return SECCLASS_NFC_SOCKET;
		case PF_VSOCK:
			return SECCLASS_VSOCK_SOCKET;
		}
	}
#if PF_MAX > 41
#error New address family defined, review Carrera socket mappings.
#endif

	return SECCLASS_SOCKET;
}

int main(void) {
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_AX25,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_AX25,SOCK_STREAM,0)==SECCLASS_AX25_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_IPX,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_IPX,SOCK_STREAM,0)==SECCLASS_IPX_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_NETROM,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_NETROM,SOCK_STREAM,0)==SECCLASS_NETROM_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_BRIDGE,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_BRIDGE,SOCK_STREAM,0)==SECCLASS_BRIDGE_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_ATMPVC,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_ATMPVC,SOCK_STREAM,0)==SECCLASS_ATMPVC_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_X25,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_X25,SOCK_STREAM,0)==SECCLASS_X25_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_ROSE,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_ROSE,SOCK_STREAM,0)==SECCLASS_ROSE_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_DECnet,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_DECnet,SOCK_STREAM,0)==SECCLASS_DECNET_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_ATMSVC,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_ATMSVC,SOCK_STREAM,0)==SECCLASS_ATMSVC_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_RDS,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_RDS,SOCK_STREAM,0)==SECCLASS_RDS_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_IRDA,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_IRDA,SOCK_STREAM,0)==SECCLASS_IRDA_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_PPPOX,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_PPPOX,SOCK_STREAM,0)==SECCLASS_PPPOX_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_LLC,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_LLC,SOCK_STREAM,0)==SECCLASS_LLC_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_CAN,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_CAN,SOCK_STREAM,0)==SECCLASS_CAN_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_TIPC,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_TIPC,SOCK_STREAM,0)==SECCLASS_TIPC_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_BLUETOOTH,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_BLUETOOTH,SOCK_STREAM,0)==SECCLASS_BLUETOOTH_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_IUCV,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_IUCV,SOCK_STREAM,0)==SECCLASS_IUCV_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_RXRPC,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_RXRPC,SOCK_STREAM,0)==SECCLASS_RXRPC_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_ISDN,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_ISDN,SOCK_STREAM,0)==SECCLASS_ISDN_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_PHONET,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_PHONET,SOCK_STREAM,0)==SECCLASS_PHONET_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_IEEE802154,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_IEEE802154,SOCK_STREAM,0)==SECCLASS_IEEE802154_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_CAIF,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_CAIF,SOCK_STREAM,0)==SECCLASS_CAIF_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_ALG,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_ALG,SOCK_STREAM,0)==SECCLASS_ALG_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_NFC,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_NFC,SOCK_STREAM,0)==SECCLASS_NFC_SOCKET);
 selinux_policycap_extsockclass=0; assert(socket_type_to_security_class(PF_VSOCK,SOCK_STREAM,0)==SECCLASS_SOCKET);
 selinux_policycap_extsockclass=1; assert(socket_type_to_security_class(PF_VSOCK,SOCK_STREAM,0)==SECCLASS_VSOCK_SOCKET);
 selinux_policycap_extsockclass=0;
 assert(socket_type_to_security_class(PF_INET,SOCK_STREAM,IPPROTO_TCP)==SECCLASS_TCP_SOCKET);
 assert(socket_type_to_security_class(PF_INET,SOCK_SEQPACKET,IPPROTO_TCP)==SECCLASS_TCP_SOCKET);
 assert(socket_type_to_security_class(PF_INET,SOCK_STREAM,IPPROTO_SCTP)==SECCLASS_RAWIP_SOCKET);
 assert(socket_type_to_security_class(PF_INET,SOCK_DGRAM,IPPROTO_ICMP)==SECCLASS_RAWIP_SOCKET);
 selinux_policycap_extsockclass=1;
 assert(socket_type_to_security_class(PF_INET,SOCK_STREAM,IPPROTO_SCTP)==SECCLASS_SCTP_SOCKET);
 assert(socket_type_to_security_class(PF_INET6,SOCK_SEQPACKET,IPPROTO_SCTP)==SECCLASS_SCTP_SOCKET);
 assert(socket_type_to_security_class(PF_INET,SOCK_DGRAM,IPPROTO_ICMP)==SECCLASS_ICMP_SOCKET);
 assert(socket_type_to_security_class(PF_UNIX,SOCK_SEQPACKET,0)==SECCLASS_UNIX_STREAM_SOCKET);
 assert(socket_type_to_security_class(PF_NETLINK,SOCK_DGRAM,NETLINK_FIREWALL)==SECCLASS_NETLINK_FIREWALL_SOCKET);
 assert(socket_type_to_security_class(PF_PACKET,SOCK_DGRAM,0)==SECCLASS_PACKET_SOCKET);
 return 0;
}
