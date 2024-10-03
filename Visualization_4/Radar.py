"""

**Visualization of Building Primary Energy Consumption by Space and Type**

This script generates a visual representation of building primary energy consumption 
by space and type using radar charts and bar charts. The data is read from multiple 
sheets of an Excel file, each representing a different space. Radar charts are used 
to compare different categories of energy consumption within each space, while bar 
charts visualize the total consumption for each category.

The script uses the Plotly library for creating interactive plots, and the data is 
fetched from an Excel file specified by the user.

Categories of energy consumption:
- Cooling
- Heating
- Ventilation
- Lighting
- Equipment
- Water Heating

Each space is represented by a separate radar chart and a corresponding bar chart.

Modules:
    - pandas: Used for data manipulation and analysis.
    - plotly.graph_objects: Used for creating radar and bar charts.
    - plotly.subplots: Used for creating subplots with multiple charts.

Functions:
    - **load_data(file_path: str, sheet_names: list) -> dict:** Loads data from the specified Excel file sheets and returns it as a dictionary of DataFrames.
    - **prepare_radar_data(df: pd.DataFrame, categories: list) -> list:** Prepares radar chart data from a DataFrame for a given set of categories.
    - **create_figures(spaces_data: dict, categories: list) -> go.Figure:** Creates a Plotly figure with radar and bar charts for each space.
    - **show_figures(fig: go.Figure) -> None:** Displays the final Plotly figure with all charts.

Usage:
   To use this script, provide the path to your Excel file and ensure that the sheet names correspond to the spaces you want to visualize. The script will generate and display an interactive Plotly figure with radar and bar charts.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def load_data(file_path: str, sheet_names: list) -> dict:
    """Loads data from the specified Excel file sheets.

    Args:
        file_path (str): Path to the Excel file containing the data.
        sheet_names (list): List of sheet names to be loaded from the Excel file.

    Returns:
        dict: A dictionary where keys are sheet names and values are DataFrames.
    """
    spaces_data = {}
    for sheet in sheet_names:
        spaces_data[sheet] = pd.read_excel(file_path, sheet_name=sheet)
    return spaces_data

def prepare_radar_data(df: pd.DataFrame, categories: list) -> list:
    """Prepares radar chart data from a DataFrame for a given set of categories.

    Args:
        df (pd.DataFrame): DataFrame containing the energy consumption data.
        categories (list): List of categories for the radar chart.

    Returns:
        list: List of dictionaries with radar chart data for each product/system.
    """
    data = []
    for _, row in df.iterrows():
        data.append({
            'name': row['Name'],
            'r': [row[cat] for cat in categories],
            'fill': row['Fill'],
            'color': row['Color'],
            'line_width': row['Line Width']
        })
    return data

def create_figures(spaces_data: dict, categories: list) -> go.Figure:
    """Creates a Plotly figure with radar and bar charts for each space.

    Args:
        spaces_data (dict): Dictionary containing processed data for each space.
        categories (list): List of categories for the radar and bar charts.

    Returns:
        go.Figure: A Plotly figure object with the generated charts.
    """
    fig = make_subplots(
        rows=2, cols=5, 
        subplot_titles=[f"<b><span style='font-size:12px'>{space}</span>" for space in spaces_data.keys()],
        specs=[[{'type': 'polar'}]*5, [{'type': 'bar'}]*5],
        column_widths=[0.5]*5,
        horizontal_spacing=0.1,
        vertical_spacing=0.01
    )

    for i, (space, products) in enumerate(spaces_data.items(), 1):
        for product in products:
            fill = 'toself' if product['fill'] else None
            r = product['r'] + [product['r'][0]]
            hover_info = 'text' if product['fill'] and product['line_width'] == 1.5 else 'none'
            hover_text = f'<b>{product["name"]}</b><br>Total Consumption: {sum(product["r"]):.2f} kWh' if hover_info == 'text' else None
            fig.add_trace(go.Scatterpolar(
                r=r,
                theta=categories + [categories[0]],
                fill=fill,
                name=product['name'],
                mode='lines',
                line=dict(color=product['color'], width=product['line_width']),
                hoverinfo=hover_info,
                hovertext=hover_text,
                showlegend=False,
            ), row=1, col=i)

        bar_data = products[i-1]
        fig.add_trace(go.Bar(
            x=categories,
            y=bar_data['r'],
            marker=dict(color=bar_data['color']),
            hovertemplate='<b>%{x}</b>: %{y} kWh<extra></extra>',
            showlegend=False
        ), row=2, col=i)

    fig.update_layout(height=650)
    fig.update_layout(title_text="Building Primary Energy Consumption (kWh) by Space and Type", title_font=dict(size=14))
    return fig

def show_figures(fig: go.Figure) -> None:
    """Displays the final Plotly figure with all charts.

    Args:
        fig (go.Figure): Plotly figure object to be displayed.
    """
    fig.show()