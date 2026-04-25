"""Central registry of all agent Agentverse addresses.

Fill these in after running each agent for the first time — the address is
printed to console on startup. All modules import from here.
"""
import os

MONITOR_AGENT_ADDRESS = os.getenv("AGENT_MONITOR_ADDRESS", "agent1q_FILL_MONITOR")
COORDINATOR_AGENT_ADDRESS = os.getenv("AGENT_COORDINATOR_ADDRESS", "agent1q_FILL_COORDINATOR")
