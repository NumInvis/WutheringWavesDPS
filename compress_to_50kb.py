#!/usr/bin/env python3
"""Compress all images to max 50KB"""

import os
from PIL import Image

sucai_dir = "/root/ai/WutheringWavesDPS/sucai"
MAX_SIZE = 50 * 1024  # 50KB
TARGET_DIMENSIONS = (120, 120)  # 减小尺寸

def compress_image(filepath):
    """Compress image to target size"""
    try:
        original_size = os.path.getsize(filepath)
        if original_size <= MAX_SIZE:
            return False, f"Skipped (already {original_size/1024:.1f}KB)"
        
        with Image.open(filepath) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize to smaller dimensions
            img_resized = img.resize(TARGET_DIMENSIONS, Image.Resampling.LANCZOS)
            
            # Get filename
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)
            
            # Try different quality levels to get under 50KB
            output_path = os.path.join(sucai_dir, f"{name}.jpg")
            
            quality = 85
            while quality >= 30:
                img_resized.save(output_path, 'JPEG', quality=quality, optimize=True)
                new_size = os.path.getsize(output_path)
                
                if new_size <= MAX_SIZE:
                    # Remove original if different
                    if filepath != output_path:
                        os.remove(filepath)
                    return True, f"{original_size/1024:.1f}KB -> {new_size/1024:.1f}KB (quality={quality})"
                
                quality -= 10
            
            # If still too big, reduce dimensions further
            img_resized = img.resize((100, 100), Image.Resampling.LANCZOS)
            img_resized.save(output_path, 'JPEG', quality=70, optimize=True)
            new_size = os.path.getsize(output_path)
            
            if filepath != output_path:
                os.remove(filepath)
            return True, f"{original_size/1024:.1f}KB -> {new_size/1024:.1f}KB (100x100)"
            
    except Exception as e:
        return False, f"Error: {e}"

# Process all files
compressed_count = 0
for filename in sorted(os.listdir(sucai_dir)):
    filepath = os.path.join(sucai_dir, filename)
    if os.path.isfile(filepath) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        success, msg = compress_image(filepath)
        if success:
            compressed_count += 1
            print(f"✓ {filename}: {msg}")
        else:
            print(f"- {filename}: {msg}")

print(f"\nTotal compressed: {compressed_count} images")
