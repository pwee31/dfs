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
        df = df[df["Projection"] > 0]  # Remove players with 0 projection
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
roster_slots = {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1, "G": 1, "F": 1, "UTIL": 1}
num_players = sum(roster_slots.values())

# User Input for Salary Cap, Number of Lineups, and Player Locks/Exclusions
user_salary_cap = st.number_input("Set Salary Cap", min_value=40000, max_value=50000, value=salary_cap, step=500)
num_lineups = st.slider("Number of Lineups", 1, 5, 3)
locked_players = st.multiselect("Lock Players (Ensure they are in every lineup)", players_df["Name"].tolist())
excluded_players = st.multiselect("Exclude Players (Remove them from all lineups)", players_df["Name"].tolist())

# Exclude excluded players from selection
players_df = players_df[~players_df["Name"].isin(excluded_players)]

# Store used lineups to prevent duplicates
used_lineups = set()

# Optimization button
if st.button("Generate Optimal Lineups") and not players_df.empty:
    optimal_lineups = []
    top_players = players_df.head(20)  # Consider top 20 projected players for variation
    
    for i in range(num_lineups):
        prob = LpProblem(f"NBA_DFS_Optimizer_{i+1}", LpMaximize)
        player_vars = {p["Name"]: LpVariable(p["Name"], 0, 1, cat="Binary") for _, p in top_players.iterrows()}
        
        # Objective: Maximize projected points
        prob += lpSum(player_vars[p["Name"]] * p["Projection"] for _, p in top_players.iterrows())
        
        # Salary cap constraint - STRICTLY ENFORCED
        prob += lpSum(player_vars[p["Name"]] * p["Salary"] for _, p in top_players.iterrows()) <= user_salary_cap
        
        # Ensure exactly 8 players are selected
        prob += lpSum(player_vars[p["Name"]] for _, p in top_players.iterrows()) == num_players
        
        # Position constraints based on DraftKings Roster Construction
        for pos, count in roster_slots.items():
            prob += lpSum(player_vars[p["Name"]] for _, p in top_players.iterrows() if p["Position"] == pos or pos == "UTIL") == count
        
        # Force inclusion of locked players
        for player in locked_players:
            if player in player_vars:
                prob += player_vars[player] == 1
        
        # Solve the problem
        try:
            prob.solve()
            selected_players = tuple(sorted([p["Name"] for _, p in top_players.iterrows() if player_vars[p["Name"]].varValue == 1]))
            
            total_salary = sum(players_df.loc[players_df["Name"].isin(selected_players), "Salary"])
            if selected_players and selected_players not in used_lineups and len(selected_players) == num_players:
                if total_salary <= user_salary_cap:  # FINAL SALARY CHECK BEFORE ADDING LINEUP
                    used_lineups.add(selected_players)
                    optimal_lineup_df = players_df[players_df["Name"].isin(selected_players)]
                    optimal_lineups.append(optimal_lineup_df)
                else:
                    st.write(f"⚠️ Lineup {i+1} exceeds salary cap. Retrying...")
        except PulpSolverError:
            st.write(f"⚠️ Optimization failed for lineup {i+1}. Generating a variation...")
            selected_players = tuple(sorted(top_players.sample(n=num_players)["Name"].tolist()))
            total_salary = sum(players_df.loc[players_df["Name"].isin(selected_players), "Salary"])
            if total_salary <= user_salary_cap:
                optimal_lineup_df = players_df[players_df["Name"].isin(selected_players)]
                optimal_lineups.append(optimal_lineup_df)
    
    # Display optimal lineups
    for idx, lineup in enumerate(optimal_lineups):
        st.write(f"### Optimal Lineup {idx+1}")
        st.dataframe(lineup)


