from PIL import Image 
import numpy as np
import os
import sys

def calculate_similarity(frame1, frame2):
    """Calculate similarity (0-1, higher = more similar)"""
    small1 = frame1.resize((32, 32)).convert('RGB')
    small2 = frame2.resize((32, 32)).convert('RGB')
    
    arr1 = np.array(small1).astype(float)
    arr2 = np.array(small2).astype(float)
    
    diff = np.abs(arr1 - arr2).mean()
    similarity = 1 - (diff / 255)
    
    return similarity

def analyze_gif(gif_path):
    """First pass: analyze the GIF and show stats"""
    print(f"\n{'='*50}")
    print("ANALYZING GIF...")
    print(f"{'='*50}")
    
    with Image.open(gif_path) as im:
        frame_count = 0
        try:
            while True:
                im.seek(frame_count)
                frame_count += 1
        except EOFError:
            pass
    
    print(f"Total frames: {frame_count}")
    
    # Suggest parameters based on frame count
    if frame_count > 60:
        suggested_target = 15
    elif frame_count > 30:
        suggested_target = 12
    else:
        suggested_target = max(5, frame_count // 2)
    
    print(f"Suggested target frames: {suggested_target}")
    print(f"\nThreshold recommendations:")
    print(f"  • Simple cartoons: 0.97 - 0.99")
    print(f"  • Real-life/detailed: 0.90 - 0.95")
    print(f"{'='*50}\n")
    
    return frame_count

def extract_frames_smart(gif_path, target_frames, min_similarity):
    """Extract frames with given parameters"""
    gif_filename = os.path.basename(gif_path)
    gif_name = os.path.splitext(gif_filename)[0]
    
    # Create folder structure
    base_folder = os.path.join("frames", gif_name)
    original_folder = os.path.join(base_folder, "original")
    final_folder = os.path.join(base_folder, "final")
    
    os.makedirs(original_folder, exist_ok=True)
    os.makedirs(final_folder, exist_ok=True)
    
    print(f"\n{'='*50}")
    print(f"PROCESSING: {gif_filename}")
    print(f"Target frames: {target_frames}")
    print(f"Similarity threshold: {min_similarity}")
    print(f"{'='*50}\n")
    
    with Image.open(gif_path) as im:
        # First pass: save all original frames
        all_frames = []
        frame_number = 0
        
        try:
            while True:
                current_frame = im.copy()
                original_path = os.path.join(original_folder, f"{gif_name}_original{frame_number + 1}.png")
                current_frame.save(original_path)
                all_frames.append(current_frame)
                frame_number += 1
                im.seek(im.tell() + 1)
        except EOFError:
            pass
        
        total_frames = len(all_frames)
        interval = max(1, total_frames // target_frames)
        
        print(f"Sampling every ~{interval} frames\n")
        
        # Second pass: smart sampling
        kept_frames = []
        last_kept_frame = None
        
        for i in range(0, total_frames, interval):
            frame = all_frames[i]
            
            if last_kept_frame is None:
                kept_frames.append((i, frame))
                last_kept_frame = frame
                print(f"✓ Frame {i + 1:3d} → final{len(kept_frames):2d} (FIRST)")
            else:
                similarity = calculate_similarity(last_kept_frame, frame)
                
                if similarity < min_similarity:
                    kept_frames.append((i, frame))
                    last_kept_frame = frame
                    print(f"✓ Frame {i + 1:3d} → final{len(kept_frames):2d} (sim: {similarity:.3f})")
                else:
                    print(f"✗ Frame {i + 1:3d} skipped (sim: {similarity:.3f})")
        
        # Always include last frame
        if kept_frames[-1][0] != total_frames - 1:
            last_frame = all_frames[-1]
            similarity = calculate_similarity(kept_frames[-1][1], last_frame)
            kept_frames.append((total_frames - 1, last_frame))
            print(f"✓ Frame {total_frames:3d} → final{len(kept_frames):2d} (LAST, sim: {similarity:.3f})")
        
        # Save final frames
        print(f"\n{'='*50}")
        for idx, (original_idx, frame) in enumerate(kept_frames):
            final_path = os.path.join(final_folder, f"{gif_name}_final{idx + 1}.png")
            frame.save(final_path)
        
        print(f"✓ Original: {total_frames} frames → {original_folder}/")
        print(f"✓ Final: {len(kept_frames)} frames → {final_folder}/")
        print(f"✓ Reduction: {total_frames / len(kept_frames):.1f}x")
        print(f"{'='*50}\n")
        
        return len(kept_frames)
if __name__ == "__main__":
        
    # Main script
    if len(sys.argv) < 2:
        print("\nUsage: python get_frames.py <gif_filename>")
        print("Example: python get_frames.py cactusbubble.gif\n")
        sys.exit(1)

    gif_filename = sys.argv[1]
    gif_path = os.path.join("input_gifs", gif_filename)

    if not os.path.exists(gif_path):
        print(f"\n❌ Error: {gif_path} not found!\n")
        sys.exit(1)

    # Step 1: Analyze
    total_frames = analyze_gif(gif_path)

    # Step 2: Get user input
    try:
        target_frames = int(input("How many frames do you want? (press Enter for default): ") or 15)
        threshold_input = input("Similarity threshold (0.90-0.99, press Enter for 0.95): ") or "0.95"
        min_similarity = float(threshold_input)
        
        if not (0.0 <= min_similarity <= 1.0):
            print("❌ Threshold must be between 0 and 1")
            sys.exit(1)
            
    except ValueError:
        print("❌ Invalid input")
        sys.exit(1)

    # Step 3: Extract
    final_count = extract_frames_smart(gif_path, target_frames, min_similarity)

    print("🎉 Done! Check your frames folder.")
    print(f"💡 Tip: If you got {final_count} frames but wanted more/less,")
    print(f"   try adjusting threshold (current: {min_similarity})")