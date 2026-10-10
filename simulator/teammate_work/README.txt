GridGuard AI Twin — dynamic simulator preview

Files:
- simulator_preview.py: Streamlit application
- sensor_simulator.py: synthetic sensor readings and 60-sample model window
- grid_simulator.py: professional Plotly grid

Install (in your project virtual environment):
    python -m pip install streamlit streamlit-autorefresh numpy plotly

Run:
    python -m streamlit run simulator_preview.py

Notes:
- This preview uses synthetic readings and demo status/RUL rules.
- It does not connect to the teammate's trained prediction model.
- Voltage/current units and simulation equations are illustrative; confirm feature order,
  units, scaler, and time step with the model-training pipeline before AI integration.
