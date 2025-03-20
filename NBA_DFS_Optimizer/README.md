# NBA DFS Optimizer

This is a free NBA Daily Fantasy Sports (DFS) optimizer built using Python and Streamlit.

## Features
- Optimizes lineups for DraftKings-style DFS contests.
- Allows setting of salary cap.
- Uses linear programming to maximize projected points.

## How to Use

### 1. Install Python Dependencies
Run this command to install necessary packages:
```bash
pip install -r requirements.txt
```

### 2. Run Locally
```bash
streamlit run nba_dfs_optimizer.py
```

### 3. Deploy to Streamlit Cloud
1. **Create a GitHub Repository** and upload these files.
2. **Go to [Streamlit Cloud](https://share.streamlit.io/)** and log in with GitHub.
3. **Click "New App"**, select your repository, and set `nba_dfs_optimizer.py` as the main file.
4. **Deploy** and access the optimizer from your browser or phone.

## Future Improvements
- Fetch real-time player projections from APIs.
- Support multiple DFS sites like FanDuel.
