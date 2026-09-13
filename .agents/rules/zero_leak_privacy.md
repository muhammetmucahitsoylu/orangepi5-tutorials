# Absolute Privacy & Zero-Leak Documentation Rule

## Strict Privacy & Security Mandate
This workspace and all associated projects are strictly constrained by the following zero-leak rules:

1. **NO Personal Data in Code or Documentation:**
   - Never write, commit, or document real local IP addresses (e.g., `192.168.x.x`), personal subnet ranges, or MAC addresses.
   - Always use generic placeholders: `<ORANGE_PI_IP>`, `<BOARD_IP>`, `<SERVER_IP>`, or dynamic runtime resolution (`socket.getsockname()`).
   - Never document personal hostnames (e.g., `soylu-desktop`), local machine usernames, or local Windows/Linux user directory paths.

2. **NO Credentials or Risky Configurations:**
   - Never record, hardcode, or log any passwords, sudo credentials, SSH private keys, API tokens, or passphrases anywhere in repository files, markdown guides, or git commit messages.
   - Any reference to credentials must use dummy placeholders such as `<YOUR_PASSWORD>` or `<SECURE_PASSPHRASE>`.

3. **Pre-Push Privacy Audit:**
   - Before proposing or executing any `git push` or committing code/docs, explicitly audit the changes to ensure 100% compliance with this zero-leak policy.
