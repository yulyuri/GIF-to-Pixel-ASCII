import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
from PIL import Image, ImageTk
import os
import threading
from pathlib import Path

# Import our pixel art functions
from pixelart_converter import create_pixel_art

class ProcessingPopup:
    """Popup window for showing processing progress"""
    def __init__(self, parent, total_frames):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Processing Frames...")
        self.popup.geometry("450x180")
        self.popup.transient(parent)
        self.popup.grab_set()
        
        # Center the popup
        self.popup.update_idletasks()
        x = (self.popup.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.popup.winfo_screenheight() // 2) - (180 // 2)
        self.popup.geometry(f"450x180+{x}+{y}")
        
        # Content
        frame = ttk.Frame(self.popup, padding=20)
        frame.pack(fill="both", expand=True)
        
        self.status_label = ttk.Label(
            frame,
            text=f"Processing 0/{total_frames} frames...",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=10)
        
        self.progress = ttk.Progressbar(
            frame,
            mode="determinate",
            length=400,
            maximum=total_frames
        )
        self.progress.pack(pady=10)
        
        self.detail_label = ttk.Label(
            frame,
            text="Please wait...",
            foreground="gray"
        )
        self.detail_label.pack()
        
        self.total_frames = total_frames
        self.current_frame = 0
    
    def update_progress(self, current, filename):
        self.current_frame = current
        self.status_label.config(text=f"Processing {current}/{self.total_frames} frames...")
        self.detail_label.config(text=f"Current: {filename}")
        self.progress['value'] = current
        self.popup.update()
    
    def update_status(self, text):
        self.status_label.config(text=text)
    
    def close(self):
        self.popup.destroy()

class PixelArtGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixel Art Converter")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # State variables
        self.input_folder = None
        self.frame_files = []
        self.output_gif = None
        self.gif_frames = []
        self.current_frame_idx = 0
        self.animation_id = None
        
        # Apply theme
        sv_ttk.set_theme("dark")
        
        # Configure root
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.main_container.rowconfigure(0, weight=0)  # Title
        self.main_container.rowconfigure(1, weight=1)  # Content
        self.main_container.columnconfigure(0, weight=3)  # Left (preview)
        self.main_container.columnconfigure(1, weight=2)  # Right (controls)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI elements"""
        
        # ===== TITLE =====
        title_frame = ttk.Frame(self.main_container, padding=15)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        title_label = ttk.Label(
            title_frame,
            text="🎨 Pixel Art Converter",
            font=("Arial", 24, "bold")
        )
        title_label.pack()
        
        subtitle = ttk.Label(
            title_frame,
            text="Convert frames to pixel art • Batch processing • Animated GIF output",
            font=("Arial", 10)
        )
        subtitle.pack()
        
        # ===== LEFT: PREVIEW =====
        left_frame = ttk.Frame(self.main_container, padding=15)
        left_frame.grid(row=1, column=0, sticky="nsew")
        
        left_frame.rowconfigure(0, weight=0)  # Folder selection
        left_frame.rowconfigure(1, weight=1)  # Preview
        left_frame.columnconfigure(0, weight=1)
        
        # Folder selection
        folder_frame = ttk.LabelFrame(left_frame, text="Input Folder", padding=15)
        folder_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.folder_label = ttk.Label(
            folder_frame,
            text="No folder selected",
            foreground="gray"
        )
        self.folder_label.pack(pady=5)
        
        browse_btn = ttk.Button(
            folder_frame,
            text="📁 Select Frame Folder",
            command=self.select_folder
        )
        browse_btn.pack(pady=5)
        
        self.frame_count_label = ttk.Label(
            folder_frame,
            text="",
            font=("Arial", 10)
        )
        self.frame_count_label.pack()
        
        # Preview container
        preview_container = ttk.LabelFrame(left_frame, text="Output Preview", padding=10)
        preview_container.grid(row=1, column=0, sticky="nsew")
        
        preview_container.rowconfigure(0, weight=1)
        preview_container.columnconfigure(0, weight=1)
        
        self.preview_label = ttk.Label(
            preview_container,
            text="🎬\n\nProcessed GIF will appear here",
            font=("Arial", 16),
            foreground="gray",
            anchor="center"
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # ===== RIGHT: CONTROLS =====
        right_frame = ttk.Frame(self.main_container, padding=15)
        right_frame.grid(row=1, column=1, sticky="nsew")
        
        right_frame.columnconfigure(0, weight=1)
        
        # Scrollable frame for controls
        canvas = tk.Canvas(right_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        row = 0
        
        # --- Dimensions Section ---
        dim_section = ttk.LabelFrame(scrollable_frame, text="Output Dimensions", padding=15)
        dim_section.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1
        
        # Width
        ttk.Label(dim_section, text="Target Width:").grid(row=0, column=0, sticky="w", pady=5)
        self.width_var = tk.IntVar(value=128)
        width_slider = ttk.Scale(
            dim_section,
            from_=32,
            to=512,
            orient="horizontal",
            variable=self.width_var,
            command=self.update_width_label
        )
        width_slider.grid(row=1, column=0, sticky="ew", pady=5)
        self.width_label = ttk.Label(dim_section, text="128 px", font=("Arial", 10, "bold"))
        self.width_label.grid(row=2, column=0, pady=5)
        
        # Height
        ttk.Label(dim_section, text="Target Height:").grid(row=3, column=0, sticky="w", pady=(10, 5))
        self.height_var = tk.IntVar(value=64)
        height_slider = ttk.Scale(
            dim_section,
            from_=32,
            to=512,
            orient="horizontal",
            variable=self.height_var,
            command=self.update_height_label
        )
        height_slider.grid(row=4, column=0, sticky="ew", pady=5)
        self.height_label = ttk.Label(dim_section, text="64 px", font=("Arial", 10, "bold"))
        self.height_label.grid(row=5, column=0, pady=5)
        
        dim_section.columnconfigure(0, weight=1)
        
        # Quick presets
        preset_frame = ttk.Frame(dim_section)
        preset_frame.grid(row=6, column=0, pady=(10, 0))
        
        ttk.Label(preset_frame, text="Presets:", foreground="gray").pack(side="left", padx=(0, 10))
        ttk.Button(preset_frame, text="128×64", command=lambda: self.set_dimensions(128, 64)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="128×32", command=lambda: self.set_dimensions(128, 32)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="96×64", command=lambda: self.set_dimensions(96, 64)).pack(side="left", padx=2)
        
        # --- Color Section ---
        color_section = ttk.LabelFrame(scrollable_frame, text="Colors", padding=15)
        color_section.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1
        
        ttk.Label(color_section, text="Palette Size:").grid(row=0, column=0, sticky="w", pady=5)
        self.colors_var = tk.IntVar(value=16)
        colors_slider = ttk.Scale(
            color_section,
            from_=4,
            to=256,
            orient="horizontal",
            variable=self.colors_var,
            command=self.update_colors_label
        )
        colors_slider.grid(row=1, column=0, sticky="ew", pady=5)
        self.colors_label = ttk.Label(color_section, text="16 colors", font=("Arial", 10, "bold"))
        self.colors_label.grid(row=2, column=0, pady=5)
        
        color_section.columnconfigure(0, weight=1)
        
        # --- Downsample Method ---
        method_section = ttk.LabelFrame(scrollable_frame, text="Downsample Method", padding=15)
        method_section.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1
        
        self.method_var = tk.StringVar(value="nearest")
        methods = [
            ("Nearest (Blocky)", "nearest"),
            ("Bilinear (Smooth)", "bilinear"),
            ("Lanczos (High Quality)", "lanczos")
        ]
        
        for text, value in methods:
            ttk.Radiobutton(
                method_section,
                text=text,
                variable=self.method_var,
                value=value
            ).pack(anchor="w", pady=2)
        
        # --- Options Section ---
        options_section = ttk.LabelFrame(scrollable_frame, text="Options", padding=15)
        options_section.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1
        
        self.preserve_aspect_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_section,
            text="Preserve Aspect Ratio",
            variable=self.preserve_aspect_var
        ).pack(anchor="w", pady=5)
        
        self.ignore_bg_var = tk.BooleanVar(value=False)
        ignore_bg_check = ttk.Checkbutton(
            options_section,
            text="Ignore Background (experimental)",
            variable=self.ignore_bg_var,
            command=self.toggle_bg_threshold
        )
        ignore_bg_check.pack(anchor="w", pady=5)
        
        # Background threshold (initially disabled)
        self.bg_threshold_frame = ttk.Frame(options_section)
        self.bg_threshold_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Label(self.bg_threshold_frame, text="  Background Threshold:").pack(anchor="w")
        self.bg_threshold_var = tk.IntVar(value=30)
        self.bg_threshold_slider = ttk.Scale(
            self.bg_threshold_frame,
            from_=10,
            to=100,
            orient="horizontal",
            variable=self.bg_threshold_var,
            command=self.update_bg_threshold_label,
            state="disabled"
        )
        self.bg_threshold_slider.pack(fill="x", padx=(10, 0), pady=2)
        self.bg_threshold_label = ttk.Label(
            self.bg_threshold_frame,
            text="30",
            font=("Arial", 9),
            foreground="gray"
        )
        self.bg_threshold_label.pack(anchor="w", padx=(10, 0))
        
        # --- GIF Options ---
        gif_section = ttk.LabelFrame(scrollable_frame, text="GIF Output", padding=15)
        gif_section.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1
        
        ttk.Label(gif_section, text="Frame Duration (ms):").grid(row=0, column=0, sticky="w", pady=5)
        self.frame_duration_var = tk.IntVar(value=100)
        duration_slider = ttk.Scale(
            gif_section,
            from_=50,
            to=500,
            orient="horizontal",
            variable=self.frame_duration_var,
            command=self.update_duration_label
        )
        duration_slider.grid(row=1, column=0, sticky="ew", pady=5)
        self.duration_label = ttk.Label(gif_section, text="100 ms (10 fps)", font=("Arial", 10, "bold"))
        self.duration_label.grid(row=2, column=0, pady=5)
        
        gif_section.columnconfigure(0, weight=1)
        
        # --- Action Buttons ---
        button_section = ttk.Frame(scrollable_frame, padding=(0, 10))
        button_section.grid(row=row, column=0, sticky="ew")
        row += 1
        
        button_section.columnconfigure(0, weight=1)
        
        self.process_btn = ttk.Button(
            button_section,
            text="🚀 Process Frames",
            command=self.process_frames,
            state="disabled"
        )
        self.process_btn.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Button(
            button_section,
            text="📂 Open Output Folder",
            command=self.open_output_folder
        ).grid(row=1, column=0, sticky="ew", pady=5)
    
    def update_width_label(self, value):
        self.width_label.config(text=f"{int(float(value))} px")
    
    def update_height_label(self, value):
        self.height_label.config(text=f"{int(float(value))} px")
    
    def update_colors_label(self, value):
        colors = int(float(value))
        self.colors_label.config(text=f"{colors} colors")
    
    def update_bg_threshold_label(self, value):
        threshold = int(float(value))
        self.bg_threshold_label.config(text=str(threshold))
    
    def update_duration_label(self, value):
        duration = int(float(value))
        fps = 1000 / duration
        self.duration_label.config(text=f"{duration} ms ({fps:.1f} fps)")
    
    def set_dimensions(self, width, height):
        self.width_var.set(width)
        self.height_var.set(height)
        self.update_width_label(width)
        self.update_height_label(height)
    
    def toggle_bg_threshold(self):
        if self.ignore_bg_var.get():
            self.bg_threshold_slider.config(state="normal")
            self.bg_threshold_label.config(foreground="white")
        else:
            self.bg_threshold_slider.config(state="disabled")
            self.bg_threshold_label.config(foreground="gray")
    
    def select_folder(self):
        """Select folder containing frames"""
        folder = filedialog.askdirectory(
            title="Select folder with frames",
            initialdir="./frames"
        )
        
        if folder:
            self.input_folder = folder
            folder_name = os.path.basename(folder)
            
            # Find all image files
            self.frame_files = sorted([
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
            ])
            
            if not self.frame_files:
                messagebox.showwarning("No Frames", "No image files found in selected folder!")
                return
            
            # Update UI
            self.folder_label.config(
                text=f"📁 {folder_name}",
                foreground="white"
            )
            self.frame_count_label.config(
                text=f"✓ {len(self.frame_files)} frames found",
                foreground="lightgreen"
            )
            
            # Enable process button
            self.process_btn.config(state="normal")
    
    def process_frames(self):
        """Start batch processing"""
        if not self.frame_files:
            messagebox.showwarning("No Frames", "Please select a folder first!")
            return
        
        # Create popup
        popup = ProcessingPopup(self.root, len(self.frame_files))
        
        # Disable button
        self.process_btn.config(state="disabled")
        
        # Run in thread
        thread = threading.Thread(target=self.do_processing, args=(popup,))
        thread.daemon = True
        thread.start()
    
    def do_processing(self, popup):
        """Process all frames"""
        try:
            # Get parameters
            target_width = self.width_var.get()
            target_height = self.height_var.get()
            num_colors = self.colors_var.get()
            method = self.method_var.get()
            preserve_aspect = self.preserve_aspect_var.get()
            ignore_background = self.ignore_bg_var.get()
            bg_threshold = self.bg_threshold_var.get()
            frame_duration = self.frame_duration_var.get()
            
            # Create output folder
            folder_name = os.path.basename(self.input_folder)
            output_folder = os.path.join("pixelart_output", folder_name)
            os.makedirs(output_folder, exist_ok=True)
            
            # Process each frame
            output_files = []
            
            for idx, input_file in enumerate(self.frame_files, 1):
                filename = os.path.basename(input_file)
                output_file = os.path.join(output_folder, f"pixelart_{filename}")
                
                # Update popup
                self.root.after(0, popup.update_progress, idx, filename)
                
                # Process frame
                create_pixel_art(
                    input_file,
                    output_file,
                    target_width=target_width,
                    target_height=target_height,
                    num_colors=num_colors,
                    downsample_method=method,
                    preserve_aspect=preserve_aspect,
                    ignore_background=ignore_background,
                    bg_threshold=bg_threshold
                )
                
                output_files.append(output_file)
            
            # Create GIF
            self.root.after(0, popup.update_status, "Creating animated GIF...")
            
            gif_path = os.path.join(output_folder, f"{folder_name}_pixelart.gif")
            
            # Load all frames
            frames = [Image.open(f) for f in output_files]
            
            # Save as GIF
            frames[0].save(
                gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration,
                loop=0
            )
            
            self.output_gif = gif_path
            
            # Success
            self.root.after(0, self.processing_complete, popup, len(output_files), gif_path)
            
        except Exception as e:
            self.root.after(0, self.processing_error, popup, str(e))
    
    def processing_complete(self, popup, frame_count, gif_path):
        """Called when processing finishes"""
        popup.close()
        self.process_btn.config(state="normal")
        
        # Load and display GIF
        self.load_gif_preview(gif_path)
        
        messagebox.showinfo(
            "Success! 🎉",
            f"Processed {frame_count} frames!\n\n"
            f"Output: {os.path.basename(os.path.dirname(gif_path))}/\n"
            f"GIF: {os.path.basename(gif_path)}"
        )
    
    def processing_error(self, popup, error_msg):
        """Called when processing fails"""
        popup.close()
        self.process_btn.config(state="normal")
        messagebox.showerror("Error", f"Processing failed:\n{error_msg}")
    
    def load_gif_preview(self, gif_path):
        """Load and animate GIF preview"""
        try:
            # Stop previous animation
            if self.animation_id:
                self.root.after_cancel(self.animation_id)
            
            # Load GIF frames
            gif = Image.open(gif_path)
            self.gif_frames = []
            
            # Get preview size
            self.preview_label.update_idletasks()
            max_width = self.preview_label.winfo_width() - 40
            max_height = self.preview_label.winfo_height() - 40
            
            if max_width < 100:
                max_width = 600
            if max_height < 100:
                max_height = 600
            
            # Load all frames
            for frame in range(gif.n_frames):
                gif.seek(frame)
                frame_img = gif.copy().convert('RGBA')
                
                # Scale up for preview (pixel art looks better big!)
                scale = min(max_width // frame_img.width, max_height // frame_img.height)
                scale = max(scale, 1)  # At least 1x
                
                new_width = frame_img.width * scale
                new_height = frame_img.height * scale
                
                # Use NEAREST for crisp pixel art
                frame_img = frame_img.resize(
                    (new_width, new_height),
                    Image.Resampling.NEAREST
                )
                
                self.gif_frames.append(ImageTk.PhotoImage(frame_img))
            
            self.current_frame_idx = 0
            
            # Start animation
            self.animate_preview()
            
        except Exception as e:
            print(f"Error loading GIF preview: {e}")
    
    def animate_preview(self):
        """Animate the GIF preview"""
        if not self.gif_frames:
            return
        
        self.preview_label.config(
            image=self.gif_frames[self.current_frame_idx],
            text=""
        )
        
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.gif_frames)
        
        # Use frame duration from slider
        duration = self.frame_duration_var.get()
        self.animation_id = self.root.after(duration, self.animate_preview)
    
    def open_output_folder(self):
        """Open output folder"""
        output_dir = os.path.abspath("pixelart_output")
        if os.path.exists(output_dir):
            os.system(f'nautilus "{output_dir}" &')
        else:
            messagebox.showwarning("No Output", "No frames processed yet!")

# ===== MAIN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = PixelArtGUI(root)
    root.mainloop()