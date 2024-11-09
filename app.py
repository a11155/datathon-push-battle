import streamlit as st
import json
import pandas as pd
import plotly.express as px
from benchmark import GameAnalyzer
import os


NUM_TRIALS = 5
st.set_page_config(
    page_title="Push Battle Analysis",
    layout="wide"
)

def load_or_generate_data():
    """Load existing data or generate new benchmark data"""
    if os.path.exists('benchmark_results.json'):
        with open('benchmark_results.json', 'r') as f:
            return json.load(f)
    else:
        analyzer = GameAnalyzer()
        analyzer.run_benchmark(NUM_TRIALS)  # Run 1 game
        stats = analyzer.export_stats()
        with open('benchmark_results.json', 'w') as f:
            json.dump(stats, f)
        return stats

def run_new_benchmark():
    """Run a new benchmark and return results"""
    analyzer = GameAnalyzer()
    analyzer.run_benchmark(NUM_TRIALS)  # Run 1 game
    stats = analyzer.export_stats()
    with open('benchmark_results.json', 'w') as f:
        json.dump(stats, f)
    return stats

def main():
    st.title("Push Battle Agent Analysis")

    # Add refresh button
    if st.button("Run New Benchmark"):
        stats = run_new_benchmark()
        st.success("New benchmark completed!")
    else:
        stats = load_or_generate_data()

    # Display total games
    st.header(f"Total Games Analyzed: {stats['totalGames']}")

    # Create two columns for the main stats
    col1, col2 = st.columns(2)

    with col1:
        # Win Rate Distribution
        st.subheader("Win Rate Distribution")
        if stats['matchupStats']:
            df_matchup = pd.DataFrame(stats['matchupStats'])
            st.dataframe(df_matchup)
            
            # Create bar chart for wins/losses/draws
            if not df_matchup.empty:
                try:
                    fig = px.bar(
                        df_matchup,
                        x='name',
                        y=['wins', 'losses', 'draws'],
                        title='Win/Loss Distribution',
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating matchup chart: {str(e)}")
        else:
            st.write("No matchup data available")

    with col2:
        # Move Quality by Phase
        st.subheader("Move Quality by Game Phase")
        if stats['moveStats']:
            df_moves = pd.DataFrame(stats['moveStats'])
            st.dataframe(df_moves)
            
            # Create bar chart for move types
            if not df_moves.empty:
                try:
                    fig = px.bar(
                        df_moves,
                        x='name',
                        y=['validMoves', 'timeouts', 'invalid'],
                        title='Move Quality Distribution',
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating moves chart: {str(e)}")
        else:
            st.write("No move quality data available")

    # Display game length distribution
    st.subheader("Game Length Distribution")
    if stats['gameLength']:
        df_length = pd.DataFrame(stats['gameLength'])
        st.dataframe(df_length)
        
        if not df_length.empty:
            try:
                fig = px.bar(
                    df_length,
                    x='length',
                    y='games',
                    title='Game Length Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating game length chart: {str(e)}")
    else:
        st.write("No game length data available")

    # Display raw data
    with st.expander("View Raw JSON Data"):
        st.json(stats)

    # Add debug information
    with st.expander("Debug Information"):
        st.write("Data Structure:")
        for key in stats.keys():
            st.write(f"{key}: {type(stats[key])}")
            if isinstance(stats[key], list):
                st.write(f"Length: {len(stats[key])}")
                if stats[key]:
                    st.write("First item:", stats[key][0])

if __name__ == "__main__":
    main()