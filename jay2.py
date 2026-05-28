from flask import Flask, render_template_string, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
import random
import sqlite3
import hashlib
import re
from datetime import datetime
import json

# ------------------------------------------------------------
#  HTML/CSS/JS with BOTH 1-on-1 AND Group Voice/Video Calls
#  Keep all original features + add group calls
# ------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes, viewport-fit=cover">
    <title>SIMU-BLOCK | Voice & Video Calls</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif;
            color: #f0f3ff;
            min-height: 100vh;
            line-height: 1.5;
        }
        .glass-card {
            background: rgba(20, 20, 45, 0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 243, 255, 0.2);
            border-radius: 28px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        .glass-card:hover { border-color: #00f3ff; box-shadow: 0 8px 32px rgba(0, 243, 255, 0.2); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade { animation: fadeIn 0.4s ease; }
        .input-field {
            background: rgba(10, 10, 26, 0.7);
            border: 1px solid rgba(0, 243, 255, 0.4);
            border-radius: 40px;
            padding: 12px 18px;
            color: white;
            width: 100%;
            outline: none;
            font-size: 1rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #00f3ff, #9d4edd);
            border: none;
            border-radius: 40px;
            padding: 12px 24px;
            font-weight: 700;
            color: #0a0a1a;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            font-size: 1rem;
            min-height: 48px;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,243,255,0.4); }
        .btn-secondary {
            background: transparent;
            border: 1px solid #00f3ff;
            border-radius: 40px;
            padding: 8px 20px;
            color: #00f3ff;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            min-height: 44px;
        }
        .btn-secondary:hover { background: rgba(0,243,255,0.2); }
        .btn-danger {
            background: transparent;
            border: 1px solid #ff4d9e;
            border-radius: 40px;
            padding: 8px 20px;
            color: #ff4d9e;
            font-weight: 600;
            cursor: pointer;
        }
        .tabs-container {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
            margin: 24px auto 0;
            padding: 0 16px;
        }
        .tab-btn {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(5px);
            color: #ccd6f6;
            border: 1px solid rgba(0, 243, 255, 0.3);
            border-radius: 60px;
            padding: 8px 20px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            font-size: 0.9rem;
            white-space: nowrap;
        }
        .tab-btn:hover { background: rgba(0, 243, 255, 0.2); border-color: #00f3ff; }
        .active-tab {
            background: linear-gradient(135deg, #00f3ff, #9d4edd);
            color: #0a0a1a;
            border: none;
            box-shadow: 0 4px 12px rgba(0, 243, 255, 0.4);
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 32px;
        }
        @media (max-width: 1024px) { .dashboard-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 640px) { .dashboard-grid { grid-template-columns: 1fr; } }
        .sms-layout {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 24px;
        }
        @media (max-width: 768px) { .sms-layout { grid-template-columns: 1fr; } }
        .user-item {
            padding: 12px;
            border-radius: 20px;
            margin-bottom: 8px;
            background: rgba(255, 255, 255, 0.03);
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            gap: 12px;
            flex-wrap: wrap;
        }
        .user-item span { font-weight: 500; word-break: break-word; }
        .call-btn {
            background: #00f3ff22;
            border: 1px solid #00f3ff;
            border-radius: 40px;
            padding: 8px 16px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
            min-height: 38px;
        }
        .video-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 20px;
            justify-content: center;
        }
        .video-box {
            flex: 1;
            min-width: 240px;
            background: #0a0a1e;
            border-radius: 28px;
            overflow: hidden;
            position: relative;
            border: 2px solid rgba(0, 243, 255, 0.5);
            box-shadow: 0 12px 28px rgba(0,0,0,0.5);
        }
        .video-box video { width: 100%; background: #000; display: block; }
        .local-video video { transform: scaleX(-1); }
        .video-label {
            position: absolute;
            bottom: 12px;
            left: 12px;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(4px);
            padding: 4px 12px;
            border-radius: 30px;
            font-size: 0.75rem;
            font-weight: bold;
            color: #00f3ff;
        }
        .call-controls {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .control-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(0,243,255,0.5);
            border-radius: 60px;
            padding: 10px 18px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            transition: all 0.2s;
            font-size: 0.9rem;
            min-height: 48px;
        }
        .control-btn.danger { border-color: #ff4d9e; color: #ff4d9e; }
        .call-window {
            background: rgba(0,0,0,0.6);
            border-radius: 32px;
            padding: 20px;
            margin-top: 20px;
        }
        .message-bubble {
            border-radius: 22px;
            padding: 10px 18px;
            margin-bottom: 12px;
            max-width: 85%;
            word-wrap: break-word;
            cursor: pointer;
        }
        .my-message {
            background: linear-gradient(135deg, #00f3ff, #9d4edd);
            color: #0a0a1a;
            margin-left: auto;
        }
        .other-message {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(0, 243, 255, 0.3);
            margin-right: auto;
        }
        .blocked-message-item {
            background: rgba(255, 77, 158, 0.15);
            border-left: 4px solid #ff4d9e;
            padding: 12px;
            border-radius: 16px;
            margin-bottom: 12px;
        }
        .risk-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .risk-fill { flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 20px; overflow: hidden; }
        .risk-fill div { height: 100%; border-radius: 20px; transition: width 0.3s; }
        .badge {
            background: #ff4d9e;
            color: white;
            border-radius: 40px;
            padding: 4px 14px;
            font-size: 0.75rem;
        }
        .incoming-box {
            margin-bottom: 20px;
            padding: 18px;
            background: #ff4d9e22;
            border-radius: 28px;
            text-align: center;
        }
        .table-responsive { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 8px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        @media (max-width: 640px) { th, td { padding: 8px 4px; font-size: 0.75rem; } }
        .main-container { max-width: 1400px; margin: 0 auto; padding: 20px 20px 40px; }
        .header-container { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
        .warning-message {
            background: #ff4d9e33;
            border-left: 4px solid #ff4d9e;
            padding: 10px;
            border-radius: 12px;
            margin-top: 8px;
            font-size: 0.85rem;
        }
        .notification-perm-btn {
            background: rgba(0,243,255,0.2);
            border: 1px solid #00f3ff;
            border-radius: 40px;
            padding: 6px 14px;
            font-size: 0.75rem;
            cursor: pointer;
        }
        .room-item {
            padding: 12px;
            margin: 8px 0;
            background: rgba(0,243,255,0.1);
            border-radius: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .participant-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
            padding: 10px;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
        }
        .participant {
            padding: 5px 12px;
            background: rgba(0,243,255,0.2);
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .create-room-form {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .group-video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
            max-height: 500px;
            overflow-y: auto;
        }
        .group-video-box {
            background: #0a0a1e;
            border-radius: 16px;
            overflow: hidden;
            position: relative;
            border: 1px solid rgba(0,243,255,0.3);
            aspect-ratio: 4/3;
        }
        .group-video-box video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .hidden { display: none; }
        .flex { display: flex; gap: 10px; align-items: center; }
        .message-actions { margin-top: 8px; gap: 8px; }
        @keyframes fadeInOut {
            0% { opacity: 0; transform: translateX(-50%) translateY(20px); }
            15% { opacity: 1; transform: translateX(-50%) translateY(0); }
            85% { opacity: 1; transform: translateX(-50%) translateY(0); }
            100% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
        }
        .toast-notification {
            animation: fadeInOut 2s ease;
        }
    </style>
</head>
<body>
<div id="app">
    <!-- Login / Register screen -->
    <div id="auth-screen" style="min-height:100vh; display:flex; align-items:center; justify-content:center; padding:20px;">
        <div class="glass-card" style="width:100%; max-width:460px; padding:32px 24px; text-align:center;">
            <div style="width:70px; height:70px; background:linear-gradient(135deg,#00f3ff,#ff4d9e); border-radius:24px; display:inline-flex; align-items:center; justify-content:center; font-size:40px; margin-bottom:20px;">🛡️</div>
            <h2 style="font-size:clamp(1.6rem, 6vw, 2.2rem);">SIMU-BLOCK</h2>
            <p style="color:#a0b0d0; margin-bottom:24px;"></p>
            <div id="login-form">
                <input type="text" id="login-username" class="input-field" placeholder="Username" style="margin-bottom:16px;">
                <input type="password" id="login-password" class="input-field" placeholder="Password" style="margin-bottom:24px;">
                <button id="do-login" class="btn-primary" style="width:100%;">Login</button>
                <p style="margin-top:20px;"><a href="#" id="show-register" style="color:#ff4d9e;">Create account</a></p>
            </div>
            <div id="register-form" style="display:none;">
                <input type="text" id="reg-username" class="input-field" placeholder="Username" style="margin-bottom:12px;">
                <input type="password" id="reg-password" class="input-field" placeholder="Password" style="margin-bottom:12px;">
                <input type="text" id="reg-phone" class="input-field" placeholder="Phone (optional)" style="margin-bottom:24px;">
                <button id="do-register" class="btn-primary" style="width:100%;">Register</button>
                <p style="margin-top:20px;"><a href="#" id="show-login" style="color:#ff4d9e;">Back to Login</a></p>
            </div>
            <div id="auth-message" style="margin-top:20px; font-size:0.85rem;"></div>
        </div>
    </div>

    <!-- Main App -->
    <div id="main-app" style="display:none;">
        <div style="background: rgba(15, 12, 41, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(0,243,255,0.3); padding:0 20px; position:sticky; top:0; z-index:100;">
            <div class="header-container" style="max-width:1400px; margin:0 auto; height:auto; min-height:70px;">
                <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
                    <div style="width:44px; height:44px; background:linear-gradient(135deg,#00f3ff,#ff4d9e); border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:26px;">🛡️</div>
                    <div><div style="font-weight:800; font-size:clamp(1.2rem, 5vw, 1.6rem);">SIMU-BLOCK</div><div style="font-size:0.7rem; color:#a0b0d0;">ALL CALLS ACTIVE</div></div>
                </div>
                <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
                    <span id="user-name" style="color:#00f3ff; font-weight:600;"></span>
                    <button id="enable-notifications" class="notification-perm-btn">🔔 Enable Notifications</button>
                    <button id="logout-btn" class="btn-secondary">Logout</button>
                </div>
            </div>
        </div>

        <div class="tabs-container">
            <button data-tab="dashboard" class="tab-btn active-tab">📊 Dashboard</button>
            <button data-tab="sms" class="tab-btn">💬 SMS</button>
            <button data-tab="blocked" class="tab-btn">🚫 Blocked</button>
            <button data-tab="voice" class="tab-btn">🎙️ voice call</button>
            <button data-tab="video" class="tab-btn">📹 Video call</button>
            <button data-tab="groupvoice" class="tab-btn">👥 Group Voice</button>
            <button data-tab="groupvideo" class="tab-btn">🎥 Group Video</button>
            <button data-tab="features" class="tab-btn">🛡️ Features</button>
            <button data-tab="scanner" class="tab-btn">🔍 Scanner</button>
            <button data-tab="about" class="tab-btn">ℹ️ About</button>
        </div>

        <div class="main-container">
            <!-- Dashboard -->
            <div id="dashboard-tab" class="tab-content animate-fade">
                <div class="glass-card" style="padding:32px 24px; margin-bottom:28px; text-align:center;">
                    <div style="font-size:0.75rem; color:#ff4d9e;">LIVE PROTECTION DASHBOARD</div>
                    <h1 style="font-size:clamp(1.8rem, 7vw, 2.8rem);">Voice/Video Security + Group Calls</h1>
                    <div style="margin-top:16px;"><span class="badge">🟢 System Active</span></div>
                </div>
                <div class="dashboard-grid">
                    <div class="glass-card" style="border-top:3px solid #ff4d9e; padding:24px 20px; text-align:center;"><div style="font-size:2.2rem;">🛡️</div><div style="font-size:clamp(1.8rem, 5vw, 2.4rem); font-weight:800; color:#ff4d9e;" id="threat-count">0</div><div>Threats Blocked</div></div>
                    <div class="glass-card" style="border-top:3px solid #00f3ff; padding:24px 20px; text-align:center;"><div style="font-size:2.2rem;">👥</div><div style="font-size:clamp(1.8rem, 5vw, 2.4rem); font-weight:800; color:#00f3ff;" id="active-rooms">0</div><div>Active Rooms</div></div>
                    <div class="glass-card" style="border-top:3px solid #9d4edd; padding:24px 20px; text-align:center;"><div style="font-size:2.2rem;">📩</div><div style="font-size:clamp(1.8rem, 5vw, 2.4rem); font-weight:800; color:#9d4edd;" id="sms-block-count">0</div><div>SMS Blocked</div></div>
                    <div class="glass-card" style="border-top:3px solid #00ff88; padding:24px 20px; text-align:center;"><div style="font-size:2.2rem;">👥</div><div style="font-size:clamp(1.8rem, 5vw, 2.4rem); font-weight:800; color:#00ff88;" id="total-participants">0</div><div>In Calls Now</div></div>
                </div>
                <div class="glass-card">
                    <div style="padding:18px 20px; border-bottom:1px solid rgba(0,243,255,0.2);"><span style="font-weight:700;">Live Threat Log</span></div>
                    <div class="table-responsive" style="padding:16px;"><table id="threat-table"><tbody></tbody></table></div>
                </div>
            </div>

            <!-- SMS Tab -->
            <div id="sms-tab" class="tab-content" style="display:none;">
                <div class="sms-layout">
                    <div id="sms-users-container" class="glass-card" style="padding:20px;">
                        <h3>Users</h3>
                        <div id="user-list-sms"></div>
                    </div>
                    <div id="sms-chat-container" class="glass-card" style="padding:20px; display:none;">
                        <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px; flex-wrap:wrap;">
                            <button id="back-to-users" class="btn-secondary" style="padding:6px 14px;">← Back</button>
                            <h3 id="chat-header" style="margin:0;">Chat</h3>
                        </div>
                        <div id="chat-messages" style="height:350px; overflow-y:auto; margin:16px 0;"></div>
                        <div style="display:flex; gap:12px; flex-wrap:wrap;">
                            <input id="message-input" class="input-field" placeholder="Type SMS..." disabled>
                            <button id="send-sms" class="btn-primary" disabled>Send</button>
                        </div>
                        <div id="sms-warning" class="warning-message" style="display:none;"></div>
                    </div>
                </div>
            </div>

            <!-- Blocked Messages Tab -->
            <div id="blocked-tab" class="tab-content" style="display:none;">
                <div class="glass-card" style="padding:28px;">
                    <h2>🚫 Blocked Messages</h2>
                    <p style="margin-bottom:20px;">Messages that were blocked because they contained suspicious content.</p>
                    <div id="blocked-list" style="max-height:500px; overflow-y:auto;"></div>
                </div>
            </div>

            <!-- 1-on-1 Voice Call Tab -->
            <div id="voice-tab" class="tab-content" style="display:none;">
                <div class="glass-card" style="padding:28px;">
                    <h2>🎙️ Voice Calls</h2>
                    <p style="margin-bottom:20px;"></p>
                    <div id="user-list-voice" style="max-height:280px; overflow-y:auto; margin-bottom:24px;"></div>
                    <div id="voice-incoming" class="incoming-box" style="display:none;">
                        <div>📞 Incoming voice call from <strong id="voice-caller-name"></strong></div>
                        <div style="margin-top:14px;"><button id="voice-accept" class="btn-primary" style="margin-right:12px;">Accept</button><button id="voice-reject" class="btn-secondary">Reject</button></div>
                    </div>
                    <div id="voice-active" style="display:none; margin-top:20px; padding:18px; background:#00ff8822; border-radius:28px; text-align:center;">
                        <div>🔴 Voice call with <strong id="voice-partner"></strong></div>
                        <div class="call-controls"><button id="voice-mute" class="control-btn">🎤 Mute</button><button id="voice-end" class="control-btn danger">🔴 End Call</button></div>
                    </div>
                    <div id="voice-status" class="call-status"></div>
                </div>
            </div>

            <!-- 1-on-1 Video Call Tab -->
            <div id="video-tab" class="tab-content" style="display:none;">
                <div class="glass-card" style="padding:28px;">
                    <h2>📹 Video Calls</h2>
                    <p style="margin-bottom:20px;"></p>
                    <div id="user-list-video" style="max-height:280px; overflow-y:auto; margin-bottom:24px;"></div>
                    <div id="video-incoming" class="incoming-box" style="display:none;">
                        <div>📹 Incoming video call from <strong id="video-caller-name"></strong></div>
                        <div style="margin-top:14px;"><button id="video-accept" class="btn-primary" style="margin-right:12px;">Accept</button><button id="video-reject" class="btn-secondary">Reject</button></div>
                    </div>
                    <div id="video-active-window" style="display:none;">
                        <div class="call-window">
                            <div class="video-container">
                                <div class="video-box local-video"><video id="localVideo" autoplay muted playsinline></video><div class="video-label">You</div></div>
                                <div class="video-box remote-video"><video id="remoteVideo" autoplay playsinline></video><div class="video-label" id="remoteLabel">Remote</div></div>
                            </div>
                            <div class="call-controls">
                                <button id="video-toggleMic" class="control-btn">🎤 Mute</button>
                                <button id="video-toggleCam" class="control-btn">📷 Camera Off</button>
                                <button id="video-shareScreen" class="control-btn">🖥️ Share Screen</button>
                                <button id="video-endCall" class="control-btn danger">🔴 End Call</button>
                            </div>
                        </div>
                    </div>
                    <div id="video-status" class="call-status"></div>
                </div>
            </div>

            <!-- GROUP VOICE CALL TAB -->
            <div id="groupvoice-tab" class="tab-content" style="display:none;">
                <div class="glass-card" style="padding:28px;">
                    <h2>👥 Group Voice Rooms</h2>
                    <p style="margin-bottom:20px;"></p>
                    
                    <div class="create-room-form">
                        <input type="text" id="voice-room-name" class="input-field" placeholder="Room name (e.g., 'Team Meeting')">
                        <button id="create-voice-room" class="btn-primary">➕ Create & Join</button>
                    </div>
                    
                    <h3>Available Voice Rooms</h3>
                    <div id="voice-rooms-list"></div>
                    
                    <div id="active-voice-room" style="display:none; margin-top:20px;">
                        <div style="background:#00ff8822; border-radius:20px; padding:15px;">
                            <div class="flex" style="justify-content:space-between;">
                                <h3>🔊 Room: <span id="current-voice-room"></span></h3>
                                <button id="leave-voice-room" class="btn-danger">🚪 Leave Room</button>
                            </div>
                            <div id="voice-participants" class="participant-list"></div>
                            <div class="call-controls">
                                <button id="voice-room-mute" class="control-btn">🎤 Mute</button>
                            </div>
                            <div id="voice-room-status" style="margin-top:10px; color:#00ff88;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- GROUP VIDEO CALL TAB -->
            <div id="groupvideo-tab" class="tab-content" style="display:none;">
                <div class="glass-card" style="padding:28px;">
                    <h2>🎥 Group Video Rooms</h2>
                    <p style="margin-bottom:20px;"></p>
                    
                    <div class="create-room-form">
                        <input type="text" id="video-room-name" class="input-field" placeholder="Video room name">
                        <button id="create-video-room" class="btn-primary">🎥 Create & Join</button>
                    </div>
                    
                    <h3>Available Video Rooms</h3>
                    <div id="video-rooms-list"></div>
                    
                    <div id="active-video-room" style="display:none; margin-top:20px;">
                        <div style="background:#00ff8822; border-radius:20px; padding:15px;">
                            <div class="flex" style="justify-content:space-between;">
                                <h3>📹 Room: <span id="current-video-room"></span></h3>
                                <button id="leave-video-room" class="btn-danger">🚪 Leave Room</button>
                            </div>
                            <div id="video-participants" class="participant-list"></div>
                            <div class="group-video-grid" id="group-video-grid"></div>
                            <div class="call-controls">
                                <button id="video-room-mute" class="control-btn">🎤 Mute</button>
                                <button id="video-room-cam" class="control-btn">📷 Camera Off</button>
                            </div>
                            <div id="video-room-status" style="margin-top:10px; color:#00ff88;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="features-tab" class="tab-content" style="display:none;"><div class="glass-card" style="padding:28px;"><h2>Security Features</h2><div id="features-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(150px,1fr)); gap:20px;"></div></div></div>
            <div id="scanner-tab" class="tab-content" style="display:none;"><div class="glass-card" style="padding:28px;"><h2>Live Scanner</h2><input id="scan-input" class="input-field" placeholder="Enter number/URL"><button id="scan-btn" class="btn-primary" style="margin-top:16px;">Scan</button><div id="scan-result"></div></div></div>
            <div id="about-tab" class="tab-content" style="display:none;"><div class="glass-card" style="padding:28px; text-align:center;"><h2>SIMU-BLOCK | Team GAJJ</h2><p>1-on-1 & Group Voice/Video Calls + Anti‑Fraud for Tanzania</p><p>Secure group conversations with threat detection</p></div></div>
        </div>
    </div>
</div>

<script>
    // ==================== GLOBALS ====================
    let socket = null;
    let currentUser = null;
    let activeChat = null;
    let notificationsEnabled = false;
    
    // 1-on-1 Voice call globals
    let voiceStream = null;
    let voicePeer = null;
    let voiceCallWith = null;
    let pendingVoiceFrom = null;
    let pendingVoiceOffer = null;
    
    // 1-on-1 Video call globals
    let videoStream = null;
    let videoPeer = null;
    let videoCallWith = null;
    let pendingVideoFrom = null;
    let pendingVideoOffer = null;
    let isScreenSharing = false;
    let originalVideoStream = null;
    
    // Group Voice globals
    let currentVoiceRoom = null;
    let groupVoiceStream = null;
    let voiceRoomPeers = new Map();
    
    // Group Video globals
    let currentVideoRoom = null;
    let groupVideoStream = null;
    let videoRoomPeers = new Map();
    
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');
    
    let currentThreats = [
        { id:1, type:"CALL", number:"+255 712 XXX 001", status:"BLOCKED", risk:98, time:"09:42", reason:"M-Pesa scam" },
        { id:2, type:"SMS", number:"+255 768 XXX 220", status:"FLAGGED", risk:84, time:"10:15", reason:"Tuma pesa haraka" }
    ];
    
    const pcConfig = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'turn:openrelay.metered.ca:80', username: 'openrelayproject', credential: 'openrelayproject' },
            { urls: 'turn:openrelay.metered.ca:443', username: 'openrelayproject', credential: 'openrelayproject' }
        ]
    };
    
    // ========== Helper Functions ==========
    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }
    
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.innerHTML = message;
        toast.style.cssText = `position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0, 243, 255, 0.9); color: #0a0a1a; padding: 12px 24px; border-radius: 40px; font-weight: bold; z-index: 9999; animation: fadeInOut 2s ease; backdrop-filter: blur(10px);`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }
    
    // ========== Notification Helpers ==========
    function requestNotificationPermission() {
        if (!("Notification" in window)) {
            alert("This browser does not support desktop notifications");
            return;
        }
        Notification.requestPermission().then(perm => {
            notificationsEnabled = (perm === "granted");
            if (notificationsEnabled) {
                document.getElementById("enable-notifications").innerText = "🔔 Notifications On";
            } else {
                document.getElementById("enable-notifications").innerText = "🔕 Notifications Blocked";
            }
        });
    }
    
    function showNotification(title, body, tag = null) {
        if (!notificationsEnabled) return;
        const options = { body, silent: false };
        if (tag) options.tag = tag;
        new Notification(title, options);
    }
    
    // ========== Auth & Main Setup ==========
    function showAuthMsg(msg, isError=true) {
        const el = document.getElementById('auth-message');
        el.innerText = msg;
        el.style.color = isError ? '#ff4d9e' : '#00ff88';
        setTimeout(() => el.innerText = '', 3000);
    }
    
    document.getElementById('do-register').onclick = async () => {
        const username = document.getElementById('reg-username').value.trim();
        const password = document.getElementById('reg-password').value;
        const phone = document.getElementById('reg-phone').value.trim();
        if (!username || !password) { showAuthMsg('Username and password required'); return; }
        const res = await fetch('/api/register', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username, password, phone}) });
        const data = await res.json();
        if (data.success) { showAuthMsg('Registered! Please login.', false); document.getElementById('show-login').click(); }
        else showAuthMsg(data.error);
    };
    
    document.getElementById('do-login').onclick = async () => {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        if (!username || !password) { showAuthMsg('Enter username and password'); return; }
        const res = await fetch('/api/login', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username, password}) });
        const data = await res.json();
        if (data.success) {
            currentUser = data.user;
            document.getElementById('user-name').innerText = currentUser.username;
            initMainApp();
        } else showAuthMsg(data.error);
    };
    
    document.getElementById('show-register').onclick = (e) => { e.preventDefault(); document.getElementById('login-form').style.display='none'; document.getElementById('register-form').style.display='block'; };
    document.getElementById('show-login').onclick = (e) => { e.preventDefault(); document.getElementById('register-form').style.display='none'; document.getElementById('login-form').style.display='block'; };
    
    document.getElementById('logout-btn').onclick = async () => {
        await fetch('/api/logout', { method:'POST' });
        if (socket) socket.disconnect();
        if (voiceStream) voiceStream.getTracks().forEach(t => t.stop());
        if (videoStream) videoStream.getTracks().forEach(t => t.stop());
        if (voicePeer) voicePeer.close();
        if (videoPeer) videoPeer.close();
        leaveVoiceRoom();
        leaveVideoRoom();
        document.getElementById('auth-screen').style.display = 'flex';
        document.getElementById('main-app').style.display = 'none';
        currentUser = null;
    };
    document.getElementById('enable-notifications').onclick = requestNotificationPermission;
    
    function renderThreatTable() {
        const tbody = document.querySelector('#threat-table tbody');
        if(!tbody) return;
        tbody.innerHTML = currentThreats.map(t => `
            <tr>
                <td>${t.type}</td>
                <td>${t.number}</td>
                <td style="color:${t.status==='BLOCKED'?'#ff4d9e':t.status==='FLAGGED'?'orange':'#00ff88'}">${t.status}</td>
                <td><div class="risk-bar"><div class="risk-fill"><div style="width:${t.risk}%; height:100%; background:${t.risk>80?'#ff4d9e':t.risk>50?'orange':'#00ff88'}"></div></div><span>${t.risk}%</span></div></td>
                <td>${t.time}</td>
                <td>${t.reason}</td>
            </tr>
        `).join('');
        document.getElementById('threat-count').innerText = currentThreats.length.toLocaleString();
    }
    
    function addThreat(threat) {
        currentThreats.unshift({ ...threat, time: new Date().toLocaleTimeString() });
        if(currentThreats.length>12) currentThreats.pop();
        renderThreatTable();
    }
    
    // ========== SMS Functions ==========
    async function loadUsersForSMS() {
        const res = await fetch('/api/users');
        const users = await res.json();
        const listDiv = document.getElementById('user-list-sms');
        listDiv.innerHTML = users.filter(u=>u.username !== currentUser.username).map(u => `<div class="user-item" data-username="${u.username}"><span>${u.username}</span></div>`).join('');
        document.querySelectorAll('#user-list-sms .user-item').forEach(el => {
            el.onclick = () => openChatForUser(el.getAttribute('data-username'));
        });
    }
    
    function openChatForUser(username) {
        activeChat = username;
        document.getElementById('chat-header').innerText = `Chat with ${activeChat}`;
        document.getElementById('message-input').disabled = false;
        document.getElementById('send-sms').disabled = false;
        document.getElementById('sms-warning').style.display = 'none';
        loadChatHistory(activeChat);
        document.getElementById('sms-users-container').style.display = 'none';
        document.getElementById('sms-chat-container').style.display = 'block';
    }
    
    function closeChatAndShowUsers() {
        activeChat = null;
        document.getElementById('message-input').disabled = true;
        document.getElementById('send-sms').disabled = true;
        document.getElementById('chat-messages').innerHTML = '';
        document.getElementById('chat-header').innerText = 'Select a user';
        document.getElementById('sms-warning').style.display = 'none';
        document.getElementById('sms-users-container').style.display = 'block';
        document.getElementById('sms-chat-container').style.display = 'none';
    }
    
    async function loadChatHistory(withUser) {
        const res = await fetch(`/api/messages/${withUser}`);
        const msgs = await res.json();
        const container = document.getElementById('chat-messages');
        container.innerHTML = '';
        msgs.forEach(msg => {
            const div = document.createElement('div');
            div.className = `message-bubble ${msg.from_username === currentUser.username ? 'my-message' : 'other-message'}`;
            div.innerHTML = `<strong>${msg.from_username}:</strong> ${msg.content}<br><small>${msg.timestamp}</small>`;
            container.appendChild(div);
        });
        container.scrollTop = container.scrollHeight;
    }
    
    function appendMessage(msg, type) {
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = `message-bubble ${type === 'sent' ? 'my-message' : 'other-message'}`;
        div.innerHTML = `<strong>${msg.from}:</strong> ${msg.content}<br><small>${msg.timestamp || new Date().toLocaleTimeString()}</small>`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
    
    function showSmsWarning(message) {
        const warnDiv = document.getElementById('sms-warning');
        warnDiv.innerText = message;
        warnDiv.style.display = 'block';
        setTimeout(() => { warnDiv.style.display = 'none'; }, 4000);
    }
    
    async function loadBlockedMessages() {
        const res = await fetch('/api/blocked');
        const blocked = await res.json();
        const container = document.getElementById('blocked-list');
        if (blocked.length === 0) {
            container.innerHTML = '<div class="glass-card" style="padding:20px; text-align:center;">No blocked messages.</div>';
            return;
        }
        container.innerHTML = blocked.map(b => `
            <div class="blocked-message-item">
                <div><strong>From:</strong> ${escapeHtml(b.from_username)}</div>
                <div><strong>Content:</strong> ${escapeHtml(b.content)}</div>
                <div><strong>Reason:</strong> ${b.reason}</div>
                <div><small>${b.timestamp}</small></div>
            </div>
        `).join('');
    }
    
    // ========== 1-on-1 Voice Call ==========
    async function startVoiceCall(target) {
        if (voiceCallWith) { document.getElementById('voice-status').innerText = 'Already in a call.'; return; }
        document.getElementById('voice-status').innerText = `Calling ${target}...`;
        try { voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true }); } catch(e) { document.getElementById('voice-status').innerText = 'Microphone access denied.'; return; }
        voiceCallWith = target;
        voicePeer = new RTCPeerConnection(pcConfig);
        voiceStream.getTracks().forEach(t => voicePeer.addTrack(t, voiceStream));
        voicePeer.ontrack = (event) => { const audio = new Audio(); audio.srcObject = event.streams[0]; audio.autoplay = true; document.getElementById('voice-status').innerHTML = '🔊 Voice call connected.'; };
        voicePeer.onicecandidate = (e) => { if(e.candidate) socket.emit('voice_ice', { to: target, candidate: e.candidate }); };
        voicePeer.oniceconnectionstatechange = () => { if(voicePeer?.iceConnectionState === 'disconnected') endVoiceCall(); };
        const offer = await voicePeer.createOffer();
        await voicePeer.setLocalDescription(offer);
        socket.emit('voice_offer', { to: target, offer });
        document.getElementById('voice-active').style.display = 'block';
        document.getElementById('voice-partner').innerText = target;
    }
    
    async function acceptVoiceCall() {
        if (!pendingVoiceFrom || !pendingVoiceOffer) return;
        const from = pendingVoiceFrom, offer = pendingVoiceOffer;
        pendingVoiceFrom = null; pendingVoiceOffer = null;
        document.getElementById('voice-incoming').style.display = 'none';
        document.getElementById('voice-status').innerText = `Connecting to ${from}...`;
        try { voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true }); } catch(e) { return; }
        voiceCallWith = from;
        voicePeer = new RTCPeerConnection(pcConfig);
        voiceStream.getTracks().forEach(t => voicePeer.addTrack(t, voiceStream));
        voicePeer.ontrack = (event) => { const audio = new Audio(); audio.srcObject = event.streams[0]; audio.autoplay = true; document.getElementById('voice-status').innerHTML = '🔊 Voice call active.'; };
        voicePeer.onicecandidate = (e) => { if(e.candidate) socket.emit('voice_ice', { to: from, candidate: e.candidate }); };
        voicePeer.oniceconnectionstatechange = () => { if(voicePeer?.iceConnectionState === 'disconnected') endVoiceCall(); };
        await voicePeer.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await voicePeer.createAnswer();
        await voicePeer.setLocalDescription(answer);
        socket.emit('voice_answer', { to: from, answer });
        document.getElementById('voice-active').style.display = 'block';
        document.getElementById('voice-partner').innerText = from;
    }
    
    function rejectVoiceCall() { if (pendingVoiceFrom) { socket.emit('voice_reject', { to: pendingVoiceFrom }); pendingVoiceFrom = null; pendingVoiceOffer = null; document.getElementById('voice-incoming').style.display = 'none'; document.getElementById('voice-status').innerText = 'Call rejected.'; } }
    function toggleVoiceMute() { if (voiceStream) { const track = voiceStream.getAudioTracks()[0]; if (track) { track.enabled = !track.enabled; document.getElementById('voice-mute').innerHTML = track.enabled ? '🎤 Mute' : '🎙️ Unmute'; } } }
    function endVoiceCall() { if (voicePeer) { voicePeer.close(); voicePeer = null; } if (voiceStream) { voiceStream.getTracks().forEach(t => t.stop()); voiceStream = null; } if (voiceCallWith) { socket.emit('end_voice', { to: voiceCallWith }); voiceCallWith = null; } document.getElementById('voice-active').style.display = 'none'; document.getElementById('voice-status').innerHTML = ''; }
    
    // ========== 1-on-1 Video Call ==========
    async function getVideoStream(videoEnabled=true) { const constraints = { audio: true, video: videoEnabled ? { width: { ideal: 1280 }, height: { ideal: 720 } } : false }; return await navigator.mediaDevices.getUserMedia(constraints); }
    
    async function startVideoCall(target) { if (videoCallWith) { document.getElementById('video-status').innerText = 'Already in a video call.'; return; } document.getElementById('video-status').innerText = `Calling ${target}...`; try { videoStream = await getVideoStream(true); if(localVideo) localVideo.srcObject = videoStream; } catch(e) { return; } videoCallWith = target; videoPeer = new RTCPeerConnection(pcConfig); videoStream.getTracks().forEach(t => videoPeer.addTrack(t, videoStream)); videoPeer.ontrack = (event) => { if(remoteVideo) remoteVideo.srcObject = event.streams[0]; document.getElementById('video-status').innerHTML = '📹 Video call connected.'; }; videoPeer.onicecandidate = (e) => { if(e.candidate) socket.emit('video_ice', { to: target, candidate: e.candidate }); }; videoPeer.oniceconnectionstatechange = () => { if(videoPeer?.iceConnectionState === 'disconnected') endVideoCall(); }; const offer = await videoPeer.createOffer(); await videoPeer.setLocalDescription(offer); socket.emit('video_offer', { to: target, offer }); document.getElementById('video-active-window').style.display = 'block'; document.getElementById('remoteLabel').innerText = target; }
    
    async function acceptVideoCall() { if (!pendingVideoFrom || !pendingVideoOffer) return; const from = pendingVideoFrom, offer = pendingVideoOffer; pendingVideoFrom = null; pendingVideoOffer = null; document.getElementById('video-incoming').style.display = 'none'; document.getElementById('video-status').innerText = `Connecting to ${from}...`; try { videoStream = await getVideoStream(true); if(localVideo) localVideo.srcObject = videoStream; } catch(e) { return; } videoCallWith = from; videoPeer = new RTCPeerConnection(pcConfig); videoStream.getTracks().forEach(t => videoPeer.addTrack(t, videoStream)); videoPeer.ontrack = (event) => { if(remoteVideo) remoteVideo.srcObject = event.streams[0]; document.getElementById('video-status').innerHTML = '📹 Video call active.'; }; videoPeer.onicecandidate = (e) => { if(e.candidate) socket.emit('video_ice', { to: from, candidate: e.candidate }); }; videoPeer.oniceconnectionstatechange = () => { if(videoPeer?.iceConnectionState === 'disconnected') endVideoCall(); }; await videoPeer.setRemoteDescription(new RTCSessionDescription(offer)); const answer = await videoPeer.createAnswer(); await videoPeer.setLocalDescription(answer); socket.emit('video_answer', { to: from, answer }); document.getElementById('video-active-window').style.display = 'block'; document.getElementById('remoteLabel').innerText = from; }
    
    function rejectVideoCall() { if (pendingVideoFrom) { socket.emit('video_reject', { to: pendingVideoFrom }); pendingVideoFrom = null; pendingVideoOffer = null; document.getElementById('video-incoming').style.display = 'none'; document.getElementById('video-status').innerText = 'Call rejected.'; } }
    function toggleVideoMic() { if (videoStream) { const track = videoStream.getAudioTracks()[0]; if (track) { track.enabled = !track.enabled; document.getElementById('video-toggleMic').innerHTML = track.enabled ? '🎤 Mute' : '🎙️ Unmute'; } } }
    function toggleVideoCam() { if (videoStream) { const track = videoStream.getVideoTracks()[0]; if (track) { track.enabled = !track.enabled; document.getElementById('video-toggleCam').innerHTML = track.enabled ? '📷 Camera Off' : '📷 Camera On'; } } }
    
    async function toggleScreenShare() { if (!videoPeer) return; if (!isScreenSharing) { try { const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true }); originalVideoStream = videoStream; const videoTrack = screenStream.getVideoTracks()[0]; const sender = videoPeer.getSenders().find(s => s.track?.kind === 'video'); if (sender) sender.replaceTrack(videoTrack); if (localVideo) localVideo.srcObject = screenStream; videoStream = screenStream; videoTrack.onended = () => stopScreenShare(); isScreenSharing = true; document.getElementById('video-shareScreen').innerHTML = '🖥️ Stop Sharing'; } catch(e) {} } else stopScreenShare(); }
    
    function stopScreenShare() { if (originalVideoStream && videoPeer) { const videoTrack = originalVideoStream.getVideoTracks()[0]; const sender = videoPeer.getSenders().find(s => s.track?.kind === 'video'); if (sender && videoTrack) sender.replaceTrack(videoTrack); if (localVideo) localVideo.srcObject = originalVideoStream; if (videoStream) videoStream.getTracks().forEach(t => t.stop()); videoStream = originalVideoStream; originalVideoStream = null; isScreenSharing = false; document.getElementById('video-shareScreen').innerHTML = '🖥️ Share Screen'; } }
    
    function endVideoCall() { if (videoPeer) { videoPeer.close(); videoPeer = null; } if (videoStream) { videoStream.getTracks().forEach(t => t.stop()); videoStream = null; } if (videoCallWith) { socket.emit('end_video', { to: videoCallWith }); videoCallWith = null; } if (remoteVideo) remoteVideo.srcObject = null; if (localVideo) localVideo.srcObject = null; document.getElementById('video-active-window').style.display = 'none'; document.getElementById('video-status').innerHTML = ''; isScreenSharing = false; originalVideoStream = null; }
    
    // ========== GROUP VOICE CALL FUNCTIONS ==========
    async function createOrJoinVoiceRoom(roomName) {
        if (currentVoiceRoom) {
            showToast('Already in a voice room. Leave first.');
            return;
        }
        
        try {
            groupVoiceStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            currentVoiceRoom = roomName;
            
            socket.emit('join_voice_room', { room: roomName });
            
            document.getElementById('active-voice-room').style.display = 'block';
            document.getElementById('current-voice-room').innerText = roomName;
            document.getElementById('voice-room-status').innerHTML = '✅ Connected to voice room - You can talk!';
            
            loadVoiceRooms();
            updateStats();
        } catch(e) {
            showToast('Microphone access denied');
            currentVoiceRoom = null;
        }
    }
    
    function leaveVoiceRoom() {
        if (currentVoiceRoom) {
            socket.emit('leave_voice_room', { room: currentVoiceRoom });
            
            voiceRoomPeers.forEach((peer, userId) => {
                peer.close();
            });
            voiceRoomPeers.clear();
            
            if (groupVoiceStream) {
                groupVoiceStream.getTracks().forEach(track => track.stop());
                groupVoiceStream = null;
            }
            
            currentVoiceRoom = null;
            document.getElementById('active-voice-room').style.display = 'none';
            document.getElementById('voice-participants').innerHTML = '';
            document.getElementById('voice-room-status').innerHTML = '';
            loadVoiceRooms();
            updateStats();
            showToast('Left voice room');
        }
    }
    
    async function loadVoiceRooms() {
        const res = await fetch('/api/voice_rooms');
        const rooms = await res.json();
        const container = document.getElementById('voice-rooms-list');
        if (rooms.length === 0) {
            container.innerHTML = '<div class="glass-card" style="padding:20px; text-align:center;">No active voice rooms. Create one!</div>';
            return;
        }
        container.innerHTML = rooms.map(room => `
            <div class="room-item">
                <span>🔊 ${escapeHtml(room.name)} (${room.participants} participants)</span>
                <button class="btn-primary" onclick="createOrJoinVoiceRoom('${escapeHtml(room.name)}')">Join</button>
            </div>
        `).join('');
        document.getElementById('active-rooms').innerText = rooms.length;
    }
    
    // ========== GROUP VIDEO CALL FUNCTIONS ==========
    async function createOrJoinVideoRoom(roomName) {
        if (currentVideoRoom) {
            showToast('Already in a video room. Leave first.');
            return;
        }
        
        try {
            groupVideoStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
            currentVideoRoom = roomName;
            
            // Add local video
            addVideoToGroup(currentUser.username, groupVideoStream, true);
            
            socket.emit('join_video_room', { room: roomName });
            
            document.getElementById('active-video-room').style.display = 'block';
            document.getElementById('current-video-room').innerText = roomName;
            document.getElementById('video-room-status').innerHTML = '✅ Connected to video room - Your camera is on!';
            
            loadVideoRooms();
            updateStats();
        } catch(e) {
            showToast('Camera/Microphone access denied');
            currentVideoRoom = null;
        }
    }
    
    function addVideoToGroup(userId, stream, isLocal = false) {
        const grid = document.getElementById('group-video-grid');
        
        let existingBox = document.getElementById(`group-video-${userId}`);
        if (existingBox) {
            const video = existingBox.querySelector('video');
            if (video && video.srcObject !== stream) {
                video.srcObject = stream;
            }
            return;
        }
        
        const videoBox = document.createElement('div');
        videoBox.className = 'group-video-box';
        videoBox.id = `group-video-${userId}`;
        videoBox.innerHTML = `
            <video autoplay ${isLocal ? 'muted' : ''} playsinline></video>
            <div class="video-label">${isLocal ? 'You' : escapeHtml(userId)}</div>
        `;
        grid.appendChild(videoBox);
        
        const video = videoBox.querySelector('video');
        video.srcObject = stream;
    }
    
    function removeVideoFromGroup(userId) {
        const videoBox = document.getElementById(`group-video-${userId}`);
        if (videoBox) videoBox.remove();
    }
    
    function leaveVideoRoom() {
        if (currentVideoRoom) {
            socket.emit('leave_video_room', { room: currentVideoRoom });
            
            videoRoomPeers.forEach((peer, userId) => {
                peer.close();
            });
            videoRoomPeers.clear();
            
            if (groupVideoStream) {
                groupVideoStream.getTracks().forEach(track => track.stop());
                groupVideoStream = null;
            }
            
            document.getElementById('group-video-grid').innerHTML = '';
            currentVideoRoom = null;
            document.getElementById('active-video-room').style.display = 'none';
            document.getElementById('video-participants').innerHTML = '';
            document.getElementById('video-room-status').innerHTML = '';
            loadVideoRooms();
            updateStats();
            showToast('Left video room');
        }
    }
    
    async function loadVideoRooms() {
        const res = await fetch('/api/video_rooms');
        const rooms = await res.json();
        const container = document.getElementById('video-rooms-list');
        if (rooms.length === 0) {
            container.innerHTML = '<div class="glass-card" style="padding:20px; text-align:center;">No active video rooms. Create one!</div>';
            return;
        }
        container.innerHTML = rooms.map(room => `
            <div class="room-item">
                <span>📹 ${escapeHtml(room.name)} (${room.participants} participants)</span>
                <button class="btn-primary" onclick="createOrJoinVideoRoom('${escapeHtml(room.name)}')">Join</button>
            </div>
        `).join('');
    }
    
    async function createPeerConnectionForVoice(targetUserId) {
        const peer = new RTCPeerConnection(pcConfig);
        
        if (groupVoiceStream) {
            groupVoiceStream.getTracks().forEach(track => {
                peer.addTrack(track, groupVoiceStream);
            });
        }
        
        peer.ontrack = (event) => {
            const audio = new Audio();
            audio.srcObject = event.streams[0];
            audio.autoplay = true;
        };
        
        peer.onicecandidate = (event) => {
            if (event.candidate) {
                socket.emit('voice_room_ice', {
                    to: targetUserId,
                    candidate: event.candidate,
                    room: currentVoiceRoom
                });
            }
        };
        
        return peer;
    }
    
    async function createPeerConnectionForVideo(targetUserId) {
        const peer = new RTCPeerConnection(pcConfig);
        
        if (groupVideoStream) {
            groupVideoStream.getTracks().forEach(track => {
                peer.addTrack(track, groupVideoStream);
            });
        }
        
        peer.ontrack = (event) => {
            addVideoToGroup(targetUserId, event.streams[0], false);
        };
        
        peer.onicecandidate = (event) => {
            if (event.candidate) {
                socket.emit('video_room_ice', {
                    to: targetUserId,
                    candidate: event.candidate,
                    room: currentVideoRoom
                });
            }
        };
        
        return peer;
    }
    
    function toggleGroupVoiceMute() {
        if (groupVoiceStream) {
            const track = groupVoiceStream.getAudioTracks()[0];
            if (track) {
                track.enabled = !track.enabled;
                document.getElementById('voice-room-mute').innerHTML = track.enabled ? '🎤 Mute' : '🎙️ Unmute';
            }
        }
    }
    
    function toggleGroupVideoMute() {
        if (groupVideoStream) {
            const track = groupVideoStream.getAudioTracks()[0];
            if (track) {
                track.enabled = !track.enabled;
                document.getElementById('video-room-mute').innerHTML = track.enabled ? '🎤 Mute' : '🎙️ Unmute';
            }
        }
    }
    
    function toggleGroupVideoCam() {
        if (groupVideoStream) {
            const track = groupVideoStream.getVideoTracks()[0];
            if (track) {
                track.enabled = !track.enabled;
                document.getElementById('video-room-cam').innerHTML = track.enabled ? '📷 Camera Off' : '📷 Camera On';
            }
        }
    }
    
    function updateStats() {
        fetch('/api/voice_rooms').then(r => r.json()).then(rooms => {
            document.getElementById('active-rooms').innerText = rooms.length;
        });
        fetch('/api/voice_rooms').then(r => r.json()).then(rooms => {
            let total = 0;
            rooms.forEach(room => total += room.participants);
            fetch('/api/video_rooms').then(r => r.json()).then(vrooms => {
                vrooms.forEach(room => total += room.participants);
                document.getElementById('total-participants').innerText = total;
            });
        });
    }
    
    // ========== Main Socket.IO ==========
    async function initMainApp() {
        document.getElementById('auth-screen').style.display = 'none';
        document.getElementById('main-app').style.display = 'block';
        await loadUsersForSMS();
        await loadBlockedMessages();
        await loadVoiceRooms();
        await loadVideoRooms();
        
        requestNotificationPermission();
        
        socket = io();
        socket.on('connect', () => { 
            socket.emit('join_user_room', { username: currentUser.username }); 
            socket.emit('register_user', { username: currentUser.username });
        });
        socket.on('new_threat', (threat) => addThreat(threat));
        
        // SMS events
        socket.on('receive_sms', (data) => {
            const from = data.from;
            if (activeChat !== from) {
                showNotification(`📩 New message from ${from}`, data.content);
            }
            if (activeChat === from) {
                appendMessage(data, 'received');
            } else if (data.from === currentUser.username && activeChat === data.to) {
                appendMessage(data, 'sent');
            }
            loadUsersForSMS();
        });
        
        socket.on('sms_blocked', (data) => {
            if (data.to === currentUser.username) {
                showNotification(`🚫 Blocked message from ${data.from}`, `Reason: ${data.reason}`);
                loadBlockedMessages();
            } else if (data.from === currentUser.username) {
                showSmsWarning(`⚠️ Message blocked: "${data.content}" contains suspicious content.`);
            }
        });
        
        // 1-on-1 Voice events
        socket.on('voice_offer', ({ from, offer }) => {
            pendingVoiceFrom = from;
            pendingVoiceOffer = offer;
            document.getElementById('voice-caller-name').innerText = from;
            document.getElementById('voice-incoming').style.display = 'block';
            showNotification(`📞 Incoming voice call from ${from}`, "Tap to answer", "voice-call");
        });
        
        socket.on('voice_answer', async ({ from, answer }) => { if(voicePeer && voiceCallWith === from) await voicePeer.setRemoteDescription(new RTCSessionDescription(answer)); });
        socket.on('voice_ice', async ({ from, candidate }) => { if(voicePeer && voiceCallWith === from && candidate) try { await voicePeer.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e){} });
        socket.on('voice_reject', ({ from }) => { if(voiceCallWith === from) { document.getElementById('voice-status').innerText = `${from} rejected the call.`; endVoiceCall(); } });
        socket.on('voice_ended', ({ from }) => { if(voiceCallWith === from) { document.getElementById('voice-status').innerText = `${from} ended the call.`; endVoiceCall(); } });
        
        // 1-on-1 Video events
        socket.on('video_offer', ({ from, offer }) => {
            pendingVideoFrom = from;
            pendingVideoOffer = offer;
            document.getElementById('video-caller-name').innerText = from;
            document.getElementById('video-incoming').style.display = 'block';
            showNotification(`📹 Incoming video call from ${from}`, "Tap to answer", "video-call");
        });
        socket.on('video_answer', async ({ from, answer }) => { if(videoPeer && videoCallWith === from) await videoPeer.setRemoteDescription(new RTCSessionDescription(answer)); });
        socket.on('video_ice', async ({ from, candidate }) => { if(videoPeer && videoCallWith === from && candidate) try { await videoPeer.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e){} });
        socket.on('video_reject', ({ from }) => { if(videoCallWith === from) { document.getElementById('video-status').innerText = `${from} rejected the call.`; endVideoCall(); } });
        socket.on('video_ended', ({ from }) => { if(videoCallWith === from) { document.getElementById('video-status').innerText = `${from} ended the call.`; endVideoCall(); } });
        
        // GROUP VOICE ROOM events
        socket.on('voice_room_participants', ({ room, participants }) => {
            if (currentVoiceRoom === room) {
                const container = document.getElementById('voice-participants');
                container.innerHTML = participants.map(p => `<span class="participant">🎤 ${escapeHtml(p)}</span>`).join('');
            }
            loadVoiceRooms();
            updateStats();
        });
        
        socket.on('voice_room_joined', ({ room, participants }) => {
            if (currentVoiceRoom === room) {
                showToast(`Joined voice room: ${room}`);
                // Create peer connections for existing participants
                participants.forEach(participant => {
                    if (participant !== currentUser.username) {
                        createPeerConnectionForVoice(participant).then(peer => {
                            voiceRoomPeers.set(participant, peer);
                            // Send offer
                            peer.createOffer().then(offer => {
                                peer.setLocalDescription(offer);
                                socket.emit('voice_room_offer', { to: participant, offer, room: currentVoiceRoom });
                            });
                        });
                    }
                });
            }
        });
        
        socket.on('voice_room_offer', async ({ from, offer }) => {
            const peer = await createPeerConnectionForVoice(from);
            voiceRoomPeers.set(from, peer);
            await peer.setRemoteDescription(new RTCSessionDescription(offer));
            const answer = await peer.createAnswer();
            await peer.setLocalDescription(answer);
            socket.emit('voice_room_answer', { to: from, answer, room: currentVoiceRoom });
        });
        
        socket.on('voice_room_answer', async ({ from, answer }) => {
            const peer = voiceRoomPeers.get(from);
            if (peer) await peer.setRemoteDescription(new RTCSessionDescription(answer));
        });
        
        socket.on('voice_room_ice', async ({ from, candidate }) => {
            const peer = voiceRoomPeers.get(from);
            if (peer && candidate) {
                try { await peer.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e) {}
            }
        });
        
        socket.on('voice_room_left', ({ room, participant }) => {
            if (currentVoiceRoom === room) {
                const peer = voiceRoomPeers.get(participant);
                if (peer) {
                    peer.close();
                    voiceRoomPeers.delete(participant);
                }
                showToast(`${participant} left the voice room`);
            }
            loadVoiceRooms();
            updateStats();
        });
        
        // GROUP VIDEO ROOM events
        socket.on('video_room_participants', ({ room, participants }) => {
            if (currentVideoRoom === room) {
                const container = document.getElementById('video-participants');
                container.innerHTML = participants.map(p => `<span class="participant">📹 ${escapeHtml(p)}</span>`).join('');
                // Remove videos for users who left
                const currentUsers = new Set(participants);
                currentUsers.add(currentUser.username);
                document.querySelectorAll('#group-video-grid .group-video-box').forEach(box => {
                    const userId = box.id.replace('group-video-', '');
                    if (!currentUsers.has(userId)) {
                        box.remove();
                    }
                });
            }
            loadVideoRooms();
            updateStats();
        });
        
        socket.on('video_room_joined', ({ room, participants }) => {
            if (currentVideoRoom === room) {
                showToast(`Joined video room: ${room}`);
                participants.forEach(participant => {
                    if (participant !== currentUser.username) {
                        createPeerConnectionForVideo(participant).then(peer => {
                            videoRoomPeers.set(participant, peer);
                            peer.createOffer().then(offer => {
                                peer.setLocalDescription(offer);
                                socket.emit('video_room_offer', { to: participant, offer, room: currentVideoRoom });
                            });
                        });
                    }
                });
            }
        });
        
        socket.on('video_room_offer', async ({ from, offer }) => {
            const peer = await createPeerConnectionForVideo(from);
            videoRoomPeers.set(from, peer);
            await peer.setRemoteDescription(new RTCSessionDescription(offer));
            const answer = await peer.createAnswer();
            await peer.setLocalDescription(answer);
            socket.emit('video_room_answer', { to: from, answer, room: currentVideoRoom });
        });
        
        socket.on('video_room_answer', async ({ from, answer }) => {
            const peer = videoRoomPeers.get(from);
            if (peer) await peer.setRemoteDescription(new RTCSessionDescription(answer));
        });
        
        socket.on('video_room_ice', async ({ from, candidate }) => {
            const peer = videoRoomPeers.get(from);
            if (peer && candidate) {
                try { await peer.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e) {}
            }
        });
        
        socket.on('video_room_left', ({ room, participant }) => {
            if (currentVideoRoom === room) {
                const peer = videoRoomPeers.get(participant);
                if (peer) {
                    peer.close();
                    videoRoomPeers.delete(participant);
                }
                removeVideoFromGroup(participant);
                showToast(`${participant} left the video room`);
            }
            loadVideoRooms();
            updateStats();
        });
        
        // UI bindings
        document.getElementById('voice-accept').onclick = acceptVoiceCall;
        document.getElementById('voice-reject').onclick = rejectVoiceCall;
        document.getElementById('voice-mute').onclick = toggleVoiceMute;
        document.getElementById('voice-end').onclick = endVoiceCall;
        
        document.getElementById('video-accept').onclick = acceptVideoCall;
        document.getElementById('video-reject').onclick = rejectVideoCall;
        document.getElementById('video-toggleMic').onclick = toggleVideoMic;
        document.getElementById('video-toggleCam').onclick = toggleVideoCam;
        document.getElementById('video-shareScreen').onclick = toggleScreenShare;
        document.getElementById('video-endCall').onclick = endVideoCall;
        
        document.getElementById('back-to-users').onclick = () => closeChatAndShowUsers();
        
        // Group call UI bindings
        document.getElementById('create-voice-room').onclick = () => {
            const roomName = document.getElementById('voice-room-name').value.trim();
            if (roomName) createOrJoinVoiceRoom(roomName);
            else showToast('Enter a room name');
        };
        document.getElementById('leave-voice-room').onclick = leaveVoiceRoom;
        document.getElementById('voice-room-mute').onclick = toggleGroupVoiceMute;
        
        document.getElementById('create-video-room').onclick = () => {
            const roomName = document.getElementById('video-room-name').value.trim();
            if (roomName) createOrJoinVideoRoom(roomName);
            else showToast('Enter a room name');
        };
        document.getElementById('leave-video-room').onclick = leaveVideoRoom;
        document.getElementById('video-room-mute').onclick = toggleGroupVideoMute;
        document.getElementById('video-room-cam').onclick = toggleGroupVideoCam;
        
        async function loadUserLists() {
            const res = await fetch('/api/users');
            const users = await res.json();
            const filtered = users.filter(u=>u.username !== currentUser.username);
            document.getElementById('user-list-voice').innerHTML = filtered.map(u => `<div class="user-item"><span>${u.username}</span><button class="call-btn" data-user="${u.username}">🎙️ Voice</button></div>`).join('');
            document.getElementById('user-list-video').innerHTML = filtered.map(u => `<div class="user-item"><span>${u.username}</span><button class="call-btn" data-user="${u.username}">📹 Video</button></div>`).join('');
            document.querySelectorAll('#user-list-voice .call-btn').forEach(btn => btn.onclick = () => startVoiceCall(btn.getAttribute('data-user')));
            document.querySelectorAll('#user-list-video .call-btn').forEach(btn => btn.onclick = () => startVideoCall(btn.getAttribute('data-user')));
        }
        loadUserLists();
        
        const features = [{icon:"👥",title:"Group Voice"},{icon:"🎥",title:"Group Video"},{icon:"🎙️",title:"1-on-1 Voice"},{icon:"📹",title:"1-on-1 Video"},{icon:"🔊",title:"Voice Alert"},{icon:"📩",title:"SMS Shield"}];
        document.getElementById('features-grid').innerHTML = features.map(f => `<div class="glass-card" style="padding:20px; text-align:center;"><div style="font-size:2.2rem;">${f.icon}</div><div>${f.title}</div></div>`).join('');
        
        document.getElementById('scan-btn').onclick = () => { const input = document.getElementById('scan-input').value; const isBad = /(tk|bonus|pesa|reward)/i.test(input); document.getElementById('scan-result').innerHTML = `<div class="glass-card" style="margin-top:16px; padding:16px;"><div style="color:${isBad?'#ff4d9e':'#00ff88'}">${isBad?'🚫 THREAT DETECTED':'✅ SAFE'}</div></div>`; };
        
        document.getElementById('send-sms').onclick = () => {
            const content = document.getElementById('message-input').value.trim();
            if (!content || !activeChat) return;
            socket.emit('send_sms', { to: activeChat, content });
            document.getElementById('message-input').value = '';
        };
        
        renderThreatTable();
        
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.onclick = () => {
                document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
                document.getElementById(btn.getAttribute('data-tab')+'-tab').style.display = 'block';
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active-tab'));
                btn.classList.add('active-tab');
                if (btn.getAttribute('data-tab') === 'sms') {
                    loadUsersForSMS();
                    closeChatAndShowUsers();
                }
                if (btn.getAttribute('data-tab') === 'blocked') loadBlockedMessages();
                if (btn.getAttribute('data-tab') === 'groupvoice') loadVoiceRooms();
                if (btn.getAttribute('data-tab') === 'groupvideo') loadVideoRooms();
                if (btn.getAttribute('data-tab') === 'voice' || btn.getAttribute('data-tab') === 'video') loadUserLists();
            };
        });
    }
</script>
</body>
</html>
"""

# ------------------------------------------------------------
#  Flask Backend with All Call Types
# ------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'simublock-all-calls-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active rooms
voice_rooms = {}
video_rooms = {}

def init_db():
    conn = sqlite3.connect('simublock.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        phone TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user INTEGER,
        to_user INTEGER,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS blocked_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user INTEGER,
        to_user INTEGER,
        content TEXT,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

THREAT_KEYWORDS = [
    "bibi sudi", "anasaidia", "bilashala", "nyota", "pesa", "mari", "pete", "rimbwata", "kuludisha",
    "mke", "mume", "uzazi", "kazi", "kesi", "cheo", ".mpige", "0663407574", "0719030503",
    "habari zauzima", "kodi yangu ya nyumba", "666", "jiunge na chama cha matajiri", "free mason",
    "umiliki pesa", "manyumba", "magari", "biashala", "bila kafara", "kuza", "kipajichauigizaji",
    "muziki", "0624617087", "tuma pesa", "mama yako ni mgonjwa"
]

def is_threat_message(content):
    content_lower = content.lower()
    for kw in THREAT_KEYWORDS:
        if kw.lower() in content_lower:
            return True, kw
    return False, None

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone', '')
    if not username or not password:
        return {'success': False, 'error': 'Missing fields'}
    conn = sqlite3.connect('simublock.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, phone) VALUES (?, ?, ?)",
                  (username, hash_password(password), phone))
        conn.commit()
        return {'success': True}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Username taken'}
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect('simublock.db')
    c = conn.cursor()
    c.execute("SELECT id, username, phone FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    if user:
        session['user_id'] = user[0]
        session['username'] = user[1]
        return {'success': True, 'user': {'id': user[0], 'username': user[1], 'phone': user[2]}}
    return {'success': False, 'error': 'Invalid credentials'}

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return {'success': True}

@app.route('/api/users')
def get_users():
    if 'user_id' not in session:
        return []
    conn = sqlite3.connect('simublock.db')
    c = conn.cursor()
    c.execute("SELECT id, username, phone FROM users WHERE id != ?", (session['user_id'],))
    users = [{'id': row[0], 'username': row[1], 'phone': row[2]} for row in c.fetchall()]
    conn.close()
    return users

@app.route('/api/messages/<other_username>')
def get_messages(other_username):
    if 'user_id' not in session:
        return []
    conn = sqlite3.connect('simublock.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (other_username,))
    other = c.fetchone()
    if not other:
        return []
    other_id = other[0]
    c.execute('''SELECT m.content, m.timestamp, u1.username as from_username, u2.username as to_username
                 FROM messages m
                 JOIN users u1 ON m.from_user = u1.id
                 JOIN users u2 ON m.to_user = u2.id
                 WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)
                 ORDER BY m.timestamp ASC''', (session['user_id'], other_id, other_id, session['user_id']))
    msgs = [{'from_username': row[2], 'to_username': row[3], 'content': row[0], 'timestamp': row[1]} for row in c.fetchall()]
    conn.close()
    return msgs

@app.route('/api/blocked')
def get_blocked_messages():
    if 'user_id' not in session:
        return []
    conn = sqlite3.connect('simublock.db')
    c = conn.cursor()
    c.execute('''SELECT b.content, b.reason, b.timestamp, u.username as from_username
                 FROM blocked_messages b
                 JOIN users u ON b.from_user = u.id
                 WHERE b.to_user = ?
                 ORDER BY b.timestamp DESC''', (session['user_id'],))
    blocked = [{'from_username': row[3], 'content': row[0], 'reason': row[1], 'timestamp': row[2]} for row in c.fetchall()]
    conn.close()
    return blocked

@app.route('/api/voice_rooms')
def get_voice_rooms():
    return [{'name': name, 'participants': list(participants)} for name, participants in voice_rooms.items()]

@app.route('/api/video_rooms')
def get_video_rooms():
    return [{'name': name, 'participants': list(participants)} for name, participants in video_rooms.items()]

# Socket.IO events
online_users = set()

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('join_user_room')
def join_user_room(data):
    username = data.get('username')
    if username:
        join_room(username)

@socketio.on('register_user')
def register_user(data):
    online_users.add(data.get('username'))

# SMS Handler
@socketio.on('send_sms')
def handle_sms(data):
    if 'user_id' not in session:
        return
    from_username = session['username']
    to_username = data.get('to')
    content = data.get('content')
    if not to_username or not content:
        return
    
    is_threat, matched_kw = is_threat_message(content)
    if is_threat:
        conn = sqlite3.connect('simublock.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (to_username,))
        to_user = c.fetchone()
        c.execute("SELECT id FROM users WHERE username=?", (from_username,))
        from_user = c.fetchone()
        if to_user and from_user:
            reason = f"Blocked keyword: '{matched_kw}'"
            c.execute("INSERT INTO blocked_messages (from_user, to_user, content, reason) VALUES (?, ?, ?, ?)",
                      (from_user[0], to_user[0], content, reason))
            conn.commit()
            threat = {
                "type": "SMS",
                "number": from_username,
                "status": "BLOCKED",
                "risk": 95,
                "reason": reason
            }
            socketio.emit('new_threat', threat)
            socketio.emit('sms_blocked', {
                'from': from_username,
                'to': to_username,
                'content': content,
                'reason': reason
            }, room=to_username)
            socketio.emit('sms_blocked', {
                'from': from_username,
                'to': to_username,
                'content': content,
                'reason': reason
            }, room=from_username)
        conn.close()
        return
    
    conn = sqlite3.connect('simublock.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (to_username,))
    to_user = c.fetchone()
    if to_user:
        c.execute("INSERT INTO messages (from_user, to_user, content) VALUES (?, ?, ?)",
                  (session['user_id'], to_user[0], content))
        conn.commit()
        socketio.emit('receive_sms', {
            'from': from_username,
            'to': to_username,
            'content': content,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=to_username)
        socketio.emit('receive_sms', {
            'from': from_username,
            'to': to_username,
            'content': content,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=from_username)
    conn.close()

# 1-on-1 Voice Signaling
@socketio.on('voice_offer')
def voice_offer(data):
    socketio.emit('voice_offer', {'from': session['username'], 'offer': data['offer']}, room=data['to'])

@socketio.on('voice_answer')
def voice_answer(data):
    socketio.emit('voice_answer', {'from': session['username'], 'answer': data['answer']}, room=data['to'])

@socketio.on('voice_ice')
def voice_ice(data):
    socketio.emit('voice_ice', {'from': session['username'], 'candidate': data['candidate']}, room=data['to'])

@socketio.on('voice_reject')
def voice_reject(data):
    socketio.emit('voice_reject', {'from': session['username']}, room=data['to'])

@socketio.on('end_voice')
def end_voice(data):
    socketio.emit('voice_ended', {'from': session['username']}, room=data['to'])

# 1-on-1 Video Signaling
@socketio.on('video_offer')
def video_offer(data):
    socketio.emit('video_offer', {'from': session['username'], 'offer': data['offer']}, room=data['to'])

@socketio.on('video_answer')
def video_answer(data):
    socketio.emit('video_answer', {'from': session['username'], 'answer': data['answer']}, room=data['to'])

@socketio.on('video_ice')
def video_ice(data):
    socketio.emit('video_ice', {'from': session['username'], 'candidate': data['candidate']}, room=data['to'])

@socketio.on('video_reject')
def video_reject(data):
    socketio.emit('video_reject', {'from': session['username']}, room=data['to'])

@socketio.on('end_video')
def end_video(data):
    socketio.emit('video_ended', {'from': session['username']}, room=data['to'])

# GROUP VOICE ROOM Handlers
@socketio.on('join_voice_room')
def join_voice_room(data):
    room = data.get('room')
    username = session.get('username')
    
    if not username or not room:
        return
    
    if room not in voice_rooms:
        voice_rooms[room] = set()
    
    voice_rooms[room].add(username)
    join_room(f"voice_{room}")
    
    # Notify all participants
    socketio.emit('voice_room_participants', {'room': room, 'participants': list(voice_rooms[room])}, room=f"voice_{room}")
    socketio.emit('voice_room_joined', {'room': room, 'participants': list(voice_rooms[room])}, room=username)

@socketio.on('leave_voice_room')
def leave_voice_room(data):
    room = data.get('room')
    username = session.get('username')
    
    if not username or not room:
        return
    
    if room in voice_rooms:
        voice_rooms[room].discard(username)
        leave_room(f"voice_{room}")
        
        socketio.emit('voice_room_left', {'room': room, 'participant': username}, room=f"voice_{room}")
        
        if len(voice_rooms[room]) == 0:
            del voice_rooms[room]

@socketio.on('voice_room_offer')
def voice_room_offer(data):
    socketio.emit('voice_room_offer', {'from': session['username'], 'offer': data['offer']}, room=data['to'])

@socketio.on('voice_room_answer')
def voice_room_answer(data):
    socketio.emit('voice_room_answer', {'from': session['username'], 'answer': data['answer']}, room=data['to'])

@socketio.on('voice_room_ice')
def voice_room_ice(data):
    socketio.emit('voice_room_ice', {'from': session['username'], 'candidate': data['candidate']}, room=data['to'])

# GROUP VIDEO ROOM Handlers
@socketio.on('join_video_room')
def join_video_room(data):
    room = data.get('room')
    username = session.get('username')
    
    if not username or not room:
        return
    
    if room not in video_rooms:
        video_rooms[room] = set()
    
    video_rooms[room].add(username)
    join_room(f"video_{room}")
    
    socketio.emit('video_room_participants', {'room': room, 'participants': list(video_rooms[room])}, room=f"video_{room}")
    socketio.emit('video_room_joined', {'room': room, 'participants': list(video_rooms[room])}, room=username)

@socketio.on('leave_video_room')
def leave_video_room(data):
    room = data.get('room')
    username = session.get('username')
    
    if not username or not room:
        return
    
    if room in video_rooms:
        video_rooms[room].discard(username)
        leave_room(f"video_{room}")
        
        socketio.emit('video_room_left', {'room': room, 'participant': username}, room=f"video_{room}")
        
        if len(video_rooms[room]) == 0:
            del video_rooms[room]

@socketio.on('video_room_offer')
def video_room_offer(data):
    socketio.emit('video_room_offer', {'from': session['username'], 'offer': data['offer']}, room=data['to'])

@socketio.on('video_room_answer')
def video_room_answer(data):
    socketio.emit('video_room_answer', {'from': session['username'], 'answer': data['answer']}, room=data['to'])

@socketio.on('video_room_ice')
def video_room_ice(data):
    socketio.emit('video_room_ice', {'from': session['username'], 'candidate': data['candidate']}, room=data['to'])

# Background threat generator
def background_threats():
    threats = [
        {"type":"CALL","number":"+255 754 XXX 112","status":"BLOCKED","risk":96,"reason":"Fake Tigo pesa"},
        {"type":"SMS","number":"+255 689 XXX 445","status":"FLAGGED","risk":88,"reason":"Bank details scam"},
        {"type":"LINK","number":"halopesa-update.ml","status":"BLOCKED","risk":99,"reason":"Phishing"},
        {"type":"CALL","number":"+255 622 XXX 873","status":"BLOCKED","risk":94,"reason":"Police impersonation"},
    ]
    while True:
        eventlet.sleep(15)
        threat = random.choice(threats)
        socketio.emit('new_threat', threat)

if __name__ == '__main__':
    eventlet.spawn(background_threats)
    print("=" * 80)
    print("🚀 SIMU-BLOCK - COMPLETE VOICE & VIDEO CALLING SYSTEM")
    print("=" * 80)
    print(f"📡 Server running at: http://localhost:5000")
    print("\n✨ ALL CALL TYPES AVAILABLE:")
    print("   🎙️ 1-on-1 Voice Calls - Private audio calls")
    print("   📹 1-on-1 Video Calls - Private video calls with screen sharing")
    print("   👥 Group Voice Rooms - Multiple people can talk simultaneously")
    print("   🎥 Group Video Rooms - See and hear everyone in real-time")
    print("   💬 SMS with Threat Detection")
    print("   🛡️ Automatic Call Blocking for Threats")
    print("\n📋 How to use:")
    print("   1-on-1 Calls: Click on any user in Voice/Video tabs")
    print("   Group Calls: Create/Join rooms in Group Voice/Video tabs")
    print("=" * 80)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)