import serial.tools.list_ports
from serial import Serial
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class ToFVisualizer:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.serial = Serial(port, baudrate)
        self.serial.timeout = 0.001
        
        # Setup plot
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.heatmap = None
        
    def init_plot(self):
        data = np.zeros((8, 8))
        # Use the correct orientation based on the 4x4 example
        self.heatmap = self.ax.imshow(data, 
                                    cmap='gray',
                                    vmin=0, 
                                    vmax=3000,
                                    interpolation='none',
                                    origin='lower')  # Start from bottom
        
        self.fig.colorbar(self.heatmap, label='Distance (mm)')
        self.ax.set_title('ToF Sensor Distance (mm)')
        
        # Add grid
        self.ax.grid(True, which='major', color='blue', linewidth=0.5, alpha=0.3)
        self.ax.set_xticks(np.arange(-0.5, 8, 1))
        self.ax.set_yticks(np.arange(-0.5, 8, 1))
        
        # Add zone numbers matching the pattern
        for i in range(8):
            for j in range(8):
                zone = i * 8 + j  # Row-major order starting from bottom
                self.ax.text(j, i, str(zone), ha='center', va='center', 
                           color='red', alpha=0.5, fontsize=8)
        
        return self.heatmap,
    
    def update_plot(self, frame):
        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8').strip()
                if line:
                    data = json.loads(line)
                    print(data)
                    # Reshape into 8x8 grid in row-major order
                    grid_data = np.array(data['data'], dtype=float).reshape(8, 8)
                    self.heatmap.set_array(grid_data)
            
        except (json.JSONDecodeError, serial.SerialException) as e:
            print(f"Error: {e}")
            
        return self.heatmap,

    @staticmethod
    def list_available_ports():
        return [p.device for p in serial.tools.list_ports.comports()]
    
    def run(self):
        ani = FuncAnimation(self.fig, self.update_plot, init_func=self.init_plot,
                          interval=1,
                          blit=True,
                          cache_frame_data=False)
        plt.show()

if __name__ == "__main__":
    ports = ToFVisualizer.list_available_ports()
    print("Available ports:", ports)
    visualizer = ToFVisualizer(port='COM3')  # Change to your port
    visualizer.run()