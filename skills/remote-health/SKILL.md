---
name: remote-health
description: Diagnose SSH, Tailscale, remote PATH, system service, lock, auth, and Codex CLI issues on named hosts. Use when the user mentions SSH, remote host, my-mini, my-arch, my-win, ty-hk, Tailscale, PATH, codex on a remote machine, apt lock, service status, or host reachability.
argument-hint: "[host]"
---

# Remote Health

Use the smallest live check that proves the path.

## SSH Basics

```bash
ssh -G <host> | sed -n '1,40p'
ssh -o BatchMode=yes -o ConnectTimeout=8 <host> 'hostname; whoami'
```

On macOS remote hosts, prefer login shell:

```bash
ssh <host> 'zsh -lc "echo $PATH; command -v node npm codex rg; codex doctor --summary --ascii"'
```

## Tailscale / Network

Do not treat ICMP ping failure as final. Check TCP or Tailscale:

```bash
ssh <jump-host> 'zsh -lc "tailscale status; tailscale netcheck"'
nc -vz <host-or-ip> 22
```

## Linux Service / Lock

```bash
ssh <host> 'systemctl --failed; systemctl list-timers | sed -n "1,80p"; sudo fuser -v /var/lib/dpkg/lock-frontend 2>/dev/null || true'
```

## Windows Key ACL

If Windows OpenSSH rejects a key, inspect ACL before rotating keys:

```powershell
icacls C:\Users\ferstar\.ssh\<key>
```

Private keys should not inherit broad sandbox or group read permissions.

## Output

Answer with: reachable yes/no, failing layer, evidence command, and next smallest fix.
