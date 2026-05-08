#!/usr/bin/env python3
"""
Create a simple icon for OMNIS - OpenCode style
Generates a 256x256 PNG icon with 'O>' text
"""
try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Create image
    size = 256
    img = Image.new('RGBA', (size, size), (13, 13, 13, 255))  # #0d0d0d background
    draw = ImageDraw.Draw(img)
    
    # Draw circle border in cyan
    draw.ellipse([8, 8, size-8, size-8], outline='#00d4ff', width=4)
    
    # Draw text "O>" in center
    try:
        font = ImageFont.truetype("consolas.ttf", 80)
    except Exception as e:
        font = ImageFont.load_default()
    
    text = "O>"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 10
    
    draw.text((x, y), text, fill='#00d4ff', font=font)
    
    # Save as both PNG and ICO
    img.save('C:\\Users\\stefa\\Desktop\\AI projects\\Projects\\Omnis\\icon.png', 'PNG')
    
    # Convert to ICO for shortcut
    img.save('C:\\Users\\stefa\\Desktop\\AI projects\\Projects\\Omnis\\icon.ico', 'ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    
    print("[OK] Icon created: icon.png and icon.ico")
    
except ImportError:
    print("[WARN] PIL/Pillow not installed. Install with: pip install Pillow")
    print("       Icon will use default.")
except Exception as e:
    print(f"[ERROR] Failed to create icon: {e}")
