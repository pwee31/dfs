import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PulpSolverError
import random

# Load NBA DFS CSV Data from File Uploader
def load_dfs_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        st.write("### Detected Columns in CSV:")
        st.write(df.columns.tolist())
        
        # Mapping based on detected column names
        rename_mapping = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "position": "Position",
            "salary": "Salary",
            "ppg_projection": "Projection"
        }
        
        df = df.rename(columns=rename_mapping)
        
        # Create a 'Name' column by combining first and last name
        if "First Name" in df.columns and "Last Name" in df.columns:
            df["Name"] = df["First Name"] + " " + df["Last Name"]
        
        missing_columns = [col for col in ["Name", "Position", "Salary", "Projection"] if col not in df.columns]
        
        if missing_columns:
            st.error(f"⚠️ Missing columns in CSV: {missing_columns}")
            return pd.DataFrame()
        
        df = df[["Name", "Position", "Salary", "Projection"]]
        df = df[df["Projection"] >= 15]  # Remove players projected under 15 points
        df["Value"] = df["Projection"] / df["Salary"]  # Compute value metric for better optimization
        return df.sort_values(by="Projection", ascending=False)
    except Exception as e:
        st.error(f"Error loading DFS data: {e}")
        return pd.DataFrame()

# Streamlit UI
st.title("NBA DFS Optimizer - DraftKings Edition")
st.write("Upload your DFS CSV file to generate optimized lineups.")

# File uploader for user to upload their CSV
uploaded_file = st.file_uploader("Upload DFS CSV", type=["csv"])

if uploaded_file:
    players_df = load_dfs_csv(uploaded_file)
else:
    players_df = pd.DataFrame()
    st.write("⚠️ No file uploaded. Please upload a valid DFS CSV file.")

# Show Data
if not players_df.empty:
    st.write("### Loaded Player Data")
    st.dataframe(players_df)

# Check if "Name" exists before proceeding
if "Name" not in players_df.columns:
    st.error("⚠️ Critical Error: 'Name' column not found in uploaded CSV. Check column headers.")
    st.stop()

# DraftKings Salary Cap & Roster Constraints
salary_cap = 50000
min_salary_cap = 45000  # Minimum salary cap for valid lineups
roster_slots = {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1, "G": 1, "F": 1, "UTIL": 1}
num_players = sum(roster_slots.values())

# User Input for Salary Cap, Number of Lineups, and Player Locks/Exclusions
user_salary_cap = st.number_input("Set Salary Cap", min_value=45000, max_value=50000, value=salary_cap, step=500)
num_lineups = st.slider("Number of Lineups", 1, 5, 3)
locked_players = st.multiselect("Lock Players (Ensure they are in every lineup)", players_df["Name"].tolist())
excluded_players = st.multiselect("Exclude Players (Remove them from all lineups)", players_df["Name"].tolist())
max_exposure = st.slider("Max Exposure % (Limit player repetition across lineups)", 10, 100, 80, step=10)

# Exclude excluded players from selection
players_df = players_df[~players_df["Name"].isin(excluded_players)]

# Store used lineups to prevent duplicates
used_lineups = set()
player_usage = {name: 0 for name in players_df["Name"]}

# Optimization button
if st.button("Generate Optimal Lineups") and not players_df.empty:
    optimal_lineups = []
    top_players = players_df  # Use all players projected >= 15 points
    max_usage = (num_lineups * (max_exposure / 100))  # Max times a player can appear
    
    for i in range(num_lineups):
        prob = LpProblem(f"NBA_DFS_Optimizer_{i+1}", LpMaximize)
        player_vars = {p["Name"]: LpVariable(p["Name"], 0, 1, cat="Binary") for _, p in top_players.iterrows()}
        
        # Objective: Maximize projected points while balancing value metric
        prob += lpSum(player_vars[p["Name"]] * (p["Projection"] + (p["Value"] * 10)) for _, p in top_players.iterrows())
        
        # Salary cap constraint (Ensure salary falls between 45,000 and 50,000)
        total_salary = lpSum(player_vars[p["Name"]] * p["Salary"] for _, p in top_players.iterrows())
        prob += total_salary <= user_salary_cap
        prob += total_salary >= min_salary_cap
        
        # Ensure exactly 8 players are selected
        prob += lpSum(player_vars[p["Name"]] for _, p in top_players.iterrows()) == num_players
        
        # Position constraints with multi-position eligibility
        for pos, count in roster_slots.items():
            prob += lpSum(player_vars[p["Name"]] for _, p in top_players.iterrows() if pos in p["Position"].split("/") or pos == "UTIL") >= count
        
        # Force inclusion of locked players
        for player in locked_players:
            if player in player_vars:
                prob += player_vars[player] == 1
        
        # Exposure constraint (limit how often a player appears across lineups)
        for player, var in player_vars.items():
            if player_usage[player] >= max_usage:
                prob += var == 0
        
        # Solve the problem
        try:
            prob.solve()
            selected_players = tuple(sorted([p["Name"] for _, p in top_players.iterrows() if player_vars[p["Name"]].varValue == 1]))
            
            total_salary_value = sum(players_df.loc[players_df["Name"].isin(selected_players), "Salary"])
            if selected_players and len(selected_players) == num_players and min_salary_cap <= total_salary_value <= user_salary_cap:
                used_lineups.add(selected_players)
                for player in selected_players:
                    player_usage[player] += 1
                optimal_lineup_df = players_df[players_df["Name"].isin(selected_players)]
                optimal_lineups.append(optimal_lineup_df)
        except PulpSolverError:
            st.write(f"⚠️ Optimization failed for lineup {i+1}. Adjusting constraints and retrying...")
    
    # Display optimal lineups
    if optimal_lineups:
        for idx, lineup in enumerate(optimal_lineups):
            st.write(f"### Optimal Lineup {idx+1}")
            st.dataframe(lineup)
    else:
        st.write("⚠️ No valid lineups generated, but trying alternative methods to generate lineups.")
        random_lineups = players_df.sample(n=num_players * num_lineups, replace=True).groupby(players_df.index // num_players)
        for idx, (_, lineup) in enumerate(random_lineups):
            st.write(f"### Alternative Lineup {idx+1}")
            st.dataframe(lineup)


