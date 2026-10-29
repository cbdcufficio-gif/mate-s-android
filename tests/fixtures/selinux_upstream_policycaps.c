/* SPDX-License-Identifier: GPL-2.0-only
 * Unchanged security_load_policycaps from upstream revision in source registry.
 * Host fixture only.
 */
static void security_load_policycaps(void)
{
	unsigned int i;
	struct ebitmap_node *node;

	selinux_policycap_netpeer = ebitmap_get_bit(&policydb.policycaps,
						  POLICYDB_CAPABILITY_NETPEER);
	selinux_policycap_openperm = ebitmap_get_bit(&policydb.policycaps,
						  POLICYDB_CAPABILITY_OPENPERM);
	selinux_policycap_extsockclass = ebitmap_get_bit(&policydb.policycaps,
					  POLICYDB_CAPABILITY_EXTSOCKCLASS);
	selinux_policycap_alwaysnetwork = ebitmap_get_bit(&policydb.policycaps,
						  POLICYDB_CAPABILITY_ALWAYSNETWORK);
	selinux_policycap_cgroupseclabel =
		ebitmap_get_bit(&policydb.policycaps,
				POLICYDB_CAPABILITY_CGROUPSECLABEL);
	selinux_policycap_nnp_nosuid_transition =
		ebitmap_get_bit(&policydb.policycaps,
				POLICYDB_CAPABILITY_NNP_NOSUID_TRANSITION);

	for (i = 0; i < ARRAY_SIZE(selinux_policycap_names); i++)
		pr_info("SELinux:  policy capability %s=%d\n",
			selinux_policycap_names[i],
			ebitmap_get_bit(&policydb.policycaps, i));

	ebitmap_for_each_positive_bit(&policydb.policycaps, node, i) {
		if (i >= ARRAY_SIZE(selinux_policycap_names))
			pr_info("SELinux:  unknown policy capability %u\n",
				i);
	}
}
