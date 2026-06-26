#!/data/data/com.termux/files/usr/bin/bash
set -e

rm -f "$PREFIX/bin/mrapweather"
rm -f "$PREFIX/bin/mrapweather-key"

echo "✅ Openweather command removed."
echo "Config file kept at: ~/.config/mrapweather/config.env"
