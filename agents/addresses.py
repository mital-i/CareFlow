"""
Agentverse addresses for all 5 CareFlow agents.
All parts import agent addresses from this file.
Fill in real addresses after registering on Agentverse.
"""
import os

# Populated after Agentverse registration; env vars keep local/dev addresses flexible.
AGENT1_ADDRESS = os.getenv("AGENT1_ADDRESS", "agent1q...")  # Vital Monitoring Agent
AGENT2_ADDRESS = os.getenv("AGENT2_ADDRESS", "agent1q...")  # Risk Assessment Agent
AGENT3_ADDRESS = os.getenv("AGENT3_ADDRESS", "agent1q...")  # Care Coordination Agent
AGENT4_ADDRESS = os.getenv("AGENT4_ADDRESS", "agent1q...")  # Patient Agent
AGENT5_ADDRESS = os.getenv("AGENT5_ADDRESS", "agent1q...")  # Provider Agent
