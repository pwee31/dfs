import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

# Sample NBA DFS Player Data (Replace with real data if available)
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
st.title("NBA DFS Optimizer - DraftKings Edition")
st.write("Generate optimized NBA DFS lineups based on DraftKings salary cap.")

# DraftKings Salary Cap & Position Constraints
salary_cap = 50000  # DraftKings cap
positions = {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1, "G": 1, "F": 1, "UTIL": 1}

# User Input for Custom Salary Cap
user_salary_cap = st.number_input("Set Salary Cap", min_value=40000, max_value=60000, value=salary_cap, step=500)

# Optimization button
if st.button("Generate Optimal Lineup"):

    # Create optimization problem
    prob = LpProblem("NBA_DFS_Optimizer", LpMaximize)

    # Create player variables (binary: 0 = not selected, 1 = selected)
    player_vars = {p["Name"]: LpVariable(p["Name"], 0, 1, cat="Binary") for p in players_data}

    # Objective: Maximize projected points
    prob += lpSum(player_vars[p["Name"]] * p["Projection"] for p in players_data)

    # Salary cap constraint
    prob += lpSum(player_vars[p["Name"]] * p["Salary"] for p in players_data) <= user_salary_cap

    # Position constraints
    for pos, count in positions.items():
        prob += lpSum(player_vars[p["Name"]] for p in players_data if p["Position"] == pos) >= count

    # Solve the problem
    prob.solve()

    # Get selected players
    selected_players = [p["Name"] for p in players_data if player_vars[p["Name"]].value() == 1]

    # Display optimal lineup
    if selected_players:
        st.write("### Optimal Lineup")
        optimal_lineup_df = players_df[players_df["Name"].isin(selected_players)]
        st.dataframe(optimal_lineup_df)
    else:
        st.write("⚠️ No valid lineup found. Adjust salary cap or player pool.")
