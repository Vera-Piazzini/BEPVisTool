"""

**Visualization of Monthly Average PMV (Predicted Mean Vote) Values by Space**

This script loads data from an Excel file, processes it using Pandas, and visualizes it with Bokeh. 
The resulting plot displays PMV values across different zones, categorized by month. 
The plot includes annotations for comfort zones based on PMV values and a legend to identify each zone.

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
    return pd.read_excel(file_path, sheet_name='PMV Data')

def prepare_data(df: pd.DataFrame) -> dict:
    """Converts the DataFrame into a ColumnDataSource dictionary for Bokeh.

    Args:
        df (pd.DataFrame): DataFrame containing the PMV data.

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
    p = figure(x_range=data_sources['zone1'].data['months'], y_range=(-3, 3), height=350, 
               title="Monthly average PMV values by space", tools="pan,wheel_zoom,reset,box_select,box_zoom,lasso_select")
    
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
    comfort_colors = ["#E9C2C1", "#F2DADA", "#F7E7E6", "#F8FAF3", "#F3F6FA", "#DAE4F1", "#C2D3E9"]
    comfort_ranges = [(2.5, 3), (1.5, 2.5), (0.5, 1.5), (-0.5, 0.5), (-1.5, -0.5), (-2.5, -1.5), (-3, -2.5)]
    comfort_labels = ["Hot", "Warm", "Slightly Warm", "Neutral", "Slightly Cool", "Cool", "Cold"]

    for color, (bottom, top) in zip(comfort_colors, comfort_ranges):
        plot.add_layout(BoxAnnotation(bottom=bottom, top=top, fill_alpha=0.7, fill_color=color, level="underlay"))

    hover_tools = [
        HoverTool(renderers=[r], tooltips=[("Space", f"{i}"), ("Month", "@months"), ("PMV Avg", f"@zone_avg{{0.00}}")])
        for i, r in enumerate(renderers, 1)
    ]
    for hover in hover_tools:
        plot.add_tools(hover)

    zone_legend = Legend(items=[LegendItem(label=f"Space {i}", renderers=[r]) for i, r in enumerate(renderers, 1)],
                         orientation="horizontal", location="top_center")
    comfort_legend = Legend(title="PMV index", items=[LegendItem(label=label, renderers=[plot.square([0], [0], fill_color=color, line_color=None)]) 
                                                      for label, color in zip(comfort_labels, comfort_colors)], 
                            location="center_right")

    plot.add_layout(zone_legend, 'above')
    plot.add_layout(comfort_legend, 'right')
    plot.legend.click_policy = "mute"

    span1 = Span(location=0.7, dimension='width', line_color='black', line_dash='dashed', line_width=0.5)
    span2 = Span(location=-0.7, dimension='width', line_color='black', line_dash='dashed', line_width=0.5)
    plot.add_layout(span1)
    plot.add_layout(span2)

def show_plot(plot: figure) -> None:
    """Displays the final Bokeh plot.

    Args:
        plot (figure): Bokeh figure to be displayed.
    """
    show(plot)