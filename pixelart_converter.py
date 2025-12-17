from PIL import Image
import numpy as np
import os

# ==================== PART 1: DOWNSAMPLING ====================

def downsample_image(input_path, target_width, target_height, 
                     method='lanczos', preserve_aspect=True):
    """Downsample image to target dimensions."""
    img = Image.open(input_path)
    original_width, original_height = img.size
    
    resample_methods = {
        'nearest': Image.Resampling.NEAREST,
        'bilinear': Image.Resampling.BILINEAR,
        'lanczos': Image.Resampling.LANCZOS
    }
    resample = resample_methods.get(method, Image.Resampling.LANCZOS)
    
    if preserve_aspect:
        width_ratio = target_width / original_width
        height_ratio = target_height / original_height
        scale_ratio = min(width_ratio, height_ratio)
        
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        
        img_resized = img.resize((new_width, new_height), resample)
        canvas = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        canvas.paste(img_resized, (x_offset, y_offset))
        
        return canvas
    else:
        return img.resize((target_width, target_height), resample)


# ==================== PART 2: K-MEANS COLOR QUANTIZATION ====================

def kmeans_color_quantization(image, num_colors=16, max_iterations=50,
                               ignore_background=True, bg_threshold=30):
    """
    Reduce image colors using K-means clustering.
    
    This is EXACTLY the K-means algorithm you learned in Pattern Recognition!
    
    Parameters:
    -----------
    image : PIL.Image
        Input image (RGB)
    num_colors : int
        Number of colors in final palette (K in K-means)
    max_iterations : int
        Maximum iterations for K-means convergence
    ignore_background : bool
        If True, exclude dark pixels from quantization (fixes black background problem)
    bg_threshold : int
        Pixels with brightness < this are considered background (0-255)
    
    Returns:
    --------
    quantized_image : PIL.Image
        Image with reduced color palette
    palette : numpy.ndarray
        The K colors found (shape: [K, 3])
    """
    
    print(f"\n{'='*60}")
    print(f"K-MEANS COLOR QUANTIZATION: Reducing to {num_colors} colors")
    if ignore_background:
        print(f"Background filtering: ON (threshold={bg_threshold})")
    else:
        print(f"Background filtering: OFF")
    print(f"{'='*60}")
    image = image.convert('RGB')
    
    # STEP 1: Convert image to numpy array of pixels
    # ----------------------------------------------
    img_array = np.array(image, dtype=np.float32)
    height, width, channels = img_array.shape
    
    print(f"\nStep 1: Image loaded")
    print(f"  Size: {width}x{height} = {width*height:,} pixels")
    print(f"  Color space: RGB (3 channels)")
    
    # STEP 2: Reshape to 2D array of pixels
    # --------------------------------------
    pixels = img_array.reshape(-1, 3)
    num_pixels = pixels.shape[0]
    
    print(f"\nStep 2: Reshaped to pixel list")
    print(f"  Shape: ({num_pixels:,} pixels, 3 colors)")
    print(f"  Each pixel is a point in 3D RGB space")
    
    # STEP 2.5: Filter background pixels (NEW!)
    # ------------------------------------------
    if ignore_background:
        # Calculate brightness for each pixel (average of R, G, B)
        brightness = np.mean(pixels, axis=1)
        foreground_mask = brightness > bg_threshold
        foreground_pixels = pixels[foreground_mask]
        
        print(f"\nStep 2.5: Filtering background pixels")
        print(f"  Total pixels: {num_pixels:,}")
        print(f"  Background pixels (brightness < {bg_threshold}): {num_pixels - len(foreground_pixels):,} ({100*(num_pixels - len(foreground_pixels))/num_pixels:.1f}%)")
        print(f"  Foreground pixels: {len(foreground_pixels):,} ({100*len(foreground_pixels)/num_pixels:.1f}%)")
        
        # Safety check: make sure we have enough pixels
        if len(foreground_pixels) < num_colors:
            print(f"  ⚠ Warning: Only {len(foreground_pixels)} foreground pixels but {num_colors} colors requested!")
            print(f"  Using all pixels instead...")
            quantize_pixels = pixels
        else:
            quantize_pixels = foreground_pixels
    else:
        quantize_pixels = pixels
    
    num_quantize_pixels = len(quantize_pixels)
    
    # STEP 3: Initialize K cluster centers
    # -------------------------------------
    np.random.seed(42)  # For reproducibility
    random_indices = np.random.choice(num_quantize_pixels, num_colors, replace=False)
    cluster_centers = quantize_pixels[random_indices].copy()
    
    print(f"\nStep 3: Initialized {num_colors} cluster centers")
    print(f"  Centers picked from {'foreground' if ignore_background else 'all'} pixels")
    
    # STEP 4: K-means iteration
    # -------------------------
    print(f"\nStep 4: Running K-means iterations...")
    
    for iteration in range(max_iterations):
        # 4a. ASSIGNMENT STEP: Assign each pixel to nearest cluster center
        distances = np.zeros((num_quantize_pixels, num_colors))
        for k in range(num_colors):
            # Euclidean distance in RGB space
            diff = quantize_pixels - cluster_centers[k]
            distances[:, k] = np.sqrt(np.sum(diff ** 2, axis=1))
        
        # Find closest cluster for each pixel
        assignments = np.argmin(distances, axis=1)
        
        # 4b. UPDATE STEP: Move cluster centers to average of assigned pixels
        new_cluster_centers = np.zeros_like(cluster_centers)
        
        for k in range(num_colors):
            # Find all pixels assigned to cluster k
            mask = (assignments == k)
            
            if np.sum(mask) > 0:
                # New center = average of all pixels in this cluster
                new_cluster_centers[k] = np.mean(quantize_pixels[mask], axis=0)
            else:
                # Empty cluster - reinitialize randomly from foreground
                print(f"  ⚠ Cluster {k} empty at iteration {iteration}, reinitializing...")
                new_cluster_centers[k] = quantize_pixels[np.random.randint(num_quantize_pixels)]
        
        # 4c. CHECK CONVERGENCE: Did centers stop moving?
        center_shift = np.sum(np.abs(new_cluster_centers - cluster_centers))
        cluster_centers = new_cluster_centers
        
        if iteration % 10 == 0:
            print(f"  Iteration {iteration}: center shift = {center_shift:.2f}")
        
        # If centers barely moved, we've converged!
        if center_shift < 1.0:
            print(f"  ✓ Converged at iteration {iteration}")
            break
    
    # STEP 5: Create quantized image (apply to ALL pixels, including background)
    # ---------------------------------------------------------------------------
    print(f"\nStep 5: Creating quantized image...")
    print(f"  Applying palette to all {num_pixels:,} pixels (including background)...")
    
    # Map each pixel to its nearest cluster center (palette color)
    distances = np.zeros((num_pixels, num_colors))
    for k in range(num_colors):
        diff = pixels - cluster_centers[k]
        distances[:, k] = np.sqrt(np.sum(diff ** 2, axis=1))
    
    assignments = np.argmin(distances, axis=1)
    
    # Replace each pixel with its cluster center color
    quantized_pixels = cluster_centers[assignments]
    
    # Reshape back to image dimensions
    quantized_array = quantized_pixels.reshape(height, width, 3)
    
    # Convert back to uint8 (0-255 range)
    quantized_array = np.clip(quantized_array, 0, 255).astype(np.uint8)
    
    # Create PIL image
    quantized_image = Image.fromarray(quantized_array)
    
    print(f"  ✓ Quantization complete!")
    
    # Print unique palette (sort by brightness for readability)
    print(f"\nFinal palette ({num_colors} colors, sorted by brightness):")
    brightness_order = np.argsort(np.mean(cluster_centers, axis=1))
    for idx, k in enumerate(brightness_order):
        r, g, b = cluster_centers[k].astype(int)
        brightness = int(np.mean(cluster_centers[k]))
        print(f"  Color {idx+1:2d}: RGB({r:3d}, {g:3d}, {b:3d}) - brightness: {brightness}")
    
    return quantized_image, cluster_centers.astype(np.uint8)


# ==================== PART 3: FULL PIPELINE ====================

def create_pixel_art(input_path, output_path, 
                     target_width=128, target_height=64,
                     num_colors=16, 
                     downsample_method='lanczos',
                     preserve_aspect=True,
                     ignore_background=True,
                     bg_threshold=30):
    """
    Full pipeline: Downsample → Color Quantization → Pixel Art!
    
    This is the complete signal processing pipeline:
    1. Spatial downsampling (reduce resolution)
    2. Color quantization (reduce color space)
    
    Parameters:
    -----------
    input_path : str
        Path to input image
    output_path : str
        Path to save output
    target_width : int
        Target width in pixels
    target_height : int
        Target height in pixels
    num_colors : int
        Number of colors in palette (2-256)
    downsample_method : str
        'nearest', 'bilinear', or 'lanczos'
    preserve_aspect : bool
        Maintain aspect ratio (adds black bars if needed)
    ignore_background : bool
        Filter out dark background pixels from quantization
    bg_threshold : int
        Brightness threshold for background filtering (0-255)
    """
    
    print(f"\n{'='*60}")
    print(f"PIXEL ART CREATION PIPELINE")
    print(f"{'='*60}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Target size: {target_width}x{target_height}")
    print(f"Colors: {num_colors}")
    print(f"Downsample method: {downsample_method}")
    print(f"Preserve aspect: {preserve_aspect}")
    
    # Step 1: Downsample
    print(f"\n{'='*60}")
    print(f"PHASE 1: DOWNSAMPLING")
    print(f"{'='*60}")
    downsampled = downsample_image(
        input_path, 
        target_width, 
        target_height,
        method=downsample_method,
        preserve_aspect=preserve_aspect
    )
    
    # Step 2: Color Quantization
    print(f"\n{'='*60}")
    print(f"PHASE 2: COLOR QUANTIZATION")
    print(f"{'='*60}")
    pixel_art, palette = kmeans_color_quantization(
        downsampled, 
        num_colors,
        ignore_background=ignore_background,
        bg_threshold=bg_threshold
    )
    
    # Save result
    pixel_art.save(output_path)
    print(f"\n{'='*60}")
    print(f"✓ COMPLETE! Saved to: {output_path}")
    print(f"{'='*60}\n")
    
    return pixel_art, palette


# ==================== TESTING ====================

if __name__ == "__main__":
    # Test with your extracted frames
    input_image = "frames/kwonyuri_heart1/final/kwonyuri_heart1_final1.png"
    os.makedirs("pixelart_output", exist_ok=True)
    
    print("\n" + "="*70)
    print("TESTING PIXEL ART CONVERTER")
    print("="*70)
    
    # Test 1: Different color counts with background filtering
    print("\nTest 1: Comparing different color counts (with background filtering)")
    print("-" * 70)
    color_counts = [8, 16, 32]
    
    for num_colors in color_counts:
        output_path = f"pixelart_output/test_{num_colors}colors_filtered.png"
        
        pixel_art, palette = create_pixel_art(
            input_image,
            output_path,
            target_width=128,
            target_height=64,
            num_colors=num_colors,
            downsample_method='nearest',
            preserve_aspect=False,  # No letterboxing for concert photos
            ignore_background=True,  # Filter dark background
            bg_threshold=40  # Adjust based on your image
        )
    
    # Test 2: Different background thresholds (for tuning)
    print("\n" + "="*70)
    print("\nTest 2: Comparing different background thresholds")
    print("-" * 70)
    thresholds = [20, 40, 60]
    
    for threshold in thresholds:
        output_path = f"pixelart_output/test_16colors_threshold{threshold}.png"
        
        pixel_art, palette = create_pixel_art(
            input_image,
            output_path,
            target_width=128,
            target_height=64,
            num_colors=16,
            downsample_method='nearest',
            preserve_aspect=False,
            ignore_background=True,
            bg_threshold=threshold
        )
    
    # Test 3: With vs without background filtering (comparison)
    print("\n" + "="*70)
    print("\nTest 3: With vs Without background filtering")
    print("-" * 70)
    
    # Without filtering
    pixel_art_no_filter, _ = create_pixel_art(
        input_image,
        "pixelart_output/test_16colors_NO_FILTER.png",
        target_width=128,
        target_height=64,
        num_colors=16,
        downsample_method='nearest',
        preserve_aspect=False,
        ignore_background=False  # No filtering
    )
    
    # With filtering
    pixel_art_with_filter, _ = create_pixel_art(
        input_image,
        "pixelart_output/test_16colors_WITH_FILTER.png",
        target_width=128,
        target_height=64,
        num_colors=16,
        downsample_method='nearest',
        preserve_aspect=False,
        ignore_background=True,  # With filtering
        bg_threshold=40
    )
    
    print("\n" + "="*70)
    print("✓ All tests complete! Check pixelart_output/ folder")
    print("  - Compare filtered vs non-filtered versions")
    print("  - Check which threshold works best for your image")
    print("  - Adjust bg_threshold in your code as needed")
    print("="*70)