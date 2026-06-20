# import cv2
# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
# from matplotlib.patches import Circle, Patch
# import threading
# import queue
# import time

# class RCCarTracker:
#     def __init__(self, track_image_path=None, real_world_width=None, real_world_height=None, origin='top-left'):
#         """Initialize the RC Car tracker."""
#         if track_image_path is None:
#             self.track_img = self.generate_l_shaped_track()
#         else:
#             self.track_img = cv2.imread(track_image_path)
#             if self.track_img is None:
#                 raise ValueError(f"Could not load image from: {track_image_path}")
        
#         self.track_img_rgb = cv2.cvtColor(self.track_img, cv2.COLOR_BGR2RGB)
        
#         # Setup coordinate system
#         self.img_height, self.img_width = self.track_img.shape[:2]
#         self.real_world_width = real_world_width
#         self.real_world_height = real_world_height
#         self.origin = origin
        
#         if real_world_width and real_world_height:
#             self.pixels_per_meter_x = self.img_width / real_world_width
#             self.pixels_per_meter_y = self.img_height / real_world_height
#         else:
#             self.pixels_per_meter_x = None
#             self.pixels_per_meter_y = None
        
#         # Process track to find drivable region
#         self.process_track_image()
        
#         # Setup for live tracking
#         self.position_queue = queue.Queue(maxsize=100)
#         self.current_position = None
#         self.position_history = []
#         self.max_history = 50
        
#         self.setup_visualization()
    
#     def generate_l_shaped_track(self, width=800, height=600):
#         """Generate default L-shaped track."""
#         img = np.zeros((height, width, 3), dtype=np.uint8)
#         track_width = 120
#         border_width = 15
        
#         v_start_x = width // 3
#         v_end_x = v_start_x + track_width
#         v_start_y = 60
#         v_end_y = height - 150
        
#         h_start_x = v_start_x
#         h_end_x = width - 120
#         h_start_y = v_end_y - track_width
#         h_end_y = v_end_y
        
#         # White drivable areas
#         cv2.rectangle(img, (v_start_x, v_start_y), (v_end_x, v_end_y), (255, 255, 255), -1)
#         cv2.rectangle(img, (h_start_x, h_start_y), (h_end_x, h_end_y), (255, 255, 255), -1)
        
#         # Blue boundaries
#         cv2.rectangle(img, (v_start_x - border_width, v_start_y - border_width), 
#                      (v_start_x, v_end_y + border_width), (255, 0, 0), -1)
#         cv2.rectangle(img, (v_start_x - border_width, v_start_y - border_width), 
#                      (v_end_x + border_width, v_start_y), (255, 0, 0), -1)
#         cv2.rectangle(img, (v_end_x, v_start_y), 
#                      (v_end_x + border_width, h_start_y), (255, 0, 0), -1)
#         cv2.rectangle(img, (v_end_x, h_start_y - border_width), 
#                      (h_end_x + border_width, h_start_y), (255, 0, 0), -1)
#         cv2.rectangle(img, (v_start_x - border_width, v_end_y), 
#                      (h_end_x + border_width, v_end_y + border_width), (255, 0, 0), -1)
#         cv2.rectangle(img, (h_end_x, h_start_y), 
#                      (h_end_x + border_width, v_end_y + border_width), (255, 0, 0), -1)
        
#         return img
    
#     def process_track_image(self):
#         """
#         Process track image to extract clean white L-shaped interior.
#         Strategy: Detect white/gray drivable surface directly, then clean it up.
#         """
#         # Convert to grayscale
#         gray = cv2.cvtColor(self.track_img, cv2.COLOR_BGR2GRAY)
        
#         # Detect blue boundaries
#         hsv = cv2.cvtColor(self.track_img, cv2.COLOR_BGR2HSV)
#         lower_blue = np.array([90, 50, 50])
#         upper_blue = np.array([130, 255, 255])
#         blue_mask_original = cv2.inRange(hsv, lower_blue, upper_blue)
        
#         print(f"Blue pixels detected: {np.sum(blue_mask_original > 0):,}")
        
#         # Threshold to find bright areas (white/gray drivable surface)
#         # The track surface is much brighter than the black background
#         _, bright_mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
        
#         print(f"Bright pixels detected: {np.sum(bright_mask > 0):,}")
        
#         # Remove blue boundary pixels from bright mask to get drivable area
#         drivable_initial = cv2.bitwise_and(bright_mask, cv2.bitwise_not(blue_mask_original))
        
#         # Clean up with morphological operations
#         kernel_open = np.ones((5, 5), np.uint8)
#         kernel_close = np.ones((10, 10), np.uint8)
        
#         # Remove small noise
#         drivable_clean = cv2.morphologyEx(drivable_initial, cv2.MORPH_OPEN, kernel_open, iterations=2)
        
#         # Close small gaps
#         drivable_clean = cv2.morphologyEx(drivable_clean, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        
#         # Keep only the largest connected component (the main track)
#         num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(drivable_clean, connectivity=8)
        
#         if num_labels > 1:
#             # Find largest component (excluding background which is label 0)
#             largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
#             largest_area = stats[largest_label, cv2.CC_STAT_AREA]
            
#             # Create mask with only the largest component
#             clean_interior = np.zeros_like(drivable_clean)
#             clean_interior[labels == largest_label] = 255
            
#             print(f"  Largest component area: {largest_area:,} pixels")
#             print(f"  Number of components: {num_labels - 1}")
#         else:
#             clean_interior = drivable_clean
#             print("⚠ Only one component found")
        
#         print(f"Final drivable pixels: {np.sum(clean_interior > 0):,}")
        
#         # Store masks
#         self.drivable_mask = clean_interior
#         self.boundary_mask = blue_mask_original
        
#         # Create visualization
#         self.track_map = np.zeros((self.img_height, self.img_width, 3), dtype=np.uint8)
#         self.track_map[clean_interior > 0] = [255, 255, 255]  # WHITE interior
#         self.track_map[blue_mask_original > 0] = [0, 0, 255]  # BLUE boundaries
#         # Everything else BLACK
        
#         drivable_pixels = np.sum(clean_interior > 0)
#         total_pixels = self.img_height * self.img_width
#         drivable_percent = 100 * drivable_pixels / total_pixels
        
#         print(f"\nTrack processed: {self.img_width}x{self.img_height} pixels")
#         print(f"Drivable area: {drivable_pixels:,} pixels ({drivable_percent:.1f}%)")
    
#     def get_drivable_region_outline(self, format='pixel', simplification_epsilon=2.0):
#         """Extract outline with bottom-left origin (0,0), Y increases upward."""
#         contours, _ = cv2.findContours(self.drivable_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
#         simplified_contours = []
#         for contour in contours:
#             if simplification_epsilon > 0:
#                 simplified = cv2.approxPolyDP(contour, simplification_epsilon, True)
#             else:
#                 simplified = contour
            
#             points = simplified.reshape(-1, 2)
            
#             # Convert to bottom-left origin
#             converted_points = []
#             for x, y in points:
#                 if format == 'pixel':
#                     transformed_x = float(x)
#                     transformed_y = float(self.img_height - y)  # Flip Y
#                     converted_points.append([transformed_x, transformed_y])
#                 elif format == 'normalized':
#                     norm_x = x / self.img_width
#                     norm_y = (self.img_height - y) / self.img_height
#                     converted_points.append([norm_x, norm_y])
#                 elif format == 'real-world':
#                     coord = self.pixel_to_coordinate(x, y)
#                     converted_points.append(list(coord))
            
#             simplified_contours.append(np.array(converted_points))
        
#         return simplified_contours
    
#     def export_drivable_outline(self, output_file='track_outline.csv', 
#                                coordinate_format='pixel', simplification_epsilon=2.0):
#         """Export outline to CSV with bottom-left origin."""
#         print(f"\n{'='*70}")
#         print(f"EXTRACTING DRIVABLE REGION OUTLINE")
#         print(f"{'='*70}\n")
        
#         contours = self.get_drivable_region_outline(coordinate_format, simplification_epsilon)
        
#         # Export to CSV
#         import csv
#         with open(output_file, 'w', newline='') as f:
#             writer = csv.writer(f)
#             writer.writerow(['contour_id', 'point_id', 'x', 'y'])
            
#             for contour_idx, contour in enumerate(contours):
#                 for point_idx, (x, y) in enumerate(contour):
#                     writer.writerow([contour_idx, point_idx, x, y])
        
#         total_points = sum(len(c) for c in contours)
        
#         print(f"  Drivable region outline saved: {output_file}")
#         print(f"\nOutline Summary:")
#         print(f"  Number of contours:    {len(contours)}")
#         print(f"  Total outline points:  {total_points}")
#         print(f"  Format:                {coordinate_format}")
#         print(f"  Coordinate system:     Bottom-left origin (0,0), Y increases upward")
        
#         if len(contours) > 0:
#             print(f"  Main contour points:   {len(contours[0])}")
#             all_x = np.concatenate([c[:, 0] for c in contours])
#             all_y = np.concatenate([c[:, 1] for c in contours])
#             print(f"\n  X range: {all_x.min():.1f} to {all_x.max():.1f}")
#             print(f"  Y range: {all_y.min():.1f} to {all_y.max():.1f}")
        
#         print(f"\n{'='*70}\n")
        
#         return contours
    
#     def pixel_to_coordinate(self, pixel_x, pixel_y):
#         """Convert pixel to coordinate."""
#         if self.pixels_per_meter_x is None:
#             return (pixel_x, pixel_y)
        
#         if self.origin == 'bottom-left':
#             x = pixel_x / self.pixels_per_meter_x
#             y = (self.img_height - pixel_y) / self.pixels_per_meter_y
#         else:
#             x = pixel_x / self.pixels_per_meter_x
#             y = pixel_y / self.pixels_per_meter_y
        
#         return (x, y)
    
#     def coordinate_to_pixel(self, x, y):
#         """Convert coordinate to pixel."""
#         if self.pixels_per_meter_x is None:
#             return (int(x), int(y))
        
#         if self.origin == 'bottom-left':
#             pixel_x = x * self.pixels_per_meter_x
#             pixel_y = self.img_height - (y * self.pixels_per_meter_y)
#         else:
#             pixel_x = x * self.pixels_per_meter_x
#             pixel_y = y * self.pixels_per_meter_y
        
#         return (int(pixel_x), int(pixel_y))
    
#     def update_car_position(self, x, y, coordinate_system='pixel'):
#         """Update car position from YOLO."""
#         if coordinate_system == 'normalized':
#             x = x * self.img_width
#             y = y * self.img_height
#         elif coordinate_system == 'real-world':
#             x, y = self.coordinate_to_pixel(x, y)
        
#         try:
#             self.position_queue.put_nowait((x, y))
#         except queue.Full:
#             self.position_queue.get()
#             self.position_queue.put((x, y))
    
#     def setup_visualization(self):
#         """Setup real-time tracking visualization."""
#         self.fig, self.ax = plt.subplots(figsize=(12, 8))
#         self.ax.set_title('RC Car Real-Time Tracker', fontsize=16, fontweight='bold')
#         self.ax.axis('off')
        
#         self.track_display = self.ax.imshow(self.track_map)
        
#         self.car_marker = Circle((0, 0), radius=10, color='red', 
#                                  fill=True, alpha=0.8, zorder=10)
#         self.ax.add_patch(self.car_marker)
#         self.car_marker.set_visible(False)
        
#         self.trajectory_line, = self.ax.plot([], [], 'r-', 
#                                              linewidth=2, alpha=0.5, zorder=5)
        
#         legend_elements = [
#             Patch(facecolor='white', edgecolor='black', label='Drivable Area'),
#             Patch(facecolor='blue', edgecolor='black', label='Track Boundary'),
#             Patch(facecolor='red', edgecolor='black', label='RC Car')
#         ]
#         self.ax.legend(handles=legend_elements, loc='upper right')
    
#     def update_visualization(self, frame):
#         """Update animation frame."""
#         while not self.position_queue.empty():
#             try:
#                 self.current_position = self.position_queue.get_nowait()
#                 self.position_history.append(self.current_position)
                
#                 if len(self.position_history) > self.max_history:
#                     self.position_history.pop(0)
#             except queue.Empty:
#                 break
        
#         if self.current_position:
#             x, y = self.current_position
#             self.car_marker.center = (x, y)
#             self.car_marker.set_visible(True)
            
#             if len(self.position_history) > 1:
#                 xs = [pos[0] for pos in self.position_history]
#                 ys = [pos[1] for pos in self.position_history]
#                 self.trajectory_line.set_data(xs, ys)
        
#         return self.car_marker, self.trajectory_line
    
#     def start_visualization(self, interval=50):
#         """Start real-time tracking visualization."""
#         self.anim = FuncAnimation(self.fig, self.update_visualization,
#                                  interval=interval, blit=True, cache_frame_data=False)
#         plt.show()


# def export_track_outline(image_path, output_file='track_outline.csv',
#                          coordinate_format='pixel', simplification=2.0,
#                          real_world_width=None, real_world_height=None):
#     """
#     Export track outline with proper white drivable area visualization.
#     """
#     print(f"\n{'='*70}")
#     print(f"EXTRACTING TRACK OUTLINE: {image_path}")
#     print(f"{'='*70}\n")
    
#     try:
#         tracker = RCCarTracker(image_path, real_world_width, real_world_height)
#     except Exception as e:
#         print(f"ERROR: Could not load image - {e}")
#         return None
    
#     contours = tracker.export_drivable_outline(
#         output_file=output_file,
#         coordinate_format=coordinate_format,
#         simplification_epsilon=simplification
#     )
    
#     print(f"Generating visualization...")
    
#     # Create 3-panel visualization
#     fig = plt.figure(figsize=(18, 6))
    
#     # Panel 1: Original image
#     ax1 = plt.subplot(1, 3, 1)
#     ax1.imshow(tracker.track_img_rgb)
#     ax1.set_title('Original Track Image', fontsize=14, fontweight='bold')
#     ax1.axis('off')
    
#     # Panel 2: Processed track - WHITE drivable, BLUE boundaries
#     ax2 = plt.subplot(1, 3, 2)
#     ax2.imshow(tracker.track_map)
#     ax2.set_title('Drivable Region\n(White = Drivable, Blue = Boundary)', fontsize=14, fontweight='bold')
#     ax2.axis('off')
    
#     # Panel 3: Extracted outline - WHITE interior with BLUE boundary line
#     ax3 = plt.subplot(1, 3, 3)
#     ax3.set_facecolor('black')
    
#     if contours and len(contours) > 0:
#         for contour in contours:
#             # Fill with WHITE
#             ax3.fill(contour[:, 0], contour[:, 1], color='white', alpha=1.0, zorder=1)
            
#             # Draw BLUE outline
#             closed_contour = np.vstack([contour, contour[0]])
#             ax3.plot(closed_contour[:, 0], closed_contour[:, 1], 'b-', linewidth=3, zorder=2)
            
#             # RED dots at each point
#             ax3.scatter(contour[:, 0], contour[:, 1], c='red', s=30, zorder=3, 
#                        edgecolors='black', linewidths=0.5)
    
#     ax3.set_xlim(0, tracker.img_width)
#     ax3.set_ylim(0, tracker.img_height)
#     ax3.set_aspect('equal')
#     ax3.set_title(f'Extracted Outline\n({len(contours[0]) if contours else 0} points)', 
#                  fontsize=14, fontweight='bold')
#     ax3.set_xlabel('X (pixels)', fontsize=12)
#     ax3.set_ylabel('Y (pixels)', fontsize=12)
#     ax3.grid(True, alpha=0.3, color='gray', linestyle='--')
    
#     # GREEN dot at origin
#     ax3.scatter([0], [0], c='lime', s=300, marker='o', 
#                edgecolors='white', linewidths=3, zorder=10, label='Origin (0,0)')
#     ax3.legend(loc='upper right', fontsize=11, framealpha=0.9)
    
#     plt.tight_layout()
#     plt.show()
    
#     return contours


# # ============================================================================
# # LIVE CAMERA MODE
# # ============================================================================

# def live_camera_tracking(camera_index=0, coordinate_format='pixel', simplification=0.3,
#                          real_world_width=None, real_world_height=None, 
#                          update_interval=100, yolo_mock=False):
#     """
#     Live camera mode with RC Car tracking: Continuously captures frames from USB camera,
#     detects track ONCE at start, then tracks car position in real-time.
    
#     Args:
#         camera_index: USB camera index (0 for default camera)
#         coordinate_format: 'pixel', 'normalized', or 'real-world'
#         simplification: Contour simplification epsilon
#         real_world_width: Optional real-world width in meters
#         real_world_height: Optional real-world height in meters
#         update_interval: Update interval in milliseconds
#         yolo_mock: If True, simulate car movement (for testing without YOLO)
    
#     Press 'q' to quit, 's' to save current frame outline, 'r' to re-detect track
    
#     YOLO Integration:
#     - YOLO should call: tracker.update_car_position(x, y, coordinate_system='normalized')
#     - Where x, y are normalized coordinates [0, 1] from YOLO bounding box center
#     """
#     print(f"\n{'='*70}")
#     print(f"LIVE CAMERA TRACKING MODE WITH RC CAR TRACKING")
#     print(f"{'='*70}\n")
#     print(f"Opening camera {camera_index}...")
    
#     # Open camera
#     cap = cv2.VideoCapture(camera_index)
    
#     if not cap.isOpened():
#         print(f"ERROR: Could not open camera {camera_index}")
#         print("Available options:")
#         print("  - Check if camera is connected")
#         print("  - Try different camera_index (0, 1, 2, etc.)")
#         return None
    
#     # Set camera properties for better performance
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#     cap.set(cv2.CAP_PROP_FPS, 30)
    
#     print(f"✓ Camera opened successfully")
#     print(f"\nDetecting track from initial frame...")
    
#     # STEP 1: Capture initial frame and detect track ONCE
#     ret, initial_frame = cap.read()
#     if not ret:
#         print("ERROR: Could not capture initial frame")
#         cap.release()
#         return None
    
#     # Save and process initial frame to create persistent track map
#     temp_path = '/tmp/initial_track_frame.jpg'
#     cv2.imwrite(temp_path, initial_frame)
    
#     # Create tracker with initial frame - THIS STAYS PERSISTENT
#     tracker = RCCarTracker(temp_path, real_world_width, real_world_height)
    
#     print(f"✓ Track detected successfully!")
#     print(f"  Track dimensions: {tracker.img_width}x{tracker.img_height} pixels")
#     print(f"  Drivable area: {np.sum(tracker.drivable_mask > 0):,} pixels")
    
#     print(f"\nControls:")
#     print(f"  'q' - Quit")
#     print(f"  's' - Save current track outline to CSV")
#     print(f"  'r' - Re-detect track from current frame")
#     print(f"  'c' - Clear car trajectory history")
#     print(f"\nStarting real-time car tracking...\n")
    
#     # Create figure with 3 panels
#     fig = plt.figure(figsize=(20, 6))
#     plt.ion()  # Interactive mode
    
#     # Panel 1: Live camera feed
#     ax1 = plt.subplot(1, 3, 1)
#     ax1.set_title('Live Camera Feed', fontsize=14, fontweight='bold')
#     ax1.axis('off')
#     camera_display = ax1.imshow(cv2.cvtColor(initial_frame, cv2.COLOR_BGR2RGB))
    
#     # Panel 2: Persistent track map with car position
#     ax2 = plt.subplot(1, 3, 2)
#     ax2.set_title('Track Map with RC Car Position', fontsize=14, fontweight='bold')
#     ax2.axis('off')
#     track_display = ax2.imshow(tracker.track_map)
    
#     # Car marker on track map
#     car_marker = Circle((0, 0), radius=15, color='red', fill=True, alpha=0.9, zorder=10)
#     ax2.add_patch(car_marker)
#     car_marker.set_visible(False)
    
#     # Trajectory line on track map
#     trajectory_line, = ax2.plot([], [], 'yellow', linewidth=3, alpha=0.7, zorder=5, label='Car Path')
#     ax2.legend(loc='upper right', fontsize=10)
    
#     # Panel 3: Digital map (bottom-left origin) with car tracking
#     ax3 = plt.subplot(1, 3, 3)
#     ax3.set_facecolor('black')
#     ax3.set_title('Digital Map - Real-Time Car Tracking', fontsize=14, fontweight='bold')
#     ax3.set_xlabel('X (pixels)', fontsize=12)
#     ax3.set_ylabel('Y (pixels)', fontsize=12)
#     ax3.grid(True, alpha=0.3, color='gray', linestyle='--')
    
#     # Draw track outline on digital map
#     contours = tracker.get_drivable_region_outline(format='pixel', simplification_epsilon=simplification)
#     if contours and len(contours) > 0:
#         for contour in contours:
#             # Fill with WHITE
#             ax3.fill(contour[:, 0], contour[:, 1], color='white', alpha=1.0, zorder=1)
#             # Draw BLUE outline
#             closed_contour = np.vstack([contour, contour[0]])
#             ax3.plot(closed_contour[:, 0], closed_contour[:, 1], 'b-', linewidth=3, zorder=2)
    
#     ax3.set_xlim(0, tracker.img_width)
#     ax3.set_ylim(0, tracker.img_height)
#     ax3.set_aspect('equal')
    
#     # Car marker on digital map
#     car_marker_digital, = ax3.plot([], [], 'ro', markersize=20, markeredgecolor='yellow', 
#                                    markeredgewidth=3, zorder=10, label='RC Car')
#     # Trajectory on digital map
#     trajectory_digital, = ax3.plot([], [], 'r-', linewidth=2, alpha=0.6, zorder=5, label='Path')
    
#     # Origin marker
#     ax3.scatter([0], [0], c='lime', s=200, marker='o', edgecolors='white', 
#                linewidths=2, zorder=8, label='Origin (0,0)')
#     ax3.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
#     plt.tight_layout()
    
#     # Tracking state
#     frame_count = 0
#     car_position_history = []  # For trajectory
#     max_history = 100  # Keep last 100 positions
#     current_car_pos = None
    
#     # Mock YOLO simulation variables (for testing)
#     mock_x, mock_y = 100, 100
#     mock_dx, mock_dy = 2, 1
    
#     try:
#         while True:
#             ret, frame = cap.read()
            
#             if not ret:
#                 print("WARNING: Failed to grab frame")
#                 continue
            
#             frame_count += 1
            
#             # STEP 2: Update camera feed display every frame
#             camera_display.set_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
#             # STEP 3: Get car position from YOLO (or mock for testing)
#             if yolo_mock:
#                 # SIMULATE CAR MOVEMENT (for testing without YOLO)
#                 mock_x += mock_dx
#                 mock_y += mock_dy
                
#                 # Bounce off edges
#                 if mock_x <= 0 or mock_x >= tracker.img_width:
#                     mock_dx *= -1
#                 if mock_y <= 0 or mock_y >= tracker.img_height:
#                     mock_dy *= -1
                
#                 # Update car position (simulate YOLO detection)
#                 tracker.update_car_position(mock_x, mock_y, coordinate_system='pixel')
            
#             # STEP 4: Get car position from tracker queue (populated by YOLO or mock)
#             while not tracker.position_queue.empty():
#                 try:
#                     current_car_pos = tracker.position_queue.get_nowait()
#                     car_position_history.append(current_car_pos)
                    
#                     if len(car_position_history) > max_history:
#                         car_position_history.pop(0)
#                 except queue.Empty:
#                     break
            
#             # STEP 5: Update car visualization on BOTH maps
#             if current_car_pos:
#                 car_x, car_y = current_car_pos
                
#                 # Update Panel 2 (track map with top-left origin)
#                 car_marker.center = (car_x, car_y)
#                 car_marker.set_visible(True)
                
#                 if len(car_position_history) > 1:
#                     traj_xs = [pos[0] for pos in car_position_history]
#                     traj_ys = [pos[1] for pos in car_position_history]
#                     trajectory_line.set_data(traj_xs, traj_ys)
                
#                 # Update Panel 3 (digital map with bottom-left origin)
#                 # Convert Y coordinate: flip for bottom-left origin
#                 digital_x = car_x
#                 digital_y = tracker.img_height - car_y
                
#                 car_marker_digital.set_data([digital_x], [digital_y])
                
#                 if len(car_position_history) > 1:
#                     digital_traj_xs = [pos[0] for pos in car_position_history]
#                     digital_traj_ys = [tracker.img_height - pos[1] for pos in car_position_history]
#                     trajectory_digital.set_data(digital_traj_xs, digital_traj_ys)
            
#             # STEP 6: Redraw display (every frame for smooth animation)
#             plt.draw()
#             plt.pause(0.001)
            
#             # Check for key press
#             key = cv2.waitKey(1) & 0xFF
            
#             if key == ord('q'):
#                 print("\nQuitting live mode...")
#                 break
#             elif key == ord('s'):
#                 # Save current track outline to CSV
#                 timestamp = time.strftime("%Y%m%d_%H%M%S")
#                 output_file = f'track_outline_live_{timestamp}.csv'
#                 tracker.export_drivable_outline(
#                     output_file=output_file,
#                     coordinate_format=coordinate_format,
#                     simplification_epsilon=simplification
#                 )
#                 print(f"✓ Saved track outline to: {output_file}")
#             elif key == ord('r'):
#                 # Re-detect track from current frame
#                 print("\nRe-detecting track...")
#                 cv2.imwrite(temp_path, frame)
#                 tracker = RCCarTracker(temp_path, real_world_width, real_world_height)
#                 track_display.set_data(tracker.track_map)
                
#                 # Redraw digital map with new contours
#                 ax3.clear()
#                 ax3.set_facecolor('black')
#                 ax3.set_title('Digital Map - Real-Time Car Tracking', fontsize=14, fontweight='bold')
#                 ax3.set_xlabel('X (pixels)', fontsize=12)
#                 ax3.set_ylabel('Y (pixels)', fontsize=12)
#                 ax3.grid(True, alpha=0.3, color='gray', linestyle='--')
                
#                 contours = tracker.get_drivable_region_outline(format='pixel', 
#                                                                simplification_epsilon=simplification)
#                 if contours and len(contours) > 0:
#                     for contour in contours:
#                         ax3.fill(contour[:, 0], contour[:, 1], color='white', alpha=1.0, zorder=1)
#                         closed_contour = np.vstack([contour, contour[0]])
#                         ax3.plot(closed_contour[:, 0], closed_contour[:, 1], 'b-', 
#                                linewidth=3, zorder=2)
                
#                 ax3.set_xlim(0, tracker.img_width)
#                 ax3.set_ylim(0, tracker.img_height)
#                 ax3.set_aspect('equal')
                
#                 car_marker_digital, = ax3.plot([], [], 'ro', markersize=20, 
#                                               markeredgecolor='yellow', markeredgewidth=3, 
#                                               zorder=10, label='RC Car')
#                 trajectory_digital, = ax3.plot([], [], 'r-', linewidth=2, alpha=0.6, 
#                                               zorder=5, label='Path')
#                 ax3.scatter([0], [0], c='lime', s=200, marker='o', edgecolors='white',
#                            linewidths=2, zorder=8, label='Origin (0,0)')
#                 ax3.legend(loc='upper right', fontsize=10, framealpha=0.9)
                
#                 print(f"✓ Track re-detected")
#             elif key == ord('c'):
#                 # Clear trajectory
#                 car_position_history.clear()
#                 trajectory_line.set_data([], [])
#                 trajectory_digital.set_data([], [])
#                 print("✓ Trajectory cleared")
    
#     except KeyboardInterrupt:
#         print("\n\nInterrupted by user")
    
#     finally:
#         # Cleanup
#         cap.release()
#         cv2.destroyAllWindows()
#         plt.close('all')
#         print("\n✓ Camera released")
#         print(f"✓ Processed {frame_count} frames")
#         print(f"✓ Tracked {len(car_position_history)} car positions")
#         print(f"\n{'='*70}\n")
    
#     return tracker, car_position_history


# # ============================================================================
# # MAIN PROGRAM
# # ============================================================================

# if __name__ == "__main__":
    
#     # ========================================================================
#     # MODE SELECTION
#     # ========================================================================
    
#     MODE = "still"  # Options: "still" or "live_with_car"
    
#     # ========================================================================
#     # STILL IMAGE MODE (Original functionality)
#     # ========================================================================
#     if MODE == "still":
#         # Export track outline from a still image
#         export_track_outline(
#             image_path=r'C:\Users\Saad Malik\Desktop\SDP\track_image.jpg',
#             output_file='track_outline.csv',
#             coordinate_format='pixel',
#             simplification=0.3
#         )
    
#     # ========================================================================
#     # LIVE CAMERA MODE WITH RC CAR TRACKING
#     # ========================================================================
#     elif MODE == "live_with_car":
#         # Process live camera feed WITH real-time car tracking
#         # 
#         # YOLO INTEGRATION INSTRUCTIONS:
#         # --------------------------------
#         # In your YOLO code, after detecting the car's bounding box, call:
#         #   tracker.update_car_position(center_x, center_y, coordinate_system='normalized')
#         # 
#         # Where center_x, center_y are the normalized [0, 1] coordinates of the 
#         # bounding box center from YOLO detection.
#         #
#         # Example YOLO integration:
#         #   results = model(frame)
#         #   for detection in results:
#         #       if detection.class == 'rc_car':
#         #           bbox = detection.bbox  # [x1, y1, x2, y2]
#         #           center_x = (bbox[0] + bbox[2]) / 2 / frame_width
#         #           center_y = (bbox[1] + bbox[3]) / 2 / frame_height
#         #           tracker.update_car_position(center_x, center_y, 'normalized')
        
#         live_camera_tracking(
#             camera_index=0,              # 0 = default USB camera
#             coordinate_format='pixel',   
#             simplification=0.3,          
#             real_world_width=None,       
#             real_world_height=None,
#             update_interval=100,
#             yolo_mock=True               # Set to False when using real YOLO
#                                         # Set to True to see simulated car movement
#         )
    
#     else:
#         print(f"ERROR: Invalid MODE '{MODE}'. Use 'still' or 'live_with_car'")

import cv2
import numpy as np
import matplotlib.pyplot as plt
import csv
import os


class TrackDigitizer:
    """
    Digitizes a physical RC car track from an overhead photograph.

    Detection strategy (robust to real-world lighting):
      1. Adaptive brightness split  – Otsu on grayscale separates the
         bright white surface from the dark background/interior.
      2. HSV red/maroon detection    – wide ranges catch dark crimson tape.
      3. Combine & clean             – morphology + connected-component
         filtering removes noise, keeps the main track shape with its
         inner cutout(s).

    Produces:
      • drivable_mask   – binary mask of the full drivable region
      • red_mask        – binary mask of the boundary tape only
      • white_only_mask – drivable minus the tape
      • digital_map     – clean BGR image (white track, red tape, black bg)
      • outer_boundary / inner_boundaries – simplified contour coords
    """

    def __init__(self, image_path, debug_dir=None):
        """
        Parameters
        ----------
        image_path : str   Path to the overhead track photograph.
        debug_dir  : str   If set, intermediate masks are saved here.
        """
        self.track_img = cv2.imread(image_path)
        if self.track_img is None:
            raise ValueError(f"Could not load image: {image_path}")

        self.img_height, self.img_width = self.track_img.shape[:2]
        self.track_img_rgb = cv2.cvtColor(self.track_img, cv2.COLOR_BGR2RGB)
        self._debug_dir = debug_dir

        # Masks populated by processing
        self.red_mask = None
        self.white_mask = None
        self.bright_mask = None         # Otsu-based brightness mask
        self.drivable_mask = None       # white + red combined, cleaned
        self.white_only_mask = None     # just the white interior (no red)

        # Contour data
        self.outer_boundary = None
        self.inner_boundaries = []

        # Digitized output image
        self.digital_map = None

        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)

        # Run the full pipeline
        self._detect_colors()
        self._build_drivable_mask()
        self._extract_boundaries()
        self._build_digital_map()

    # ------------------------------------------------------------------ #
    #  Debug helper
    # ------------------------------------------------------------------ #
    def _save_debug(self, name, mask):
        if self._debug_dir is not None:
            path = os.path.join(self._debug_dir, f'debug_{name}.png')
            cv2.imwrite(path, mask)

    # ------------------------------------------------------------------ #
    #  STEP 1 – Colour detection (brightness + HSV red)
    # ------------------------------------------------------------------ #
    def _detect_colors(self):
        hsv = cv2.cvtColor(self.track_img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(self.track_img, cv2.COLOR_BGR2GRAY)

        # --- A) Brightness-based white detection (Otsu) ---
        # Otsu automatically finds the best split between the bright white
        # surface and the dark background, regardless of lighting.
        # We apply a small blur first to reduce texture noise.
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        otsu_thresh, self.bright_mask = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # --- B) HSV-based white detection (relaxed) ---
        # Catches off-white areas that Otsu may put on the wrong side
        # of the threshold if there's a strong shadow gradient.
        #   Value >= 130  (was 195 — way too strict for real surfaces)
        #   Saturation <= 70  (was 45 — too strict under warm lighting)
        self.white_mask = cv2.inRange(
            hsv, np.array([0, 0, 130]), np.array([180, 70, 255])
        )

        # --- C) Red / maroon / crimson tape detection ---
        # The boundary tape is often dark maroon under indoor lighting:
        #   Hue wraps around 0°/180° in OpenCV's 0-179 range.
        #   Saturation >= 40   (was 70 — too strict for dark maroon)
        #   Value >= 25        (was 50 — dark tape in shadow can go lower)
        red1 = cv2.inRange(hsv, np.array([0,   40, 25]), np.array([15,  255, 255]))
        red2 = cv2.inRange(hsv, np.array([165, 40, 25]), np.array([180, 255, 255]))
        self.red_mask = cv2.bitwise_or(red1, red2)

        # Clean the red mask: open to remove single-pixel noise, then
        # dilate to bridge small gaps in the painted tape.
        k_red = np.ones((5, 5), np.uint8)
        self.red_mask = cv2.morphologyEx(self.red_mask, cv2.MORPH_OPEN,
                                         k_red, iterations=1)
        self.red_mask = cv2.dilate(self.red_mask, k_red, iterations=2)

        self._save_debug('01_bright_otsu', self.bright_mask)
        self._save_debug('02_white_hsv', self.white_mask)
        self._save_debug('03_red_hsv', self.red_mask)

        t = self.img_height * self.img_width
        b = np.sum(self.bright_mask > 0)
        w = np.sum(self.white_mask > 0)
        r = np.sum(self.red_mask > 0)
        print(f"Color detection  (Otsu threshold = {otsu_thresh:.0f}):")
        print(f"  Bright (Otsu): {b:>10,}  ({100*b/t:.1f}%)")
        print(f"  White (HSV):   {w:>10,}  ({100*w/t:.1f}%)")
        print(f"  Red/maroon:    {r:>10,}  ({100*r/t:.1f}%)")

    # ------------------------------------------------------------------ #
    #  STEP 2 – Build a clean drivable mask
    # ------------------------------------------------------------------ #
    def _build_drivable_mask(self):
        """
        Combine brightness + HSV white + red tape into one mask,
        then clean with morphology and connected-component filtering.

        Key insight: select the largest connected component BEFORE
        aggressive morphological closing.  Otherwise closing bridges
        the gap between the track and nearby objects (wooden frame,
        wall, equipment) that happen to be bright, merging them into
        one blob.
        """
        # Union of all three detections
        combined = self.bright_mask.copy()
        combined = cv2.bitwise_or(combined, self.white_mask)
        combined = cv2.bitwise_or(combined, self.red_mask)
        self._save_debug('04_combined_raw', combined)

        # ── Step A: Clear a thin border strip ──
        # Objects at the image edge (wooden frame, wall, cables) are not
        # part of the track.  Zeroing a margin prevents them from merging
        # with the track during morphological operations.
        margin = max(8, int(0.005 * min(self.img_height, self.img_width)))
        combined[:margin, :]  = 0      # top
        combined[-margin:, :] = 0      # bottom
        combined[:, :margin]  = 0      # left
        combined[:, -margin:] = 0      # right
        self._save_debug('04b_border_cleared', combined)

        # ── Step B: Light open — remove small noise ──
        k_small = np.ones((5, 5), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, k_small, iterations=2)
        self._save_debug('04c_after_open', combined)

        # ── Step C: Select the LARGEST connected component ──
        # At this point the track and any stray edge objects should be
        # separate blobs; pick the biggest one (the track).
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            combined, connectivity=8
        )
        if num_labels > 1:
            largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            combined = np.zeros_like(combined)
            combined[labels == largest] = 255
        self._save_debug('04d_largest_cc', combined)

        # ── Step D: NOW close to fill small gaps inside the track ──
        k = np.ones((7, 7), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k, iterations=3)
        self._save_debug('05_combined_morphed', combined)

        self.drivable_mask = combined

        # ── Step E: Fill tiny holes (texture noise) ──
        inv = cv2.bitwise_not(self.drivable_mask)
        n_hole, hole_lbl, hole_stats, _ = cv2.connectedComponentsWithStats(
            inv, connectivity=8
        )
        noise_limit = 0.01 * self.img_height * self.img_width
        for lbl in range(1, n_hole):
            if hole_stats[lbl, cv2.CC_STAT_AREA] < noise_limit:
                self.drivable_mask[hole_lbl == lbl] = 255

        # ── Step F: Remove small stray islands ──
        n_w, w_lbl, w_stats, _ = cv2.connectedComponentsWithStats(
            self.drivable_mask, connectivity=8
        )
        if n_w > 1:
            largest_w = 1 + np.argmax(w_stats[1:, cv2.CC_STAT_AREA])
            island_limit = 0.02 * self.img_height * self.img_width
            for lbl in range(1, n_w):
                if lbl != largest_w and w_stats[lbl, cv2.CC_STAT_AREA] < island_limit:
                    self.drivable_mask[w_lbl == lbl] = 0

        # ── Step G: Clip red mask to the track vicinity ──
        # The raw red_mask may contain false positives (ruler markings,
        # wood grain, etc.) far from the track.  Keep only red pixels
        # that fall within a slightly dilated version of the drivable mask.
        k_vicinity = np.ones((15, 15), np.uint8)
        track_vicinity = cv2.dilate(self.drivable_mask, k_vicinity, iterations=2)
        self.red_mask = cv2.bitwise_and(self.red_mask, track_vicinity)

        # White-only mask = drivable minus the red tape
        self.white_only_mask = cv2.bitwise_and(
            self.drivable_mask, cv2.bitwise_not(self.red_mask)
        )

        self._save_debug('06_drivable_final', self.drivable_mask)
        self._save_debug('07_white_only', self.white_only_mask)

        d = np.sum(self.drivable_mask > 0)
        t = self.img_height * self.img_width
        print(f"  Drivable:      {d:>10,}  ({100*d/t:.1f}%)")

    # ------------------------------------------------------------------ #
    #  STEP 3 – Extract outer + inner boundary contours
    # ------------------------------------------------------------------ #
    def _extract_boundaries(self, simplification_epsilon=None):
        """
        Uses RETR_CCOMP to get a 2-level hierarchy:
          - parent contours  = outer boundary of drivable region
          - child contours   = inner holes (black no-go zones)
        Small holes (noise from textured surfaces) are filtered out.

        If simplification_epsilon is None it defaults to ~0.1% of the
        image diagonal, which keeps enough points for smooth curves
        while still reducing noise jitter.
        """
        if simplification_epsilon is None:
            diag = np.sqrt(self.img_width**2 + self.img_height**2)
            simplification_epsilon = max(1.0, diag * 0.001)

        # Gentle smoothing — just 1 round with a small kernel.
        # Heavy smoothing (3× Gaussian-9) was rounding off the V-notch
        # and other sharp track geometry.
        smooth_mask = self.drivable_mask.copy()
        smooth_mask = cv2.GaussianBlur(smooth_mask, (5, 5), 1)
        _, smooth_mask = cv2.threshold(smooth_mask, 127, 255, cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(
            smooth_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours or hierarchy is None:
            print("WARNING: No contours found")
            return

        h = hierarchy[0]  # shape (N, 4)

        # Minimum area to keep — 0.5% of total image area
        min_hole_area = 0.005 * self.img_height * self.img_width

        outer_contours = []
        inner_contours = []
        for i, info in enumerate(h):
            raw_area = cv2.contourArea(contours[i])

            if simplification_epsilon > 0:
                approx = cv2.approxPolyDP(contours[i], simplification_epsilon, True)
            else:
                approx = contours[i]
            pts = approx.reshape(-1, 2).astype(float)

            if info[3] == -1:          # outer (no parent)
                outer_contours.append((raw_area, pts))
            else:                      # inner (has parent)
                if raw_area >= min_hole_area:
                    inner_contours.append((raw_area, pts))

        if outer_contours:
            outer_contours.sort(key=lambda x: x[0], reverse=True)
            self.outer_boundary = outer_contours[0][1]

        inner_contours.sort(key=lambda x: x[0], reverse=True)
        self.inner_boundaries = [pts for _, pts in inner_contours]

        print(f"\nBoundary extraction:")
        print(f"  Outer boundary:   {len(self.outer_boundary) if self.outer_boundary is not None else 0} points")
        print(f"  Inner boundaries: {len(self.inner_boundaries)} hole(s)")
        for i, ib in enumerate(self.inner_boundaries):
            print(f"    Hole {i}: {len(ib)} points")

    # ------------------------------------------------------------------ #
    #  STEP 4 – Build a clean digital map image
    # ------------------------------------------------------------------ #
    def _build_digital_map(self):
        self.digital_map = np.zeros(
            (self.img_height, self.img_width, 3), dtype=np.uint8
        )
        self.digital_map[self.drivable_mask > 0] = [255, 255, 255]   # white
        self.digital_map[self.red_mask > 0]      = [0, 0, 255]       # red (BGR)
        self._save_debug('08_digital_map', self.digital_map)

    # ------------------------------------------------------------------ #
    #  Export boundary coordinates to CSV
    # ------------------------------------------------------------------ #
    def export_boundaries(self, output_csv='track_boundaries.csv'):
        """Export x,y coordinates for all white-region boundaries.

        Coordinate system: bottom-left origin (0,0).
          • X increases rightward   (same as image pixels)
          • Y increases upward      (flipped from image pixels)

        Conversion:  exported_y = (img_height - 1) - pixel_y
        """
        max_y = self.img_height - 1

        rows = []
        if self.outer_boundary is not None:
            for pt in self.outer_boundary:
                rows.append(('outer', pt[0], max_y - pt[1]))
        for idx, ib in enumerate(self.inner_boundaries):
            for pt in ib:
                rows.append((f'inner_{idx}', pt[0], max_y - pt[1]))

        with open(output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['boundary', 'x', 'y'])
            for r in rows:
                writer.writerow(r)

        print(f"\nExported {len(rows)} boundary points → {output_csv}")
        print(f"  Coordinate system: bottom-left origin (0,0)")
        print(f"  X range: 0 – {self.img_width - 1}  (rightward)")
        print(f"  Y range: 0 – {max_y}  (upward)")
        return output_csv

    # ------------------------------------------------------------------ #
    #  Visualization
    # ------------------------------------------------------------------ #
    def visualize(self, save_path=None):
        fig, axes = plt.subplots(1, 3, figsize=(22, 7))

        # --- Panel 1: Original ---
        axes[0].imshow(self.track_img_rgb)
        axes[0].set_title('Original Image', fontsize=14, fontweight='bold')
        axes[0].axis('off')

        # --- Panel 2: Detected regions ---
        overlay = self.track_img_rgb.copy()
        green_tint = np.zeros_like(overlay)
        green_tint[self.white_only_mask > 0] = [0, 200, 0]
        overlay = cv2.addWeighted(overlay, 0.6, green_tint, 0.4, 0)
        red_tint = np.zeros_like(overlay)
        red_tint[self.red_mask > 0] = [255, 0, 0]
        overlay = cv2.addWeighted(overlay, 0.8, red_tint, 0.2, 0)

        axes[1].imshow(overlay)
        axes[1].set_title('Detected Regions\n(Green=Drivable, Red=Boundary)',
                          fontsize=14, fontweight='bold')
        axes[1].axis('off')

        # --- Panel 3: Digitized map with boundary contours ---
        # Uses bottom-left origin (0,0) to match the exported CSV.
        ax3 = axes[2]
        ax3.set_facecolor('black')
        max_y = self.img_height - 1

        if self.outer_boundary is not None:
            # Flip Y for plotting: plot_y = max_y - pixel_y
            outer_plot = self.outer_boundary.copy()
            outer_plot[:, 1] = max_y - outer_plot[:, 1]

            ax3.fill(outer_plot[:, 0], outer_plot[:, 1],
                     color='white', alpha=1.0, zorder=1)

            for ib in self.inner_boundaries:
                ib_plot = ib.copy()
                ib_plot[:, 1] = max_y - ib_plot[:, 1]
                ax3.fill(ib_plot[:, 0], ib_plot[:, 1],
                         color='black', alpha=1.0, zorder=2)

            oc = np.vstack([outer_plot, outer_plot[0]])
            ax3.plot(oc[:, 0], oc[:, 1], 'r-', linewidth=2, zorder=3,
                     label='Outer boundary')

            for i, ib in enumerate(self.inner_boundaries):
                ib_plot = ib.copy()
                ib_plot[:, 1] = max_y - ib_plot[:, 1]
                ic = np.vstack([ib_plot, ib_plot[0]])
                lbl = 'Inner boundary' if i == 0 else None
                ax3.plot(ic[:, 0], ic[:, 1], color='#FF6600',
                         linewidth=2, zorder=3, label=lbl)

        ax3.set_xlim(0, self.img_width)
        ax3.set_ylim(0, self.img_height)          # Y=0 at bottom, increases up
        ax3.set_aspect('equal')
        ax3.set_title('Digitized Track\n(boundary coordinates)',
                       fontsize=14, fontweight='bold')
        ax3.set_xlabel('X (px)')
        ax3.set_ylabel('Y (px)')
        ax3.grid(True, alpha=0.2, color='gray', linestyle='--')
        ax3.legend(loc='upper right', fontsize=10, framealpha=0.9)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            print(f"Visualization saved → {save_path}")
        plt.close()

    def save_digital_track_image(self, path='digital_track.png'):
        """Save the clean digitized track as a standalone image."""
        cv2.imwrite(path, self.digital_map)
        print(f"Digital track image saved → {path}")


# ======================================================================
# Live Tracker  –  Racing-game mini-map overlay
# ======================================================================

import threading
import queue
import time
from collections import deque


class LiveTracker:
    """
    Real-time mini-map display for an RC car on a digitized track.

    Takes the digital map produced by TrackDigitizer as a fixed background
    and overlays the car's current position (received from a YOLO model or
    any other coordinate source) as a coloured dot.  A fading trajectory
    trail is drawn behind the car so you can see where it has been.

    The coordinate interface is thread-safe: your YOLO detection loop can
    call `update_position()` from any thread while the display loop runs
    on the main thread.

    Typical usage
    -------------
        td = TrackDigitizer('track_image.jpeg')
        tracker = LiveTracker(td)

        # — In your YOLO thread —
        tracker.update_position(x, y)          # pixel coords
        tracker.update_position(nx, ny, 'normalized')  # 0-1 coords

        # — On the main thread —
        tracker.run()            # opens the mini-map window
        # or
        tracker.run_headless()   # no window, just updates internal state

    To stop the display loop, press 'q' in the OpenCV window or call
    tracker.stop() from any thread.
    """

    # ------------------------------------------------------------------ #
    #  Construction
    # ------------------------------------------------------------------ #
    def __init__(self, digitizer: TrackDigitizer, *,
                 marker_radius: int = 12,
                 marker_color: tuple = (0, 0, 255),      # BGR red
                 trail_color: tuple = (0, 200, 255),      # BGR yellow-ish
                 trail_length: int = 150,
                 trail_thickness: int = 2,
                 trail_fade: bool = True,
                 window_name: str = 'RC Car Mini-Map',
                 target_fps: int = 60):
        """
        Parameters
        ----------
        digitizer       : TrackDigitizer with a .digital_map already built.
        marker_radius   : radius in pixels of the car dot.
        marker_color    : BGR colour tuple for the car dot.
        trail_color     : BGR colour tuple for the trajectory line.
        trail_length    : how many past positions to keep in the trail.
        trail_thickness : line width for the trajectory.
        trail_fade      : if True the trail fades from bright to dim.
        window_name     : OpenCV window title.
        target_fps      : approximate refresh rate for the display loop.
        """
        if digitizer.digital_map is None:
            raise ValueError("TrackDigitizer has no digital_map — run the "
                             "pipeline first.")

        # Fixed background (never mutated)
        self._bg = digitizer.digital_map.copy()
        self._h, self._w = self._bg.shape[:2]

        # Display parameters
        self.marker_radius = marker_radius
        self.marker_color = marker_color
        self.trail_color = trail_color
        self.trail_thickness = trail_thickness
        self.trail_fade = trail_fade
        self.window_name = window_name
        self._frame_delay = max(1, int(1000 / target_fps))  # ms

        # Position state (thread-safe)
        self._pos_queue: queue.Queue = queue.Queue(maxsize=512)
        self._current_pos: tuple | None = None
        self._trail: deque = deque(maxlen=trail_length)
        self._lock = threading.Lock()

        # Run flag
        self._running = False

    # ------------------------------------------------------------------ #
    #  Public API – push coordinates from any thread
    # ------------------------------------------------------------------ #
    def update_position(self, x: float, y: float,
                        coord_system: str = 'pixel') -> None:
        """
        Push a new car position.

        Parameters
        ----------
        x, y           : coordinates of the car.
        coord_system   : 'pixel'      – raw image-pixel coords (top-left origin)
                         'normalized'  – values in [0, 1] relative to image size
        """
        if coord_system == 'normalized':
            x = x * self._w
            y = y * self._h

        px, py = int(round(x)), int(round(y))
        # Clamp to image bounds
        px = max(0, min(self._w - 1, px))
        py = max(0, min(self._h - 1, py))

        try:
            self._pos_queue.put_nowait((px, py))
        except queue.Full:
            # Drop oldest to make room
            try:
                self._pos_queue.get_nowait()
            except queue.Empty:
                pass
            self._pos_queue.put_nowait((px, py))

    def get_current_position(self) -> tuple | None:
        """Return the last known (x, y) pixel position, or None."""
        with self._lock:
            return self._current_pos

    def get_trail(self) -> list:
        """Return a copy of the current trail as a list of (x, y) tuples."""
        with self._lock:
            return list(self._trail)

    def clear_trail(self) -> None:
        """Erase the trajectory history."""
        with self._lock:
            self._trail.clear()

    def stop(self) -> None:
        """Signal the display loop to exit."""
        self._running = False

    # ------------------------------------------------------------------ #
    #  Internal – drain the queue & update state
    # ------------------------------------------------------------------ #
    def _consume_queue(self):
        """Drain all queued positions into the trail."""
        positions = []
        while True:
            try:
                positions.append(self._pos_queue.get_nowait())
            except queue.Empty:
                break

        if positions:
            with self._lock:
                for pos in positions:
                    self._trail.append(pos)
                self._current_pos = positions[-1]

    # ------------------------------------------------------------------ #
    #  Internal – render one frame
    # ------------------------------------------------------------------ #
    def _render_frame(self) -> np.ndarray:
        """Compose the background + trail + car dot into a display frame."""
        frame = self._bg.copy()

        with self._lock:
            trail = list(self._trail)
            car = self._current_pos

        # Draw trajectory trail
        if len(trail) > 1:
            n = len(trail)
            for i in range(1, n):
                if self.trail_fade:
                    # Alpha ramps from ~0.15 (oldest) to 1.0 (newest)
                    alpha = 0.15 + 0.85 * (i / (n - 1))
                    color = tuple(int(c * alpha) for c in self.trail_color)
                else:
                    color = self.trail_color

                cv2.line(frame, trail[i - 1], trail[i],
                         color, self.trail_thickness, cv2.LINE_AA)

        # Draw car marker (filled circle + bright outline)
        if car is not None:
            cv2.circle(frame, car, self.marker_radius,
                       self.marker_color, -1, cv2.LINE_AA)
            cv2.circle(frame, car, self.marker_radius,
                       (255, 255, 255), 2, cv2.LINE_AA)

        return frame

    # ------------------------------------------------------------------ #
    #  Display loops
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        """
        Main-thread display loop using an OpenCV window.

        Press 'q' to quit, 'c' to clear the trail, 's' to save a snapshot.
        """
        self._running = True
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self._w, self._h)
        print(f"\n{'=' * 55}")
        print(f"  LIVE TRACKER  –  Mini-Map")
        print(f"{'=' * 55}")
        print(f"  Window : {self.window_name}")
        print(f"  Size   : {self._w} x {self._h}")
        print(f"  Keys   : q = quit | c = clear trail | s = snapshot")
        print(f"{'=' * 55}\n")

        frame_count = 0
        try:
            while self._running:
                self._consume_queue()
                frame = self._render_frame()
                cv2.imshow(self.window_name, frame)
                frame_count += 1

                key = cv2.waitKey(self._frame_delay) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    self.clear_trail()
                    print("  ✓ Trail cleared")
                elif key == ord('s'):
                    ts = time.strftime('%Y%m%d_%H%M%S')
                    path = f'minimap_snapshot_{ts}.png'
                    cv2.imwrite(path, frame)
                    print(f"  ✓ Snapshot saved → {path}")
        finally:
            self._running = False
            cv2.destroyWindow(self.window_name)
            print(f"\n  Tracker stopped after {frame_count} frames.\n")

    def run_headless(self, duration: float | None = None) -> None:
        """
        Run without an OpenCV window (useful for automated pipelines).
        Keeps consuming positions and building the trail so that
        get_current_position() / get_trail() stay up-to-date.

        Parameters
        ----------
        duration : seconds to run, or None to run until stop() is called.
        """
        self._running = True
        t0 = time.monotonic()
        try:
            while self._running:
                self._consume_queue()
                time.sleep(0.005)
                if duration and (time.monotonic() - t0) >= duration:
                    break
        finally:
            self._running = False

    def get_snapshot(self) -> np.ndarray:
        """Return the current rendered frame (background + trail + car)."""
        self._consume_queue()
        return self._render_frame()


# ======================================================================
# Convenience helpers  –  YOLO integration examples
# ======================================================================

def demo_simulated_car(digitizer: TrackDigitizer, duration_sec: float = 30):
    """
    Demo: run the mini-map with a simulated car bouncing around the
    drivable area.  Useful for testing the display without a real camera
    or YOLO model.
    """
    tracker = LiveTracker(digitizer, trail_length=200)

    # --- simulation thread ---
    def _simulate():
        h, w = digitizer.img_height, digitizer.img_width
        x, y = w // 3, h // 3
        dx, dy = 3, 2
        while tracker._running:
            x += dx
            y += dy
            # Bounce off image edges
            if x <= 0 or x >= w - 1:
                dx = -dx
            if y <= 0 or y >= h - 1:
                dy = -dy
            tracker.update_position(x, y)
            time.sleep(0.02)  # ~50 Hz

    sim = threading.Thread(target=_simulate, daemon=True)
    sim.start()
    tracker.run()       # blocks on main thread until 'q' pressed


def yolo_integration_example():
    """
    Pseudocode showing how to wire a YOLO model to the LiveTracker.

    This is NOT runnable as-is — adapt it to your actual YOLO pipeline
    and camera setup.
    """
    print("""
    # --------------------------------------------------------
    # YOLO ↔ LiveTracker integration sketch
    # --------------------------------------------------------
    from ultralytics import YOLO
    import cv2, threading

    # 1. Build the track map (done once)
    td = TrackDigitizer('track_image.jpeg')

    # 2. Create the live tracker
    tracker = LiveTracker(td)

    # 3. YOLO detection thread
    model = YOLO('your_rc_car_model.pt')
    cap   = cv2.VideoCapture(0)       # overhead camera

    def yolo_loop():
        while cap.isOpened() and tracker._running:
            ret, frame = cap.read()
            if not ret:
                continue
            results = model(frame, verbose=False)
            for det in results[0].boxes:
                # Assuming class 0 = rc_car
                if int(det.cls[0]) == 0:
                    x1, y1, x2, y2 = det.xyxy[0].tolist()
                    cx = (x1 + x2) / 2 / frame.shape[1]   # normalized
                    cy = (y1 + y2) / 2 / frame.shape[0]
                    tracker.update_position(cx, cy, 'normalized')
        cap.release()

    t = threading.Thread(target=yolo_loop, daemon=True)
    t.start()

    # 4. Display mini-map on main thread (blocks until 'q')
    tracker.run()
    """)


# ======================================================================
# Main execution
# ======================================================================
if __name__ == '__main__':
    IMAGE_PATH = r'C:\Users\Saad Malik\Desktop\SDP\track_image3.png'
    OUTPUT_DIR = r'C:\Users\Saad Malik\Desktop\SDP\Outputs'
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("  TRACK DIGITIZER  –  Red boundary detection")
    print("=" * 60, "\n")

    td = TrackDigitizer(IMAGE_PATH)

    # Save outputs
    td.export_boundaries(os.path.join(OUTPUT_DIR, 'track_boundaries.csv'))
    td.save_digital_track_image(os.path.join(OUTPUT_DIR, 'digital_track.png'))
    td.visualize(save_path=os.path.join(OUTPUT_DIR, 'track_visualization.png'))

    print("\nDone.")

    # ------------------------------------------------------------------
    # LIVE TRACKING MODE
    # ------------------------------------------------------------------
    # Uncomment ONE of the following to launch the mini-map:
    #
    # ▸ Option A — simulated car (no camera / YOLO needed):
    #     demo_simulated_car(td, duration_sec=60)
    #
    # ▸ Option B — real YOLO pipeline (adapt to your setup):
    #     tracker = LiveTracker(td)
    #     # … start your YOLO thread that calls tracker.update_position() …
    #     tracker.run()
    #
    # ▸ Option C — headless (no display window):
    #     tracker = LiveTracker(td)
    #     # … push positions from YOLO …
    #     tracker.run_headless()
    #     snapshot = tracker.get_snapshot()
    #     cv2.imwrite('minimap_latest.png', snapshot)