from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'u19-secure-military-grade'
socketio = SocketIO(app, cors_allowed_origins=["https://u19sender.pages.dev"], async_mode='eventlet')

rooms = {}

@app.route('/')
def index():
    return "U19 Secure Backend Online - HF Deployment"

@socketio.on('join_room')
def on_join(data):
    room = data['code']
    user_type = data['type']
    
    join_room(room)
    if room not in rooms:
        rooms[room] = {'sender': False, 'receiver': False}
        
    rooms[room][user_type] = True
    
    emit('room_status', {
        'status': 'active' if rooms[room]['sender'] and rooms[room]['receiver'] else 'waiting',
        'room': room
    }, room=room)
    
    emit('room_joined', {'room_active': True}, to=request.sid)

@socketio.on('ping_keepalive')
def on_ping():
    emit('pong')

@socketio.on('send_text')
def handle_send_text(data):
    room = data.get('code')
    # Server strictly acts as an ephemeral router. It cannot decrypt the AES payload.
    emit('receive_text', data, room=room, include_self=False)

@socketio.on('typing_command')
def handle_typing_command(data):
    room = data.get('code')
    emit('typing_command', data, room=room, include_self=False)

@socketio.on('typing_progress')
def handle_typing_progress(data):
    room = data.get('code')
    emit('typing_progress', data, room=room, include_self=False)

@socketio.on('disconnect')
def test_disconnect():
    for room, state in rooms.items():
        if state['sender'] or state['receiver']:
            # For strict privacy, we don't hold states long term. Just emit drops.
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    socketio.run(app, host='0.0.0.0', port=port)
