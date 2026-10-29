/* SPDX-License-Identifier: GPL-2.0-only
 * Unchanged security_load_policycaps from huawei revision in source registry.
 * Host fixture only.
 */
static void security_load_policycaps(void)
{
	selinux_policycap_netpeer = ebitmap_get_bit(&policydb.policycaps,
						  POLICYDB_CAPABILITY_NETPEER);
	selinux_policycap_openperm = ebitmap_get_bit(&policydb.policycaps,
						  POLICYDB_CAPABILITY_OPENPERM);
}
