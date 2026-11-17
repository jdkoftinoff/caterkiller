#!/bin/bash
# Login shell wrapper for SSH-based game serving.
#
# Set this script as a user's login shell (or as an SSH ForceCommand) so
# that connecting over SSH drops the user straight into the game with no
# shell access.
#
# Setup (as root):
#
#   1. Create a dedicated user with this script as their shell:
#
#        useradd -m -s /path/to/serve_ssh.sh caterkiller
#        passwd caterkiller            # set a password, or use keys only
#
#      The script must be listed in /etc/shells.
#
#   2. Or, for key-only access, add to ~caterkiller/.ssh/authorized_keys:
#
#        command="/path/to/serve_ssh.sh",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA...
#
#   3. Or, restrict a user in /etc/ssh/sshd_config:
#
#        Match User caterkiller
#            ForceCommand /path/to/serve_ssh.sh
#            AllowTcpForwarding no
#            X11Forwarding no
#
#   Then: ssh caterkiller@yourhost
#
# When the player quits, the SSH session ends.
#
# Environment overrides:
#   CATERKILLER_TUI    path to the caterkiller-tui binary
#   CATERKILLER_BIN    path to the game binary to run
#   CATERKILLER_LOAD   load address (default 0x6000)
#   CATERKILLER_START  start PC (default 0x7200)

set -e

# Reject remote command requests ("ssh host ls" invokes the shell as "-c <cmd>").
case "${1:-}" in
    -c) echo "Shell access is not available. Disconnecting."; exit 1 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/../.."

TUI="${CATERKILLER_TUI:-}"
if [ -z "$TUI" ]; then
    for candidate in "$SCRIPT_DIR/caterkiller-tui" "$SCRIPT_DIR/target/release/caterkiller-tui"; do
        if [ -x "$candidate" ]; then TUI="$candidate"; break; fi
    done
fi
if [ -z "$TUI" ]; then
    echo "caterkiller-tui not found. Build it with 'make tui' or set CATERKILLER_TUI."
    exit 1
fi

BINARY="${CATERKILLER_BIN:-}"
if [ -z "$BINARY" ]; then
    for candidate in "$SCRIPT_DIR/caterkiller2026.bin" \
                     "$ROOT/build/caterkiller/caterkiller2026.bin" \
                     "$ROOT/games/caterkiller/original/level3.bin"; do
        if [ -f "$candidate" ]; then BINARY="$candidate"; break; fi
    done
fi
if [ -z "$BINARY" ]; then
    echo "No game binary found. Set CATERKILLER_BIN or run 'make caterkiller2026'."
    exit 1
fi

LOAD_ADDR="${CATERKILLER_LOAD:-0x6000}"
START_PC="${CATERKILLER_START:-0x7200}"

export TERM="${TERM:-xterm-256color}"

exec "$TUI" "$BINARY" --load="$LOAD_ADDR" --start="$START_PC"
