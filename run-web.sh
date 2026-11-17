#!/bin/sh
# Build Caterkiller 2026 and play it in the local browser.
#
# Assembles the game, serves the repository over HTTP (the pages use ES module
# imports, which browsers refuse to load from file://), opens the player page
# in the default browser, and keeps serving until Ctrl-C.
#
#   ./run-web.sh            serve on port 8000
#   ./run-web.sh 8080       serve on another port
#
# Environment:
#   CATERKILLER_WEB_PORT   default port (the argument wins)
#   CATERKILLER_NO_OPEN=1  do not launch a browser, just print the URLs
#
# Edit the assembly, run this again, and reload the page: play.html fetches the
# binary with caching disabled, so a rebuild is picked up on the next reload.

set -e
cd "$(dirname "$0")"

PORT="${1:-${CATERKILLER_WEB_PORT:-8000}}"
URL="http://localhost:$PORT/frontends/web/play.html"
DEV_URL="http://localhost:$PORT/frontends/web/"

make caterkiller2026

python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null; echo; echo "Server stopped."' EXIT INT TERM

# A server that cannot bind the port exits at once; give it a moment, then make
# sure it is still there before probing (another server on the port would answer too)
sleep 0.5
if ! kill -0 $SERVER 2>/dev/null; then
    echo "Could not start a web server on port $PORT (already in use?). Try: $0 8080" >&2
    trap - EXIT
    exit 1
fi
i=0
until python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$PORT/', timeout=1)" 2>/dev/null; do
    i=$((i + 1))
    if [ $i -ge 50 ]; then
        echo "The web server on port $PORT is not answering." >&2
        exit 1
    fi
    sleep 0.1
done

echo
echo "Playing:         $URL"
echo "Developer page:  $DEV_URL"
echo "Press Ctrl-C to stop the server."
echo

if [ "${CATERKILLER_NO_OPEN:-0}" != "1" ]; then
    case "$(uname -s)" in
        Darwin)                 open "$URL" ;;
        MINGW*|MSYS*|CYGWIN*)   start "$URL" ;;
        *)
            if grep -qi microsoft /proc/version 2>/dev/null && command -v cmd.exe >/dev/null 2>&1; then
                cmd.exe /c start "$URL"            # WSL
            elif command -v xdg-open >/dev/null 2>&1; then
                xdg-open "$URL"
            else
                echo "No browser launcher found; open the URL above by hand."
            fi
            ;;
    esac
fi

wait $SERVER
