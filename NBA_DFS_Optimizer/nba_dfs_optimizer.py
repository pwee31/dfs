import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PulpSolverError

# Function to scrape player data from ESPN NBA
def scrape_espn_data():
    url = "https://www.espn.com/nba/stats/player"  # ESPN stats page
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to fetch data. Status code:", response.status_code)
        return pd.DataFrame()
    
    soup = BeautifulSoup(response.text, "html.parser")
    players = []
    
    # Find table
    table = soup.find("table")
    if not table:
        print("⚠️ Failed to locate player table on ESPN.")
        return pd.DataFrame()
    
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 5:
            try:
                name = cols[0].text.strip()
                position = "N/A"  # ESPN may not have position data
                salary = 5000  # Placeholder salary if unavailable
                projection = float(cols[1].text.strip())  # Assuming second column is projected points
                players.append({"Name": name, "Position": position, "Salary": salary, "Projection": projection})
            except ValueError:
                continue
    
    return pd.DataFrame(players)

# Streamlit UI
st.title("NBA DFS Optimizer - DraftKings Edition")
st.write("Generate up to 5 optimized NBA DFS lineups based on DraftKings salary cap.")

# Scrape player data
st.write("Fetching latest player projections...")
players_df = scrape_espn_data()
st.write("### Scraped Player Data")
st.dataframe(players_df)

# DraftKings Salary Cap & Roster Constraints
salary_cap = 50000
roster_slots = {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1, "G": 1, "F": 1, "UTIL": 1}
num_players = sum(roster_slots.values())

# User Input for Salary Cap and Number of Lineups
user_salary_cap = st.number_input("Set Salary Cap", min_value=40000, max_value=60000, value=salary_cap, step=500)
num_lineups = st.slider("Number of Lineups", 1, 5, 3)

# Optimization button
if st.button("Generate Optimal Lineups"):
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
