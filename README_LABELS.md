# 🖨️ ZPL Label Printing Guide

## Overview
BOM Manager includes a built-in ZPL label generator for creating storage location labels compatible with Zebra thermal printers.

## Label Specifications
- **Size**: 2 x 1 inch (50.8 x 25.4 mm)
- **Resolution**: 203 DPI
- **Format**: ZPL (Zebra Programming Language)
- **Content**: 
  - Code 128 barcode
  - Text: "Storage: [location]"

## Part Number Categorization System

Parts are automatically categorized based on their first digit:

| First Digit | Category | Example | Description |
|-------------|----------|---------|-------------|
| **1xx** | Electronic Components | 155 | Component ID 55 |
| **2xx** | Screws | 2010 | Screw ID 010 |
| **3xx** | Nuts | 345 | Nut ID 45 |
| **4xx** | Bearings | 4100 | Bearing ID 100 |
| **5xx** | Cables | 512 | Cable ID 12 |

### Example Part Numbers
- `155` → Electronic Components (category 1, ID 55)
- `2345` → Screws (category 2, ID 345)
- `3001` → Nuts (category 3, ID 001)

## How to Use

### 1. Open Print Labels Tab
Click the **"🖨️ Print Labels"** button on the main screen.

### 2. Enter Location Code
Type the storage location code (e.g., `A1`, `B23`, `SHELF-05`).

### 3. Generate ZPL
The ZPL code is automatically generated as you type. Click **"Generate ZPL Code"** for confirmation.

### 4. Export Options
- **Copy to Clipboard**: Copy ZPL code for pasting into printer software
- **Save to File**: Save as `.zpl` file for later use

## Example ZPL Code

For location "A1":
```zpl
^XA
^FO50,20^BY2^BCN,100,Y,N,N^FDA1^FS
^FO50,140^A0N,30,30^FDStorage: A1^FS
^XZ
```

## Printing Instructions

### Method 1: Using Zebra Setup Utilities
1. Copy ZPL code to clipboard
2. Open Zebra Setup Utilities
3. Go to "Tools" → "Send File"
4. Paste ZPL code
5. Click "Send"

### Method 2: Save to File
1. Save ZPL to `.zpl` file
2. Send file directly to printer using printer driver

### Method 3: Direct Network Printing
```bash
# Send ZPL directly to network printer
cat label.zpl | nc printer-ip-address 9100
```

## Workflow Integration

### Complete Storage Setup Process:
1. **Scan Parts** (Tab 1: Scanning) - Import parts from QR codes
2. **Allocate Storage** (Tab 2: Allocating) - Assign storage locations
3. **Print Labels** (Tab 3: Print Labels) - Create physical labels
4. **Apply Labels** - Stick labels on storage bins/shelves

## Tips
- Use consistent location naming (e.g., A1-A99, B1-B99)
- Test print on plain paper first
- Adjust label size in printer settings if needed
- Keep spare labels for reorganization

## Troubleshooting

**Label prints too small/large**
- Adjust printer DPI settings
- Verify label size matches 2x1 inch

**Barcode not scanning**
- Increase barcode size in ZPL (`^BY` parameter)
- Check printer darkness setting
- Ensure clean print head

**Text cut off**
- Adjust `^FO` coordinates in ZPL
- Reduce font size

## ZPL Command Reference

Key ZPL commands used:
- `^XA` - Start format
- `^FO` - Field origin (position)
- `^BY` - Barcode field default
- `^BC` - Code 128 barcode
- `^A0` - Font selection
- `^FD` - Field data
- `^FS` - Field separator
- `^XZ` - End format

For more information, visit: [Zebra Programming Guide](https://www.zebra.com/us/en/support-downloads/knowledge-articles/zpl-commands.html)
