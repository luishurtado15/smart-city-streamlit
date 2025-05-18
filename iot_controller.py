import streamlit as st
import requests
import json
import google.generativeai as genai
import time
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="IoT Device Controller & Gemini AI",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    .sensor-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
    }
    .actuator-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = []
if 'actuator_states' not in st.session_state:
    st.session_state.actuator_states = []
if 'gemini_conversations' not in st.session_state:
    st.session_state.gemini_conversations = []
if 'device_status' not in st.session_state:
    st.session_state.device_status = "Unknown"
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

# Sidebar configuration
st.sidebar.header("🔧 Device Configuration")

# ESP32 IP configuration
base_url = st.sidebar.text_input(
    "ESP32 Base URL",
    value="http://192.168.43.64",
    help="Enter the IP address of your ESP32 device"
)

# Auto-refresh settings
st.session_state.auto_refresh = st.sidebar.checkbox(
    "Auto-refresh sensor data",
    value=st.session_state.auto_refresh
)

if st.session_state.auto_refresh:
    refresh_interval = st.sidebar.selectbox(
        "Refresh interval (seconds)",
        options=[1, 2, 5, 10, 30],
        index=2
    )

# Main title
st.markdown('<h1 class="main-header">🌐 IoT Device Controller & Gemini AI</h1>', unsafe_allow_html=True)

# API functions based on your original code
def get_sensor():
    """Makes GET /sensor and returns the JSON."""
    url = f"{base_url}/sensor"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()

def set_actuator(state: int):
    """Makes POST /actuator with JSON {'state': state} and returns the JSON."""
    url = f"{base_url}/actuator"
    payload = {"state": state}
    resp = requests.post(url, json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()

# Function to check device status
def check_device_status():
    """Check if the ESP32 device is online."""
    try:
        response = requests.get(f"{base_url}/sensor", timeout=3)
        if response.status_code == 200:
            return "Online"
        else:
            return "Offline"
    except:
        return "Offline"

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Device Dashboard", "🔧 Manual Control", "🤖 Gemini AI", "📈 Data Analytics"])

# Tab 1: Device Dashboard
with tab1:
    st.markdown('<h2 class="section-header">Device Dashboard</h2>', unsafe_allow_html=True)
    
    # Device status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Check Device Status", type="primary"):
            st.session_state.device_status = check_device_status()
        
        if st.session_state.device_status == "Online":
            st.markdown('<p class="status-online">🟢 Device Status: Online</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-offline">🔴 Device Status: Offline</p>', unsafe_allow_html=True)
    
    with col2:
        st.metric("Base URL", base_url.split("//")[1] if "//" in base_url else base_url)
    
    with col3:
        st.metric("Total Data Points", len(st.session_state.sensor_data))
    
    # Real-time sensor data
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="sensor-card">', unsafe_allow_html=True)
        st.subheader("📡 Sensor Data")
        
        if st.button("📊 Read Sensor Data", type="secondary") or st.session_state.auto_refresh:
            try:
                with st.spinner("Reading sensor data..."):
                    sensor_data = get_sensor()
                    timestamp = datetime.now()
                    
                    # Add timestamp to sensor data
                    sensor_data['timestamp'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    sensor_data['datetime'] = timestamp
                    
                    # Store in session state
                    st.session_state.sensor_data.append(sensor_data)
                    
                    # Keep only last 100 readings
                    if len(st.session_state.sensor_data) > 100:
                        st.session_state.sensor_data = st.session_state.sensor_data[-100:]
                    
                    st.success("✅ Sensor data updated successfully!")
                    
                    # Display current readings
                    if sensor_data:
                        for key, value in sensor_data.items():
                            if key not in ['timestamp', 'datetime']:
                                st.metric(key.capitalize(), value)
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {str(e)}")
                st.session_state.device_status = "Offline"
            except Exception as e:
                st.error(f"❌ Error reading sensor: {str(e)}")
        
        # Display last reading if available
        if st.session_state.sensor_data:
            last_reading = st.session_state.sensor_data[-1]
            st.write("**Last Reading:**")
            st.json({k: v for k, v in last_reading.items() if k not in ['datetime']})
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="actuator-card">', unsafe_allow_html=True)
        st.subheader("⚡ Quick Actuator Control")
        
        # Quick actuator buttons
        col_on, col_off = st.columns(2)
        
        with col_on:
            if st.button("🟢 Turn ON", type="primary"):
                try:
                    with st.spinner("Setting actuator..."):
                        result = set_actuator(1)
                        st.session_state.actuator_states.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'state': 1,
                            'response': result
                        })
                        st.success("✅ Actuator turned ON")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col_off:
            if st.button("🔴 Turn OFF", type="secondary"):
                try:
                    with st.spinner("Setting actuator..."):
                        result = set_actuator(0)
                        st.session_state.actuator_states.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'state': 0,
                            'response': result
                        })
                        st.success("✅ Actuator turned OFF")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Display last actuator state
        if st.session_state.actuator_states:
            last_state = st.session_state.actuator_states[-1]
            state_text = "ON" if last_state['state'] == 1 else "OFF"
            st.write(f"**Last State:** {state_text}")
            st.write(f"**Time:** {last_state['timestamp']}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Tab 2: Manual Control
with tab2:
    st.markdown('<h2 class="section-header">Manual Device Control</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📡 Sensor Operations")
        
        # Manual sensor reading
        if st.button("📊 Get Sensor Data", type="primary"):
            try:
                with st.spinner("Fetching sensor data..."):
                    data = get_sensor()
                    st.success("✅ Data retrieved successfully!")
                    st.json(data)
                    
                    # Store with timestamp
                    data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data['datetime'] = datetime.now()
                    st.session_state.sensor_data.append(data)
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to device. Check the IP address and ensure the device is online.")
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. Device might be slow to respond.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
        
        # Custom endpoint testing
        st.subheader("🔧 Custom Endpoint")
        custom_endpoint = st.text_input("Custom endpoint", value="/sensor", help="Enter endpoint path (e.g., /status, /config)")
        method = st.selectbox("Method", ["GET", "POST"])
        
        if method == "POST":
            custom_payload = st.text_area("JSON Payload", value='{"key": "value"}')
        
        if st.button("Send Custom Request"):
            try:
                url = f"{base_url}{custom_endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    payload = json.loads(custom_payload)
                    response = requests.post(url, json=payload, timeout=5)
                
                st.success(f"✅ Response (Status: {response.status_code})")
                try:
                    st.json(response.json())
                except:
                    st.text(response.text)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("⚡ Actuator Control")
        
        # Actuator state input
        actuator_state = st.selectbox(
            "Actuator State",
            options=[0, 1],
            format_func=lambda x: "OFF (0)" if x == 0 else "ON (1)"
        )
        
        if st.button("🎯 Set Actuator State", type="primary"):
            try:
                with st.spinner("Setting actuator state..."):
                    result = set_actuator(actuator_state)
                    st.success(f"✅ Actuator set to {'ON' if actuator_state == 1 else 'OFF'}")
                    st.json(result)
                    
                    # Store state change
                    st.session_state.actuator_states.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'state': actuator_state,
                        'response': result
                    })
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to device. Check the IP address and ensure the device is online.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
        
        # Actuator state history
        if st.session_state.actuator_states:
            st.subheader("📝 Recent Actuator States")
            for i, state in enumerate(reversed(st.session_state.actuator_states[-5:])):
                state_icon = "🟢" if state['state'] == 1 else "🔴"
                state_text = "ON" if state['state'] == 1 else "OFF"
                st.write(f"{state_icon} {state['timestamp']} - {state_text}")

# Tab 3: Gemini AI Integration
with tab3:
    st.markdown('<h2 class="section-header">Gemini AI for IoT Analysis</h2>', unsafe_allow_html=True)
    
    # Gemini API key configuration
    gemini_api_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key"
    )
    
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🤖 AI Analysis Options")
            
            analysis_type = st.selectbox(
                "Analysis Type",
                [
                    "Analyze Current Sensor Data",
                    "Analyze Actuator Performance",
                    "Generate Device Report",
                    "Predict Maintenance Needs",
                    "Custom Analysis"
                ]
            )
            
            if analysis_type == "Custom Analysis":
                user_prompt = st.text_area(
                    "Your Question",
                    height=150,
                    placeholder="Ask about your IoT device data..."
                )
            else:
                # Pre-built prompts
                prompts = {
                    "Analyze Current Sensor Data": f"Analyze this IoT sensor data and provide insights: {st.session_state.sensor_data[-5:] if st.session_state.sensor_data else 'No data available'}",
                    "Analyze Actuator Performance": f"Analyze the actuator state changes and performance: {st.session_state.actuator_states[-10:] if st.session_state.actuator_states else 'No data available'}",
                    "Generate Device Report": f"Generate a comprehensive report for this IoT device based on sensor data: {st.session_state.sensor_data[-10:] if st.session_state.sensor_data else 'No data available'} and actuator states: {st.session_state.actuator_states[-5:] if st.session_state.actuator_states else 'No data available'}",
                    "Predict Maintenance Needs": f"Based on this sensor data, predict potential maintenance needs: {st.session_state.sensor_data[-10:] if st.session_state.sensor_data else 'No data available'}"
                }
                user_prompt = prompts[analysis_type]
                st.text_area("Generated Prompt", value=user_prompt, height=150, disabled=True)
            
            # Gemini settings
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
            max_tokens = st.number_input("Max Tokens", 100, 4000, 1000)
        
        with col2:
            st.subheader("🗨️ AI Analysis Results")
            
            if st.button("🚀 Analyze with Gemini", type="primary"):
                if user_prompt:
                    try:
                        model = genai.GenerativeModel('gemini-pro')
                        
                        with st.spinner("Analyzing with Gemini AI..."):
                            response = model.generate_content(
                                user_prompt,
                                generation_config=genai.types.GenerationConfig(
                                    temperature=temperature,
                                    max_output_tokens=max_tokens
                                )
                            )
                        
                        if response.text:
                            st.success("✅ Analysis complete!")
                            st.markdown(response.text)
                            
                            # Save conversation
                            st.session_state.gemini_conversations.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "analysis_type": analysis_type,
                                "prompt": user_prompt,
                                "response": response.text
                            })
                        else:
                            st.warning("⚠️ No response generated.")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please enter a prompt.")
        
        # Recent analyses
        if st.session_state.gemini_conversations:
            st.subheader("📋 Recent Analyses")
            for i, conv in enumerate(reversed(st.session_state.gemini_conversations[-3:])):
                with st.expander(f"{conv['analysis_type']} - {conv['timestamp']}"):
                    st.markdown(conv['response'])
    else:
        st.info("🔑 Please enter your Gemini API key in the sidebar to enable AI analysis.")

# Tab 4: Data Analytics
with tab4:
    st.markdown('<h2 class="section-header">Data Analytics & Visualization</h2>', unsafe_allow_html=True)
    
    if st.session_state.sensor_data:
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(st.session_state.sensor_data)
        
        # Data overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Overview")
            st.write(f"Total readings: {len(df)}")
            st.write(f"Time range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
            
            # Numeric columns for plotting
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                st.write("Available sensors:", ", ".join(numeric_cols))
        
        with col2:
            st.subheader("🔧 Visualization Settings")
            if 'datetime' in df.columns and len(df) > 1:
                chart_type = st.selectbox("Chart Type", ["Line Chart", "Scatter Plot", "Bar Chart"])
                
                if numeric_cols:
                    selected_sensors = st.multiselect(
                        "Select sensors to plot",
                        numeric_cols,
                        default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols
                    )
        
        # Plotting
        if 'datetime' in df.columns and numeric_cols and len(df) > 1:
            st.subheader("📈 Sensor Data Visualization")
            
            if chart_type == "Line Chart":
                fig = go.Figure()
                for sensor in selected_sensors:
                    fig.add_trace(go.Scatter(
                        x=df['datetime'],
                        y=df[sensor],
                        mode='lines+markers',
                        name=sensor.capitalize()
                    ))
                fig.update_layout(
                    title="Sensor Data Over Time",
                    xaxis_title="Time",
                    yaxis_title="Value",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Scatter Plot":
                if len(selected_sensors) >= 2:
                    fig = px.scatter(
                        df, 
                        x=selected_sensors[0], 
                        y=selected_sensors[1],
                        title=f"{selected_sensors[0].capitalize()} vs {selected_sensors[1].capitalize()}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Please select at least 2 sensors for scatter plot.")
        
        # Statistical summary
        if numeric_cols:
            st.subheader("📋 Statistical Summary")
            st.dataframe(df[numeric_cols].describe())
        
        # Raw data table
        with st.expander("🔍 View Raw Data"):
            st.dataframe(df.drop('datetime', axis=1) if 'datetime' in df.columns else df)
        
        # Export data
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Sensor Data as CSV"):
                csv = df.drop('datetime', axis=1).to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📥 Download Actuator Data as CSV"):
                if st.session_state.actuator_states:
                    actuator_df = pd.DataFrame(st.session_state.actuator_states)
                    csv = actuator_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"actuator_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    else:
        st.info("📊 No sensor data available yet. Start collecting data in the Device Dashboard tab.")

# Auto-refresh logic
if st.session_state.auto_refresh and 'refresh_interval' in locals():
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🌐 IoT Device Controller | Built with Streamlit | 🤖 Powered by Gemini AI</p>
</div>
""", unsafe_allow_html=True)