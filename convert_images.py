#!/usr/bin/env python3
"""Convert all character images to Base64 and generate characterImages.js"""

import os
import base64

sucai_dir = "/root/ai/WutheringWavesDPS/sucai"
output_file = "/root/ai/WutheringWavesDPS/frontend/src/characterImages.js"

# Get all image files
image_files = []
for f in os.listdir(sucai_dir):
    if f.endswith(('.png', '.jpg', '.jpeg')):
        # Get character name without extension
        name = os.path.splitext(f)[0]
        image_files.append((name, f))

# Sort by name
image_files.sort(key=lambda x: x[0])

print(f"Found {len(image_files)} images")

# Generate the JS file
js_content = "export const characterImages = {\n"

total_size = 0
for name, filename in image_files:
    filepath = os.path.join(sucai_dir, filename)
    
    # Determine mime type
    if filename.endswith('.png'):
        mime_type = 'image/png'
    else:
        mime_type = 'image/jpeg'
    
    # Read and encode
    with open(filepath, 'rb') as f:
        image_data = f.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')
    
    size_kb = len(base64_data) / 1024
    total_size += size_kb
    
    # Add to JS content
    js_content += f"  '{name}': 'data:{mime_type};base64,{base64_data}',\n"
    print(f"Converted: {name} ({size_kb:.1f} KB)")

js_content += "};\n"

# Write to file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"\nDone! Generated {output_file}")
print(f"Total Base64 size: {total_size:.1f} KB ({total_size/1024:.2f} MB)")
