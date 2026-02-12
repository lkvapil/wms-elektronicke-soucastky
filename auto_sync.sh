#!/bin/bash
# Automatické sledování změn v .tex souborech a push na GitHub

WATCH_DIR="/Users/lukaskvapil/Documents/bomManager/odevzdani"
REPO_DIR="/Users/lukaskvapil/Documents/bomManager"

echo "🔍 Sledování změn v .tex souborech..."
echo "📁 Adresář: $WATCH_DIR"
echo "💡 Stiskni Ctrl+C pro ukončení"
echo ""

# Sledování změn v .tex souborech
fswatch -0 "$WATCH_DIR"/*.tex | while read -d "" event
do
    echo "📝 Detekována změna: $(basename "$event")"
    echo "⏳ Synchronizace s GitHub..."
    
    cd "$REPO_DIR"
    
    # Přidání změn
    git add .
    
    # Commit s timestampem a názvem souboru
    FILE_NAME=$(basename "$event")
    git commit -m "Auto-update: $FILE_NAME ($(date '+%Y-%m-%d %H:%M:%S'))"
    
    # Push na GitHub
    if git push origin main; then
        echo "✅ Úspěšně nahráno na GitHub!"
    else
        echo "❌ Chyba při nahrávání na GitHub"
    fi
    
    echo ""
done
