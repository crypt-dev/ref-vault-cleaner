import os
import sys
import argparse
import base64
from pathlib import Path
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

def calculate_dhash(image_path: Path, hash_size: int = 8) -> int:
    """Computes a 64-bit difference hash (dHash) for an image."""
    try:
        with Image.open(image_path) as img:
            # Convert to 8-bit grayscale and resize to (hash_size + 1, hash_size)
            resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(resized.getdata())

            difference = []
            for row in range(hash_size):
                row_offset = row * (hash_size + 1)
                for col in range(hash_size):
                    pixel_left = pixels[row_offset + col]
                    pixel_right = pixels[row_offset + col + 1]
                    difference.append(pixel_left > pixel_right)

            # Pack boolean array into an integer
            decimal_value = 0
            for index, value in enumerate(difference):
                if value:
                    decimal_value += 1 << index
            return decimal_value
    except Exception:
        return None

def get_image_metadata(image_path: Path) -> dict:
    """Extracts resolution, file size, and generates an embedded thumbnail."""
    try:
        stat = image_path.stat()
        file_size_kb = round(stat.st_size / 1024, 2)
        with Image.open(image_path) as img:
            width, height = img.size
            # Generate small base64 thumbnail for offline report viewing
            img.thumbnail((250, 250))
            from io import BytesIO
            buffer = BytesIO()
            img.convert("RGB").save(buffer, format="JPEG", quality=70)
            thumb_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "path": str(image_path.resolve()),
            "name": image_path.name,
            "size_kb": file_size_kb,
            "resolution": f"{width}x{height}",
            "pixels": width * height,
            "thumb": f"data:image/jpeg;base64,{thumb_b64}"
        }
    except Exception:
        return None

def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculates the bitwise Hamming distance between two hashes."""
    x = hash1 ^ hash2
    return bin(x).count("1")

def find_duplicate_clusters(scanned_images: list, max_distance: int = 4) -> list:
    """Groups images into similarity clusters based on Hamming distance threshold."""
    clusters = []
    visited = set()
    total = len(scanned_images)

    for i in range(total):
        if i in visited:
            continue

        item_a = scanned_images[i]
        cluster = [item_a["meta"]]
        visited.add(i)

        for j in range(i + 1, total):
            if j in visited:
                continue

            item_b = scanned_images[j]
            dist = hamming_distance(item_a["hash"], item_b["hash"])
            if dist <= max_distance:
                cluster.append(item_b["meta"])
                visited.add(j)

        if len(cluster) > 1:
            # Sort cluster by resolution descending (highest resolution first)
            cluster.sort(key=lambda x: x["pixels"], reverse=True)
            clusters.append(cluster)

    return clusters

def generate_html_report(clusters: list, output_file: Path):
    """Produces an interactive, zero-dependency offline HTML report."""
    total_duplicates = sum(len(c) - 1 for c in clusters)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ref Vault Duplicate Report</title>
<style>
    body {{
        background: #111215;
        color: #d1d5db;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        padding: 30px;
        margin: 0;
    }}
    h1 {{ color: #ffffff; margin-bottom: 5px; }}
    .stats {{ color: #9ca3af; margin-bottom: 25px; font-size: 14px; }}
    .cluster {{
        background: #1c1d22;
        border: 1px solid #2d2f36;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
    }}
    .cluster-title {{
        font-size: 15px;
        font-weight: 600;
        color: #f3f4f6;
        margin-bottom: 15px;
    }}
    .grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
    }}
    .card {{
        background: #141518;
        border: 1px solid #2d2f36;
        border-radius: 6px;
        padding: 12px;
        width: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .card.primary {{
        border-color: #059669;
        box-shadow: 0 0 10px rgba(5, 150, 105, 0.2);
    }}
    .badge {{
        background: #059669;
        color: #ffffff;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        width: fit-content;
        margin-bottom: 8px;
    }}
    .img-wrap {{
        height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #090a0c;
        border-radius: 4px;
        overflow: hidden;
    }}
    .img-wrap img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }}
    .meta {{
        font-size: 12px;
        margin-top: 10px;
        word-break: break-all;
    }}
    .meta span {{ display: block; margin-top: 3px; color: #9ca3af; }}
    .meta .file-name {{ font-weight: 600; color: #ffffff; }}
    .path {{ font-family: monospace; font-size: 11px; color: #6b7280; }}
</style>
</head>
<body>
    <h1>Reference Vault Duplicate Report</h1>
    <div class="stats">Identified <strong>{len(clusters)}</strong> visual clusters containing <strong>{total_duplicates}</strong> redundant files.</div>
"""

    for idx, cluster in enumerate(clusters, 1):
        html += f"""
    <div class="cluster">
        <div class="cluster-title">Visual Cluster #{idx} ({len(cluster)} variations)</div>
        <div class="grid">
"""
        for i, item in enumerate(cluster):
            is_best = (i == 0)
            primary_class = " primary" if is_best else ""
            badge_html = '<div class="badge">HIGHEST RESOLUTION</div>' if is_best else ""
            html += f"""
            <div class="card{primary_class}">
                <div>
                    {badge_html}
                    <div class="img-wrap"><img src="{item['thumb']}" alt="{item['name']}"></div>
                    <div class="meta">
                        <div class="file-name">{item['name']}</div>
                        <span>Resolution: <strong>{item['resolution']}</strong></span>
                        <span>Size: <strong>{item['size_kb']} KB</strong></span>
                    </div>
                </div>
                <div class="path">{item['path']}</div>
            </div>
"""
        html += """
        </div>
    </div>
"""

    html += """
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    parser = argparse.ArgumentParser(description="Scan and find visually duplicate reference images.")
    parser.add_argument("directory", type=str, help="Directory to scan recursively")
    parser.add_argument("--threshold", type=int, default=4, help="Maximum Hamming distance for matching (default: 4)")
    parser.add_argument("--output", type=str, default="duplicates_report.html", help="HTML report output path")
    args = parser.parse_args()

    target_dir = Path(args.directory)
    if not target_dir.is_dir():
        print(f"Error: Provided path '{target_dir}' is not a directory.")
        sys.exit(1)

    print(f"[*] Scanning '{target_dir}' for images...")
    image_paths = [
        p for p in target_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    print(f"[*] Found {len(image_paths)} image assets. Generating visual perceptual hashes...")

    valid_entries = []
    for p in image_paths:
        h = calculate_dhash(p)
        if h is not None:
            meta = get_image_metadata(p)
            if meta:
                valid_entries.append({"hash": h, "meta": meta})

    print(f"[*] Clustered {len(valid_entries)} images. Calculating similarity matrix...")
    clusters = find_duplicate_clusters(valid_entries, max_distance=args.threshold)

    if not clusters:
        print("[+] No visual duplicates found within the given threshold.")
        return

    output_path = Path(args.output).resolve()
    generate_html_report(clusters, output_path)
    print(f"[+] Complete: Identified {len(clusters)} duplicate clusters.")
    print(f"[+] Offline review report generated: {output_path}")

if __name__ == "__main__":
    main()
