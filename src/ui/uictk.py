import json
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from src.ui.customgraphframe import CustomGraphFrame
from src.ui.graphframe import GraphFrame
from src.ui.optionsframe import OptionsFrame
from src.ui.parameterframe import ParameterFrame
from src.ui.scrollingbuttonframe import ScrollingCheckButtonFrame

from src import parseradfile
from src import utils
from src.graphing.hodograph import HodoGraph
from src.graphing.xygraph import XYGraph
from src import datapath
from src.utils import read_params
from src import runGDL
from src.parseradfile import  get_latitude_value
from src.ui.errorframe import ErrorFrame
from src.ui import windowicon


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # vars
        self.logo_label = None
        self.upload_button = None
        self.scrollable_frame = None
        self.strato_graph_frame = None
        self.tropo_graph_frame = None
        self.strato_param_frame = None
        self.tropo_param_frame = None
        self.is_main_layout = False

        self.station = None
        self.graph_objects = {}
        self.strato_params = None
        self.tropo_params = None

        #Load up the options
        self.options = utils.load_options()

        self.setup_initial_layout()

    def setup_initial_layout(self):
        """
        @return:
        """
        self.title("Gravity Wave Analysis Tool")

        # Set Icon
        windowicon.set_icon(self)

        # setup grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # logo
        logo = ctk.CTkImage(light_image=Image.open(datapath.getDataPath("media/logo_text.png")),
                            dark_image=Image.open(datapath.getDataPath("media/logo_text.png")), size=(600, 600))
        self.logo_label = ctk.CTkLabel(self, image=logo, text="")
        self.logo_label.grid(row=0, column=0, padx=10, pady=10)

        # upload button
        self.upload_button = ctk.CTkButton(self, text="Upload File", command=self.upload_file)
        self.upload_button.grid(row=1, column=0, padx=10, pady=(0, 10))

    def switch_to_main_layout(self, strato_params, tropo_params):
        """
        @param strato_params:
        @param tropo_params:
        @return:
        """
        self.is_main_layout = True
        # remove logo
        self.logo_label.destroy()

        # setup grid
        # +---+---+-------+---+
        # | u | o |       | p |
        # +---+---+ strato+ a +
        # | graph |       | r |
        # + select+-------+ a +
        # |       |       | m |
        # +---+---+ tropo +---+
        # | custom|       | e |
        # +---+---+-------+---+
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=0)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        # col 0-1
        self.upload_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        options_button = ctk.CTkButton(self, text="Options", command=self.show_options)
        options_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.scrollable_frame \
            = ScrollingCheckButtonFrame(master=self, graph_objects=self.graph_objects, station=self.station,
                                        but_cmd=self.select_graph, export_cmd=self.export_graphs)
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew", rowspan=2, columnspan=2)

        custom_graph_button = ctk.CTkButton(self, text="Create Custom Graph", command=self.create_custom_graph)
        custom_graph_button.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew", columnspan=2)

        # col 2
        self.strato_graph_frame = GraphFrame(self)
        self.strato_graph_frame.grid(row=0, column=2, padx=(0, 10), pady=10, sticky="nsew", rowspan=2)

        self.tropo_graph_frame = GraphFrame(self)
        self.tropo_graph_frame.grid(row=2, column=2, padx=(0, 10), pady=(0, 10), sticky="nsew", rowspan=2)

        # col 3
        if strato_params:
            param_label = ctk.CTkLabel(self, text="Gravity Wave Parameters")
            param_label.grid(row=0, column=3, padx=(0, 10), pady=10, sticky="ew")

            self.strato_param_frame = ParameterFrame(master=self, params=strato_params, title="Stratosphere", width=350)
            self.strato_param_frame.grid(row=1, column=3, padx=(0, 10), pady=(0, 10), sticky="nsew")

            self.tropo_param_frame = ParameterFrame(master=self, params=tropo_params, title="Troposphere", width=350)
            self.tropo_param_frame.grid(row=2, column=3, padx=(0, 10), pady=(0, 10), sticky="nsew", rowspan=1)

            export_param_button = ctk.CTkButton(self, text="Export Parameters", command=self.export_params)
            export_param_button.grid(row=3, column=3, padx=(0, 10), pady=(0, 10), sticky="ew")

    def upload_file(self):
        """
        @return:
        """
        file_path = filedialog.askopenfilename()

        if not file_path:
            return

        self.station = parseradfile.generate_profile_data(file_path)

        gdl_or_idl = runGDL.detect_gdl_idl()
        if gdl_or_idl != 'none':
            try:
                runGDL.runGDL(file_path, get_latitude_value(file_path), gdl_or_idl)
                self.tropo_params, self.strato_params = read_params()
            except FileNotFoundError as e:
                ErrorFrame(self).showerror("No file found at '" + file_path + "'")
            except runGDL.GDLError:
                ErrorFrame(self).showerror("Unable to extract gravity wave parameters")
        else:
            ErrorFrame(self).showerror("Neither GDL nor IDL was detected. \n"
                                       "Please install GDL from https://gnudatalanguage.github.io/\n"
                                       "If you know GDL or IDL is installed, make sure it's accessible in PATH.")


        # GENERATE GRAPHS
        self.generate_graphs()

        if self.is_main_layout:
            self.strato_param_frame.set_params(self.strato_params)
            self.tropo_param_frame.set_params(self.tropo_params)
        else:
            self.switch_to_main_layout(self.strato_params, self.tropo_params)
            self.select_graph(next(iter(self.graph_objects)))

    def export_graphs(self, selected_graphs):
        """
        @param selected_graphs:
        @return:
        """

        # TODO: simply disable button if none are selected
        if not selected_graphs or len(selected_graphs) == 0:
            ErrorFrame(self).showerror("No graphs selected")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                 filetypes=(("PDF file", "*.pdf"), ("PNG files", "*.png")),
                                                 initialfile="graphs")

        if file_path:
            utils.save_graph_to_file(self.graph_objects, file_path, selected_graphs)

    def export_params(self):
        """
        @return:
        """
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="parameters")
        if filepath:
            utils.save_params_to_file(self.strato_params, self.tropo_params, filepath)

    def create_custom_graph(self):
        """
        @return:
        """
        CustomGraphFrame(self, self, self.station)

    def show_options(self):
        """
        @return:
        """
        OptionsFrame(self, self.graph_objects, self.station, self.options)

    def select_graph(self, title):
        """
        @param title:
        @return:
        """
        self.strato_graph_frame.draw_plot(self.graph_objects[title].get_figure("strato"))
        self.tropo_graph_frame.draw_plot(self.graph_objects[title].get_figure("tropo"))

    def generate_graphs(self):
        """
        @return:
        """
        with open(datapath.getDataPath("default_graphs.json"), 'r') as json_file:
            default_graphs = json.load(json_file)

        for graph_name, params in default_graphs.items():
            if params['type'] == 'XYGraph':
                self.graph_objects[graph_name] = XYGraph(
                    title=params['title'],
                    x=params['x'],
                    y=params['y'],
                    degree=params['degree'],
                    x_label=params['x_label'],
                    y_label=params['y_label'],
                    best_fit=params['best_fit'],
                    draw_lines=params['draw_lines']
                )
            elif params['type'] == 'HodoGraph':
                self.graph_objects[graph_name] = HodoGraph(
                    title=params['title'],
                    comp_range=params['comp_range'],
                    line_width=params['line_width'],
                    alt_threshold=params['alt_threshold']
                )

        # Generate their figures
        for _, graph in self.graph_objects.items():
            graph.generate_graph(self.station.strato_df, "strato")
            graph.generate_graph(self.station.tropo_df, "tropo")


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme(datapath.getDataPath("orange_theme.json"))
    app = GUI()
    app.mainloop()
