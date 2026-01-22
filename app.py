from flask import Flask, render_template, Response, jsonify, request
import cv2
import time
import threading
from config import SIMULATION_SOURCES, LIVE_SOURCES, DEFAULT_MODE
from core.ai_engine import TrafficAI

app = Flask(__name__)

# --- GLOBAL STATE ---
state = {
    'mode': DEFAULT_MODE, # 'LIVE' or 'SIMULATION'
    'active_lane': 'north',
    'lanes': {
        'north': {'count': 0, 'signal': 'RED', 'timer': 0},
        'south': {'count': 0, 'signal': 'RED', 'timer': 0},
        'east':  {'count': 0, 'signal': 'RED', 'timer': 0},
        'west':  {'count': 0, 'signal': 'RED', 'timer': 0}
    }
}

ai_engine = TrafficAI()

# --- VIDEO GENERATOR ---
def generate_frames(direction):
    """
    Smart Generator jo Mode ke hisaab se source switch karta hai
    """
    current_source = None
    cap = None

    while True:
        # 1. Check current mode and set source
        target_source = SIMULATION_SOURCES[direction] if state['mode'] == 'SIMULATION' else LIVE_SOURCES[direction]
        
        # 2. Initialize or Switch Camera
        if current_source != target_source or cap is None or not cap.isOpened():
            if cap: cap.release()
            current_source = target_source
            print(f"[STREAM] Switching {direction} to {state['mode']} Source: {current_source}")
            cap = cv2.VideoCapture(current_source)
        
        success, frame = cap.read()
        
        # 3. Handle Video Loop (Simulation) or Error
        if not success:
            if state['mode'] == 'SIMULATION':
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
                continue
            else:
                # Live cam disconnect handling
                time.sleep(1) 
                continue

        # 4. AI Processing
        # Resize for display performance if needed, keeping 4K aspect ratio
        frame = cv2.resize(frame, (1280, 720)) 
        
        count, processed_frame = ai_engine.process_frame(frame)
        
        # Update Global Count
        state['lanes'][direction]['count'] = count

        # 5. Encode
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- TRAFFIC LOGIC (Background Thread) ---
def logic_loop():
    cycle = ['north', 'south', 'east', 'west']
    idx = 0
    
    while True:
        current_dir = cycle[idx]
        
        # 1. Calculate Time based on Density
        vehicle_count = state['lanes'][current_dir]['count']
        green_time = max(5, min(60, 5 + (vehicle_count * 1.5))) # Min 5s, Max 60s
        
        # 2. GREEN PHASE
        state['active_lane'] = current_dir
        update_signals(current_dir, 'GREEN')
        
        # Countdown
        for t in range(int(green_time), 0, -1):
            state['lanes'][current_dir]['timer'] = t
            time.sleep(1)
            
        # 3. YELLOW PHASE
        update_signals(current_dir, 'YELLOW')
        state['lanes'][current_dir]['timer'] = 3
        time.sleep(3)
        
        # 4. RED PHASE & SWITCH
        update_signals(current_dir, 'RED')
        state['lanes'][current_dir]['timer'] = 0
        
        idx = (idx + 1) % 4

def update_signals(active_dir, status):
    for direction in state['lanes']:
        if direction == active_dir:
            state['lanes'][direction]['signal'] = status
        else:
            state['lanes'][direction]['signal'] = 'RED'

# Start Logic
t = threading.Thread(target=logic_loop, daemon=True)
t.start()

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed/<direction>')
def video_feed(direction):
    return Response(generate_frames(direction), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    return jsonify(state)

@app.route('/api/toggle_mode', methods=['POST'])
def toggle_mode():
    new_mode = request.json.get('mode')
    if new_mode in ['LIVE', 'SIMULATION']:
        state['mode'] = new_mode
        print(f"[SYSTEM] Mode Switched to {new_mode}")
        return jsonify({'status': 'success', 'mode': new_mode})
    return jsonify({'status': 'error'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)