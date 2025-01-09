import threading  # For running the serial reader in a separate thread
import tkinter as tk
from tkinter import filedialog, simpledialog
import serial  # Newly added for serial communication
from PIL import Image, ImageTk
from PIL.PngImagePlugin import PngInfo


class BuildingLayoutApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Beacon Layout Visualizer")
        self.root.attributes("-fullscreen", True)

        # Initialize variables
        self.image = None
        self.canvas = None
        self.canvas_image = None
        self.cells = []
        self.beacon_cells = []
        self.beacon_data = {}  # To store beacon IDs and coordinates
        self.grid_size = 0.5  # Default grid size

        # Create UI elements
        self.create_ui()

        # Serial reader will be initiated by the user via the "Start Serial Reader" button

        # Beacon simulation functionality
        self.beacon_circles = {}  # Dictionary to track visualized distances

    def create_ui(self):
        self.canvas = tk.Canvas(self.root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True, anchor=tk.N)

        self.canvas.bind("<Button-1>", self.select_cell)

        self.upload_button = tk.Button(
            self.root, text="Upload Image", command=self.upload_image
        )
        self.upload_button.pack()

        self.export_button = tk.Button(
            self.root, text="Export Image", command=self.export_image_with_metadata
        )
        self.export_button.pack()

        self.close_button = tk.Button(
            self.root, text="Close", command=self.root.destroy
        )
        self.close_button.pack()

        dimensions_frame = tk.Frame(self.root)
        dimensions_frame.pack()

        tk.Label(dimensions_frame, text="Width (m):").grid(row=0, column=0)
        self.width_entry = tk.Entry(dimensions_frame, width=5)
        self.width_entry.grid(row=0, column=1)

        tk.Label(dimensions_frame, text="Height (m):").grid(row=0, column=2)
        self.height_entry = tk.Entry(dimensions_frame, width=5)
        self.height_entry.grid(row=0, column=3)

        grid_size_frame = tk.Frame(self.root)
        grid_size_frame.pack()

        tk.Label(grid_size_frame, text="Grid Size (m):").grid(row=0, column=0)
        self.grid_size_entry = tk.Entry(grid_size_frame, width=5)
        self.grid_size_entry.insert(0, "0.5")  # Default value
        self.grid_size_entry.grid(row=0, column=1)

        self.generate_grid_button = tk.Button(
            self.root, text="Generate Grid", command=self.generate_grid
        )
        self.generate_grid_button.pack()

        # Serial port configuration inputs
        serial_frame = tk.Frame(self.root)
        serial_frame.pack()

        tk.Label(serial_frame, text="COM Port:").grid(row=0, column=0)
        self.com_port_entry = tk.Entry(serial_frame, width=10)
        self.com_port_entry.insert(0, "COM3")  # Default COM port
        self.com_port_entry.grid(row=0, column=1)

        tk.Label(serial_frame, text="Baud Rate:").grid(row=0, column=2)
        self.baud_rate_entry = tk.Entry(serial_frame, width=10)
        self.baud_rate_entry.insert(0, "115200")  # Default baud rate
        self.baud_rate_entry.grid(row=0, column=3)

        self.start_serial_button = tk.Button(
            serial_frame, text="Start Serial Reader", command=self.start_serial_reader
        )
        self.start_serial_button.grid(row=0, column=4)

        # Input for beacon simulation
        beacon_simulation_frame = tk.Frame(self.root)
        beacon_simulation_frame.pack()

        tk.Label(beacon_simulation_frame, text="Beacon ID:").grid(row=0, column=0)
        self.beacon_id_entry = tk.Entry(beacon_simulation_frame, width=10)
        self.beacon_id_entry.grid(row=0, column=1)

        tk.Label(beacon_simulation_frame, text="Distance (m):").grid(row=0, column=2)
        self.distance_entry = tk.Entry(beacon_simulation_frame, width=10)
        self.distance_entry.grid(row=0, column=3)

        self.simulate_button = tk.Button(
            beacon_simulation_frame,
            text="Simulate",
            command=self.simulate_beacon_distance,
        )
        self.simulate_button.grid(row=0, column=4)

        # Listbox for active beacons and distances
        self.beacon_listbox = tk.Listbox(self.root, height=10, width=50)
        self.beacon_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    def upload_image(self):
        """Upload and display an image on the canvas while resizing canvas to fit the image."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
        )
        if not file_path:
            print("No file selected.")
            return
        try:
            uploaded_img = Image.open(file_path)

            # Get screen dimensions
            screen_height = self.root.winfo_screenheight()

            # Limit image height to half of the screen
            max_height = screen_height // 2
            img_width, img_height = uploaded_img.size
            if img_height > max_height:
                aspect_ratio = img_width / img_height
                img_height = max_height
                img_width = int(max_height * aspect_ratio)
                uploaded_img = uploaded_img.resize(
                    (img_width, img_height), Image.Resampling.LANCZOS
                )

            self.image = uploaded_img

            # Adjust canvas size to fit the image
            self.canvas.config(width=img_width, height=img_height)

            self.canvas_image = ImageTk.PhotoImage(uploaded_img)

            # Calculate horizontal offset to center the image if necessary
            offset_x = max((self.canvas.winfo_width() - img_width) // 2, 0)
            self.image_offset_x = offset_x  # Store the horizontal offset
            self.image_offset_y = 0  # Vertical offset is always 0
            self.canvas.create_image(
                self.image_offset_x,
                self.image_offset_y,
                anchor=tk.NW,
                image=self.canvas_image,
            )
            print(f"Image uploaded successfully: {file_path}")

            # Check for all metadata and dynamically apply settings
            metadata = {}
            for key, value in uploaded_img.info.items():
                try:
                    # Decode metadata bytes, if applicable
                    decoded_value = (
                        value.decode("utf-8") if isinstance(value, bytes) else value
                    )
                    metadata[key] = decoded_value
                except Exception:
                    print(f"Failed to decode metadata key {key}: {value}")
            if metadata:
                self.apply_metadata(metadata)
            else:
                print("No metadata found in the image.")
        except Exception as e:
            print(f"Error uploading image: {e}")

    def export_image_with_metadata(self):
        """Save the canvas as an image with metadata."""
        if self.image is None:
            print("No image available to export.")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png", filetypes=[("PNG files", "*.png")]
            )
            if not file_path:
                return

            # Create a copy of the existing image
            export_image = self.image.copy()

            # Embed metadata into image (as a dictionary)
            metadata = {
                "width": self.width_entry.get(),
                "height": self.height_entry.get(),
                "grid_size": self.grid_size_entry.get(),
                "beacons": self.beacon_data,
            }

            # Save the image as PNG with metadata
            export_image.save(
                file_path, "PNG", pnginfo=self.create_png_metadata(metadata)
            )
            print(f"Image exported successfully with metadata to {file_path}.")
        except Exception as e:
            print(f"Error during export: {e}")

    def create_png_metadata(self, metadata):
        """Create a PNGInfo object with metadata."""

        png_metadata = PngInfo()
        for key, value in metadata.items():
            png_metadata.add_text(key, str(value))
        return png_metadata

    def apply_metadata(self, metadata):
        """Apply metadata settings to the visualizer."""
        try:
            # Apply known keys dynamically where applicable
            if "width" in metadata:
                self.width_entry.delete(0, tk.END)
                self.width_entry.insert(0, metadata["width"])
            if "height" in metadata:
                self.height_entry.delete(0, tk.END)
                self.height_entry.insert(0, metadata["height"])
            if "grid_size" in metadata:
                self.grid_size_entry.delete(0, tk.END)
                self.grid_size_entry.insert(0, metadata["grid_size"])
                self.generate_grid()

            if "beacons" in metadata:
                self.beacon_data = (
                    eval(metadata["beacons"])
                    if isinstance(metadata["beacons"], str)
                    else metadata["beacons"]
                )
                self.beacon_cells = []
                for beacon_id, (row, col) in self.beacon_data.items():
                    self.cells[row][col]["beacon"] = True
                    self.canvas.itemconfig(self.cells[row][col]["rect"], fill="red")

            # Log unused metadata keys
            for key in metadata.keys():
                if key not in ["width", "height", "grid_size", "beacons"]:
                    print(
                        f"Unused metadata key detected: {key}. Consider adding support for it."
                    )
        except Exception as e:
            print(f"Error applying metadata: {e}")

    def start_serial_reader(self):
        """Starts a thread to continuously read data from a serial device."""
        com_port = self.com_port_entry.get().strip()
        baud_rate = self.baud_rate_entry.get().strip()
        try:
            if not com_port or not baud_rate.isdigit():
                raise ValueError(
                    "Invalid COM port or baud rate. Please enter valid inputs."
                )

            baud_rate = int(baud_rate)

            def read_from_serial():
                while True:
                    try:
                        # Initialize serial port
                        with serial.Serial(com_port, baud_rate, timeout=1) as ser:
                            while ser.is_open:
                                # Read a line from the serial port
                                data = ser.readline().strip()
                                if data:  # Ensure data is not empty
                                    self.process_serial_data(data)
                    except serial.SerialException as e:
                        print("Serial port error:", e)
                        print("Retrying connection in 5 seconds...")
                        # Sleep for a few seconds before retrying
                        threading.Event().wait(5)
                    except Exception as e:
                        print("Unexpected error in serial reader:", e)

            # Run the serial reader in a separate thread
            serial_thread = threading.Thread(target=read_from_serial, daemon=True)
            serial_thread.start()
            print(f"Serial reader started on {com_port} at {baud_rate} baud.")
        except ValueError as e:
            print(e)

    def process_serial_data(self, data):
        """Parse and process incoming serial data dynamically."""
        try:
            # Decode bytes if necessary, then strip unwanted characters
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace").strip()
            # Example logic to parse dynamic incoming data
            # Assume data format: BEACON_ID:DISTANCE
            if ":" in data:
                beacon_id, distance = data.split(":")
                distance = float(distance)
                self.visualize_distances({beacon_id: distance})
            else:
                print("Unrecognized data format:", data)
        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error parsing serial data: {e}")

    def generate_grid(self):
        if not self.image:
            print("Please upload an image first.")
            return

        # Clear the existing grid and all beacons
        for row in self.cells:
            for cell in row:
                self.canvas.delete(
                    cell["rect"]
                )  # Remove all grid cells from the canvas
        self.cells = []
        self.beacon_cells = []
        self.beacon_data = {}

        # Reset relevant cell properties
        img_width, img_height = self.image.size  # Ensure image dimensions are used

        try:
            self.grid_size = float(
                self.grid_size_entry.get()
            )  # Get grid size from user
        except ValueError:
            print("Invalid grid size. Using default value of 0.5.")
            self.grid_size = 0.5

        try:
            width_m = float(self.width_entry.get())
            height_m = float(self.height_entry.get())
        except ValueError:
            print("Invalid width or height. Please provide valid dimensions.")
            return

        # Ensure correct dimensions for rows and columns
        num_cols = max(1, int(width_m / self.grid_size))
        num_rows = max(1, int(height_m / self.grid_size))

        cell_width = img_width / num_cols
        cell_height = img_height / num_rows

        self.cells = []
        for row in range(num_rows):
            row_cells = []
            for col in range(num_cols):
                x1 = self.image_offset_x + col * cell_width
                y1 = self.image_offset_y + row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height

                rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")
                row_cells.append({"rect": rect, "beacon": False, "overlap_count": 0})
            self.cells.append(row_cells)

    def select_cell(self, event):
        if not self.cells or not self.image:
            return

        x, y = event.x - self.image_offset_x, event.y - self.image_offset_y
        img_width, img_height = self.image.size

        # Restrict clicks to the image area only
        if x < 0 or y < 0 or x >= img_width or y >= img_height:
            print("Click outside the image. Ignoring.")
            return

        cell_width = img_width / len(self.cells[0])
        cell_height = img_height / len(self.cells)

        col = int(max(0, x) / cell_width)
        row = int(max(0, y) / cell_height)

        if 0 <= row < len(self.cells) and 0 <= col < len(self.cells[0]):
            cell = self.cells[row][col]
            if not cell["beacon"]:
                beacon_id = tk.simpledialog.askstring(
                    "Beacon ID", "Enter a unique ID for this beacon:"
                )
                if beacon_id and beacon_id not in self.beacon_data:
                    self.canvas.itemconfig(cell["rect"], fill="red")
                    cell["beacon"] = True
                    self.beacon_data[beacon_id] = (row, col)
                    self.beacon_cells.append((row, col))
                else:
                    print("Invalid or duplicate ID. Try again.")
            else:
                self.canvas.itemconfig(cell["rect"], fill="")
                cell["beacon"] = False
                beacon_id = [k for k, v in self.beacon_data.items() if v == (row, col)]
                if beacon_id:
                    del self.beacon_data[beacon_id[0]]
                self.beacon_cells.remove((row, col))

    def update_beacon_list(self):
        """Update the listbox to display active beacons and their distances."""
        self.beacon_listbox.delete(0, tk.END)
        for beacon_id, (row, col) in self.beacon_data.items():
            # Retrieve distance if available; otherwise, set as 'N/A'
            self.beacon_listbox.insert(tk.END, f"Beacon {beacon_id}: ({row}, {col})")
        print(f"Beacon list updated: {self.beacon_data}")

    def visualize_distances(self, distances):
        # Clear visuals for updated beacons
        for beacon_id, distance in distances.items():
            if beacon_id in self.beacon_data:
                row, col = self.beacon_data[beacon_id]
                # Draw the new visuals
                self.draw_circle((row, col), distance, beacon_id)

        # Update the beacon list view
        self.update_beacon_list()

        # Apply green color to cells affected by 3 or more distinct beacons
        for row_cells in self.cells:
            for cell in row_cells:
                if (
                    "in_range_beacons" in cell
                    and len(set(cell["in_range_beacons"])) >= 3
                ):
                    self.canvas.itemconfig(cell["rect"], fill="green", stipple="")
                elif (
                    "in_range_beacons" in cell
                    and len(set(cell["in_range_beacons"])) > 0
                ):
                    # Retain a lighter gray shade for overlapped areas
                    self.canvas.itemconfig(
                        cell["rect"], fill="#D3D3D3", stipple="gray75"
                    )
                else:
                    # Clear visuals only if no beacons affect the cell
                    self.canvas.itemconfig(cell["rect"], fill="", stipple="")

        # Redraw beacon squares after updating distances
        for beacon_id, (b_row, b_col) in self.beacon_data.items():
            self.canvas.itemconfig(
                self.cells[b_row][b_col]["rect"], fill="red", stipple=""
            )

    def draw_circle(self, cell, distance, beacon_id):
        """Update grid cells within range without altering grid alignment or overall appearance."""
        row, col = cell
        img_width, img_height = self.image.size  # Use image dimensions

        cell_width = img_width / len(self.cells[0])
        cell_height = img_height / len(self.cells)

        # Calculate pixel distance for the radius using grid size
        pixel_distance = (distance / self.grid_size) * cell_width
        rows = len(self.cells)
        cols = len(self.cells[0])

        # Iterate over cells to determine if they fall within beacon range
        for r in range(rows):
            for c in range(cols):
                cell_center_x = c * cell_width + cell_width / 2
                cell_center_y = r * cell_height + cell_height / 2

                center_x = col * cell_width + cell_width / 2
                center_y = row * cell_height + cell_height / 2

                # Calculate the Euclidean distance between cell center and beacon center
                distance_to_cell = (
                    (center_x - cell_center_x) ** 2 + (center_y - cell_center_y) ** 2
                ) ** 0.5
                if distance_to_cell <= pixel_distance:
                    # Mark cell as in range of this beacon
                    self.cells[r][c].setdefault("in_range_beacons", []).append(
                        beacon_id
                    )
                    self.cells[r][c]["overlap_count"] += 1
                    # Update fill color without deleting grid rectangles
                    self.canvas.itemconfig(
                        self.cells[r][c]["rect"], fill="#D3D3D3", stipple="gray75"
                    )

    def simulate_beacon_distance(self):
        beacon_id = self.beacon_id_entry.get()
        try:
            distance = float(self.distance_entry.get())
            if beacon_id in self.beacon_data:
                # Clear previous visuals for the beacon
                self.clear_beacon_visual(beacon_id)
                # Render updated distance
                self.visualize_distances({beacon_id: distance})
                # Refresh the beacon list
                self.update_beacon_list()
            else:
                print(f"Beacon ID {beacon_id} not found.")
        except ValueError:
            print("Enter a valid distance (numeric value).")

    def clear_beacon_visual(self, beacon_id):
        """Remove all visuals associated with a specific beacon's previous measurement."""
        if beacon_id not in self.beacon_data:
            return

        rows = len(self.cells)
        cols = len(self.cells[0])
        for r in range(rows):
            for c in range(cols):
                cell = self.cells[r][c]
                if "in_range_beacons" in cell and beacon_id in cell["in_range_beacons"]:
                    cell["in_range_beacons"].remove(beacon_id)
                    cell["overlap_count"] -= 1
                    if cell["overlap_count"] < 3:
                        self.canvas.itemconfig(cell["rect"], fill="", stipple="")


if __name__ == "__main__":
    root = tk.Tk()
    app = BuildingLayoutApp(root)
    root.mainloop()
