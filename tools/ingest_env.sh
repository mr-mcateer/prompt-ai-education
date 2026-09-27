#!/bin/zsh
# Move a secret from the clipboard into .env without it ever appearing on screen, in history or in a chat.
# Usage: copy the key, then run   zsh tools/ingest_env.sh CANVAS_API_TOKEN   (or GEMINI_API_KEY)
# The clipboard is cleared afterward. .env is gitignored and kept at mode 600.
set -eu
cd "${0:A:h}/.."
name="${1:-}"
case "$name" in CANVAS_API_TOKEN|GEMINI_API_KEY) ;; *) print "usage: zsh tools/ingest_env.sh CANVAS_API_TOKEN|GEMINI_API_KEY"; exit 2 ;; esac
val="$(pbpaste | tr -d '\r\n[:space:]')"
[ ${#val} -ge 20 ] || { print "Clipboard holds ${#val} characters, too short for a key. Copy it again."; exit 1; }
umask 077
[ -f .env ] || print "CANVAS_API_URL=https://csd509j.instructure.com" > .env
grep -v "^$name=" .env > .env.tmp || true
print -r -- "$name=$val" >> .env.tmp
mv .env.tmp .env && chmod 600 .env
print -n "" | pbcopy
print "Saved $name (${#val} characters). Clipboard cleared."
