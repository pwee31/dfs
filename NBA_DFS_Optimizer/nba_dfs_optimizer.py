import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PulpSolverError

# Load NBA DFS CSV Data from Upload
def load_dfs_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)

        st.write("### Detected Columns in CSV:")
        st.write(df.columns.tolist())  # Debugging: Show actual column names

        # Auto-detect relevant columns
        expected_columns = {
            "Name": ["Name", "Player", "Full Name"],
            "Position": ["Position", "POS"],
            "Salary": ["Salary", "Cost"],
            "Projection": ["Projection", "FPTS", "Proj Points", "FantasyPoints"]
        }

        # Create a mapping dictionary for renaming
        rename_mapping = {}
        for standard_col, possible_names in expected_columns.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    rename_mapping[possible_name] = standard_col
                    break

        # Rename columns accordingly
        df = df.rename(columns=rename_mapping)

        # Check if all required columns exist
        missing_columns = [col for col in ["Name", "Position", "Salary"] if col not in df.columns]
        if missing_columns:
            st.error(f"⚠️ Missing critical columns: {missing_columns}")
            return pd.DataFrame()

        # If "Projection" is missing, allow manual input
        if "Projection" not in df.columns:
            st.warning("⚠️ No 'Projection' column found. Please enter a default projection value.")
            df["Projection"] = st.number_input("Enter default projection for all players", min_value=0.0, value=20.0)

        # Keep only necessary columns
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

# User Input for Salary Cap and Number of Lineups
user_salary_cap = st.number_input("Set Salary Cap", min_value=40000, max_value=60000, value=salary_cap, step=500)
num_lineups = st.slider("Number of Lineups", 1, 5, 3)

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
        
        # Position constraints
        for pos, count in roster_slots.items():
            if pos == "G":
                prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] in ["PG", "SG"]) >= count
            elif pos == "F":
                prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] in ["SF", "PF"]) >= count
            elif pos == "UTIL":
                prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows()) >= count
            else:
                prob += lpSum(player_vars[p["Name"]] for _, p in players_df.iterrows() if p["Position"] == pos) == count
        
        # Solve the problem
        try:
            prob.solve()
            selected_players = [p["Name"] for _, p in players_df.iterrows() if player_vars[p["Name"]].varValue == 1]
            
            if selected_players:
                optimal_lineup_df = players_df[players_df["Name"].isin(selected_players)]
                optimal_lineups.append(optimal_lineup_df)
            else:
                st.write(f"⚠️ No valid lineup found for lineup {i+1}. Adjust salary cap or player pool.")
        except PulpSolverError:
            st.write(f"⚠️ Optimization failed for lineup {i+1}. Try adjusting constraints.")
    
    # Display optimal lineups
    for idx, lineup in enumerate(optimal_lineups):
        st.write(f"### Optimal Lineup {idx+1}")
        st.dataframe(lineup)


