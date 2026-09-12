# AE1200 Digital — Amazfit Bip 6

Styled after [Casio AE-1200WHD-1AV](https://www.casio.com/us/watches/casio/product.AE-1200WHD-1AV/).

Package layout matches Zeus Bip 6 targets (`configVersion` v2, `390x450-amazfit-bip-6`).
Runtime uses **apiVersion 1.0** + `shared/device-polyfill` so the classic `hmUI` face renders (API 2.0 + hmUI = black screen on Bip 6).

| Region | Content |
|--------|---------|
| Top-left dial | Step goal progress + step count |
| Map well | Heart rate |
| Top-right | Battery |
| Bottom | Day, month-day, HH:MM |

## Review

```bash
xdg-open prototype/ae1200.html
xdg-open prototype/preview-390x450.png
```

Reference photo: `reference/ae1200-1.jpg`

## Build / preview

```bash
python3 scripts/generate_ae1200_assets.py
npm install   # optional if zeus is already global
zeus login
zeus preview  # or: npm run preview
```

Scan the QR from **Zepp → bound device → Developer Mode** (not the phone camera).
