import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

# Sample NBA DFS Player Data (can be replaced with live projections)
players_data = [
    {"Name": "Luka Doncic", "Position": "PG", "Salary": 11000, "Projection": 55},
    {"Name": "Stephen Curry", "Position": "PG", "Salary": 9800, "Projection": 50},
    {"Name": "James Harden", "Position": "SG", "Salary": 9400, "Projection": 47},
    {"Name": "Devin Booker", "Position": "SG", "Salary": 8900, "Projection": 45},
    {"Name": "LeBron James", "Position": "SF", "Salary": 10200, "Projection": 52},
    {"Name": "Kevin Durant", "Position": "SF", "Salary": 9700, "Projection": 50},
    {"Name": "Jayson Tatum", "Position": "PF", "Salary": 9500, "Projection": 48},
    {"Name": "Giannis Antetokounmpo", "Position": "PF", "Salary": 11200, "Projection": 58},
    {"Name": "Nikola Jokic", "Position": "C", "Salary": 11300, "Projection": 60},
    {"Name": "Joel Embiid", "Position": "C", "Salary": 10900, "Projection": 57},
]

# Convert to DataFrame
players_df = pd.DataFrame(players_data)

# Streamlit UI
st.title("NBA DFS Optimizer")

salary_cap = st.number_input("Salary Cap", min_value=40000, max_value=60000, value=50000, step=500)

# Define DFS constraints (DraftKings format)
positions = {"PG": 2, "SG": 2, "SF": 2, "PF": 2, "C": 1}

# Create optimization problem
prob = LpProblem("NBA_DFS_Optimizer", LpMaximize)

# Create player variables (binary: 0 = not selected, 1 = selected)
player_vars = {p["Name"]: LpVariable(p["Name"], 0, 1, cat="Binary") for p in players_data}

# Objective: Maximize projected points
prob += lpSum(player_vars[p["Name"]] * p["Projection"] for p in players_data)

# Salary cap constraint
prob += lpSum(player_vars[p["Name"]] * p["Salary"] for p in players_data) <= salary_cap

# Position constraints
for pos, count in positions.items():
    prob += lpSum(player_vars[p["Name"]] for p in players_data if p["Position"] == pos) == count

# Solve the problem
prob.solve()

# Get selected players
selected_players = [p["Name"] for p in players_data if player_vars[p["Name"]].value() == 1]

# Display optimal lineup
if st.button("Generate Optimal Lineup"):
    # Solve the optimization problem
    prob.solve()

    # Get selected players
    selected_players = [p["Name"] for p in players_data if player_vars[p["Name"]].value() == 1]

    # Display optimal lineup
    if selected_players:
        st.write("### Optimal Lineup")
        st.dataframe(players_df[players_df["Name"].isin(selected_players)])
    else:
        st.write("No valid lineup found. Adjust salary cap or data.")
