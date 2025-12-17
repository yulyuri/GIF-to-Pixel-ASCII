"""
ASCII Art Converter - Direct Python translation of the C implementation
from gouwsxander/ascii-view

This matches the original C code exactly.
"""

import numpy as np
from PIL import Image
import colorsys
import math

# ==================== CONSTANTS ====================

VALUE_CHARS = " .-=+*x#$&X@"

# Sobel kernels
SOBEL_X = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1]
], dtype=np.float64)

SOBEL_Y = np.array([
    [1, 2, 1],
    [0, 0, 0],
    [-1, -2, -1]
], dtype=np.float64)

# ==================== HSV CONVERSION ====================

def rgb_to_hsv_manual(r, g, b):
    """
    RGB to HSV conversion matching the C implementation.
    Returns hue in degrees (0-360), saturation and value in 0-1 range.
    """
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    
    value = max_val
    chroma = max_val - min_val
    
    # Calculate saturation
    if abs(value) < 1e-4:
        saturation = 0.0
    else:
        saturation = chroma / value
    
    # Calculate hue
    if chroma < 1e-4:
        hue = 0.0
    elif max_val == r:
        hue = 60.0 * ((g - b) / chroma % 6.0)
        if hue < 0.0:
            hue += 360.0
    elif max_val == g:
        hue = 60.0 * (2.0 + (b - r) / chroma)
    else:  # max_val == b
        hue = 60.0 * (4.0 + (r - g) / chroma)
    
    return hue, saturation, value


def hsv_to_rgb_manual(hue, saturation, value):
    """
    HSV to RGB conversion matching the C implementation.
    Hue in degrees (0-360), saturation and value in 0-1 range.
    Returns RGB in 0-1 range.
    """
    c = value * saturation
    h_prime = hue / 60.0
    x = c * (1.0 - abs(h_prime % 2.0 - 1.0))
    
    if 0.0 <= h_prime < 1.0:
        r1, g1, b1 = c, x, 0.0
    elif 1.0 <= h_prime < 2.0:
        r1, g1, b1 = x, c, 0.0
    elif 2.0 <= h_prime < 3.0:
        r1, g1, b1 = 0.0, c, x
    elif 3.0 <= h_prime < 4.0:
        r1, g1, b1 = 0.0, x, c
    elif 4.0 <= h_prime < 5.0:
        r1, g1, b1 = x, 0.0, c
    else:
        r1, g1, b1 = c, 0.0, x
    
    m = value - c
    return r1 + m, g1 + m, b1 + m

# ==================== CHARACTER SELECTION ====================

def get_ascii_char(grayscale):
    """
    Map grayscale value (0-1) to ASCII character.
    Matches C implementation exactly.
    """
    index = int(grayscale * len(VALUE_CHARS))
    if index >= len(VALUE_CHARS):
        index = len(VALUE_CHARS) - 1
    return VALUE_CHARS[index]


def get_sobel_angle_char(angle_degrees):
    """
    Map Sobel angle to directional character.
    Matches C implementation exactly.
    """
    if (22.5 <= angle_degrees <= 67.5) or (-157.5 <= angle_degrees <= -112.5):
        return '\\'
    elif (67.5 <= angle_degrees <= 112.5) or (-112.5 <= angle_degrees <= -67.5):
        return '_'
    elif (112.5 <= angle_degrees <= 157.5) or (-67.5 <= angle_degrees <= -22.5):
        return '/'
    else:
        return '|'

# ==================== IMAGE PROCESSING ====================

def rgb_to_luminance(r, g, b):
    """
    Convert RGB to grayscale using Rec. 709 coefficients.
    Matches C implementation.
    """
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def resize_with_averaging(img_array, target_width, target_height):
    """
    Resize image using area averaging, matching the C implementation.
    """
    original_height, original_width, channels = img_array.shape
    
    resized = np.zeros((target_height, target_width, channels), dtype=np.float64)
    
    for j in range(target_height):
        y1 = (j * original_height) // target_height
        y2 = ((j + 1) * original_height) // target_height
        
        for i in range(target_width):
            x1 = (i * original_width) // target_width
            x2 = ((i + 1) * original_width) // target_width
            
            # Average the region
            region = img_array[y1:y2, x1:x2, :]
            resized[j, i, :] = region.mean(axis=(0, 1))
    
    return resized


def sobel_edge_detection(grayscale):
    """
    Apply Sobel edge detection.
    Returns Gx and Gy arrays (NOT magnitude and direction).
    """
    from scipy.ndimage import convolve
    
    Gx = convolve(grayscale, SOBEL_X, mode='constant', cval=0.0)
    Gy = convolve(grayscale, SOBEL_Y, mode='constant', cval=0.0)
    
    return Gx, Gy

# ==================== MAIN CONVERSION ====================

def image_to_ascii(image_path, max_width=80, max_height=48, 
                   edge_threshold=4.0, character_ratio=1.0,
                   use_retro_colors=False):
    """
    Convert image to colored ASCII art.
    
    Parameters:
    - max_width, max_height: maximum dimensions in characters
    - edge_threshold: threshold for edge detection (default 4.0 = disabled)
    - character_ratio: height/width ratio (1.0 for image render, 2.0 for terminal)
    - use_retro_colors: use 8-color retro palette instead of truecolor
    
    Returns ASCII art as string with ANSI color codes.
    
    NOTE: For IMAGE rendering, use character_ratio=1.0 to preserve aspect ratio!
          For TERMINAL display, use character_ratio=2.0 to compensate for tall chars.
    """
    print(f"\n{'='*60}")
    print(f"ASCII Art Converter (C Implementation)")
    print(f"{'='*60}")
    print(f"Input: {image_path}")
    print(f"Max dimensions: {max_width}x{max_height} characters")
    print(f"Edge threshold: {edge_threshold}")
    print(f"Character ratio: {character_ratio}")
    print(f"Retro colors: {use_retro_colors}")
    
    # Load image
    print(f"\nLoading image...")
    img = Image.open(image_path).convert('RGB')
    original_width, original_height = img.size
    print(f"  Original: {original_width}x{original_height}px")
    
    # Calculate target dimensions maintaining aspect ratio
    # If character_ratio=1.0, preserves original aspect ratio (for image rendering)
    # If character_ratio=2.0, squashes vertically (for terminal display)
    proposed_height = (original_height * max_width) // (character_ratio * original_width)
    if proposed_height <= max_height:
        width, height = max_width, int(proposed_height)
    else:
        width = int((character_ratio * original_width * max_height) / original_height)
        height = max_height
    
    print(f"  Target: {width}x{height} characters")
    
    # Convert to numpy array (0-1 range)
    img_array = np.array(img, dtype=np.float64) / 255.0
    
    # Resize using area averaging
    print(f"\nResizing with area averaging...")
    resized = resize_with_averaging(img_array, width, height)
    
    # Create grayscale version for edge detection
    print(f"Converting to grayscale...")
    grayscale = rgb_to_luminance(resized[:,:,0], resized[:,:,1], resized[:,:,2])
    
    # Edge detection
    sobel_x = None
    sobel_y = None
    if edge_threshold < 4.0:
        print(f"Applying Sobel edge detection...")
        sobel_x, sobel_y = sobel_edge_detection(grayscale)
    
    # Convert to ASCII
    print(f"\nConverting to ASCII art...")
    ascii_lines = []
    
    for y in range(height):
        line = ""
        for x in range(width):
            r, g, b = resized[y, x]
            
            # Convert to HSV
            hue, saturation, value = rgb_to_hsv_manual(r, g, b)
            
            # Calculate grayscale with contrast boost (value^2)
            pixel_grayscale = value * value
            
            # Set value to 1.0 for vivid colors
            # Character choice controls apparent brightness
            display_hue = hue
            display_sat = saturation
            display_value = 1.0
            
            # Retro color quantization
            if use_retro_colors:
                # Quantize hue to nearest 60 degrees
                display_hue = round(hue / 60.0) * 60.0
                if display_hue >= 360.0:
                    display_hue = 0.0
                # Quantize saturation: 0% or 100%
                display_sat = 0.0 if saturation < 0.25 else 1.0
            
            # Convert back to RGB for display
            disp_r, disp_g, disp_b = hsv_to_rgb_manual(display_hue, display_sat, display_value)
            
            # Convert to 0-255 range for ANSI codes
            ansi_r = int(disp_r * 255)
            ansi_g = int(disp_g * 255)
            ansi_b = int(disp_b * 255)
            
            # Choose character
            ascii_char = get_ascii_char(pixel_grayscale)
            
            # Check for edge
            if sobel_x is not None:
                sx = sobel_x[y, x]
                sy = sobel_y[y, x]
                square_sobel_magnitude = sx * sx + sy * sy
                
                if square_sobel_magnitude >= edge_threshold * edge_threshold:
                    sobel_angle = math.atan2(sy, sx) * 180.0 / math.pi
                    ascii_char = get_sobel_angle_char(sobel_angle)
            
            # Create ANSI colored character
            colored_char = f"\x1b[38;2;{ansi_r};{ansi_g};{ansi_b}m{ascii_char}"
            line += colored_char
        
        ascii_lines.append(line)
        
        if (y + 1) % max(1, height // 10) == 0:
            print(f"  Progress: {100 * (y + 1) // height}%")
    
    # Reset color at end
    ascii_art = '\n'.join(ascii_lines) + '\x1b[0m'
    
    print(f"\n{'='*60}")
    print(f"✓ Conversion complete!")
    print(f"{'='*60}\n")
    
    return ascii_art, width, height


def save_ascii_to_file(ascii_art, output_path):
    """Save ASCII art to text file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ascii_art)
    print(f"✓ Saved to: {output_path}")

# ==================== RENDERING TO IMAGE ====================

def render_ascii_to_image(ascii_art, output_path, font_size=8, bg_color=(0, 0, 0)):
    """
    Render colored ASCII art to PNG image.
    """
    from PIL import ImageDraw, ImageFont
    import re
    
    print(f"\n{'='*60}")
    print(f"Rendering ASCII to Image")
    print(f"{'='*60}")
    
    lines = ascii_art.split('\n')
    
    # Try to load monospace font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Calculate character dimensions
    test_img = Image.new('RGB', (100, 100))
    test_draw = ImageDraw.Draw(test_img)
    bbox = test_draw.textbbox((0, 0), 'M', font=font)
    char_width = bbox[2] - bbox[0]
    char_height = bbox[3] - bbox[1]
    
    print(f"Font size: {font_size}px")
    print(f"Character dimensions: {char_width}x{char_height}px")
    
    # Calculate image size
    max_line_length = max(len(re.sub(r'\x1b\[[0-9;]*m', '', line)) for line in lines)
    img_width = max_line_length * char_width
    img_height = len(lines) * char_height
    
    print(f"Image size: {img_width}x{img_height}px")
    
    # Create image
    img = Image.new('RGB', (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw each line
    print(f"\nRendering...")
    ansi_pattern = r'\x1b\[38;2;(\d+);(\d+);(\d+)m(.)'
    
    for y_line, line in enumerate(lines):
        x_pos = 0
        
        for match in re.finditer(ansi_pattern, line):
            r = int(match.group(1))
            g = int(match.group(2))
            b = int(match.group(3))
            char = match.group(4)
            
            x = x_pos * char_width
            y = y_line * char_height
            draw.text((x, y), char, fill=(r, g, b), font=font)
            
            x_pos += 1
        
        if (y_line + 1) % max(1, len(lines) // 10) == 0:
            print(f"  Progress: {100 * (y_line + 1) // len(lines)}%")
    
    img.save(output_path)
    
    print(f"\n{'='*60}")
    print(f"✓ Image saved: {output_path}")
    print(f"{'='*60}\n")
    
    return img

# ==================== TESTING ====================

if __name__ == "__main__":
    import os
    
    # Test image
    input_image = "pixelart_output/kwonyuri_heart1/pixelart_kwonyuri_heart1_final1.png"
    
    if not os.path.exists(input_image):
        print(f"Error: Image not found: {input_image}")
        exit(1)
    
    os.makedirs("ascii_output", exist_ok=True)
    
    print("\n" + "="*70)
    print("ASCII CONVERTER - C Implementation in Python")
    print("="*70)
    
    # Test configurations
    configs = [
        {
            'name': 'standard',
            'width': 120,
            'height': 60,
            'edge_threshold': 2.5,
            'font_size': 6,
            'retro': False
        },
        {
            'name': 'high_detail',
            'width': 160,
            'height': 80,
            'edge_threshold': 2.0,
            'font_size': 5,
            'retro': False
        },
        {
            'name': 'retro',
            'width': 120,
            'height': 60,
            'edge_threshold': 2.5,
            'font_size': 6,
            'retro': True
        }
    ]
    
    for config in configs:
        print(f"\n{'='*70}")
        print(f"Configuration: {config['name']}")
        print(f"{'='*70}")
        
        # Convert to ASCII with character_ratio=1.0 for image rendering
        ascii_art, w, h = image_to_ascii(
            input_image,
            max_width=config['width'],
            max_height=config['height'],
            edge_threshold=config['edge_threshold'],
            character_ratio=1.0,  # Use 1.0 for image rendering!
            use_retro_colors=config['retro']
        )
        
        # Save text file
        txt_path = f"ascii_output/{config['name']}.txt"
        save_ascii_to_file(ascii_art, txt_path)
        
        # Render to image
        img_path = f"ascii_output/{config['name']}.png"
        render_ascii_to_image(ascii_art, img_path, font_size=config['font_size'])
    
    print("\n" + "="*70)
    print("✓ All conversions complete! Check ascii_output/ folder")
    print("="*70)