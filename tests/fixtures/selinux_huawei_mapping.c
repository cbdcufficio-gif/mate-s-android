/* SPDX-License-Identifier: GPL-2.0-only; original Huawei functions, source registry revision. */
static int selinux_set_mapping(struct policydb *pol,
			       struct security_class_mapping *map,
			       struct selinux_mapping **out_map_p,
			       u16 *out_map_size)
{
	struct selinux_mapping *out_map = NULL;
	size_t size = sizeof(struct selinux_mapping);
	u16 i, j;
	unsigned k;
	bool print_unknown_handle = false;

	/* Find number of classes in the input mapping */
	if (!map)
		return -EINVAL;
	i = 0;
	while (map[i].name)
		i++;

	/* Allocate space for the class records, plus one for class zero */
	out_map = kcalloc(++i, size, GFP_ATOMIC);
	if (!out_map)
		return -ENOMEM;

	/* Store the raw class and permission values */
	j = 0;
	while (map[j].name) {
		struct security_class_mapping *p_in = map + (j++);
		struct selinux_mapping *p_out = out_map + j;

		/* An empty class string skips ahead */
		if (!strcmp(p_in->name, "")) {
			p_out->num_perms = 0;
			continue;
		}

		p_out->value = string_to_security_class(pol, p_in->name);
		if (!p_out->value) {
			printk(KERN_INFO
			       "SELinux:  Class %s not defined in policy.\n",
			       p_in->name);
			if (pol->reject_unknown)
				goto err;
			p_out->num_perms = 0;
			print_unknown_handle = true;
			continue;
		}

		k = 0;
		while (p_in->perms && p_in->perms[k]) {
			/* An empty permission string skips ahead */
			if (!*p_in->perms[k]) {
				k++;
				continue;
			}
			p_out->perms[k] = string_to_av_perm(pol, p_out->value,
							    p_in->perms[k]);
			if (!p_out->perms[k]) {
				printk(KERN_INFO
				       "SELinux:  Permission %s in class %s not defined in policy.\n",
				       p_in->perms[k], p_in->name);
				if (pol->reject_unknown)
					goto err;
				print_unknown_handle = true;
			}

			k++;
		}
		p_out->num_perms = k;
	}

	if (print_unknown_handle)
		printk(KERN_INFO "SELinux: the above unknown classes and permissions will be %s\n",
		       pol->allow_unknown ? "allowed" : "denied");

	*out_map_p = out_map;
	*out_map_size = i;
	return 0;
err:
	kfree(out_map);
	return -EINVAL;
}

static void map_decision(u16 tclass, struct av_decision *avd,
			 int allow_unknown)
{
	if (tclass < current_mapping_size) {
		unsigned i, n = current_mapping[tclass].num_perms;
		u32 result;

		for (i = 0, result = 0; i < n; i++) {
			if (avd->allowed & current_mapping[tclass].perms[i])
				result |= 1<<i;
			if (allow_unknown && !current_mapping[tclass].perms[i])
				result |= 1<<i;
		}
		avd->allowed = result;

		for (i = 0, result = 0; i < n; i++)
			if (avd->auditallow & current_mapping[tclass].perms[i])
				result |= 1<<i;
		avd->auditallow = result;

		for (i = 0, result = 0; i < n; i++) {
			if (avd->auditdeny & current_mapping[tclass].perms[i])
				result |= 1<<i;
			if (!allow_unknown && !current_mapping[tclass].perms[i])
				result |= 1<<i;
		}
		/*
		 * In case the kernel has a bug and requests a permission
		 * between num_perms and the maximum permission number, we
		 * should audit that denial
		 */
		for (; i < (sizeof(u32)*8); i++)
			result |= 1<<i;
		avd->auditdeny = result;
	}
}
