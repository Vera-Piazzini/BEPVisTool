"""

**Visualization of the Relationship between Outdoor Air Temperature and the Total Heating Rate**

This script generates a scatter plot to visualize the relationship between outdoor air temperature 
and the total heating rate for a specific space, using data from an Excel file. The data is divided 
into different time ranges, and for each range, a linear trend line is calculated and plotted.

The script uses the Bokeh library to create interactive visualizations, allowing users to explore 
the data with various tools like zooming, panning, and tooltips.

The plot includes:
- Scatter points colored based on 8-hour time ranges.
- A general trend line for the entire dataset.
- Individual trend lines for each time range.
- Interactive legends and tooltips.

Modules:
    - pandas: Used for data manipulation and analysis.
    - bokeh.plotting: Provides high-level plotting functions for Bokeh.
    - bokeh.io: Handles output operations for Bokeh visualizations.
    - bokeh.models: Used for customizing Bokeh plots (e.g., legends, hover tools).
    - scipy.stats: Provides statistical functions including linear regression.
    - itertools: Used for iterating over elements, specifically for cycling through colors.
    - numpy: Used for numerical operations and handling arrays.

Functions:
    - **load_data(file_path: str) -> pd.DataFrame:** Loads data from the specified Excel file and returns it as a DataFrame.
    - **extract_time_ranges(df: pd.DataFrame) -> pd.DataFrame:** Extracts and adds the 'Hour' column to the DataFrame for categorizing data into time ranges.
    - **create_scatter_plot(df: pd.DataFrame) -> figure:** Creates a Bokeh scatter plot with scatter points and trend lines based on time ranges.
    - **add_trend_lines(p: figure, x: pd.Series, y: pd.Series, df: pd.DataFrame) -> None:** Adds a general trend line and individual trend lines for each time range.
    - **configure_plot(p: figure) -> None:** Configures the plot with labels, legends, and tooltips.
    - **save_and_show_plot(p: figure, output_filename: str) -> None:** Saves the plot to an HTML file and displays it in a browser.
"""

import pandas as pd
from bokeh.plotting import figure, show
from bokeh.io import output_file
import numpy as np
from scipy.stats import linregress
from bokeh.palettes import viridis
import itertools
from bokeh.models import HoverTool, Legend

def load_data(file_path: str) -> pd.DataFrame:
    """Loads data from the specified Excel file.

    Args:
        file_path (str): Path to the Excel file containing the data.

    Returns:
        pd.DataFrame: DataFrame containing the loaded data.
    """
    return pd.read_excel(file_path)

def extract_time_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts and adds the 'Hour' column to the DataFrame for categorizing data into time ranges.

    Args:
        df (pd.DataFrame): DataFrame containing the date/time data.

    Returns:
        pd.DataFrame: Updated DataFrame with an additional 'Hour' column.
    """
    df['Hour'] = df['Date/Time'].str.split().str[-1].str.split(':').str[0].astype(int)
    return df

def create_scatter_plot(df: pd.DataFrame) -> figure:
    """Creates a Bokeh scatter plot with scatter points and trend lines based on time ranges.

    Args:
        df (pd.DataFrame): DataFrame containing the outdoor temperature and heating rate data.

    Returns:
        figure: Bokeh figure with scatter points and trend lines.
    """
    # Extract relevant columns
    x = df['SPACE1-1:Zone Outdoor Air Drybulb Temperature [C](Hourly)']
    y = df['ZONE 1 IDEAL LOADS:Zone Ideal Loads Zone Total Heating Rate [W](Hourly)']

    # Create the scatter plot figure
    p = figure(title="Total Heating Rate (W) vs Outdoor Temperature (°C) - Space 1",
               tools="crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,examine,help")
    
    return p, x, y

def add_trend_lines(p: figure, x: pd.Series, y: pd.Series, df: pd.DataFrame) -> None:
    """Adds a general trend line and individual trend lines for each time range.

    Args:
        p (figure): Bokeh figure to add trend lines to.
        x (pd.Series): Series of outdoor temperature values.
        y (pd.Series): Series of total heating rate values.
        df (pd.DataFrame): DataFrame with the 'Hour' column for time range categorization.
    """
    # General trend line for all data points
    slope, intercept, _, _, _ = linregress(x, y)
    general_trend_x = np.array([min(x), max(x)])
    general_trend_y = intercept + slope * general_trend_x
    p.line(general_trend_x, general_trend_y, line_width=2, line_color="black", legend_label="General Trend Line")

    # Define the number of 8-hour ranges and corresponding colors
    num_ranges = 3
    colors = itertools.cycle(viridis(num_ranges))

    # Add scatter points and trend lines for each 8-hour range
    for i, hour_range in enumerate([(0, 8), (8, 19), (19, 24)]):
        x_range = x[(df['Hour'] >= hour_range[0]) & (df['Hour'] < hour_range[1])]
        y_range = y[(df['Hour'] >= hour_range[0]) & (df['Hour'] < hour_range[1])]
        color = next(colors)
        p.scatter(x_range, y_range, radius=0.2, fill_color=color, fill_alpha=0.6, line_color=None, legend_label=f"{hour_range[0]}-{hour_range[1]} hours")
        
        if len(x_range) > 1:
            slope, intercept, _, _, _ = linregress(x_range, y_range)
            trend_x = np.array([min(x_range), max(x_range)])
            trend_y = intercept + slope * trend_x
            p.line(trend_x, trend_y, line_width=2, line_color=color, legend_label=f"Trend Line {hour_range[0]}-{hour_range[1]} hours", visible=False)

def configure_plot(p: figure) -> None:
    """Configures the plot with labels, legends, and tooltips.

    Args:
        p (figure): Bokeh figure to configure.
    """
    # Set axis labels
    p.xaxis.axis_label = 'Hourly Outdoor Temperature [°C]'
    p.yaxis.axis_label = 'Hourly Total Heating Rate [W]'

    # Set y-axis range to start at 0
    p.y_range.start = 0

    # Customize the legend
    p.legend.title = "Hour Range"
    p.legend.location = "top_right"
    p.legend.click_policy = "hide"
    p.legend.label_text_font_size = "9pt"
    p.legend.spacing = 1

    # Customize the tooltip for hover tool
    hover = HoverTool(tooltips=[("Outdoor Temperature", "@x{0.0} °C"), ("Heating Rate", "@y{0} W")])
    p.add_tools(hover)

def save_and_show_plot(p: figure, output_filename: str) -> None:
    """Saves the plot to an HTML file and displays it in a browser.

    Args:
        p (figure): Bokeh figure to be saved and displayed.
        output_filename (str): The filename for the HTML output.
    """
    output_file(output_filename)
    show(p)
    