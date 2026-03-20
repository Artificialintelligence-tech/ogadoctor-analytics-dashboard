"""
OgaDoctor - Twilio Video Integration
====================================
Creates anonymous video rooms for secure consultations
No phone numbers exposed between doctor and patient
"""

from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
import os
from datetime import datetime, timedelta

class TwilioVideoManager:
    """Manages Twilio Video rooms and access tokens"""
    
    def __init__(self, account_sid, auth_token, api_key_sid, api_key_secret):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.api_key_sid = api_key_sid
        self.api_key_secret = api_key_secret
        self.client = Client(account_sid, auth_token)
    
    def create_room(self, consultation_id):
        """
        Create a unique video room for a consultation
        Returns: room SID and room name
        """
        room_name = f"consultation-{consultation_id}"
        
        try:
            # Create room with specific settings
            room = self.client.video.v1.rooms.create(
                unique_name=room_name,
                type='group',  # Allows multiple participants
                max_participants=2,  # Doctor + Patient only
                record_participants_on_connect=False,  # Privacy: no auto-recording
                status_callback_method='POST'
            )
            
            return {
                'room_sid': room.sid,
                'room_name': room.unique_name,
                'status': room.status
            }
        
        except Exception as e:
            # Room might already exist
            rooms = self.client.video.v1.rooms.list(unique_name=room_name, limit=1)
            if rooms:
                return {
                    'room_sid': rooms[0].sid,
                    'room_name': rooms[0].unique_name,
                    'status': rooms[0].status
                }
            raise e
    
    def generate_access_token(self, room_name, identity, duration_hours=1):
        """
        Generate access token for a participant
        
        Args:
            room_name: Unique room identifier
            identity: Participant name (e.g., "Dr. Smith" or "Patient")
            duration_hours: Token validity duration
        
        Returns: Access token string
        """
        # Create access token
        token = AccessToken(
            self.account_sid,
            self.api_key_sid,
            self.api_key_secret,
            identity=identity,
            ttl=duration_hours * 3600  # Convert to seconds
        )
        
        # Grant video access to this room
        video_grant = VideoGrant(room=room_name)
        token.add_grant(video_grant)
        
        return token.to_jwt()
    
    def end_room(self, room_sid):
        """End a video room (disconnects all participants)"""
        try:
            room = self.client.video.v1.rooms(room_sid).update(status='completed')
            return {'status': 'completed', 'room_sid': room.sid}
        except Exception as e:
            return {'error': str(e)}
    
    def get_room_participants(self, room_sid):
        """Get list of participants currently in a room"""
        try:
            participants = self.client.video.v1.rooms(room_sid).participants.list()
            return [
                {
                    'identity': p.identity,
                    'status': p.status,
                    'duration': p.duration
                }
                for p in participants
            ]
        except Exception as e:
            return {'error': str(e)}


# Streamlit component for embedding video
def render_video_interface(access_token, room_name):
    """
    Renders Twilio Video interface in Streamlit
    Returns HTML/JavaScript code for embedding
    """
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OgaDoctor Video Consultation</title>
        <script src="https://sdk.twilio.com/js/video/releases/2.27.0/twilio-video.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: #1a1a1a;
            }}
            
            #video-container {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                padding: 10px;
                height: 100vh;
                max-height: 600px;
            }}
            
            .video-participant {{
                background: #000;
                border-radius: 10px;
                overflow: hidden;
                position: relative;
            }}
            
            video {{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}
            
            .participant-name {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 14px;
            }}
            
            #controls {{
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                gap: 10px;
                z-index: 1000;
            }}
            
            .control-btn {{
                padding: 12px 24px;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            
            .btn-mute {{
                background: #4CAF50;
                color: white;
            }}
            
            .btn-mute.muted {{
                background: #f44336;
            }}
            
            .btn-video {{
                background: #2196F3;
                color: white;
            }}
            
            .btn-video.off {{
                background: #f44336;
            }}
            
            .btn-end {{
                background: #f44336;
                color: white;
            }}
            
            #status {{
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(76, 175, 80, 0.9);
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 1000;
            }}
        </style>
    </head>
    <body>
        <div id="status">Connecting to video room...</div>
        <div id="video-container">
            <div id="local-media" class="video-participant">
                <div class="participant-name">You</div>
            </div>
            <div id="remote-media" class="video-participant">
                <div class="participant-name">Waiting for other participant...</div>
            </div>
        </div>
        
        <div id="controls">
            <button id="btn-mute-audio" class="control-btn btn-mute">🎤 Mute</button>
            <button id="btn-mute-video" class="control-btn btn-video">📹 Camera Off</button>
            <button id="btn-disconnect" class="control-btn btn-end">End Call</button>
        </div>
        
        <script>
            const Video = Twilio.Video;
            const token = '{access_token}';
            const roomName = '{room_name}';
            
            let activeRoom;
            let localAudioTrack;
            let localVideoTrack;
            
            // Connect to the room
            Video.connect(token, {{
                name: roomName,
                audio: true,
                video: {{ width: 640, height: 480 }}
            }}).then(room => {{
                console.log('Connected to Room:', room.name);
                activeRoom = room;
                
                // Update status
                document.getElementById('status').textContent = '🟢 Connected';
                
                // Attach local participant's tracks
                const localParticipant = room.localParticipant;
                localParticipant.tracks.forEach(publication => {{
                    if (publication.track) {{
                        document.getElementById('local-media').appendChild(publication.track.attach());
                        
                        if (publication.track.kind === 'audio') {{
                            localAudioTrack = publication.track;
                        }} else if (publication.track.kind === 'video') {{
                            localVideoTrack = publication.track;
                        }}
                    }}
                }});
                
                // Handle remote participants
                room.participants.forEach(participantConnected);
                room.on('participantConnected', participantConnected);
                room.on('participantDisconnected', participantDisconnected);
                
                // Handle disconnection
                room.on('disconnected', () => {{
                    document.getElementById('status').textContent = 'Call ended';
                    document.getElementById('status').style.background = 'rgba(244, 67, 54, 0.9)';
                }});
                
            }}).catch(error => {{
                console.error('Error connecting to room:', error);
                document.getElementById('status').textContent = 'Connection failed: ' + error.message;
                document.getElementById('status').style.background = 'rgba(244, 67, 54, 0.9)';
            }});
            
            // Participant connected
            function participantConnected(participant) {{
                console.log('Participant connected:', participant.identity);
                
                const div = document.getElementById('remote-media');
                div.querySelector('.participant-name').textContent = participant.identity;
                
                participant.tracks.forEach(publication => {{
                    if (publication.isSubscribed) {{
                        div.appendChild(publication.track.attach());
                    }}
                }});
                
                participant.on('trackSubscribed', track => {{
                    div.appendChild(track.attach());
                }});
            }}
            
            // Participant disconnected
            function participantDisconnected(participant) {{
                console.log('Participant disconnected:', participant.identity);
                document.getElementById('remote-media').innerHTML = 
                    '<div class="participant-name">Participant left</div>';
            }}
            
            // Control buttons
            document.getElementById('btn-mute-audio').addEventListener('click', function() {{
                if (localAudioTrack) {{
                    if (localAudioTrack.isEnabled) {{
                        localAudioTrack.disable();
                        this.textContent = '🎤 Unmute';
                        this.classList.add('muted');
                    }} else {{
                        localAudioTrack.enable();
                        this.textContent = '🎤 Mute';
                        this.classList.remove('muted');
                    }}
                }}
            }});
            
            document.getElementById('btn-mute-video').addEventListener('click', function() {{
                if (localVideoTrack) {{
                    if (localVideoTrack.isEnabled) {{
                        localVideoTrack.disable();
                        this.textContent = '📹 Camera On';
                        this.classList.add('off');
                    }} else {{
                        localVideoTrack.enable();
                        this.textContent = '📹 Camera Off';
                        this.classList.remove('off');
                    }}
                }}
            }});
            
            document.getElementById('btn-disconnect').addEventListener('click', function() {{
                if (activeRoom) {{
                    activeRoom.disconnect();
                    window.parent.postMessage('call_ended', '*');
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html_code
