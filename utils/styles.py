import streamlit as st

def load_css() -> None:
    """Load custom CSS styles."""
    st.markdown("""
        <style>
        /* Main container */
        .main {
            padding: 2rem;
        }
        
        /* Sidebar */
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        
        /* Headers */
        h1 {
            color: #1E88E5;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        
        h2 {
            color: #0D47A1;
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }
        
        h3 {
            color: #1565C0;
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 0.6rem;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 1.4rem;
            font-weight: 600;
            color: #1E88E5;
        }
        
        [data-testid="stMetricDelta"] {
            font-size: 1rem;
            font-weight: 500;
        }
        
        /* Tables */
        .dataframe {
            font-size: 0.9rem;
        }
        
        .dataframe th {
            background-color: #E3F2FD;
            font-weight: 600;
            padding: 0.5rem;
        }
        
        .dataframe td {
            padding: 0.5rem;
        }
        
        /* Forms */
        .stButton>button {
            width: 100%;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            background-color: #1E88E5;
            color: white;
            font-weight: 500;
            border: none;
            transition: background-color 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #1565C0;
        }
        
        /* Alerts */
        .stAlert {
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        /* Progress bars */
        .stProgress > div > div {
            background-color: #1E88E5;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px;
            color: #1E88E5;
            font-size: 1rem;
            font-weight: 500;
            border: none;
            padding: 0.5rem 1rem;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #E3F2FD;
        }
        
        /* Tooltips */
        .stTooltipIcon {
            color: #1E88E5;
        }
        
        /* Trade signals */
        .signal-buy {
            color: #4CAF50;
            font-weight: 600;
        }
        
        .signal-sell {
            color: #F44336;
            font-weight: 600;
        }
        
        .signal-neutral {
            color: #9E9E9E;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

def format_number(number: float, decimals: int = 2) -> str:
    """Format a number with commas and specified decimal places."""
    return f"{number:,.{decimals}f}"

def format_pct(number: float, decimals: int = 1) -> str:
    """Format a number as a percentage."""
    return f"{number:.{decimals}f}%"

def format_currency(number: float, decimals: int = 2) -> str:
    """Format a number as currency."""
    return f"${number:,.{decimals}f}" 