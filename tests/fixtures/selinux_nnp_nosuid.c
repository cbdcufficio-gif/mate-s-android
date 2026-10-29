/* SPDX-License-Identifier: GPL-2.0-only
 * Unchanged function from torvalds/linux af63f4193f9fbbbac50fc766417d74735afd87ef
 * security/selinux/hooks.c. Test-only; not a Huawei kernel patch.
 */
static int check_nnp_nosuid(const struct linux_binprm *bprm,
			    const struct task_security_struct *old_tsec,
			    const struct task_security_struct *new_tsec)
{
	int nnp = (bprm->unsafe & LSM_UNSAFE_NO_NEW_PRIVS);
	int nosuid = !mnt_may_suid(bprm->file->f_path.mnt);
	int rc;
	u32 av;

	if (!nnp && !nosuid)
		return 0; /* neither NNP nor nosuid */

	if (new_tsec->sid == old_tsec->sid)
		return 0; /* No change in credentials */

	/*
	 * If the policy enables the nnp_nosuid_transition policy capability,
	 * then we permit transitions under NNP or nosuid if the
	 * policy allows the corresponding permission between
	 * the old and new contexts.
	 */
	if (selinux_policycap_nnp_nosuid_transition) {
		av = 0;
		if (nnp)
			av |= PROCESS2__NNP_TRANSITION;
		if (nosuid)
			av |= PROCESS2__NOSUID_TRANSITION;
		rc = avc_has_perm(old_tsec->sid, new_tsec->sid,
				  SECCLASS_PROCESS2, av, NULL);
		if (!rc)
			return 0;
	}

	/*
	 * We also permit NNP or nosuid transitions to bounded SIDs,
	 * i.e. SIDs that are guaranteed to only be allowed a subset
	 * of the permissions of the current SID.
	 */
	rc = security_bounded_transition(old_tsec->sid, new_tsec->sid);
	if (!rc)
		return 0;

	/*
	 * On failure, preserve the errno values for NNP vs nosuid.
	 * NNP:  Operation not permitted for caller.
	 * nosuid:  Permission denied to file.
	 */
	if (nnp)
		return -EPERM;
	return -EACCES;
}
