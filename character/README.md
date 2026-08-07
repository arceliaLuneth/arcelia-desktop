# character/

Berisi semua yang dipakai buat render avatar VRM Arcelia.

- `index.html` + `viewer.js` — halaman & logic render (three.js + `@pixiv/three-vrm`)
- `vendor/` — library three.js & three-vrm yang sudah di-vendor lokal (offline, tidak butuh internet saat runtime)

## Taruh file VRM kamu di sini

Copy file `.vrm` hasil export VRoid Studio kamu ke folder ini (nama bebas,
misal `arcelia.vrm`), lalu di Arcelia buka **Settings** → bagian "Karakter
(avatar VRM)":
- Centang **Tampilkan jendela karakter di desktop**
- Klik **Pilih...**, arahkan ke file `.vrm` kamu
- **Simpan**

Jendela karakter (transparan, selalu di atas, bisa di-drag pindah posisi)
akan langsung muncul. Mulutnya bakal "flap" pas Arcelia lagi ngomong
(TTS aktif), dan berkedip otomatis secara idle.

## Kalau mau ganti/update library-nya

```bash
cd character
npm init -y
npm install three @pixiv/three-vrm
# lalu copy ulang ke vendor/ (lihat komentar di ui/character_panel.py
# untuk struktur folder yang diharapkan)
```
