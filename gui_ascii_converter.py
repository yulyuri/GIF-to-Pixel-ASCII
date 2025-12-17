"""
ASCII Art Converter GUI
Batch convert frames to ASCII art with real-time preview
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import threading
from pathlib import Path
import glob

# Import our ASCII converter
from asciiart_converter import image_to_ascii, render_ascii_to_image

class ASCIIConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCII Art Converter")
        self.root.geometry("1000x800")
        
        # Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar(value="ascii_frames")
        self.max_width = tk.IntVar(value=120)
        self.max_height = tk.IntVar(value=200)
        self.edge_threshold = tk.DoubleVar(value=2.5)
        self.character_ratio = tk.DoubleVar(value=1.33)
        self.font_size = tk.IntVar(value=6)
        self.use_retro = tk.BooleanVar(value=False)
        
        self.processing = False
        self.preview_image = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # ===== INPUT/OUTPUT SECTION =====
        ttk.Label(main_frame, text="📁 Folders", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Input folder
        ttk.Label(main_frame, text="Input Folder:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_folder, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_input).grid(
            row=row, column=2, padx=5)
        row += 1
        
        # Output folder
        ttk.Label(main_frame, text="Output Folder:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_folder, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(
            row=row, column=2, padx=5)
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # ===== PARAMETERS SECTION =====
        ttk.Label(main_frame, text="🎨 Parameters", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Max Width
        ttk.Label(main_frame, text="Max Width (characters):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        width_slider = ttk.Scale(main_frame, from_=40, to=240, variable=self.max_width,
                                 orient='horizontal', command=self.update_width_label)
        width_slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        self.width_label = ttk.Label(main_frame, text=f"{self.max_width.get()}")
        self.width_label.grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        # Max Height
        ttk.Label(main_frame, text="Max Height (characters):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        height_slider = ttk.Scale(main_frame, from_=40, to=300, variable=self.max_height,
                                  orient='horizontal', command=self.update_height_label)
        height_slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        self.height_label = ttk.Label(main_frame, text=f"{self.max_height.get()}")
        self.height_label.grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        # Edge Threshold
        ttk.Label(main_frame, text="Edge Threshold (0.5-4.0):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        edge_slider = ttk.Scale(main_frame, from_=0.5, to=4.0, variable=self.edge_threshold,
                                orient='horizontal', command=self.update_edge_label)
        edge_slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        self.edge_label = ttk.Label(main_frame, text=f"{self.edge_threshold.get():.1f}")
        self.edge_label.grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(main_frame, text="   (Lower = more edges, 4.0 = disabled)",
                  font=('Arial', 8), foreground='gray').grid(
            row=row, column=1, sticky=tk.W, pady=(0, 5))
        row += 1
        
        # Character Ratio
        ttk.Label(main_frame, text="Character Ratio:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        ratio_slider = ttk.Scale(main_frame, from_=1.0, to=2.0, variable=self.character_ratio,
                                 orient='horizontal', command=self.update_ratio_label)
        ratio_slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        self.ratio_label = ttk.Label(main_frame, text=f"{self.character_ratio.get():.2f}")
        self.ratio_label.grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        ttk.Label(main_frame, text="   (1.33 = correct aspect, 2.0 = terminal display)",
                  font=('Arial', 8), foreground='gray').grid(
            row=row, column=1, sticky=tk.W, pady=(0, 5))
        row += 1
        
        # Font Size
        ttk.Label(main_frame, text="Font Size (pixels):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        font_slider = ttk.Scale(main_frame, from_=3, to=12, variable=self.font_size,
                                orient='horizontal', command=self.update_font_label)
        font_slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        self.font_label = ttk.Label(main_frame, text=f"{self.font_size.get()}")
        self.font_label.grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        # Retro Colors
        ttk.Checkbutton(main_frame, text="🕹️ Use Retro Colors (8-color palette)",
                        variable=self.use_retro).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # ===== PREVIEW SECTION =====
        ttk.Label(main_frame, text="👁️ Preview", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Preview buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="🔍 Preview First Frame",
                   command=self.preview_first).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🎬 Convert All Frames",
                   command=self.convert_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🎞️ Create Animated GIF",
                   command=self.create_gif_preview).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(main_frame, bg='black', width=600, height=400)
        self.preview_canvas.grid(row=row, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.rowconfigure(row, weight=1)
        row += 1
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
    
    # ===== LABEL UPDATES =====
    
    def update_width_label(self, value):
        self.width_label.config(text=f"{int(float(value))}")
    
    def update_height_label(self, value):
        self.height_label.config(text=f"{int(float(value))}")
    
    def update_edge_label(self, value):
        self.edge_label.config(text=f"{float(value):.1f}")
    
    def update_ratio_label(self, value):
        self.ratio_label.config(text=f"{float(value):.2f}")
    
    def update_font_label(self, value):
        self.font_label.config(text=f"{int(float(value))}")
    
    # ===== BROWSE FUNCTIONS =====
    
    def browse_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder with Frames")
        if folder:
            self.input_folder.set(folder)
            self.update_status(f"Input folder: {folder}")
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
    
    # ===== PROCESSING FUNCTIONS =====
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def get_frame_files(self):
        """Get all image files from input folder"""
        if not self.input_folder.get():
            messagebox.showerror("Error", "Please select an input folder!")
            return []
        
        folder = self.input_folder.get()
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(folder, ext)))
        
        files.sort()  # Sort by name
        return files
    
    def preview_first(self):
        """Preview the first frame with current settings"""
        files = self.get_frame_files()
        if not files:
            messagebox.showwarning("No Frames", "No image files found in input folder!")
            return
        
        self.update_status("Generating preview...")
        
        # Process first frame
        first_frame = files[0]
        
        def process():
            try:
                # Convert to ASCII
                ascii_art, w, h = image_to_ascii(
                    first_frame,
                    max_width=self.max_width.get(),
                    max_height=self.max_height.get(),
                    edge_threshold=self.edge_threshold.get(),
                    character_ratio=self.character_ratio.get(),
                    use_retro_colors=self.use_retro.get()
                )
                
                # Render to image
                temp_path = "/tmp/ascii_preview.png"
                render_ascii_to_image(ascii_art, temp_path, font_size=self.font_size.get())
                
                # Display in canvas
                self.display_preview(temp_path)
                self.update_status(f"Preview: {os.path.basename(first_frame)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Preview failed: {str(e)}")
                self.update_status("Preview failed")
        
        # Run in thread
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def display_preview(self, image_path):
        """Display image in preview canvas"""
        try:
            img = Image.open(image_path)
            
            # Resize to fit canvas
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 600, 400
            
            img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.preview_image = ImageTk.PhotoImage(img)
            
            # Display on canvas
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.preview_image, anchor=tk.CENTER
            )
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def convert_all(self):
        """Convert all frames"""
        files = self.get_frame_files()
        if not files:
            messagebox.showwarning("No Frames", "No image files found in input folder!")
            return
        
        if self.processing:
            messagebox.showwarning("Busy", "Already processing!")
            return
        
        # Create output folder
        output_dir = self.output_folder.get()
        os.makedirs(output_dir, exist_ok=True)
        
        self.processing = True
        self.progress['maximum'] = len(files)
        self.progress['value'] = 0
        
        def process():
            try:
                for i, frame_path in enumerate(files):
                    self.update_status(f"Processing {i+1}/{len(files)}: {os.path.basename(frame_path)}")
                    
                    # Convert to ASCII
                    ascii_art, w, h = image_to_ascii(
                        frame_path,
                        max_width=self.max_width.get(),
                        max_height=self.max_height.get(),
                        edge_threshold=self.edge_threshold.get(),
                        character_ratio=self.character_ratio.get(),
                        use_retro_colors=self.use_retro.get()
                    )
                    
                    # Generate output filename
                    base_name = os.path.splitext(os.path.basename(frame_path))[0]
                    output_path = os.path.join(output_dir, f"{base_name}_ascii.png")
                    
                    # Render to image
                    render_ascii_to_image(ascii_art, output_path, font_size=self.font_size.get())
                    
                    # Update progress
                    self.progress['value'] = i + 1
                    self.root.update_idletasks()
                
                self.update_status(f"✓ Complete! {len(files)} frames converted to {output_dir}")
                messagebox.showinfo("Success", f"Converted {len(files)} frames!\n\nOutput: {output_dir}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Conversion failed: {str(e)}")
                self.update_status("Conversion failed")
            
            finally:
                self.processing = False
                self.progress['value'] = 0
        
        # Run in thread
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def create_gif_preview(self):
        """Create animated GIF from converted frames"""
        output_dir = self.output_folder.get()
        
        if not os.path.exists(output_dir):
            messagebox.showwarning("No Output", "Please convert frames first!")
            return
        
        # Get converted frames
        frames = sorted(glob.glob(os.path.join(output_dir, "*_ascii.png")))
        
        if not frames:
            messagebox.showwarning("No Frames", "No converted frames found in output folder!")
            return
        
        self.update_status("Creating GIF...")
        
        def process():
            try:
                # Load all frames
                images = []
                for frame_path in frames:
                    img = Image.open(frame_path)
                    images.append(img)
                
                # Generate GIF name based on input folder
                input_folder_name = os.path.basename(self.input_folder.get().rstrip('/\\'))
                if not input_folder_name:
                    input_folder_name = "frames"
                
                gif_name = f"{input_folder_name}_ascii.gif"
                gif_path = os.path.join(output_dir, gif_name)
                
                # Save as GIF
                images[0].save(
                    gif_path,
                    save_all=True,
                    append_images=images[1:],
                    duration=100,  # 100ms per frame
                    loop=0
                )
                
                self.update_status(f"✓ GIF created: {gif_name}")
                messagebox.showinfo("Success", f"Animated GIF created!\n\n{gif_path}\n\n{len(images)} frames @ 10 FPS")
                
                # Display first frame
                self.display_preview(frames[0])
                
            except Exception as e:
                messagebox.showerror("Error", f"GIF creation failed: {str(e)}")
                self.update_status("GIF creation failed")
        
        # Run in thread
        thread = threading.Thread(target=process, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = ASCIIConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()