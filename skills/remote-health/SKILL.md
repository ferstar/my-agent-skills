---
name: remote-health
description: Diagnose the live remote-access layer: SSH resolution, reachability, Tailscale, login-shell PATH, service state, package-manager locks, and remote CLI auth. Use when a named remote host or service is unreachable or unhealthy; do not use for deploy planning or ordinary local repo work.
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
icacls C:\Users\<username>\.ssh\<key>
```

Private keys should not inherit broad sandbox or group read permissions.

## Output

Answer with: reachable yes/no, failing layer, evidence command, and next smallest fix.
