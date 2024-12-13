import serial.tools.list_ports
from serial import Serial
import json
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import threading
import queue
import time

class ToFVisualizer3D:
    def __init__(self, port='COM3', baudrate=115200):
        self.serial = Serial(port, baudrate)
        self.serial.timeout = 0.001
        self.data_queue = queue.Queue()
        
        self.app = Dash(__name__)
        
        # Setup layout
        self.app.layout = html.Div([
            html.H1('ToF Sensor Point Cloud'),
            dcc.Graph(id='live-3d-plot', style={'height': '800px'}),
            dcc.Interval(
                id='interval-component',
                interval=50,
                n_intervals=0
            )
        ])
        
        @self.app.callback(
            Output('live-3d-plot', 'figure'),
            Input('interval-component', 'n_intervals')
        )
        def update_graph(n):
            try:
                if not self.data_queue.empty():
                    grid_data = self.data_queue.get()
                else:
                    grid_data = np.zeros((8, 8))
                
                # Create coordinates for all points
                x = []
                y = []
                z = []
                
                # Create point cloud data
                for i in range(8):
                    for j in range(8):
                        x.append(i)
                        y.append(j)
                        z.append(grid_data[i][j])
                
                # Create the 3D scatter plot
                fig = go.Figure(data=[go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=z,
                        colorscale='Greys',
                        cmin=0,
                        cmax=3000,
                        showscale=True,
                        colorbar=dict(title='Distance (mm)')
                    )
                )])
                
                # Set fixed ranges and layout
                fig.update_layout(
                    scene=dict(
                        xaxis=dict(range=[-1, 8], title='X'),
                        yaxis=dict(range=[-1, 8], title='Y'),
                        zaxis=dict(range=[0, 3000], title='Distance (mm)'),
                        aspectmode='manual',
                        aspectratio=dict(x=1, y=1, z=2),
                        camera=dict(
                            eye=dict(x=1.5, y=1.5, z=1.2),
                            up=dict(x=0, y=0, z=1)
                        )
                    ),
                    margin=dict(l=0, r=0, b=0, t=30),
                    uirevision=True  # Keeps the camera position on updates
                )
                
                return fig
                
            except Exception as e:
                print(f"Error updating graph: {e}")
                return go.Figure()
    
    def read_serial(self):
        while True:
            try:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line:
                        data = json.loads(line)
                        grid_data = np.array(data['data'], dtype=float).reshape(8, 8)
                        # Keep only latest data
                        while not self.data_queue.empty():
                            self.data_queue.get()
                        self.data_queue.put(grid_data)
            except Exception as e:
                print(f"Error reading serial: {e}")
            time.sleep(0.001)
    
    @staticmethod
    def list_available_ports():
        return [p.device for p in serial.tools.list_ports.comports()]
    
    def run(self):
        serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        serial_thread.start()
        self.app.run_server(debug=False)

if __name__ == "__main__":
    ports = ToFVisualizer3D.list_available_ports()
    print("Available ports:", ports)
    visualizer = ToFVisualizer3D(port='COM3')  # Change to your COM port
    visualizer.run()