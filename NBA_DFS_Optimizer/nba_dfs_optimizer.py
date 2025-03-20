import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PulpSolverError

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
        return df
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

# DraftKings Salary Cap & Roster Constraints
salary_cap = 50000
roster_slots = {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1, "G": 1, "F": 1, "UTIL": 1}
num_players = sum(roster_slots.values())

# User Input for Salary Cap, Number of Lineups, and Player Locks/Exclusions
user_salary_cap = st.number_input("Set Salary Cap", min_value=40000, max_value=60000, value=salary_cap, step=500)
num_lineups = st.slider("Number of Lineups", 1, 5, 3)
locked_players = st.multiselect("Lock Players (Ensure they are in every lineup)", players_df["Name"].tolist())
excluded_players = st.multiselect("Exclude Players (Remove them from all lineups)", players_df["Name"].tolist())

# Store used lineups to prevent duplicates
used_lineups = set()

# Optimization button
if st.button("Generate Optimal Lineups") and not players_df.empty:
    optimal_lineups = []
    
    for i in range(num_lineups):
        prob = LpProblem(f"NBA_DFS_Optimizer_{i+1}", LpMaximize)
        player_vars = {p["Name"]: LpVariable(p["Name"], 0, 1, cat="Binary") for _, p in players_df.iterrows()}
        
        # Objective: Maximize projected points
        prob += lpSum(player_vars[p["Name"]] * p["Projection"] for _, p in players_df.iterrows())
        
        # Salary cap constraint
        prob += lpSum(player_vars[p["Name"]] * p["Salary"] for _, p in players_df.iterrows()) <= user_salary_cap
        
        # Ensure exactly 8 players are selected
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows()) == num_players
        
        # Position constraints based on DraftKings Roster Construction
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] == "PG") == 1
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] == "SG") == 1
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] == "SF") == 1
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] == "PF") == 1
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] == "C") == 1
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] in ["PG", "SG"]) == 1  # G Slot
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] in ["SF", "PF"]) == 1  # F Slot
        prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows()) == num_players  # UTIL Slot
        
        # Lock and Exclude Players
        for player in locked_players:
            prob += player_vars[player] == 1
        for player in excluded_players:
            prob += player_vars[player] == 0
        
        # Solve the problem
        try:
            prob.solve()
            selected_players = tuple(sorted([p["Name"] for _, p in players_df.iterrows() if player_vars[p["Name"]].varValue == 1]))
            
            if selected_players and selected_players not in used_lineups:
                used_lineups.add(selected_players)
                optimal_lineup_df = players_df[players_df["Name"].isin(selected_players)]
                optimal_lineups.append(optimal_lineup_df)
            else:
                st.write(f"⚠️ Duplicate lineup found for lineup {i+1}. Generating a new one...")
        except PulpSolverError:
            st.write(f"⚠️ Optimization failed for lineup {i+1}. Try adjusting constraints.")
    
    # Display optimal lineups
    for idx, lineup in enumerate(optimal_lineups):
        st.write(f"### Optimal Lineup {idx+1}")
        st.dataframe(lineup)




