"""
Radar Chart Visualizations
==========================

This module implements the ``rdr`` class used in the BEPVis project to generate
one radar chart per building zone, with an associated bar chart providing
a secondary view of the same indicators.

Each zone receives:
    - A radar chart (primary energy contributions per category)
    - A bar chart (absolute values per category)

The radar displays:
    - A set of unfilled traces (one per zone) for comparison
    - A filled trace highlighting the active zone
    - Hover information for the highlighted zone
    - Colors assigned automatically using the Glasbey palette

The bar chart displays:
    - The absolute primary energy consumption for the selected zone
    - Consistent colors with the radar filled trace

The layout is produced using Plotly, with 2 rows:
    Row 1: Radar charts (polar)
    Row 2: Bar charts

Input Format
------------
The Excel file must contain:

    Zone | Category1 | Category2 | Category3 | ...

Each row represents one space/zone.
Every column after "Zone" is a primary energy category.

Authors: Ofelia Vera-Piazzini, Massimiliano Scarpa (Università Iuav di Venezia)  
License: MIT
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import colorcet as cc

# ============================================================================
# RADAR CLASS
# ============================================================================
class rdr:
    """
    Generate a radar chart + bar chart for each zone in the dataset.

    Parameters
    ----------
    source_file_pathandname : str
        Path to an Excel file.  
        Columns must include:
            - 'Zone' (string)
            - All other columns are radar categories.
    filesave_name : str
        Output filename (HTML) without extension.

    Notes
    -----
    - The function generates one radar per zone, aligned horizontally.
    - Each radar has a filled line for the selected zone, and thin lines for
      all other zones for comparison.
    - A bar chart below each radar shows the absolute values per category.
    """
    def __init__(self, source_file_pathandname = '?', filesave_name = '?'):
        
        # Load and prepare data
        df = pd.read_excel(source_file_pathandname)
        df = df.drop(columns = ['Unnamed: 0']) # Remove unnecessary column
        s_zone_name = df['Zone'].to_list() # List of zone names
        categories = list(df.columns[1:]) # Radar axes: column names excluding 'Zone'

        # Initialize dictionary to store data for each space
        spaces_data = {}

        # --------------------------------------------------------------
        # CREATE TRACE STRUCTURE FOR EACH ZONE
        # --------------------------------------------------------------

        # Read data from each sheet
        for n_zone_name in range(len(s_zone_name)):
            s_color = cc.glasbey_bw[0:len(s_zone_name)] # Assign unique color to each space

            # Process each row in the dataframe
            data = []

            for _, row in df.iterrows():
                # Unfilled radar line for comparison
                data.append({
                    'name': row['Zone'],
                    'r': [row[item] for item in list(df.columns[1:])],
                    'fill': False,
                    'color': 'rgb(' + str(int(s_color[_][0] * 255)) + ',' \
                                + str(int(s_color[_][1] * 255)) + ',' \
                                + str(int(s_color[_][2] * 255)) + ')',
                    'line_width': 0.8
                })
                # Filled radar line for the current zone
                if s_zone_name[n_zone_name] == row['Zone']:
                    data.append({
                        'name': row['Zone'],
                        'r': [row[item] for item in df.columns[1:]],
                        'fill': True,
                        'color': data[-1]['color'],
                        'line_width': 1.5
                    })

            # Add processed zone data to the dictionary
            spaces_data[s_zone_name[n_zone_name]] = data

        # --------------------------------------------------------------
        # INITIALIZE SUBPLOTS
        # --------------------------------------------------------------

        # Create subplots with 2 rows and 5 columns, each with a polar layout
        fig = make_subplots(
            rows=2, cols=len(s_zone_name),
            subplot_titles=[f"<b><span style='font-size:12px'>{space}</span>" for space in spaces_data.keys()],
            specs=[[{'type': 'polar'}]*len(s_zone_name), [{'type': 'bar'}]*len(s_zone_name)],
            column_widths=[0.5]*len(s_zone_name),
            horizontal_spacing=0.1,
            vertical_spacing=0.01
        )

        # --------------------------------------------------------------
        # ADD RADAR CHARTS (ROW 1)
        # --------------------------------------------------------------

        # Loop through each space
        for i, (space, products) in enumerate(spaces_data.items(), 1):
            # Find the product that should display the hover text (Fill=True, Line Width=1.5, and matching name)
            hover_product = next((product for product in products if product['fill'] and product['line_width'] == 1.5 and product['name'] == space), None)
            
            # Add traces for each product in the space
            for product in products:
                fill = 'toself' if product['fill'] else None  # Determine fill property based on the current product
                r = [abs(item) for item in product['r']] + [abs(product['r'][0])]  # Convertir valores negativos a positivos
                #r = product['r'] + [product['r'][0]]  # Append the starting point to close the line
                hover_info = 'text' if product == hover_product else 'none'  # Show hover text only for the hover product
                hover_text = None 

                # Display hover text only for the hover product
                if hover_info == 'text':
                    total_consumption = sum([abs(val) for val in product['r']]) 
                    #total_consumption = sum(product['r'])
                    hover_text = f'<b>{product["name"]}</b><br>Total Consumption: {total_consumption:.2f} kWh/m2'
                        
                fig.add_trace(go.Scatterpolar(
                    r=r,
                    theta=categories + [categories[0]],  # Append the first category to close the line
                    fill=fill,
                    name=product['name'],
                    mode='lines',  # Set mode to 'lines' to remove points on edges
                    line=dict(color=product['color'], width=product['line_width']),  # Customize line color and width
                    hoverinfo=hover_info,
                    hovertext=hover_text,
                    showlegend=False,
                ), row=1, col=i)

        # --------------------------------------------------------------
        # DETERMINE GLOBAL MAX FOR BAR CHART AXIS
        # --------------------------------------------------------------

        max_y_value = 0
        for index, row in df.iterrows():
            for n_category in range(1, len(row)):
                max_y_value = max(max_y_value, abs(row[n_category]))

        # --------------------------------------------------------------
        # ADD BAR CHARTS (ROW 2)
        # --------------------------------------------------------------

        for i, (space, products) in enumerate(spaces_data.items(), start=1):
            # Define the index of the line to use for the bar chart for each space
            bar_line_index = i - 1  # Assuming each space's bar chart uses the corresponding line

            # Use the first line as the "bar reference"
            bar_data = products[bar_line_index]
            bar_data['r'] = [abs(val) for val in bar_data['r']]


            # Add bar chart for each space
            fig.add_trace(go.Bar(
                x=categories,
                y=bar_data['r'],  # Use the 'r' data from the specified line
                marker=dict(color=bar_data['color']),
                hovertemplate='<b>%{x}</b>: %{y} kWh/m2<extra></extra>',  # Remove "trace" label in tooltip
                showlegend=False
            ), row=2, col=i)

            # Axis and layout customization for each bar chart
            fig.update_xaxes(title_text=" ", row=1, col=i, title_font=dict(size=9), title_standoff=0)
            fig.update_yaxes(title_text=" ", row=2, col=i, title_font=dict(size=9), title_standoff=0)
            fig.update_layout(title=f"{space}", font=dict(size=9))
            fig.update_xaxes(title_text=f"{space}", row=1, col=i)

            # Update y-axis range and title for the bar chart to ensure consistency
            fig.update_yaxes(range=[0, max_y_value], row=2, col=i, title_text="Primary Energy Consumption (kWh/m2)")

        # --------------------------------------------------------------
        # LAYOUT SETTINGS
        # --------------------------------------------------------------
        
        fig.update_layout(
            height = 650,
            title_text="Building Primary Energy Consumption (kWh/m2) by Space and Type", 
            title_font=dict(size=14)
            )
        # Export HTML
        fig.write_html(filesave_name + ".html")
        fig.show()