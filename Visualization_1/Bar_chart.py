"""

**Visualization of Annual and Monthly Energy Balance of a Building**

This module provides functionality to visualize the energy balance of a building 
over a year using stacked bar charts. The data is loaded from an Excel file, 
processed, and then visualized using Bokeh.

Functions:
    - **load_excel_data(file_path: str, sheet_name: str) -> pd.DataFrame:** Loads data from an Excel sheet into a DataFrame.
    - **calculate_annual_sums(df_gains: pd.DataFrame, df_losses: pd.DataFrame) -> tuple:** Calculates the annual sums of gains and losses from the data.
    - **prepare_data_for_visualization(df_gains: pd.DataFrame, df_losses: pd.DataFrame) -> tuple:** Prepares data for total annual and monthly balance visualization.
    - **create_figure(title: str, x_range, y_range, x_label: str, y_label: str) -> figure:** Creates a Bokeh figure for plotting.
    - **plot_stacked_bars(p: figure, types: list, source_data: dict, reverse_palette: list, losses: bool = False) -> None:** Plots stacked bars for the given figure.
    - **configure_figure(p: figure, title: str, x_label: str, y_label: str) -> None:** Configures the appearance of the Bokeh figure.
    - **visualize_energy_balance(df_gains: pd.DataFrame, df_losses: pd.DataFrame) -> None:** Visualizes the energy balance using Bokeh.

"""


import pandas as pd
from bokeh.models import ColumnDataSource, Legend, NumeralTickFormatter, Span
from bokeh.palettes import RdYlBu11
from bokeh.plotting import figure, show
from bokeh.layouts import row

def load_excel_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Loads data from an Excel sheet into a DataFrame.

    Args:
        file_path (str): The path to the Excel file.
        sheet_name (str): The sheet name to load data from.

    Returns:
        pd.DataFrame: The loaded data.
    """
    return pd.read_excel(file_path, sheet_name=sheet_name)

def calculate_annual_sums(df_gains: pd.DataFrame, df_losses: pd.DataFrame) -> tuple:
    """Calculates the annual sums of gains and losses from the data.

    Args:
        df_gains (pd.DataFrame): DataFrame containing energy gains data.
        df_losses (pd.DataFrame): DataFrame containing energy losses data.

    Returns:
        tuple: Annual gains and losses as lists.
    """
    types = df_gains.columns[1:].tolist()  # Ignore the 'Month' column
    annual_gains = [sum(df_gains[type]) for type in types]
    annual_losses = [sum(df_losses[type]) for type in types]
    return annual_gains, annual_losses

def prepare_data_for_visualization(df_gains: pd.DataFrame, df_losses: pd.DataFrame) -> tuple:
    """Prepares data for total annual and monthly balance visualization.

    Args:
        df_gains (pd.DataFrame): DataFrame containing energy gains data.
        df_losses (pd.DataFrame): DataFrame containing energy losses data.

    Returns:
        tuple: Two dictionaries containing data for the total annual and monthly balance graphs.
    """
    months = df_gains['Month'].tolist()
    types = df_gains.columns[1:].tolist()

    # Data for the total annual balance graph
    source_data = {
        'x': ['Annual'],
        **{type: [sum(df_gains[type])] for type in types},
        **{type+"_losses": [sum(df_losses[type])] for type in types}}

    # Data for the monthly balance graph
    source_data_p2 = {
        'x': months,
        **{type: df_gains[type].tolist() for type in types},
        **{type+"_losses": df_losses[type].tolist() for type in types}}

    return source_data, source_data_p2

def create_figure(title: str, x_range, y_range, x_label: str, y_label: str) -> figure:
    """Creates a Bokeh figure for plotting.

    Args:
        title (str): The title of the figure.
        x_range (list or str): The range of the x-axis.
        y_range (tuple): The range of the y-axis.
        x_label (str): The label for the x-axis.
        y_label (str): The label for the y-axis.

    Returns:
        figure: The created Bokeh figure.
    """
    return figure(x_range=x_range, y_range=y_range, height=600, width=380, title=title,
                  toolbar_location="above", tools="hover")

def plot_stacked_bars(p: figure, types: list, source_data: dict, reverse_palette: list, losses: bool = False) -> None:
    """Plots stacked bars for the given figure.

    Args:
        p (figure): The Bokeh figure to plot on.
        types (list): The list of energy types.
        source_data (dict): The data source for the plot.
        reverse_palette (list): The color palette to use.
        losses (bool): If True, plots losses; otherwise, plots gains. Defaults to False.
    """
    suffix = "_losses" if losses else ""
    p.vbar_stack([type + suffix for type in types], x='x', width=0.9, 
                 color=reverse_palette[:len(types)], source=ColumnDataSource(data=source_data))

def configure_figure(p: figure, title: str, x_label: str, y_label: str) -> None:
    """Configures the appearance of the Bokeh figure.

    Args:
        p (figure): The Bokeh figure to configure.
        title (str): The title of the figure.
        x_label (str): The label for the x-axis.
        y_label (str): The label for the y-axis.
    """
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")

def visualize_energy_balance(df_gains: pd.DataFrame, df_losses: pd.DataFrame) -> None:
    """Visualizes the energy balance using Bokeh.

    Args:
        df_gains (pd.DataFrame): DataFrame containing energy gains data.
        df_losses (pd.DataFrame): DataFrame containing energy losses data.
    """
    # Prepare data
    source_data, source_data_p2 = prepare_data_for_visualization(df_gains, df_losses)
    original_palette = RdYlBu11
    reverse_palette = original_palette[::-1]

    # Create figures
    p = create_figure("Total Annual Energy Balance by Type", ['Annual'], (0, 3000), "Year", "Energy Balance (kWh)")
    p2 = create_figure("Building Energy Balance by Month and Type", df_gains['Month'].tolist(), (-3000, 3000), "Months", "Energy Balance (kWh)")

    # Plot stacked bars
    plot_stacked_bars(p, df_gains.columns[1:], source_data, reverse_palette)
    plot_stacked_bars(p2, df_gains.columns[1:], source_data_p2, reverse_palette)
    plot_stacked_bars(p, df_gains.columns[1:], source_data, reverse_palette, losses=True)
    plot_stacked_bars(p2, df_gains.columns[1:], source_data_p2, reverse_palette, losses=True)

    # Configure figures
    configure_figure(p, "Total Annual Energy Balance by Type", "Year", "Energy Balance (kWh)")
    configure_figure(p2, "Building Energy Balance by Month and Type", "Months", "Energy Balance (kWh)")

    # Add legend and spans
    legend = Legend(items=[(t, [p2.renderers[i]]) for i, t in enumerate(df_gains.columns[1:])], location="center")
    legend.border_line_color = None
    p2.add_layout(legend, 'right')
    p2.legend.click_policy = "hide"

    span1 = Span(location=0, dimension='width', line_color='black', line_width=2)
    p.add_layout(span1)
    p2.add_layout(span1)

    # Layout the two plots side by side
    layout = row(p, p2)

    # Display the layout
    show(layout)
