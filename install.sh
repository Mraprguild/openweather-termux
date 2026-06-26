#!/data/data/com.termux/files/usr/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$PREFIX/bin"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌦 Installing Openweather for Termux"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pkg update -y
pkg install -y python

chmod +x "$PROJECT_DIR/weather.py"
chmod +x "$PROJECT_DIR/scripts/mrapweather-key"

cat > "$BIN_DIR/mrapweather" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
python "$PROJECT_DIR/weather.py" "\$@"
EOF

cp "$PROJECT_DIR/scripts/mrapweather-key" "$BIN_DIR/mrapweather-key"

chmod +x "$BIN_DIR/mrapweather"
chmod +x "$BIN_DIR/mrapweather-key"

echo "✅ Installed successfully."
echo ""
echo "Set API key:"
echo "  mrapweather-key YOUR_OPENWEATHER_API_KEY"
echo ""
echo "Run:"
echo "  mrapweather select"
echo "  mrapweather current --city \"Chennai,IN\""
echo "  mrapweather forecast --city \"Chennai,IN\" --limit 10"
