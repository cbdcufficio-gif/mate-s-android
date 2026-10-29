#include <assert.h>
#include <errno.h>
#include <stddef.h>
#include <stdbool.h>
typedef unsigned int u32;
#define LSM_UNSAFE_NO_NEW_PRIVS 1
#define LSM_UNSAFE_SHARE 2
#define LSM_UNSAFE_PTRACE 4
#define LSM_UNSAFE_PTRACE_CAP 8
#define MNT_NOSUID 1
#define LSM_AUDIT_DATA_PATH 2
#define likely(x) (x)
#define PROCESS2__NNP_TRANSITION 1
#define PROCESS2__NOSUID_TRANSITION 2
#define SECCLASS_PROCESS2 9
#define SECCLASS_PROCESS 1
#define SECCLASS_FILE 2
#define FILE__EXECUTE_NO_TRANS 1
#define FILE__ENTRYPOINT 2
#define PROCESS__TRANSITION 4
#define PROCESS__SHARE 8
#define PROCESS__PTRACE 16
#define PER_CLEAR_ON_SETID 32
#define LSM_AUDIT_DATA_FILE 1
struct task_security_struct { u32 sid,osid,exec_sid,create_sid,keycreate_sid,sockcreate_sid; };
struct inode_security_struct { u32 sid; };
struct inode { struct inode_security_struct *i_security; };
struct vfsmount { int mnt_flags; int ours; };
struct path { struct vfsmount *mnt; };
struct file { struct path f_path; struct inode *inode; };
struct cred { struct task_security_struct *security; };
struct linux_binprm { int unsafe,cred_prepared; unsigned int per_clear; struct file *file; struct cred *cred; };
struct common_audit_data { int type; union { struct file *file; struct path path; } u; };
static struct task_security_struct old;
static int selinux_policycap_nnp_nosuid_transition, policy_allow, bound_allow;
static int deny_class,deny_perm, transition_error, calls,exec_no_trans,transitions,entrypoints;
static struct task_security_struct *current_security(void) { return &old; }
static struct inode *file_inode(struct file *f) { return f->inode; }
static int our_mnt(struct vfsmount *m) { return m->ours; }
struct task_struct { int unused; }; static struct task_struct task;
static struct task_security_struct tracer_sec={.sid=30};
static struct cred tracer_cred={&tracer_sec};
static struct task_struct *current=&task;
static void rcu_read_lock(void) {} static void rcu_read_unlock(void) {}
static struct task_struct *ptrace_parent(struct task_struct *t) { (void)t; return &task; }
static struct cred *__task_cred(struct task_struct *t) { (void)t; return &tracer_cred; }
static int cap_rc,cap_calls;
static int cap_bprm_set_creds(struct linux_binprm *b) { (void)b;cap_calls++;return cap_rc; }
static int security_transition_sid(u32 a,u32 b,int cls,void *name,u32 *sid) {
 assert(a==10 && b==100 && cls==SECCLASS_PROCESS && !name);
 *sid=20;return transition_error;
}
static int security_bounded_transition(u32 a,u32 b) { assert(a==10&&b==20);return bound_allow?0:-EPERM; }
static int avc_has_perm(u32 a,u32 b,int cls,u32 av,void *audit) {
 (void)a;(void)b;(void)audit;calls++;
 if(cls==SECCLASS_PROCESS2) return policy_allow?0:-EACCES;
 if(cls==SECCLASS_FILE && av==FILE__EXECUTE_NO_TRANS) exec_no_trans++;
 if(cls==SECCLASS_FILE && av==FILE__ENTRYPOINT) entrypoints++;
 if(cls==SECCLASS_PROCESS && av==PROCESS__TRANSITION) transitions++;
 return cls==deny_class && av==(u32)deny_perm?-EACCES:0;
}

static bool carrera_mnt_may_suid(struct vfsmount *mnt)
{
#ifdef CONFIG_USER_NS
	(void)mnt;
	return false;
#else
	return !(mnt->mnt_flags & MNT_NOSUID) && our_mnt(mnt);
#endif
}

static int check_nnp_nosuid(const struct linux_binprm *bprm,
			    const struct task_security_struct *old_tsec,
			    const struct task_security_struct *new_tsec)
{
	int nnp = (bprm->unsafe & LSM_UNSAFE_NO_NEW_PRIVS);
	int nosuid = !carrera_mnt_may_suid(bprm->file->f_path.mnt);
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


static int selinux_bprm_set_creds(struct linux_binprm *bprm)
{
	const struct task_security_struct *old_tsec;
	struct task_security_struct *new_tsec;
	struct inode_security_struct *isec;
	struct common_audit_data ad;
	struct inode *inode = file_inode(bprm->file);
	int rc;

	rc = cap_bprm_set_creds(bprm);
	if (rc)
		return rc;

	/* SELinux context only depends on initial program or script and not
	 * the script interpreter */
	if (bprm->cred_prepared)
		return 0;

	old_tsec = current_security();
	new_tsec = bprm->cred->security;
	isec = inode->i_security;

	/* Default to the current task SID. */
	new_tsec->sid = old_tsec->sid;
	new_tsec->osid = old_tsec->sid;

	/* Reset fs, key, and sock SIDs on execve. */
	new_tsec->create_sid = 0;
	new_tsec->keycreate_sid = 0;
	new_tsec->sockcreate_sid = 0;

	if (old_tsec->exec_sid) {
		new_tsec->sid = old_tsec->exec_sid;
		/* Reset exec SID on execve. */
		new_tsec->exec_sid = 0;

		rc = check_nnp_nosuid(bprm, old_tsec, new_tsec);
		if (rc)
			return rc;
	} else {
		/* Check for a default transition on this program. */
		rc = security_transition_sid(old_tsec->sid, isec->sid,
					     SECCLASS_PROCESS, NULL,
					     &new_tsec->sid);
		if (rc)
			return rc;
		rc = check_nnp_nosuid(bprm, old_tsec, new_tsec);
		if (rc)
			new_tsec->sid = old_tsec->sid;
	}

	ad.type = LSM_AUDIT_DATA_PATH;
	ad.u.path = bprm->file->f_path;

	if (new_tsec->sid == old_tsec->sid) {
		rc = avc_has_perm(old_tsec->sid, isec->sid,
				  SECCLASS_FILE, FILE__EXECUTE_NO_TRANS, &ad);
		if (rc)
			return rc;
	} else {
		/* Check permissions for the transition. */
		rc = avc_has_perm(old_tsec->sid, new_tsec->sid,
				  SECCLASS_PROCESS, PROCESS__TRANSITION, &ad);
		if (rc)
			return rc;

		rc = avc_has_perm(new_tsec->sid, isec->sid,
				  SECCLASS_FILE, FILE__ENTRYPOINT, &ad);
		if (rc)
			return rc;

		/* Check for shared state */
		if (bprm->unsafe & LSM_UNSAFE_SHARE) {
			rc = avc_has_perm(old_tsec->sid, new_tsec->sid,
					  SECCLASS_PROCESS, PROCESS__SHARE,
					  NULL);
			if (rc)
				return -EPERM;
		}

		/* Make sure that anyone attempting to ptrace over a task that
		 * changes its SID has the appropriate permit */
		if (bprm->unsafe &
		    (LSM_UNSAFE_PTRACE | LSM_UNSAFE_PTRACE_CAP)) {
			struct task_struct *tracer;
			struct task_security_struct *sec;
			u32 ptsid = 0;

			rcu_read_lock();
			tracer = ptrace_parent(current);
			if (likely(tracer != NULL)) {
				sec = __task_cred(tracer)->security;
				ptsid = sec->sid;
			}
			rcu_read_unlock();

			if (ptsid != 0) {
				rc = avc_has_perm(ptsid, new_tsec->sid,
						  SECCLASS_PROCESS,
						  PROCESS__PTRACE, NULL);
				if (rc)
					return -EPERM;
			}
		}

		/* Clear any possibly unsafe personality bits on exec: */
		bprm->per_clear |= PER_CLEAR_ON_SETID;
	}

	return 0;
}

static int run_case(int explicit,int nnp,int nosuid,int allow,int bound,int cls,int perm,int unsafe,int prepared,int terr) {
 old=(struct task_security_struct){.sid=10,.exec_sid=explicit?20:0};
 struct task_security_struct next={.exec_sid=99,.create_sid=99,.keycreate_sid=99,.sockcreate_sid=99};
 struct inode_security_struct isec={100};struct inode inode={&isec};
 struct vfsmount m={nosuid?MNT_NOSUID:0,1};struct file file={{&m},&inode};struct cred cred={&next};
 struct linux_binprm b={nnp|unsafe,prepared,0,&file,&cred};
 selinux_policycap_nnp_nosuid_transition=1;policy_allow=allow;bound_allow=bound;cap_calls=0;
 deny_class=cls;deny_perm=perm;transition_error=terr;calls=exec_no_trans=transitions=entrypoints=0;
 int rc=selinux_bprm_set_creds(&b); assert(cap_calls==1); if(cap_rc) { assert(rc==cap_rc); return rc; }
 if(prepared) { assert(rc==0 && calls==0 && next.create_sid==99); return rc; }
 assert(next.create_sid==0 && next.keycreate_sid==0 && next.sockcreate_sid==0);
 if(!rc) {
   if(next.sid==10) assert(exec_no_trans==1 && transitions==0 && b.per_clear==0);
   else assert(next.sid==20 && transitions==1 && entrypoints==1 && b.per_clear==PER_CLEAR_ON_SETID);
 }
 return rc;
}
int main(void) {
 struct vfsmount foreign={0,0}; assert(!carrera_mnt_may_suid(&foreign));
 for(int explicit=0;explicit<2;explicit++) for(int nnp=0;nnp<2;nnp++)
 for(int nosuid=0;nosuid<2;nosuid++) for(int allow=0;allow<2;allow++)
 for(int bound=0;bound<2;bound++) {
   int blocked=(nnp||nosuid)&&!allow&&!bound;
   int expected=explicit&&blocked?(nnp?-EPERM:-EACCES):0;
   assert(run_case(explicit,nnp,nosuid,allow,bound,0,0,0,0,0)==expected);
   if(!explicit && blocked) assert(exec_no_trans==1 && transitions==0);
 }
 assert(run_case(0,1,0,0,0,SECCLASS_FILE,FILE__EXECUTE_NO_TRANS,0,0,0)==-EACCES);
 assert(run_case(1,0,0,1,0,SECCLASS_PROCESS,PROCESS__TRANSITION,0,0,0)==-EACCES);
 assert(run_case(1,0,0,1,0,SECCLASS_FILE,FILE__ENTRYPOINT,0,0,0)==-EACCES);
 assert(run_case(1,0,0,1,0,SECCLASS_PROCESS,PROCESS__SHARE,LSM_UNSAFE_SHARE,0,0)==-EPERM);
 assert(run_case(1,0,0,1,0,SECCLASS_PROCESS,PROCESS__PTRACE,LSM_UNSAFE_PTRACE,0,0)==-EPERM);
 assert(run_case(0,0,0,1,0,0,0,0,0,-EINVAL)==-EINVAL);
 assert(run_case(0,0,0,1,0,0,0,0,1,0)==0);
 cap_rc=-EACCES;assert(run_case(0,0,0,1,0,0,0,0,0,0)==-EACCES);
 return 0;
}
