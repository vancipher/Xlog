from PIL import Image, ImageDraw

# Create a simple icon (256x256)
img = Image.new('RGB', (256, 256), color='#617388')
draw = ImageDraw.Draw(img)

# Draw a simple library book symbol
# Outer rectangle (book cover)
draw.rectangle([30, 40, 226, 216], outline='#D4B5A8', width=4)

# Spine (left side)
draw.rectangle([30, 40, 60, 216], outline='#D4B5A8', width=2, fill='#4A5568')

# Pages lines (book pages)
for y in range(80, 180, 15):
    draw.line([(70, y), (210, y)], fill='#D4B5A8', width=2)

# Save as ICO
img.save('app_icon.ico')
print("✅ Icon created: app_icon.ico (256x256)")
