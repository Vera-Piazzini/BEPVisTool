"""

**Visualization of Monthly Average PPD (Predicted Percentage od Dissatisfied) Values by Space**

This script loads data from an Excel file, processes it using Pandas, and visualizes it with Bokeh. 
The resulting plot displays PPD values across different zones, categorized by month. 
The plot includes annotations for comfort zones based on PPD values and a legend to identify each zone.

PPD is a measure of thermal comfort that predicts the percentage of occupants likely to be dissatisfied with the thermal environment. 
This visualization helps in assessing and comparing the comfort levels across different spaces over time.

Modules:
    - pandas: Used for data manipulation and analysis.
    - bokeh.models: Used for creating interactive Bokeh plots.
    - bokeh.plotting: Provides high-level plotting functions for Bokeh.

Functions:
    - **load_data(file_path: str) -> pd.DataFrame:** Loads data from the specified Excel file and returns it as a DataFrame.
    - **prepare_data(df: pd.DataFrame) -> dict:** Converts the DataFrame into a ColumnDataSource dictionary for Bokeh.
    - **create_plot(data_sources: dict) -> figure:** Creates the Bokeh plot with lines for each zone, annotations, and legends.
    - **add_annotations_and_legends(plot: figure) -> None:** Adds box annotations and legends to the Bokeh plot.
    - **show_plot(plot: figure) -> None:** Displays the final Bokeh plot.

"""

import pandas as pd
from bokeh.models import BoxAnnotation, HoverTool, Legend, LegendItem, Span, ColumnDataSource
from bokeh.plotting import figure, show

def load_data(file_path: str) -> pd.DataFrame:
    """Loads data from the specified Excel file.

    Args:
        file_path (str): Path to the Excel file containing the data.

    Returns:
        pd.DataFrame: DataFrame containing the loaded data.
    """
    return pd.read_excel(file_path, sheet_name='PPD Data')

def prepare_data(df: pd.DataFrame) -> dict:
    """Converts the DataFrame into a ColumnDataSource dictionary for Bokeh.

    Args:
        df (pd.DataFrame): DataFrame containing the PPD data.

    Returns:
        dict: Dictionary of ColumnDataSource objects for each zone.
    """
    sources = {}
    for i in range(1, 6):
        sources[f'zone{i}'] = ColumnDataSource(data=dict(
            months=df['Month'],
            zone_avg=df[f'Zone{i}'],
            zone_max=df[f'Zone{i}max'],
            zone_min=df[f'Zone{i}min'],
        ))
    return sources

def create_plot(data_sources: dict) -> figure:
    """Creates the Bokeh plot with lines for each zone.

    Args:
        data_sources (dict): Dictionary of ColumnDataSource objects.

    Returns:
        figure: Bokeh figure with the plotted data.
    """
    p = figure(x_range=data_sources['zone1'].data['months'], y_range=(0, 35), height=350, 
               title="Monthly average PPD values by space", tools="pan,wheel_zoom,reset,box_select,box_zoom,lasso_select")
    
    colors = ['#374649', '#01B8AA', '#FD625E', '#F2C80C', '#A865B5']
    renderers = []
    
    for i, color in enumerate(colors, 1):
        r = p.line(x='months', y='zone_avg', source=data_sources[f'zone{i}'], color=color, line_width=1.5)
        p.line(x='months', y='zone_max', source=data_sources[f'zone{i}'], color=color, line_width=0.2)
        p.line(x='months', y='zone_min', source=data_sources[f'zone{i}'], color=color, line_width=0.2)
        renderers.append(r)
    
    return p, renderers

def add_annotations_and_legends(plot: figure, renderers: list) -> None:
    """Adds box annotations and legends to the Bokeh plot.

    Args:
        plot (figure): Bokeh figure to add annotations and legends to.
        renderers (list): List of line renderers for each zone.
    """
    # Add comfort and out-of-range annotations
    comfort_box = BoxAnnotation(bottom=20, top=35, fill_alpha=0.7, fill_color="#F2DADA", level="underlay")
    out_of_range_box = BoxAnnotation(bottom=0, top=20, fill_alpha=0.7, fill_color="#F8FAF3", level="underlay")
    plot.add_layout(comfort_box)
    plot.add_layout(out_of_range_box)

    # Add hover tools for each zone
    for i, r in enumerate(renderers, 1):
        hover = HoverTool(renderers=[r], tooltips=[("Space", f"{i}"), ("Month", "@months"), ("PPD Avg", f"@zone_avg{{0.00}}")])
        plot.add_tools(hover)

    # Create and add legends
    zone_legend = Legend(items=[LegendItem(label=f"Space {i}", renderers=[r]) for i, r in enumerate(renderers, 1)],
                         orientation="horizontal", location="top_center")

    comfort_legend = Legend(title="PPD ranges", items=[
                            LegendItem(label="Comfort range (20%-35%)", renderers=[plot.square([0], [0], fill_color="#F2DADA", line_color=None)]),
                            LegendItem(label="Out of range (0%-20%)", renderers=[plot.square([0], [0], fill_color="#F8FAF3", line_color=None)])],
                            location="center_right")

    plot.add_layout(zone_legend, 'above')
    plot.add_layout(comfort_legend, 'right')
    plot.legend.click_policy = "mute"

    # Add span lines for ISO 7730 guidelines
    span1 = Span(location=20, dimension='width', line_color='black', line_dash='dashed', line_width=0.5)
    plot.add_layout(span1)

def show_plot(plot: figure) -> None:
    """Displays the final Bokeh plot.

    Args:
        plot (figure): Bokeh figure to be displayed.
    """
    show(plot)