#!/usr/bin/env node
/**
 * Backend API Service
 * Bridges MQTT messages to WebSocket clients
 */

const mqtt = require('mqtt');
const WebSocket = require('ws');
const http = require('http');

// CONFIGURATION
const MQTT_BROKER = 'mqtt://157.173.101.159:1883';
const WS_PORT = 9002;
const TEAM_ID = 'BACK-BENCHERS';

// MQTT Topics
const TOPIC_MOVEMENT = `vision/${TEAM_ID}/movement`;
const TOPIC_HEARTBEAT = `vision/${TEAM_ID}/heartbeat`;
const TOPIC_STATUS = `iot/status/#`;

// ========================================
// MQTT Client Setup
// ========================================
console.log('Connecting to MQTT broker...');
const mqttClient = mqtt.connect(MQTT_BROKER, {
    clientId: `backend_api_${TEAM_ID}_${Date.now()}`,
    clean: true,
    reconnectPeriod: 1000
});

mqttClient.on('connect', () => {
    console.log('✓ Connected to MQTT broker');
    
    // Subscribe to topics
    mqttClient.subscribe(TOPIC_MOVEMENT, (err) => {
        if (!err) {
            console.log(`✓ Subscribed to: ${TOPIC_MOVEMENT}`);
        }
    });
    
    mqttClient.subscribe(TOPIC_HEARTBEAT, (err) => {
        if (!err) {
            console.log(`✓ Subscribed to: ${TOPIC_HEARTBEAT}`);
        }
    });
    
    mqttClient.subscribe(TOPIC_STATUS, (err) => {
        if (!err) {
            console.log(`✓ Subscribed to: ${TOPIC_STATUS}`);
        }
    });
});

mqttClient.on('error', (error) => {
    console.error('MQTT Error:', error);
});

mqttClient.on('offline', () => {
    console.log('✗ MQTT client offline');
});

mqttClient.on('reconnect', () => {
    console.log('→ Reconnecting to MQTT...');
});

// WebSocket Server Setup
const server = http.createServer((req, res) => {
    // Simple health check endpoint
    if (req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            mqtt: mqttClient.connected,
            ws_clients: wss.clients.size,
            timestamp: Date.now()
        }));
    } else {
        res.writeHead(404);
        res.end('Not Found');
    }
});

const wss = new WebSocket.Server({ server });

console.log(`WebSocket server starting on port ${WS_PORT}...`);

// Track connected clients
let clientCount = 0;

wss.on('connection', (ws, req) => {
    const clientId = ++clientCount;
    const clientIp = req.socket.remoteAddress;
    
    console.log(`✓ WebSocket client #${clientId} connected from ${clientIp}`);
    console.log(`  Total clients: ${wss.clients.size}`);
    
    // Send welcome message
    ws.send(JSON.stringify({
        type: 'welcome',
        message: 'Connected to Face Tracking Backend',
        team_id: TEAM_ID,
        timestamp: Date.now()
    }));
    
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            console.log(`← Client #${clientId}:`, data);
            
        } catch (error) {
            console.error('Error parsing client message:', error);
        }
    });
    
    ws.on('close', () => {
        console.log(`✗ Client #${clientId} disconnected`);
        console.log(`  Total clients: ${wss.clients.size}`);
    });
    
    ws.on('error', (error) => {
        console.error(`Client #${clientId} error:`, error.message);
    });
});

// MQTT to WebSocket Bridge
mqttClient.on('message', (topic, message) => {
    const msgString = message.toString();
    let payload;
    let messageType;

    try {

        // ===== Route by topic =====
        if (topic === TOPIC_MOVEMENT) {
            messageType = 'movement';
            payload = JSON.parse(msgString);

        } else if (topic === TOPIC_HEARTBEAT) {
            messageType = 'heartbeat';
            payload = JSON.parse(msgString);

        } else if (topic.startsWith('iot/status/')) {
            messageType = 'device_status';

            // Status messages are plain text
            payload = {
                status: msgString
            };

        } else {
            messageType = 'unknown';
            payload = { raw: msgString };
        }

        const wsMessage = {
            type: messageType,
            topic: topic,
            data: payload,
            received_at: Date.now()
        };

        let sentCount = 0;
        wss.clients.forEach((client) => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify(wsMessage));
                sentCount++;
            }
        });

        if (sentCount > 0) {
            console.log(`→ [${messageType}] Broadcast to ${sentCount} client(s)`);
        }

    } catch (error) {
        console.error('Error processing MQTT message on topic:', topic);
        console.error('Message content:', msgString);
        console.error(error);
    }
});

server.listen(WS_PORT, () => {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`✓ Backend API Service Running`);
    console.log(`${'='.repeat(50)}`);
    console.log(`WebSocket Server: ws://localhost:${WS_PORT}`);
    console.log(`HTTP Health Check: http://localhost:${WS_PORT}/health`);
    console.log(`Team ID: ${TEAM_ID}`);
    console.log(`MQTT Topics:`);
    console.log(`  - ${TOPIC_MOVEMENT}`);
    console.log(`  - ${TOPIC_HEARTBEAT}`);
    console.log(`  - ${TOPIC_STATUS}`);
    console.log(`${'='.repeat(50)}\n`);
});

// Graceful Shutdown
process.on('SIGINT', () => {
    console.log('\n\n✓ Shutting down gracefully...');
    
    // Close WebSocket server
    wss.clients.forEach((client) => {
        client.close();
    });
    
    wss.close(() => {
        console.log('✓ WebSocket server closed');
    });
    
    // Disconnect MQTT
    mqttClient.end(() => {
        console.log('✓ MQTT client disconnected');
        process.exit(0);
    });
});

// Error handling
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});