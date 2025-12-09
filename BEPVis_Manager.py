"""
BEPVis Manager
--------------

This module orchestrates the full BEPVis workflow. It loads EnergyPlus output
files (SQLite + epJSON), extracts and preprocesses simulation data, builds
intermediate datasets, and calls the visualization modules contained in the
`Visualizations/` directory.

Main responsibilities:
- Load and optimize access to EnergyPlus SQLite outputs
- Parse epJSON simulation description
- Compute gains/losses per zone and aggregated indicators
- Generate datasets for heatmaps, line charts, scatter plots, and radar charts
- Automatically save Excel intermediate files
- Trigger each visualization function
- Manage logging (console + file)

Authors: Ofelia Vera-Piazzini, Massimiliano Scarpa (Università Iuav di Venezia)
Part of the BEPVis project – Tools for automatic visualization of EnergyPlus data
License: MIT
"""

import logging
import pandas as pd
import os
import sys
import __main__
import sqlite3
import duckdb
import calendar
import subprocess
import json
import numpy as np
import polars as pl

def clean_string(string_toprocess = '?', string_forbiddenchars = '?*,<>^\'"£$%&\/()\\!'):
    return ''.join(c for c in string_toprocess if c not in string_forbiddenchars)
# ================================
# General Utility Class Definition
# ================================
class gnrl:
    def __init__(self):
        # Determine application folder path based on execution context (frozen executable or script)
        if getattr(sys, 'frozen', False):
            self.app_folder = os.path.dirname(sys.executable)
        else:
            self.app_folder = os.path.dirname(os.path.abspath(__file__))

    def get_logger(self, name, console_level = logging.INFO, file_level = logging.DEBUG, log_file = 'app.log'):
        
        """
        Create and configure a logger with two handlers:
        - Console handler with a specified logging level
        - File handler writing detailed logs to a file
        """

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicate logs
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Console handler configuration
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)        
        formatter_console = logging.Formatter(
            '%(asctime)s.%(msecs)03d | %(filename)-24s | %(lineno)05d | %(funcName)-24s | %(levelname)-10s | %(message)s',
            datefmt = '%Y-%m-%d %H:%M:%S',
        )
        console_handler.setFormatter(formatter_console)

        # File handler configuration
        file_handler = logging.FileHandler(os.path.normpath(os.path.join(self.app_folder, log_file)), delay = False)
        file_handler.setLevel(file_level)
        formatter_file = logging.Formatter(
            '%(asctime)s.%(msecs)03d,%(filename)-24s,%(lineno)05d,%(funcName)-24s,%(levelname)-10s,%(message)s',
            datefmt = '%Y-%m-%d %H:%M:%S',
        )
        file_handler.setFormatter(formatter_file)

        # Attach handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def logger_close(self):
        # Close all handlers and shut down logging
        for handler in logger.handlers:
            handler.close()
        logging.shutdown()

# ==================================
# EnergyPlus Output Translator Class
# ==================================
class ep_otpt_trnslt:
    """
    EnergyPlus Output Translator and Visualization Launcher.

    Parameters
    ----------
    app_dir : str
        Absolute path of the BEPVis project directory.
    logger : logging.Logger
        Logger instance for debug and progress tracking.
    ep_output_mainfolder_name : str
        Folder containing EnergyPlus simulation results
        (SQLite database + epJSON).
    s_simulation_code : list[str]
        List of simulation identifiers (folder names).

    Description
    ----------
    For each simulation code, the class:
    - Reads the epJSON model description
    - Loads tables from EnergyPlus SQLite output
    - Extracts zones, variables, HVAC associations, occupancy objects
    - Builds monthly and annual energy datasets
    - Saves temporary Excel files in `/Visualizations`
    - Calls the corresponding chart modules in sequence

    The class supports multiple simulations and can be used in batch mode.
    """
    def __init__(self, app_dir = '?', logger = '?', ep_output_mainfolder_name = '?', s_simulation_code = '?'):    
        
        """
        Initialize the translator with paths, logging, and simulation codes.
        Set default visualization actions and load visualizations folder.
        """

        self.app_dir = app_dir
        self.logger = logger
        self.ep_output_mainfolder_pathandname = os.path.normpath(os.path.join(self.app_dir, ep_output_mainfolder_name))
        self.action = {'GainsAndLosses_Spaces': True,
                       'GainsAndLosses_Parameters':True,
                       'line_chart': True,
                       'heatmap': True,
                       'scatter_plot': True,
                       'radar': True}
        self.visualizations_folder_path = os.path.normpath(os.path.join(self.app_dir, 'Visualizations'))
        sys.path.append(os.path.join(self.app_dir, 'Visualizations'))

        self.logger.debug("Diagramming... Start")
        
        # Process each simulation code
        for n in range(len(s_simulation_code)):
            simulation_code = str(s_simulation_code[n])
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Setting the paths')
            
            # Define paths to output folders and files
            ep_output_folder_pathandname = os.path.normpath(os.path.join(self.ep_output_mainfolder_pathandname, simulation_code))
            ep_output_sqlite_file_pathandname = os.path.normpath(os.path.join(ep_output_folder_pathandname, 'eplusout.sql'))
            
            # Load simulation JSON file
            with open(os.path.normpath(os.path.join(self.ep_output_mainfolder_pathandname, simulation_code + '.epJSON')), 'r') as file:
                self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the epJSON file')
                self.sim_epjson = json.load(file)
            
            # Load simulation data from SQLite database
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file...')
            self.get_data(ep_output_sqlite_file_pathandname, simulation_code = simulation_code)
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file... Done')
            
            # Generate visualizations
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams...')
            self.show(simulation_code = simulation_code)
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams... Done')

    def get_data(self, ep_output_sqlite_file_pathandname = '?', simulation_code = '?'):
        
        """
        Load and preprocess EnergyPlus SQLite output.

        This method:
        - Opens the EnergyPlus SQLite database
        - Applies performance-enhancing PRAGMA settings
        - Loads `ReportVariableWithTime`, `Time`, `Zones`, and `NominalPeople`
        - Converts the main table into a typed Pandas DataFrame
        - Registers DataFrames in DuckDB for fast SQL queries
        - Extracts key lists such as:
            * zone names
            * nominal people objects
            * HVAC-connected zones
            * total HVAC floor area
        """

        conn = sqlite3.connect(ep_output_sqlite_file_pathandname)
        cursor = conn.cursor()
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file... Increasing the speed of access to file')
        
        # SQLite pragmas for performance improvement
        cursor.execute("PRAGMA journal_mode=WAL;")      # Enable write-ahead logging for concurrency
        cursor.execute("PRAGMA synchronous=NORMAL;")    # Balance between speed and safety
        cursor.execute("PRAGMA temp_store=MEMORY;")     # Use memory for temporary tables
        cursor.execute("PRAGMA cache_size=-1048576;")   # Set cache size to 1GB
        cursor.execute("PRAGMA optimize;")              # SQLite automatic optimizations
        conn.commit()
        cursor.execute("VACUUM;")                       # Defragment database file
        conn.commit()
        
        # Read ReportVariableWithTime table fully
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file... Reading table "reportvariablewithtime"')
        cursor.execute('SELECT "TimeIndex", "Month", "Day", "Hour", "Minute", "Name", "KeyValue", "Value" FROM ReportVariableWithTime')
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        
        self.df_reportvariablewithtime = pd.DataFrame(data, columns = columns)
        
        # Cast columns to appropriate data types for performance and accuracy
        self.df_reportvariablewithtime['TimeIndex'] = self.df_reportvariablewithtime['TimeIndex'].astype(int)
        self.df_reportvariablewithtime['Month'] = self.df_reportvariablewithtime['Month'].astype(int)
        self.df_reportvariablewithtime['Day'] = self.df_reportvariablewithtime['Day'].astype(int)
        self.df_reportvariablewithtime['Hour'] = self.df_reportvariablewithtime['Hour'].astype(int)
        self.df_reportvariablewithtime['Minute'] = self.df_reportvariablewithtime['Minute'].astype(int)
        self.df_reportvariablewithtime['Value'] = self.df_reportvariablewithtime['Value'].astype(float)

                # TO BE USED ONLY IF TYPICAL ReportVariableWithTime tables have very large size
                # logging.debug("Session of diagramming - Simulation: " + simulation_code + ' - Reading the sql file... Reading table "reportvariablewithtime" in  chunks')
                # cursor.execute('SELECT "Month", "Day", "Hour", "Minute", "Name", "KeyValue", "Value" FROM ReportVariableWithTime')
                # chunk_size = 1000000  # Leggi a blocchi di 10k righe
                # dfs = []
                # columns = [col[0] for col in cursor.description]
                # while True:
                #     data = cursor.fetchmany(chunk_size)
                #     if not data:
                #         break
                #     data_array = np.array(data)  # Converte in array NumPy
                #     dfs.append(pd.DataFrame.from_records(data_array, columns = columns))
                # self.df_reportvariablewithtime = pd.concat(dfs, ignore_index = True)
        
        # Load additional tables from database using pandas read_sql
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file... Reading table "zones"')
        self.df_zones = pd.read_sql('select * from Zones', con = conn)
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file... Reading table "time"')
        self.df_time = pd.read_sql('select * from Time', con = conn)
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file... Reading table "NominalPeople"')
        self.df_nominalpeople = pd.read_sql('select * from NominalPeople', con = conn)

        conn.close()
        
        # Register DataFrames with duckdb for advanced querying
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Reading the sql file... Registering dataframes for use in duckdb')
        df_zones = self.df_zones
        df_time = self.df_time
        df_nominalpeople = self.df_nominalpeople
        df_reportvariablewithtime = self.df_reportvariablewithtime
        
        # Extract zone names
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Preparing data... Getting variable s_zone_name')
        query = 'select zonename from df_zones'
        self.s_zone_name = duckdb.query(query).df()['ZoneName'].tolist()
        
        # Extract nominal people object names
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Preparing data... Getting variable s_nominal_people_object_name')
        query = 'select ObjectName from df_nominalpeople'
        self.s_nominal_people_object_name = duckdb.query(query).df()['ObjectName'].tolist()
        
        # Extract zones to consider for HVAC systems from JSON
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Preparing data... Getting variable s_zone_toconsider_hvac')
        self.s_zone_toconsider_hvac = []
        
        for item in self.sim_epjson['ZoneHVAC:EquipmentConnections'].values():
            self.s_zone_toconsider_hvac.append(str(item['zone_name']))
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Preparing data... Getting variable floor_area_total_hvac')
        
        # Calculate total floor area of HVAC zones
        self.floor_area_total_hvac = 0
        for index, row in self.df_zones.iterrows():
            if row['ZoneName'] in self.s_zone_toconsider_hvac and row['IsPartOfTotalArea'] == 1:
                self.floor_area_total_hvac = self.floor_area_total_hvac + row['FloorArea']
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Preparing data... Getting variables s_floor_area_and_overall, s_zone_name_and_overall')
        
         # Prepare lists for floor areas and zone names including an overall entry
        self.s_floor_area_and_overall = []
        self.s_zone_name_and_overall = []
        for index, row in self.df_zones.iterrows():
            self.s_floor_area_and_overall.append(row['FloorArea'])
            self.s_zone_name_and_overall.append(row['ZoneName'])
        self.s_zone_name_and_overall.append('*AllBuilding*')
        self.s_floor_area_and_overall.append(sum(self.s_floor_area_and_overall))

    def show(self, simulation_code = '?'):
        
        """
        Generate all visualizations for one simulation.

        Includes:
        - Gains & Losses bar charts (per zone, per parameter)
        - Heatmaps of air temperature (hourly resolution)
        - PMV/PPD line charts (monthly aggregates)
        - Scatter plots of heating/cooling rate vs outdoor temperature
        - Radar chart of annual energy balance

        Each visualization produces:
        - An Excel dataset
        - A graphical output saved in `/Visualizations/`
        """
        
        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams...')

        df_reportvariablewithtime = self.df_reportvariablewithtime
        df_time = self.df_time
        df_zones = self.df_zones

        # ---------------------------
        # Bar Chart Gains and Losses
        # ---------------------------

        # Check if gains and losses visualization is requested
        if self.action['GainsAndLosses_Spaces'] or self.action['GainsAndLosses_Spaces']:
            
            from GainsAndLosses import GainsAndLosses_Spaces, GainsAndLosses_Parameters
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams... Retrieving data of heat gains and losses...')
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams... Gains & Losses - Preparing dataframes...')
            
            df_gains = pd.DataFrame()
            df_losses = pd.DataFrame()
            
            dict_gains = {'Month': [calendar.month_abbr[month + 1] for month in range(12)]}
            dict_losses = {'Month': [calendar.month_abbr[month + 1] for month in range(12)]}
            
            for n_zone in range(len(self.s_zone_name_and_overall)):
                zone_name = str(self.s_zone_name_and_overall[n_zone])
                self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams... Gains & Losses - Preparing dataframes... Data from zone ' + zone_name)
                floor_area = self.s_floor_area_and_overall[n_zone]
                query_zone = '?'
                query_zone_ilas = '?'

                # Prepare query filters depending on zone type
                if zone_name.upper() == '*ALLBUILDING*':
                    query_zone = ''
                    query_zone_ilas = ''
                else:
                    query_zone = " and KeyValue = '" + zone_name + "'" 
                    # Attempt to find the IdealLoadsAirSystem association for the zone
                    s_correspondance = [{'find': zone_name, 'among objects': 'ZoneHVAC:EquipmentConnections', 'in field': 'zone_name', 'get value from field': 'zone_conditioning_equipment_list_name', 'results_class': 'ZoneHVAC:EquipmentList'},
                                        {'find': '?', 'among objects': '?', 'in field': '*id*', 'get value from field': 'equipment|zone_equipment_object_type=ZoneHVAC:IdealLoadsAirSystem|zone_equipment_name', 'results_class': 'ZoneHVAC:EquipmentList'}]
                    try:
                        idealloadsairsystem = self.create_association_amongobjects(sim_epjson = self.sim_epjson,
                                                                                s_correspondance = s_correspondance)[0]
                        query_zone_ilas = " and KeyValue = '" + idealloadsairsystem.upper() + "'"
                    except:
                        query_zone_ilas = '*NO*'

                # Queries for gains
                query_base = "select SUM(Value) as sum from df_reportvariablewithtime where Name = '*NAME*"
                dict_name = {'Solar': 'Zone Windows Total Transmitted Solar Radiation Energy' + "' " + query_zone + " group by Month order by Month",
                          'Lights': 'Zone Lights Electricity Energy' + "' " + query_zone + " group by Month order by Month",
                          'People': 'Zone People Total Heating Energy' + "' " + query_zone + " group by Month order by Month",
                          'Equipment': 'Zone Electric Equipment Total Heating Energy' + "' " + query_zone + " group by Month order by Month",
                          'Opaque conduction - Gains': 'Zone Opaque Surface Inside Faces Total Conduction Heat Gain Energy' + "' " + query_zone + " group by Month order by Month",
                          'Glazing conduction - Gains': 'Zone Windows Total Heat Gain Energy' + "' " + query_zone + " group by Month order by Month",
                          'Infiltration - Gains': 'Zone Infiltration Total Heat Gain Energy' + "' " + query_zone + " group by Month order by Month",
                          'Natural ventilation - Gains': '_' + "' " + query_zone + " group by Month order by Month",
                          'Mechanical ventilation - Gains': '_' + "' " + query_zone + " group by Month order by Month",
                          'Heating': 'Zone Ideal Loads Zone Total Heating Energy' + "' " + query_zone_ilas + " group by Month order by Month"}
                
                # Retrieve gains data
                for key in dict_name.keys():
                    query = query_base.replace('*NAME*', dict_name[key])
                    try:
                        df_data = duckdb.query(query).df()['sum'].to_list()
                        if len(df_data) != 0:
                            df_data = [df_data[n] / 3600000 / floor_area for n in range(len(df_data))]
                        else:
                            raise Exception("No value in df_data")
                    except Exception as e:
                        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams... Gains & Losses - Preparing dataframes... Data from zone... Error in duckdb ' + str(e))
                        df_data = [0 for i in range(12)]
                    dict_gains['*' + zone_name + '* - ' + key] = df_data

                # Queries for losses
                dict_name = {'Opaque conduction - Losses': 'Zone Opaque Surface Inside Faces Total Conduction Heat Loss Energy' + "' " + query_zone + " group by Month order by Month",
                            'Glazing conduction - Losses': 'Zone Windows Total Heat Loss Energy' + "' " + query_zone + " group by Month order by Month",
                            'Infiltration - Losses': 'Zone Infiltration Total Heat Loss Energy' + "' " + query_zone + " group by Month order by Month",
                            'Natural ventilation - Losses': '_' + "' " + query_zone + " group by Month order by Month",
                            'Mechanical ventilation - Losses': '_' + "' " + query_zone + " group by Month order by Month",
                            'Cooling': 'Zone Ideal Loads Zone Total Cooling Energy' + "' " + query_zone_ilas + " group by Month order by Month"}
                
                # Retrieve losses data
                for key in dict_name.keys():
                    query = query_base.replace('*NAME*', dict_name[key])
                    try:
                        df_data = duckdb.query(query).df()['sum'].to_list()
                        if len(df_data) != 0:
                            df_data = [df_data[n] / 3600000 / floor_area for n in range(len(df_data))]
                        else:
                            raise Exception("No value in df_data")
                    except Exception as e:
                        self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams... Gains & Losses - Preparing dataframes... Data from zone... Error in duckdb ' + str(e))
                        df_data = [0 for i in range(12)]
                    dict_losses['*' + zone_name + '* - ' + key] = [-df_data[i] for i in range(12)]

            # Create DataFrames for gains and losses
            df_gains = pd.DataFrame.from_dict(dict_gains)
            df_losses = pd.DataFrame.from_dict(dict_losses)
            df_gains = df_gains.fillna(0)
            df_losses = df_losses.fillna(0)
            
            # Save data to Excel
            self.logger.debug("Diagramming... Simulation: " + simulation_code + ' - Showing diagrams... Saving file of heat gains and losses...')
            data_file_pathandname = os.path.normpath(os.path.join(self.visualizations_folder_path, 'DataBar.xlsx'))
            df_gains.to_excel(data_file_pathandname, sheet_name = 'Gains')
            with pd.ExcelWriter(data_file_pathandname, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_losses.to_excel(writer, sheet_name = 'Losses')

            # Find max and min for chart scaling
            gains_max_month =  - sys.float_info.max
            losses_min_month = sys.float_info.max
            gains_max_year = - sys.float_info.max
            losses_min_year = sys.float_info.max
            
            for n_zone in range(len(self.s_zone_name_and_overall)):
                zone_name = self.s_zone_name_and_overall[n_zone]
                # Max gains by month and year
                columns = df_gains.filter(like = '*' + zone_name + '*').columns
                df_supp = df_gains[columns]
                for index, row in df_supp.iterrows():
                    gains_max_month = max(gains_max_month, sum(row))
                gains_max_year = max(gains_max_year, df_supp.sum().sum())
                # Min losses by month and year
                columns = df_losses.filter(like = '*' + zone_name + '*').columns
                df_supp = df_losses[columns]
                for index, row in df_supp.iterrows():
                    losses_min_month = min(losses_min_month, sum(row))
                losses_min_year = min(losses_min_year, df_supp.sum().sum())

            # Generate charts for each zone
            for n_zone in range(len(self.s_zone_name_and_overall)):
                zone_name = str(self.s_zone_name_and_overall[n_zone])
                columns = ['Month']
                columns.extend(df_gains.filter(like = zone_name).columns)
                df_gains_single = df_gains[columns]
                columns = ['Month']
                columns.extend(df_losses.filter(like = zone_name).columns)
                df_losses_single = df_losses[columns]
                if self.action['GainsAndLosses_Spaces']:
                    filesave_name = clean_string(string_toprocess = "barchart_gainsandlosses_zone_" + str(zone_name) + "_sim_" + str(simulation_code))
                    GainsAndLosses_Spaces_Chart = GainsAndLosses_Spaces(df_gains = df_gains_single, df_losses = df_losses_single, gains_max_month =  gains_max_month, gains_max_year = gains_max_year, losses_min_month = losses_min_month, losses_min_year = losses_min_year, filesave_name = filesave_name)

            # Aggregate gains and losses for parameters visualization
            row = {}
            df_gains_s_column = df_gains.columns.to_list()
            for column in df_gains_s_column:
                row[column] = [df_gains[column].sum()]
            data_gains = pd.DataFrame.from_dict(row)
            row = {}
            df_losses_s_column = df_losses.columns.to_list()
            for column in df_losses_s_column:
                row[column] = [df_losses[column].sum()]
            data_losses = pd.DataFrame.from_dict(row)
            
            # Generate parameter charts if requested
            if self.action['GainsAndLosses_Parameters']:
                filesave_name = clean_string(string_toprocess = "barchart_gainsandlosses_sim_" + str(simulation_code))
                GainsAndLosses_Parameters_Chart = GainsAndLosses_Parameters(data_gains = data_gains, data_losses = data_losses, s_zone_name = self.s_zone_name_and_overall, filesave_name = filesave_name)
        
        # ----------------------
        # Heatmap
        # ----------------------

        # Check if heatmap visualization is requested
        if self.action['heatmap']:
            for zone_name in self.s_zone_name:
                # Query air temperature data for the zone
                query = "select KeyValue, TimeIndex, Value from df_reportvariablewithtime where Name = 'Zone Air Temperature' and KeyValue = '" + zone_name + "'"
                df_data = duckdb.query(query).df()
                query = 'select KeyValue, Year, Month, Day, Hour, Minute, Value from df_data INNER JOIN df_time ON df_time.TimeIndex = df_data.TimeIndex'
                df_data = duckdb.query(query).df()

                # Helper function to format date elements to two digits
                def date_el_rjust(el):
                    el = str(el).rjust(2, '0')
                    return el
                
                # Create a Date column in MM/DD/YYYY format
                df_data["Date"] = df_data['Month'].apply(date_el_rjust) + "/" + df_data['Day'].apply(date_el_rjust) + "/" + df_data['Year'].apply(str)

                # Drop unneeded columns and rename KeyValue for clarity
                df_data = df_data.drop(['Year', 'Month', 'Day', 'Minute'], axis = 1)
                df_data = df_data.rename({'KeyValue': 'Space'}, axis = 1)
                source_file_pathandname = os.path.normpath(os.path.join(self.visualizations_folder_path, 'DataHeatmap.xlsx'))

                # Import and call the heatmap function
                from Heatmap import htmp
                filesave_name = clean_string(string_toprocess = "heatmap_temps_zone_" + str(zone_name) + "_sim_" + str(simulation_code))
                heatmap = htmp(df = df_data,
                               source_file_pathandname = source_file_pathandname,
                               zone_name = zone_name,
                               parameter_title = 'Temperature',
                               parameter_unit = '°C',
                               ns_color = 12,           # Number of colors to use in heatmap gradient
                               #s_limit = [20, 25],     # Optional: fixed limits for color scale
                               s_limit_best = [20, 26], # Admitted comfortable range for anomalies
                               filesave_name = filesave_name) 
                pass

            # PMV in zones - AVG + MIN + MAX
            query = 'select zonename from df_zones'
            s_zone_name = duckdb.query(query).df()['ZoneName'].tolist()
            df_data = pd.DataFrame()

        # ------------------------
        # PMV and PPD Line Charts
        # ------------------------

        # Check if line chart visualization is requested
        if self.action['line_chart']:
            # Prepare dataframe for PMV (Predicted Mean Vote)
            df_data = pd.DataFrame()
            for month in range(12):
                row = {'Month': calendar.month_abbr[month + 1]}
                for nominal_people_object_name in self.s_nominal_people_object_name:
                    query = "select avg(\"Value\"), min(\"Value\"), max(\"Value\") from df_reportvariablewithtime where Name = 'Zone Thermal Comfort Fanger Model PMV' and KeyValue = '?*nominal_people_object_name*?' and Month = ?*month*?"
                    query = query.replace("?*nominal_people_object_name*?", nominal_people_object_name).replace("?*month*?", str(month + 1))
                    df_temp = duckdb.query(query).df()
                    # Store aggregated PMV stats per zone
                    row[nominal_people_object_name] = [df_temp['avg("Value")'][0]]
                    row[nominal_people_object_name + "min"] = [df_temp['min("Value")'][0]]
                    row[nominal_people_object_name + "max"] = [df_temp['max("Value")'][0]]
                df_data = pd.concat([df_data, pd.DataFrame.from_dict(row)], axis = 0, ignore_index = True)
            
            source_file_pathandname = os.path.normpath(os.path.join(self.visualizations_folder_path, 'DataLine.xlsx'))
            df_data.to_excel(source_file_pathandname, sheet_name = 'PMV Data')
            
            # Prepare dataframe for PPD (Predicted Percentage Dissatisfied)
            df_data = pd.DataFrame()
            
            for month in range(12):
                row = {'Month': calendar.month_abbr[month + 1]}
                for nominal_people_object_name in self.s_nominal_people_object_name:
                    query = "select avg(Value), min(Value), max(Value) from df_reportvariablewithtime where Name = 'Zone Thermal Comfort Fanger Model PPD' and KeyValue = '?*nominal_people_object_name*?' and Month = ?*month*?"
                    query = query.replace("?*nominal_people_object_name*?", nominal_people_object_name).replace("?*month*?", str(month + 1))
                    df_temp = duckdb.query(query).df()
                    # Store aggregated PPD stats per zone
                    row[nominal_people_object_name] = [df_temp['avg("Value")'][0]]
                    row[nominal_people_object_name + "min"] = [df_temp['min("Value")'][0]]
                    row[nominal_people_object_name + "max"] = [df_temp['max("Value")'][0]]
                df_data = pd.concat([df_data, pd.DataFrame.from_dict(row)], axis = 0, ignore_index = True)
            
            # Append PPD data as a new sheet in the same Excel file
            source_file_pathandname = os.path.normpath(os.path.join(self.visualizations_folder_path, 'DataLine.xlsx'))
            with pd.ExcelWriter(source_file_pathandname, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:  
                df_data.to_excel(writer, sheet_name = 'PPD Data')

            # Import and call the line chart function
            from LineChart import lnchrt
            filesave_name = clean_string(string_toprocess = "linechart_pmv_sim_" + str(simulation_code))
            linechart = lnchrt(source_file_pathandname = source_file_pathandname,
                                    s_nominal_people_object_name = self.s_nominal_people_object_name,
                                    html_file_pathandname = os.path.normpath(os.path.join(self.app_dir, 'Visualizations\Zones - PMV - Monthly')),
                                    target = 'PMV',
                                    filesave_name = filesave_name)
            filesave_name = clean_string(string_toprocess = "linechart_ppd_sim_" + str(simulation_code))
            linechart = lnchrt(source_file_pathandname = source_file_pathandname,
                                    s_nominal_people_object_name = self.s_nominal_people_object_name,
                                    html_file_pathandname = os.path.normpath(os.path.join(self.app_dir, 'Visualizations\Zones - PMV - Monthly')),
                                    target = 'PPD',
                                    filesave_name = filesave_name)
            
        # ------------------------
        # Scatter Plot
        # ------------------------

        # Check if scatter plot visualization is requested
        if self.action['scatter_plot']:
            
            # Retrieve outdoor air drybulb temperature data
            query = "select TimeIndex, Value from df_reportvariablewithtime where Name = 'Site Outdoor Air Drybulb Temperature' and KeyValue = 'Environment'"
            df_outdtemp = duckdb.query(query).df()
            
            # Join with the time dataframe to get Year, Month, Day, Hour, Minute
            query = 'select Year, Month, Day, Hour, Minute, Value as outdtemp, df_time.TimeIndex from df_outdtemp INNER JOIN df_time ON df_time.TimeIndex = df_outdtemp.TimeIndex'
            df_outdtemp = duckdb.query(query).df()
            
            # Process data for each zone
            value_max_heating = 0
            value_max_cooling = 0
            n_zone = -1
            s_source_file_pathandname = []
            dict_ilas = {}
            for zone_name in self.s_zone_name:
                n_zone = n_zone + 1
                # Get floor area for the current zone
                zone_floor_area = df_zones[df_zones['ZoneName'] == zone_name]['FloorArea'].values[0]
                
                # Associate HVAC equipment objects for the zone
                s_correspondance = [{'find': zone_name, 'among objects': 'ZoneHVAC:EquipmentConnections', 'in field': 'zone_name', 'get value from field': 'zone_conditioning_equipment_list_name', 'results_class': 'ZoneHVAC:EquipmentList'},
                                                                                {'find': '?', 'among objects': '?', 'in field': '*id*', 'get value from field': 'equipment|zone_equipment_object_type=ZoneHVAC:IdealLoadsAirSystem|zone_equipment_name', 'results_class': 'ZoneHVAC:EquipmentList'}]
                s_idealloadsairsystem = self.create_association_amongobjects(sim_epjson = self.sim_epjson,
                                                    s_correspondance = s_correspondance)
                
                # Process heating and cooling data for each Ideal Loads Air System associated
                for idealloadsairsystem in s_idealloadsairsystem:
                    
                    # Query heating data normalized by floor area
                    query = "select TimeIndex, Value as H from df_reportvariablewithtime where Name = 'Zone Ideal Loads Zone Total Heating Rate' and KeyValue = '" + idealloadsairsystem.upper() + "'"
                    df_data = duckdb.query(query).df()
                    df_data['H'] = df_data['H'] / zone_floor_area
                    value_max_heating = max(value_max_heating, df_data['H'].max())
                    
                    # Query cooling data normalized by floor area
                    query = "select TimeIndex, Value as C from df_reportvariablewithtime where Name = 'Zone Ideal Loads Zone Total Cooling Rate' and KeyValue = '" + idealloadsairsystem.upper() + "'"
                    df_data_c = duckdb.query(query).df()
                    df_data_c['C'] = df_data_c['C'] / zone_floor_area
                    value_max_cooling = max(value_max_cooling, df_data_c['C'].max())

                    # Join heating data with outdoor temperature and date/time info
                    query = 'select Year, Month, Day, Hour, Minute, df_outdtemp.TimeIndex, outdtemp, H from df_data INNER JOIN df_outdtemp ON df_outdtemp.TimeIndex = df_data.TimeIndex'
                    df_data = duckdb.query(query).df()
                    
                    # Join cooling data with heating data to get all info in one dataframe
                    query = 'select Year, Month, Day, Hour, Minute, H, df_data.TimeIndex, outdtemp, C from df_data_c INNER JOIN df_data ON df_data.TimeIndex = df_data_c.TimeIndex'
                    df_data = duckdb.query(query).df()

                    # Function to format date/time elements with leading zeros
                    def date_el_rjust(el):
                        el = str(el).rjust(2, '0')
                        return el
                    
                    # Create formatted "Date/Time" column (MM//DD//YYYY HH:MM)
                    df_data["Date/Time"] = df_data['Month'].apply(date_el_rjust) + "//" + df_data['Day'].apply(date_el_rjust) + "//" + df_data['Year'].apply(str) + " " + df_data['Hour'].apply(date_el_rjust) + ":" + df_data['Minute'].apply(date_el_rjust)

                    # Clean dataframe: drop unused columns and rename for clarity
                    df_data = df_data.drop(['Year', 'Month', 'Day', 'Hour', 'Minute', 'TimeIndex'], axis = 1)
                    df_data = df_data.rename({'outdtemp': 'Outdoor_Temperature', 'H': 'Zone_ILAS_HeatingRate', 'C': 'Zone_ILAS_CoolingRate'}, axis = 1)
                    
                    # Save data to Excel file for scatter plot generation
                    source_file_pathandname = os.path.normpath(os.path.join(self.visualizations_folder_path, 'DataScatter_Heating_Cooling' + str(n_zone) + '.xlsx'))
                    df_data.to_excel(source_file_pathandname)
                    s_source_file_pathandname.append(source_file_pathandname)
                    dict_ilas[str(zone_name)] = str(idealloadsairsystem)
            # Import and call the scatter plot function
            from Scatter_Plot import scttr_plt
            n_ilas = -1
            for key, value in dict_ilas.items():
                n_ilas += 1
                filesave_name = clean_string(string_toprocess = "scatterplot_ilas_zone_" + key + "_sim_" + str(simulation_code))
                scttr_plt_htng = scttr_plt(source_file_pathandname = s_source_file_pathandname[n_ilas], zone_name = key, value_max_heating = value_max_heating, value_max_cooling = value_max_cooling,
                                           filesave_name = filesave_name)
        # ------------------------
        # Radar Chart
        # ------------------------
        
        # Check if radar chart visualization is requested
        if self.action['radar']:
            # Initialize empty DataFrame to store zone energy data
            df = pd.DataFrame()
            
            # Process each zone to extract energy consumption normalized by floor area
            for zone_name in self.s_zone_name:
                # Get floor area for current zone
                floor_area = df_zones[df_zones['ZoneName'] == zone_name]['FloorArea'].to_list()[0]
                # Prepare dictionary to hold energy data for this zone
                row = {'Zone': zone_name}
                
                # Query and normalize lights electricity energy (convert from Joules to kWh, divide by floor area)
                query = "select SUM(Value) as sum from df_reportvariablewithtime where Name = 'Zone Lights Electricity Energy' and KeyValue = '" + zone_name + "'"
                df_data = duckdb.query(query).df()['sum'].to_list()[0] / 3600000 / floor_area
                row['Lights'] = [df_data]
                
                # Query and normalize electric equipment heating energy
                query = "select SUM(Value) as sum from df_reportvariablewithtime where Name = 'Zone Electric Equipment Total Heating Energy' and KeyValue = '" + zone_name + "'"
                df_data = duckdb.query(query).df()['sum'].to_list()[0] / 3600000 / floor_area
                row['Equipment'] = [df_data]
                
                # Query and normalize people heating energy
                query = "select SUM(Value) as sum from df_reportvariablewithtime where Name = 'Zone People Total Heating Energy' and KeyValue = '" + zone_name + "'"
                df_data = duckdb.query(query).df()['sum'].to_list()[0] / 3600000 / floor_area
                row['People'] = [df_data]
                                
                # Get HVAC equipment associations related to the zone
                s_item = self.create_association_amongobjects(sim_epjson = self.sim_epjson,
                                                                    s_correspondance = [{'find': zone_name, 'among objects': 'ZoneHVAC:EquipmentConnections', 'in field': 'zone_name', 'get value from field': 'zone_conditioning_equipment_list_name', 'results_class': 'ZoneHVAC:EquipmentList'},
                                                                                        {'find': '?', 'among objects': '?', 'in field': '*id*', 'get value from field': 'equipment|zone_equipment_object_type=ZoneHVAC:IdealLoadsAirSystem|zone_equipment_name', 'results_class': 'ZoneHVAC:EquipmentList'}])
                # For each associated Ideal Loads Air System, get heating and cooling energy normalized by floor area
                for item in s_item:
                    query = "select SUM(Value) as sum from df_reportvariablewithtime where Name = 'Zone Ideal Loads Zone Total Heating Energy' and KeyValue = UPPER('" + item + "')"
                    df_data = duckdb.query(query).df()['sum'].to_list()[0] / 3600000 / floor_area
                    row['Heating'] = [df_data]
                    query = "select SUM(Value) as sum from df_reportvariablewithtime where Name = 'Zone Ideal Loads Zone Total Cooling Energy' and KeyValue = UPPER('" + item + "')"
                    df_data = duckdb.query(query).df()['sum'].to_list()[0] / 3600000 / floor_area
                    row['Cooling'] = [-df_data]
                
                 # Placeholder for hot water heating (currently zero)
                row['Hot water Heating'] = [0 / floor_area]
                
                # Append this zone's data to the dataframe
                df = pd.concat([df, pd.DataFrame.from_dict(row)], axis = 0)
            
            # Save the collected data for radar chart visualization to an Excel file
            source_file_pathandname = os.path.normpath(os.path.join(self.visualizations_folder_path, 'DataRadar.xlsx'))
            df.to_excel(source_file_pathandname, sheet_name = 'Radar')

            # Import and call the radar chart function
            from Radar import rdr
            filesave_name = clean_string(string_toprocess = "radarchart_energyconsumption_sim_" + str(simulation_code))
            Radar = rdr(source_file_pathandname = source_file_pathandname,
                        filesave_name = filesave_name) 

    # -------------------------------------------------------------------
    # Function to Create Associations Between Objects in EnergyPlus JSON
    # -------------------------------------------------------------------
    def create_association_amongobjects(self, sim_epjson = '?', s_correspondance = '?'):
        """
        This function establishes associations between objects within the EnergyPlus JSON structure.
        It searches for specified values within given object fields and extracts linked values,
        supporting multi-step associations and nested lookups.

        Parameters:
        - sim_epjson: The EnergyPlus simulation JSON data.
        - s_correspondance: A list of dictionaries defining the search criteria and extraction rules.

        Returns:
        - The list of matched results from the final search step.
        """
        n = -1
        for correspondance in s_correspondance:
            n = n + 1
            s_correspondance[n]['results'] = []
            
            if n == 0:
                # First level: search within specified object type
                for id, object in sim_epjson[correspondance['among objects']].items():
                    if correspondance['in field'] == '*id*':
                        if id == correspondance['find']:
                            s_correspondance[n]['results'].append(id)
                    else:
                        if object[correspondance['in field']] == correspondance['find']:
                            if correspondance['get value from field'] == '*id*':
                                s_correspondance[n]['results'].append(id)
                            else:
                                if correspondance['get value from field'].find('|') >= 0:
                                    split = correspondance['get value from field'].split('|')
                                    array_name = split[0]
                                    equivalence = split[1]
                                    equivalence_field = equivalence.split('=')[0]
                                    equivalence_value = equivalence.split('=')[1]
                                    field_name = split[2]
                                    for item in object[array_name]:
                                        if str(item[equivalence_field]) == str(equivalence_value):
                                            s_correspondance[n]['results'].append(item[field_name])
                                else:
                                    s_correspondance[n]['results'].append(object[correspondance['get value from field']])
            else:
                # Subsequent levels: search within results from previous level
                for item in s_correspondance[n - 1]['results']:
                    for id, object in sim_epjson[s_correspondance[n - 1]['results_class']].items():
                        Found = False
                        if correspondance['in field'] == '*id*':
                            if id == item:
                                Found = True
                        else:
                            if object[correspondance['in field']] == item:
                                Found = True
                        if Found == True:
                            if correspondance['get value from field'] == '*id*':
                                s_correspondance[n]['results'].append(id)
                            else:
                                if correspondance['get value from field'].find('|') >= 0:
                                    split = correspondance['get value from field'].split('|')
                                    array_name = split[0]
                                    equivalence = split[1]
                                    equivalence_field = equivalence.split('=')[0]
                                    equivalence_value = equivalence.split('=')[1]
                                    field_name = split[2]
                                    for item in object[array_name]:
                                        if str(item[equivalence_field]) == str(equivalence_value):
                                            s_correspondance[n]['results'].append(item[field_name])
                                else:
                                    s_correspondance[n]['results'].append(object['get value from field'])
        return s_correspondance[n]['results']

# ================================
# Main Execution Entry Point
# ================================
    
if __name__ == "__main__":
    general = gnrl()
    logger = general.get_logger(__name__, console_level = logging.DEBUG, file_level = logging.DEBUG, log_file = 'app.log')
    logger.debug('Ecco')
    ep_output_translate = ep_otpt_trnslt(app_dir = general.app_folder,
                                         logger = logger,
                                         ep_output_mainfolder_name = '..\\CODE - Error generation\\IN',
                                         s_simulation_code = ['5Zone_IdealLoadsAirSystems_ReturnPlenum'])
    general.logger_close()