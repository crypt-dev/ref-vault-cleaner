# ref-vault-cleaner

<p align="center">
  <strong>Local-first perceptual image deduplicator for reference libraries, moodboards, and digital art archives.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/dependencies-Pillow-orange.svg" alt="Dependencies">
  <img src="https://img.shields.io/badge/telemetry-none-red.svg" alt="No Telemetry">
</p>

---

Traditional file deduplicators rely on exact cryptographic checksums (MD5, SHA-256). If an image has been converted to WebP, slightly resized, saved with different JPEG compression levels, or stripped of EXIF metadata, hash-based detectors fail completely.

**ref-vault-cleaner** computes 64-bit difference hashes (`dHash`) directly from image luminance gradients. It groups visually identical and near-identical files into clusters, marks the highest-resolution version in each group, and exports a self-contained, offline HTML report with embedded base64 thumbnails for safe review.

## Key Features

- **Perceptual Gradient Hashing:** Identifies matching artwork and photos even across resolution shifts, heavy compression artifacts, and format conversions (`.png`, `.jpg`, `.webp`, `.bmp`, `.tiff`).
- **Zero Cloud Footprint:** Runs 100% locally on your machine. No accounts, API keys, tracking, or outbound network calls.
- **Standalone Offline Reports:** Generates an interactive, dark-mode HTML inspection gallery with embedded base64 thumbnails, letting you visually review matches without altering files automatically.
- **Smart Primary Asset Flagging:** Automatically highlights the highest pixel-count version inside every duplicate cluster.
- **Tunable Strictness:** Adjust the Hamming distance threshold via command-line flags to balance between strict duplicates and loose visual variants.

---

## Installation

Ensure you have Python 3.9+ installed, then clone the repository:

```bash
git clone [https://github.com/crypt-dev/ref-vault-cleaner.git](https://github.com/crypt-dev/ref-vault-cleaner.git)
cd ref-vault-cleaner
pip install -r requirements.txt
