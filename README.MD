# 🎯 Distributed Face-Locked Servo System

A complete distributed vision-control system implementing real-time face tracking with servo motor actuation using MQTT messaging and WebSocket-based web visualization.

**Live Dashboard**: [Access on VPS](http://157.173.101.159:9403/uploads/web-dashboard/dashboard.html) | **GitHub**: [paradie2to4/face_servo](https://github.com/paradie2to4/face_servo)

> **📌 Live URL**: http://157.173.101.159:9403/uploads/web-dashboard/dashboard.html

---

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐          ┌──────────────┐   ┌──────────────┐ │
│  │   PC Linux   │          │   VPS/Cloud  │   │   Browser    │ │
│  │   Camera     │──MQTT────│  Broker +    │───│  Dashboard   │ │
│  │   Vision     │          │  Backend     │   │  WebSocket   │ │
│  └──────────────┘          └──────────────┘   └──────────────┘ │
│         │                         │                               │
│         │                         │ MQTT                         │
│         │                         │                               │
│         └────────────────────────┬────────────────────────────  │
│                                  │                               │
│                          ┌───────▼────────┐                     │
│                          │   ESP8266      │                     │
│                          │   NodeMCU      │                     │
│                          │   Servo Motor  │                     │
│                          └────────────────┘                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Components:
1. **PC Vision Node** - OpenCV-based face detection & tracking
2. **MQTT Broker** - Message distribution (Mosquitto)
3. **Backend Service** - MQTT-to-WebSocket bridge (Node.js)
4. **Web Dashboard** - Real-time visualization & monitoring
5. **ESP8266 Controller** - Servo motor actuation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (for vision node)
- Node.js 16+ (for backend)
- MQTT Broker (Mosquitto)
- Webcam & ESP8266 with servo motor

### Local Development (5 minutes)

#### 1. Backend Server
```bash
cd backend
npm install
npm start
# Runs on http://localhost:9002
```

#### 2. Vision Node
```bash
cd pc-vision
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python vision_node.py
```

#### 3. Dashboard
Open `web-dashboard/dashboard.html` in your browser.

---

## 🌐 VPS Deployment

### Dashboard Access
Your dashboard is now live at:
```
http://157.173.101.159:9403/uploads/web-dashboard/dashboard.html
```

**Direct Link**: [Open Dashboard](http://157.173.101.159:9403/uploads/web-dashboard/dashboard.html)

### Step 1: Provision VPS
```bash
# SSH into your VPS
ssh user@your-vps-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install MQTT Broker
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### Step 2: Deploy Backend & Dashboard
```bash
# Upload dashboard to uploads folder (you've already done this!)
scp -r web-dashboard/ user@your-vps-ip:~/uploads/

# Upload backend to home directory
scp -r backend/ user@your-vps-ip:/home/user/

# SSH into VPS
ssh user@your-vps-ip

# Setup backend
cd backend
npm install

# Install PM2 for process management
sudo npm install -g pm2
pm2 start server.js --name "face-servo"
pm2 save
pm2 startup
```

### Step 3: Dashboard Access
Your dashboard is now available at:
```
~/uploads/web-dashboard/dashboard.html
```

**Access in browser:**
- Direct file: Open locally from VPS
- Via HTTP: `http://YOUR-VPS-IP-OR-DOMAIN/uploads/web-dashboard/dashboard.html`
- Via Nginx: Set up virtual host pointing to `~/uploads/` folder

### Step 4: Configure
Update configuration in all three nodes:

**backend/server.js** (line 11):
```javascript
const MQTT_BROKER = 'mqtt://YOUR-VPS-IP:1883';
const WS_PORT = 9002;
```

**pc-vision/vision_node.py** (lines 12-13):
```python
MQTT_BROKER = "YOUR-VPS-IP"
MQTT_PORT = 1883
```

**web-dashboard/dashboard.html** (JavaScript section):
```javascript
const WS_URL = 'wss://YOUR-VPS-IP:9002';  // or ws:// for non-HTTPS
const MQTT_BROKER = 'mqtt://YOUR-VPS-IP:1883';
```

### Access Your VPS Dashboard

Once deployed, access your dashboard using one of these methods:

**1. From Your VPS (VMI2305190):**
```bash
# SSH into your VPS
ssh user403@vmi2305190.contaboserver.com

# View dashboard directly
cat ~/uploads/web-dashboard/dashboard.html
```

**2. From Browser:**
- **Direct Link**: [http://157.173.101.159:9403/uploads/web-dashboard/dashboard.html](http://157.173.101.159:9403/uploads/web-dashboard/dashboard.html)

**3. Set up Web Server (Optional):**
```bash
# Using simple HTTP server
cd ~/uploads/web-dashboard
npx http-server -p 9403

# Then access: http://157.173.101.159:9403/dashboard.html
```

---

## 📁 Project Structure

```
face-servo/
├── README.md                    # This file
├── .gitignore
│
├── backend/                     # Node.js Backend Service
│   ├── package.json
│   ├── server.js               # MQTT-to-WebSocket bridge
│   └── node_modules/
│
├── pc-vision/                   # Python Vision Node
│   ├── vision_node.py          # Face detection & MQTT broadcast
│   ├── requirements.txt
│   └── venv/                   # Virtual environment
│
├── esp8266/                     # MicroPython Controller
│   └── main.py                 # Servo control via MQTT
│
└── web-dashboard/              # Web Interface
    └── dashboard.html          # Single-file dashboard
```

---

## 🔧 Configuration Guide

### MQTT Topics

| Topic | Direction | Format | Description |
|-------|-----------|--------|-------------|
| `vision/{TEAM_ID}/movement` | PC → Broker | `{"status": "MOVE_LEFT", "x": 120, "confidence": 0.95}` | Face position data |
| `vision/{TEAM_ID}/heartbeat` | PC → Broker | `{"node": "pc", "status": "ONLINE"}` | Node health check |
| `servo/{TEAM_ID}/command` | Backend → ESP | `{"angle": 90, "speed": 50}` | Servo control |
| `iot/status/#` | All → Broker | Various | System status updates |

### Environment Variables

Create `.env` in backend folder:
```
MQTT_BROKER=mqtt://157.173.101.159:1883
WS_PORT=9002
TEAM_ID=BACK-BENCHERS
LOG_LEVEL=info
```

---

## 🎯 Features

✅ **Real-time Face Tracking**
- OpenCV-based face detection
- Confidence scoring
- Multi-face handling

✅ **Distributed Architecture**
- Message broker (MQTT)
- Stateless backend service
- Horizontal scalability

✅ **Web Dashboard**
- Live movement visualization
- System status monitoring
- Message logging
- Real-time charts
- Responsive design

✅ **Hardware Integration**
- ESP8266/NodeMCU support
- Servo motor control
- Pulse width modulation (PWM)

---

## 📊 Dashboard Features

### Real-Time Metrics
- **Face Position**: X/Y coordinates from video feed
- **Confidence Score**: Detection confidence (0-1)
- **Servo Angle**: Current motor position
- **System Status**: Node connectivity & health

### Visualizations
- Movement direction indicators
- Real-time position tracking chart
- Component status badges
- Message log with timestamps

### Controls
- Manual servo control (optional)
- Enable/disable face tracking
- Adjust detection parameters
- View system logs

---

## 🔌 API Endpoints

### Backend WebSocket Messages

**Incoming (Dashboard receives):**
```javascript
{
  "type": "movement",
  "data": {
    "status": "CENTERED|MOVE_LEFT|MOVE_RIGHT|NO_FACE",
    "face_position": { "x": 320, "y": 240 },
    "confidence": 0.95,
    "timestamp": 1675000000
  }
}

{
  "type": "heartbeat",
  "data": {
    "node": "pc|esp8266",
    "status": "ONLINE|OFFLINE",
    "timestamp": 1675000000
  }
}
```

### Health Check Endpoint
```bash
curl http://localhost:9002/health
# Response:
# {
#   "status": "healthy",
#   "mqtt": true,
#   "ws_clients": 2,
#   "timestamp": 1675000000
# }
```

---

## 🐛 Troubleshooting

### Dashboard Shows "Disconnected"
```bash
# Check backend is running
ps aux | grep node

# Check MQTT broker
sudo systemctl status mosquitto

# Check network connectivity
ping YOUR-VPS-IP
```

### MQTT Connection Fails
```bash
# Verify broker is accessible
mosquitto_pub -h YOUR-VPS-IP -t "test" -m "hello"

# Check firewall
sudo ufw allow 1883
sudo ufw allow 9002
```

### Vision Node Not Publishing
```bash
# Test MQTT connection
python -c "import paho.mqtt.client as mqtt; mqtt.Client().connect('YOUR-VPS-IP', 1883)"

# Check camera access
# Linux: ls /dev/video*
# Windows: Use Python OpenCV test
```

### ESP8266 Not Receiving Commands
```bash
# Monitor MQTT messages
mosquitto_sub -h YOUR-VPS-IP -t "servo/#" -v

# Verify ESP8266 firmware
# MicroPython 1.19+ recommended
```

---

## 📈 Performance Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Face Detection FPS | 30+ | ✅ |
| MQTT Latency | <100ms | ✅ |
| Dashboard Update Rate | 10-30Hz | ✅ |
| WebSocket Connections | 100+ | ✅ |

---

## 🔐 Security Considerations

### Production Deployment

1. **Enable MQTT Authentication**
```bash
sudo nano /etc/mosquitto/mosquitto.conf
# Add:
# password_file /etc/mosquitto/passwd
# allow_anonymous false
```

2. **Use WebSocket Secure (WSS)**
```javascript
// Use wss:// instead of ws://
const WS_URL = 'wss://your-domain.com:9002';
```

3. **Firewall Configuration**
```bash
sudo ufw default deny incoming
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 1883/tcp    # MQTT
sudo ufw allow 9002/tcp    # WebSocket
```

4. **SSL/TLS Certificates**
```bash
# Use Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

---

## 📚 Documentation

- [MQTT Specification](https://mqtt.org/)
- [ESP8266 MicroPython](https://docs.micropython.org/en/latest/esp8266/quickref.html)
- [OpenCV Face Detection](https://docs.opencv.org/master/db/d28/tutorial_cascade_classifier.html)
- [Node.js WebSocket](https://github.com/websockets/ws)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👥 Team

- **Back-benchers** - IoT & Vision Systems
- **Contributors**: [List contributors here]

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/paradie2to4/face_servo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/paradie2to4/face_servo/discussions)
- **Email**: [contact@example.com]

---

## 📦 Dependencies

### Backend
- mqtt ^5.3.0
- ws ^8.16.0
- node ^16.0.0

### PC Vision
- opencv-python
- paho-mqtt
- numpy

### ESP8266
- MicroPython 1.19+
- umqtt.simple (built-in)

---

## 🔗 References

- **Gabriel Baziramwabo** – [ResearchGate](https://www.researchgate.net/profile/Gabriel-Baziramwabo)
- **BenaxMedia** – [YouTube Channel](https://www.youtube.com/@BenaxMedia)

---

**Last Updated**: February 2026  
**Status**: ✅ Active Development
