import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
from flask import Flask, request, jsonify
import queue

# Page configuration
st.set_page_config(
    page_title="IoT API Server & Visualizer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .api-endpoint {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
    }
    .sensor-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)
# Obtener data_queue o inicializar con valor por defecto
data_queue = st.session_state.get('data_queue', [])

# Initialize session state
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = []
if 'api_server_running' not in st.session_state:
    st.session_state.api_server_running = False
if 'data_queue' not in st.session_state:
    st.session_state.data_queue = queue.Queue()
if 'server_port' not in st.session_state:
    st.session_state.server_port = 5002

# Flask API Server
app = Flask(__name__)

@app.route('/sensor/data', methods=['POST'])
def receive_sensor_data():
    """Endpoint para recibir datos de sensores via POST"""
    try:
        data = request.get_json()
        st.session_state.data_queue = queue.Queue()

        # Validar que se recibieron datos
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        # Agregar timestamp
        data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data['datetime'] = datetime.now()
        
        # Poner los datos en la cola para que Streamlit los procese
        if 'data_queue' not in st.session_state:
         st.session_state.data_queue = queue.Queue()
        
        st.session_state.data_queue.put(data)
        
        return jsonify({
            "status": "success",
            "message": "Data received successfully",
            "received_data": data
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sensor/status', methods=['GET'])
def api_status():
    """Endpoint para verificar el estado de la API"""
    return jsonify({
        "status": "running",
        "message": "Sensor API is running",
        "endpoints": {
            "POST /sensor/data": "Receive sensor data",
            "GET /sensor/status": "Check API status",
            "GET /sensor/latest": "Get latest sensor reading"
        },
        "total_readings": len(st.session_state.sensor_data)
    }), 200

@app.route('/sensor/latest', methods=['GET'])
def get_latest_data():
    """Endpoint para obtener la última lectura"""
    if st.session_state.sensor_data:
        latest = st.session_state.sensor_data[-1].copy()
        # Remover datetime para serialización JSON
        if 'datetime' in latest:
            del latest['datetime']
        return jsonify(latest), 200
    else:
        return jsonify({"message": "No data available"}), 404

def run_flask_server(port):
    """Ejecutar el servidor Flask en un hilo separado"""
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def process_queue_data():
    """Procesar datos de la cola y agregarlos a session_state"""
    while not st.session_state.data_queue.empty():
        try:
            data = st.session_state.data_queue.get_nowait()
            st.session_state.sensor_data.append(data)
            
            # Mantener solo los últimos 1000 registros
            if len(st.session_state.sensor_data) > 1000:
                st.session_state.sensor_data = st.session_state.sensor_data[-1000:]
        except queue.Empty:
            break

# Main title
st.markdown('<h1 class="main-header">📡 IoT API Server & Real-time Visualizer</h1>', unsafe_allow_html=True)

# Sidebar - API Configuration
st.sidebar.header("🔧 API Server Configuration")

# Server port configuration
server_port = st.sidebar.number_input(
    "Server Port", 
    min_value=5000, 
    max_value=9999, 
    value=st.session_state.server_port,
    help="Puerto donde se ejecutará la API"
)

# Server control
if not st.session_state.api_server_running:
    if st.sidebar.button("🚀 Start API Server", type="primary"):
        try:
            # Iniciar servidor Flask en un hilo separado
            server_thread = threading.Thread(
                target=run_flask_server, 
                args=(server_port,),
                daemon=True
            )
            server_thread.start()
            st.session_state.api_server_running = True
            st.session_state.server_port = server_port
            #st.session_state.data_queue = queue.Queue()
            st.sidebar.success(f"✅ API Server started on port {server_port}")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Error starting server: {str(e)}")
else:
    if st.sidebar.button("🛑 Stop Server", type="secondary"):
        st.session_state.api_server_running = False
        st.sidebar.info("Server stopped (restart app to fully stop)")
        st.rerun()

# Server status
if st.session_state.api_server_running:
    st.sidebar.success(f"🟢 API Server Running on port {st.session_state.server_port}")
else:
    st.sidebar.info("🔴 API Server Stopped")

# Auto-refresh
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5s)", value=True)

# API Documentation
with st.sidebar.expander("📚 API Documentation"):
    st.markdown(f"""
    **Base URL:** `http://localhost:{st.session_state.server_port}`
    
    **Endpoints:**
    - `POST /sensor/data` - Enviar datos de sensores
    - `GET /sensor/status` - Estado de la API
    - `GET /sensor/latest` - Última lectura
    
    **Ejemplo POST:**
    ```json
    {{
        "temperature": 25.5,
        "humidity": 60.2,
        "pressure": 1013.25,
        "sensor_id": "ESP32_001"
    }}
    ```
    """)

# Process incoming data from queue
process_queue_data()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Real-time Dashboard", "🔧 API Testing", "📈 Data Analytics", "📋 API Logs"])

# Tab 1: Real-time Dashboard
with tab1:
    st.markdown('<h2 class="section-header">Real-time Sensor Dashboard</h2>', unsafe_allow_html=True)
    
    # API Server Status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state.api_server_running:
            st.markdown('<div class="metric-card"><h3>🟢 API Status</h3><p>Running</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card"><h3>🔴 API Status</h3><p>Stopped</p></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="metric-card"><h3>🔌 Port</h3><p>{st.session_state.server_port}</p></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="metric-card"><h3>📊 Total Readings</h3><p>{len(st.session_state.sensor_data)}</p></div>', unsafe_allow_html=True)
    
    with col4:
        last_update = "Never"
        if st.session_state.sensor_data:
            last_update = st.session_state.sensor_data[-1]['timestamp']
        st.markdown(f'<div class="metric-card"><h3>🕒 Last Update</h3><p>{last_update}</p></div>', unsafe_allow_html=True)
    
    # Current API Endpoints
    st.subheader("🔗 Available API Endpoints")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="api-endpoint">
            <strong>POST</strong> http://localhost:{st.session_state.server_port}/sensor/data<br>
            <small>Recibe datos de sensores en formato JSON</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="api-endpoint">
            <strong>GET</strong> http://localhost:{st.session_state.server_port}/sensor/status<br>
            <small>Verifica el estado de la API</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Latest sensor readings
    if st.session_state.sensor_data:
        st.subheader("📡 Latest Sensor Readings")
        
        latest_data = st.session_state.sensor_data[-1]
        
        # Display metrics for numeric values
        numeric_data = {k: v for k, v in latest_data.items() 
                       if isinstance(v, (int, float)) and k not in ['datetime']}
        
        if numeric_data:
            cols = st.columns(min(len(numeric_data), 4))
            for i, (key, value) in enumerate(numeric_data.items()):
                with cols[i % 4]:
                    st.metric(
                        label=key.replace('_', ' ').title(),
                        value=f"{value:.2f}" if isinstance(value, float) else str(value)
                    )
        
        # Show all data
        with st.expander("🔍 View Complete Latest Reading"):
            display_data = {k: v for k, v in latest_data.items() if k != 'datetime'}
            st.json(display_data)
        
        # Real-time charts
        if len(st.session_state.sensor_data) > 1:
            st.subheader("📈 Real-time Sensor Charts")
            
            df = pd.DataFrame(st.session_state.sensor_data)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols and 'datetime' in df.columns:
                # Select sensors to plot
                selected_sensors = st.multiselect(
                    "Select sensors to plot:",
                    numeric_cols,
                    default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols
                )
                
                if selected_sensors:
                    # Create subplots
                    fig = go.Figure()
                    
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
                    
                    for i, sensor in enumerate(selected_sensors):
                        fig.add_trace(go.Scatter(
                            x=df['datetime'],
                            y=df[sensor],
                            mode='lines+markers',
                            name=sensor.replace('_', ' ').title(),
                            line=dict(color=colors[i % len(colors)]),
                            marker=dict(size=6)
                        ))
                    
                    fig.update_layout(
                        title="Real-time Sensor Data",
                        xaxis_title="Time",
                        yaxis_title="Value",
                        hovermode='x unified',
                        height=500,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Waiting for sensor data... Start the API server and send POST requests to begin visualization.")
        
        # Show example curl command
        st.subheader("📝 Example Usage")
        st.code(f"""
# Ejemplo con curl:
curl -X POST http://localhost:{st.session_state.server_port}/sensor/data \\
     -H "Content-Type: application/json" \\
     -d '{{"temperature": 25.5, "humidity": 60.2, "pressure": 1013.25, "sensor_id": "ESP32_001"}}'

# Ejemplo con Python requests:
import requests
data = {{"temperature": 25.5, "humidity": 60.2, "pressure": 1013.25}}
response = requests.post("http://localhost:{st.session_state.server_port}/sensor/data", json=data)
print(response.json())
        """, language="bash")

# Tab 2: API Testing
with tab2:
    st.markdown('<h2 class="section-header">API Testing Interface</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧪 Test API Endpoints")
        
        # Test API status
        if st.button("🔍 Test API Status"):
            if st.session_state.api_server_running:
                try:
                    response = requests.get(f"http://localhost:{st.session_state.server_port}/sensor/status")
                    st.success("✅ API is responding!")
                    st.json(response.json())
                except Exception as e:
                    st.error(f"❌ API not responding: {str(e)}")
            else:
                st.warning("⚠️ API server is not running")
        
        # Test POST endpoint
        st.subheader("📤 Send Test Sensor Data")
        
        # Sample data generator
        if st.button("🎲 Generate Random Data"):
            import random
            test_data = {
                "temperature": round(random.uniform(20, 30), 2),
                "humidity": round(random.uniform(40, 80), 2),
                "pressure": round(random.uniform(1000, 1020), 2),
                "light": round(random.uniform(0, 1000), 1),
                "sensor_id": f"TEST_{random.randint(100, 999)}"
            }
            
            if st.session_state.api_server_running:
                try:
                    response = requests.post(
                        f"http://localhost:{st.session_state.server_port}/sensor/data",
                        json=test_data
                    )
                    if response.status_code == 200:
                        st.success("✅ Test data sent successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Request failed: {str(e)}")
            else:
                st.warning("⚠️ Start the API server first")
        
        # Custom data input
        st.subheader("✏️ Send Custom Data")
        custom_json = st.text_area(
            "JSON Data",
            value='{\n  "temperature": 25.5,\n  "humidity": 60.2,\n  "sensor_id": "custom_test"\n}',
            height=150
        )
        
        if st.button("📤 Send Custom Data"):
            try:
                data = json.loads(custom_json)
                if st.session_state.api_server_running:
                    response = requests.post(
                        f"http://localhost:{st.session_state.server_port}/sensor/data",
                        json=data
                    )
                    if response.status_code == 200:
                        st.success("✅ Custom data sent successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                else:
                    st.warning("⚠️ Start the API server first")
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format")
            except Exception as e:
                st.error(f"❌ Request failed: {str(e)}")
    
    with col2:
        st.subheader("📊 API Response Monitor")
        
        # Show recent API calls
        if st.session_state.sensor_data:
            st.write(f"**Recent API Calls:** {len(st.session_state.sensor_data)}")
            
            # Show last 5 calls
            recent_data = st.session_state.sensor_data[-5:]
            for i, data in enumerate(reversed(recent_data)):
                with st.expander(f"Call #{len(st.session_state.sensor_data)-i} - {data['timestamp']}"):
                    display_data = {k: v for k, v in data.items() if k != 'datetime'}
                    st.json(display_data)
        else:
            st.info("No API calls received yet")

# Tab 3: Data Analytics
with tab3:
    st.markdown('<h2 class="section-header">Data Analytics</h2>', unsafe_allow_html=True)
    
    if st.session_state.sensor_data:
        df = pd.DataFrame(st.session_state.sensor_data)
        
        # Statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Statistics")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                st.dataframe(df[numeric_cols].describe())
        
        with col2:
            st.subheader("📈 Data Trends")
            if len(numeric_cols) > 0:
                selected_metric = st.selectbox("Select metric for trend analysis:", numeric_cols)
                
                if len(df) > 1:
                    # Calculate trend
                    recent_avg = df[selected_metric].tail(10).mean()
                    overall_avg = df[selected_metric].mean()
                    trend = "📈 Increasing" if recent_avg > overall_avg else "📉 Decreasing"
                    
                    st.metric(
                        f"{selected_metric.title()} Trend",
                        f"{recent_avg:.2f}",
                        f"{recent_avg - overall_avg:.2f}"
                    )
                    st.write(f"**Trend:** {trend}")
        
        # Data export
        st.subheader("💾 Export Data")
        if st.button("📥 Download CSV"):
            csv_df = df.drop('datetime', axis=1) if 'datetime' in df.columns else df
            csv = csv_df.to_csv(index=False)
            st.download_button(
                label="Download Sensor Data",
                data=csv,
                file_name=f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No data available for analytics")

# Tab 4: API Logs
with tab4:
    st.markdown('<h2 class="section-header">API Activity Logs</h2>', unsafe_allow_html=True)
    
    if st.session_state.sensor_data:
        st.subheader(f"📋 Total API Calls: {len(st.session_state.sensor_data)}")
        
        # Recent activity
        df = pd.DataFrame(st.session_state.sensor_data)
        
        # Activity timeline
        if 'datetime' in df.columns:
            st.subheader("📊 Activity Timeline")
            
            # Group by hour
            df['hour'] = df['datetime'].dt.floor('H')
            hourly_counts = df.groupby('hour').size().reset_index(name='count')
            
            fig = px.bar(
                hourly_counts, 
                x='hour', 
                y='count',
                title="API Calls per Hour",
                labels={'hour': 'Time', 'count': 'Number of Calls'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed logs
        st.subheader("📜 Detailed API Logs")
        
        # Show pagination
        logs_per_page = 10
        total_logs = len(st.session_state.sensor_data)
        total_pages = (total_logs - 1) // logs_per_page + 1
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1), index=total_pages-1)
            start_idx = (page - 1) * logs_per_page
            end_idx = min(start_idx + logs_per_page, total_logs)
            logs_to_show = st.session_state.sensor_data[start_idx:end_idx]
        else:
            logs_to_show = st.session_state.sensor_data
        
        # Display logs
        for i, log in enumerate(reversed(logs_to_show)):
            log_num = total_logs - i if total_pages == 1 else total_logs - start_idx - i
            with st.expander(f"📝 Log #{log_num} - {log['timestamp']}"):
                display_log = {k: v for k, v in log.items() if k != 'datetime'}
                st.json(display_log)
        
        # Clear logs
        if st.button("🗑️ Clear All Logs"):
            st.session_state.sensor_data = []
            st.success("✅ All logs cleared!")
            st.rerun()
    else:
        st.info("📋 No API activity logs available")

# Auto-refresh logic
if auto_refresh and st.session_state.api_server_running:
    time.sleep(5)
    st.rerun()

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>📡 IoT API Server & Visualizer | Built with Streamlit & Flask</p>
</div>
""", unsafe_allow_html=True)