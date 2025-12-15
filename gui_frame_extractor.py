import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk, ImageSequence
import numpy as np
import os
import threading

from get_frames import calculate_similarity

class ProcessingPopup:
    """Popup window for showing processing progress"""
    def __init__(self, parent):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Processing...")
        self.popup.geometry("400x150")
        self.popup.transient(parent)
        self.popup.grab_set()
        
        # Center the popup
        self.popup.update_idletasks()
        x = (self.popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.popup.winfo_screenheight() // 2) - (150 // 2)
        self.popup.geometry(f"400x150+{x}+{y}")
        
        # Content
        frame = ttk.Frame(self.popup, padding=20)
        frame.pack(fill="both", expand=True)
        
        self.status_label = ttk.Label(
            frame,
            text="Extracting frames...",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=10)
        
        self.progress = ttk.Progressbar(
            frame,
            mode="indeterminate",
            length=350
        )
        self.progress.pack(pady=10)
        self.progress.start()
        
        self.detail_label = ttk.Label(
            frame,
            text="Please wait...",
            foreground="gray"
        )
        self.detail_label.pack()
    
    def update_status(self, text):
        self.status_label.config(text=text)
    
    def update_detail(self, text):
        self.detail_label.config(text=text)
    
    def close(self):
        self.progress.stop()
        self.popup.destroy()

class GIFFrameExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Frame Extractor")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)  # Minimum window size
        
        # State variables
        self.gif_path = None
        self.total_frames = 0
        self.gif_name = ""
        self.gif_frames = []
        self.current_frame_idx = 0
        self.animation_id = None
        
        # Apply theme
        sv_ttk.set_theme("dark")
        
        # Configure root to expand
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure main container grid
        self.main_container.rowconfigure(0, weight=0)  # Title row - fixed height
        self.main_container.rowconfigure(1, weight=1)  # Content row - expands
        self.main_container.columnconfigure(0, weight=3)  # Left column - 60%
        self.main_container.columnconfigure(1, weight=2)  # Right column - 40%
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI elements in responsive two-column layout"""
        
        # ===== TITLE (spans both columns) =====
        title_frame = ttk.Frame(self.main_container, padding=15)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        title_label = ttk.Label(
            title_frame,
            text="🎬 GIF Frame Extractor",
            font=("Arial", 24, "bold")
        )
        title_label.pack()
        
        subtitle = ttk.Label(
            title_frame,
            text="Drag & drop or browse for a GIF • Preview • Extract optimized frames",
            font=("Arial", 10)
        )
        subtitle.pack()
        
        # ===== LEFT COLUMN: GIF PREVIEW =====
        left_frame = ttk.Frame(self.main_container, padding=15)
        left_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure left frame to expand
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        
        # Preview container
        preview_container = ttk.LabelFrame(left_frame, text="GIF Preview", padding=10)
        preview_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure preview container to expand
        preview_container.rowconfigure(0, weight=1)  # Preview label expands
        preview_container.rowconfigure(1, weight=0)  # Button fixed
        preview_container.rowconfigure(2, weight=0)  # Info fixed
        preview_container.columnconfigure(0, weight=1)
        
        # Preview label - this is where GIF displays
        self.preview_label = ttk.Label(
            preview_container,
            text="📁\n\nDrag & Drop GIF here\nor\nClick Browse below",
            font=("Arial", 16),
            foreground="gray",
            anchor="center",
            justify="center"
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Browse button
        browse_btn = ttk.Button(
            preview_container,
            text="📁 Browse for GIF",
            command=self.select_file
        )
        browse_btn.grid(row=1, column=0, pady=10)
        
        # Frame info
        self.frame_info = ttk.Label(
            preview_container,
            text="",
            font=("Arial", 11, "bold")
        )
        self.frame_info.grid(row=2, column=0, pady=(5, 10))
        
        # Enable drag and drop
        self.preview_label.drop_target_register(DND_FILES)
        self.preview_label.dnd_bind('<<Drop>>', self.drop_file)
        
        # ===== RIGHT COLUMN: CONTROLS =====
        right_frame = ttk.Frame(self.main_container, padding=15)
        right_frame.grid(row=1, column=1, sticky="nsew")
        
        # Configure right frame
        right_frame.rowconfigure(0, weight=1)  # Target section
        right_frame.rowconfigure(1, weight=1)  # Threshold section
        right_frame.rowconfigure(2, weight=0)  # Buttons - fixed
        right_frame.columnconfigure(0, weight=1)
        
        # --- Target Frames Section ---
        target_section = ttk.LabelFrame(right_frame, text="Target Frame Count", padding=20)
        target_section.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        target_section.rowconfigure(0, weight=0)
        target_section.rowconfigure(1, weight=0)
        target_section.rowconfigure(2, weight=1)
        target_section.columnconfigure(0, weight=1)
        
        self.target_var = tk.IntVar(value=15)
        target_slider = ttk.Scale(
            target_section,
            from_=5,
            to=50,
            orient="horizontal",
            variable=self.target_var,
            command=self.update_target_label
        )
        target_slider.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.target_value_label = ttk.Label(
            target_section,
            text="15 frames",
            font=("Arial", 12, "bold")
        )
        self.target_value_label.grid(row=1, column=0, pady=(0, 15))
        
        target_rec = ttk.Label(
            target_section,
            text="💡 More frames = smoother animation\n💡 Fewer frames = faster processing",
            font=("Arial", 9),
            foreground="gray",
            justify="left"
        )
        target_rec.grid(row=2, column=0, sticky="nw")
        
        # --- Similarity Threshold Section ---
        threshold_section = ttk.LabelFrame(right_frame, text="Similarity Threshold", padding=20)
        threshold_section.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        threshold_section.rowconfigure(0, weight=0)
        threshold_section.rowconfigure(1, weight=0)
        threshold_section.rowconfigure(2, weight=1)
        threshold_section.columnconfigure(0, weight=1)
        
        self.threshold_var = tk.DoubleVar(value=0.95)
        threshold_slider = ttk.Scale(
            threshold_section,
            from_=0.80,
            to=0.999,
            orient="horizontal",
            variable=self.threshold_var,
            command=self.update_threshold_label
        )
        threshold_slider.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.threshold_value_label = ttk.Label(
            threshold_section,
            text="0.950 (balanced)",
            font=("Arial", 12, "bold")
        )
        self.threshold_value_label.grid(row=1, column=0, pady=(0, 15))
        
        threshold_rec = ttk.Label(
            threshold_section,
            text="💡 Simple cartoons: 0.970 - 0.999\n💡 Real-life/detailed: 0.900 - 0.950\n💡 Higher = stricter (fewer frames)",
            font=("Arial", 9),
            foreground="gray",
            justify="left"
        )
        threshold_rec.grid(row=2, column=0, sticky="nw")
        
        # --- Action Buttons ---
        button_section = ttk.Frame(right_frame, padding=(0, 10))
        button_section.grid(row=2, column=0, sticky="sew")
        
        button_section.columnconfigure(0, weight=1)
        
        self.extract_btn = ttk.Button(
            button_section,
            text="🚀 Extract Frames",
            command=self.extract_frames,
            state="disabled"
        )
        self.extract_btn.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        open_folder_btn = ttk.Button(
            button_section,
            text="📂 Open Output Folder",
            command=self.open_output_folder
        )
        open_folder_btn.grid(row=1, column=0, sticky="ew")
    
    def update_target_label(self, value):
        """Update target frames label"""
        self.target_value_label.config(text=f"{int(float(value))} frames")
    
    def update_threshold_label(self, value):
        """Update threshold label"""
        threshold = float(value)
        
        if threshold >= 0.97:
            hint = " (strict - for cartoons)"
        elif threshold <= 0.92:
            hint = " (lenient - for detailed)"
        else:
            hint = " (balanced)"
        
        self.threshold_value_label.config(text=f"{threshold:.3f}{hint}")
    
    def drop_file(self, event):
        """Handle drag and drop"""
        filepath = event.data.strip('{}')
        if filepath.lower().endswith('.gif'):
            self.load_gif(filepath)
        else:
            messagebox.showwarning("Invalid File", "Please drop a GIF file!")
    
    def select_file(self):
        """Browse for GIF file"""
        filepath = filedialog.askopenfilename(
            title="Select a GIF file",
            initialdir="./input_gifs",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
        )
        
        if filepath:
            self.load_gif(filepath)
    
    def load_gif(self, filepath):
        """Load and preview GIF with animation"""
        self.gif_path = filepath
        self.gif_name = os.path.splitext(os.path.basename(filepath))[0]
        
        try:
            # Stop previous animation
            if self.animation_id:
                self.root.after_cancel(self.animation_id)
            
            # Load all frames
            gif = Image.open(filepath)
            self.gif_frames = []
            
            # Get preview label size for proper scaling
            self.preview_label.update_idletasks()
            max_width = self.preview_label.winfo_width() - 40
            max_height = self.preview_label.winfo_height() - 40
            
            # Use reasonable defaults if window hasn't sized yet
            if max_width < 100:
                max_width = 600
            if max_height < 100:
                max_height = 600
            
            for frame in ImageSequence.Iterator(gif):
                # Resize to fit preview area
                frame = frame.copy().convert('RGBA')
                frame.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                self.gif_frames.append(ImageTk.PhotoImage(frame))
            
            self.total_frames = len(self.gif_frames)
            self.current_frame_idx = 0
            
            # Start animation
            self.animate_gif()
            
            # Update info
            self.frame_info.config(
                text=f"✓ {self.gif_name}.gif • {self.total_frames} frames",
                foreground="lightgreen"
            )
            
            # Enable extract button
            self.extract_btn.config(state="normal")
            
            # Suggest parameters
            if self.total_frames > 60:
                suggested = 15
            elif self.total_frames > 30:
                suggested = 12
            else:
                suggested = max(5, self.total_frames // 2)
            
            self.target_var.set(suggested)
            self.update_target_label(suggested)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load GIF:\n{str(e)}")
    
    def animate_gif(self):
        """Animate the GIF preview"""
        if not self.gif_frames:
            return
        
        # Show current frame
        self.preview_label.config(image=self.gif_frames[self.current_frame_idx], text="")
        
        # Move to next frame
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.gif_frames)
        
        # Schedule next frame (100ms = 10fps)
        self.animation_id = self.root.after(100, self.animate_gif)
    
    def extract_frames(self):
        """Start extraction with popup"""
        # Create processing popup
        popup = ProcessingPopup(self.root)
        
        # Disable extract button
        self.extract_btn.config(state="disabled")
        
        # Run extraction in thread
        thread = threading.Thread(target=self.do_extraction, args=(popup,))
        thread.daemon = True
        thread.start()
    
    def do_extraction(self, popup):
        """Extraction logic"""
        try:
            target_frames = self.target_var.get()
            min_similarity = self.threshold_var.get()
            
            # Update popup
            self.root.after(0, popup.update_detail, f"Target: {target_frames} frames, Threshold: {min_similarity:.3f}")
            
            # Create folders
            base_folder = os.path.join("frames", self.gif_name)
            original_folder = os.path.join(base_folder, "original")
            final_folder = os.path.join(base_folder, "final")
            
            os.makedirs(original_folder, exist_ok=True)
            os.makedirs(final_folder, exist_ok=True)
            
            with Image.open(self.gif_path) as im:
                # Save all frames
                all_frames = []
                frame_number = 0
                
                self.root.after(0, popup.update_status, "Saving original frames...")
                
                try:
                    while True:
                        current_frame = im.copy()
                        original_path = os.path.join(
                            original_folder,
                            f"{self.gif_name}_original{frame_number + 1}.png"
                        )
                        current_frame.save(original_path)
                        all_frames.append(current_frame)
                        frame_number += 1
                        im.seek(im.tell() + 1)
                except EOFError:
                    pass
                
                # Smart sampling
                self.root.after(0, popup.update_status, "Analyzing similarity...")
                
                total_frames = len(all_frames)
                interval = max(1, total_frames // target_frames)
                
                kept_frames = []
                last_kept_frame = None
                
                for i in range(0, total_frames, interval):
                    frame = all_frames[i]
                    
                    if last_kept_frame is None:
                        kept_frames.append(frame)
                        last_kept_frame = frame
                    else:
                        similarity = calculate_similarity(last_kept_frame, frame)
                        
                        if similarity < min_similarity:
                            kept_frames.append(frame)
                            last_kept_frame = frame
                
                # Always include last
                if len(kept_frames) == 0 or all_frames[-1] is not kept_frames[-1]:
                    kept_frames.append(all_frames[-1])
                
                # Save final frames
                self.root.after(0, popup.update_status, "Saving final frames...")
                
                for idx, frame in enumerate(kept_frames):
                    final_path = os.path.join(
                        final_folder,
                        f"{self.gif_name}_final{idx + 1}.png"
                    )
                    frame.save(final_path)
            
            # Success!
            self.root.after(0, self.extraction_complete, popup, len(kept_frames), total_frames)
            
        except Exception as e:
            self.root.after(0, self.extraction_error, popup, str(e))
    
    def extraction_complete(self, popup, final_count, total_count):
        """Called when extraction finishes"""
        popup.close()
        self.extract_btn.config(state="normal")
        
        messagebox.showinfo(
            "Success! 🎉",
            f"Extraction complete!\n\n"
            f"Original: {total_count} frames\n"
            f"Final: {final_count} frames\n"
            f"Reduction: {total_count/final_count:.1f}x\n\n"
            f"Frames saved to: frames/{self.gif_name}/"
        )
    
    def extraction_error(self, popup, error_msg):
        """Called when extraction fails"""
        popup.close()
        self.extract_btn.config(state="normal")
        messagebox.showerror("Error", f"Extraction failed:\n{error_msg}")
    
    def open_output_folder(self):
        """Open frames folder"""
        frames_dir = os.path.abspath("frames")
        if os.path.exists(frames_dir):
            os.system(f'nautilus "{frames_dir}" &')
        else:
            messagebox.showwarning("No Output", "No frames extracted yet!")

# ===== MAIN =====
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = GIFFrameExtractorGUI(root)
    root.mainloop()