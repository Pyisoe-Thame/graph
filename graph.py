import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GraphVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Graph Visualizer")

        self.label_file_path = tk.Label(root, text="CSV File:")
        self.label_file_path.grid(row=0, column=0, padx=5, pady=5)

        self.entry_file_path = tk.Entry(root, width=50)
        self.entry_file_path.grid(row=0, column=1, padx=5, pady=5)

        self.button_browse = tk.Button(root, text="Browse", command=self.browse_file)
        self.button_browse.grid(row=0, column=2, padx=5, pady=5)

        self.button_visualize = tk.Button(root, text="Visualize Graph", command=self.visualize_graph)
        self.button_visualize.grid(row=1, column=0, pady=10)

        self.button_shortest_path = tk.Button(root, text="Shortest Path", command=self.calculate_shortest_path)
        self.button_shortest_path.grid(row=1, column=1, pady=10)

        self.button_clear_highlights = tk.Button(root, text="Clear Highlights", command=self.clear_highlights)
        self.button_clear_highlights.grid(row=1, column=2, pady=10)

        self.button_exit = tk.Button(root, text="Exit", command=self.exit_app)
        self.button_exit.grid(row=3, column=1, pady=10)

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        self.canvas = None
        self.figure = None
        self.G = None
        self.pos = None
        self.ax = None
        self.scatter = None  # Scatter plot for nodes
        self.start_node = None
        self.end_node = None
        self.node_colors = {}

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        self.entry_file_path.delete(0, tk.END)
        self.entry_file_path.insert(0, file_path)

    def visualize_graph(self):
        file_path = self.entry_file_path.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a CSV file.")
            return

        try:
            df = pd.read_csv(file_path)

            if not {'source', 'target', 'weight'}.issubset(df.columns):
                messagebox.showerror("Error", "CSV file must contain 'source', 'target', and 'weight' columns.")
                return

            self.G = nx.from_pandas_edgelist(df, 'source', 'target', ['weight'])

            self.figure, self.ax = plt.subplots()
            # self.pos = nx.spring_layout(self.G)  # Layout algorithm
            self.pos = nx.circular_layout(self.G)  # Layout algorithm
            self.node_colors = {node: 'skyblue' for node in self.G.nodes()}

            self.draw_graph()

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            self.canvas = FigureCanvasTkAgg(self.figure, master=self.canvas_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            self.canvas.mpl_connect('button_press_event', self.on_node_click)

        except FileNotFoundError:
            messagebox.showerror("Error", "File not found.")
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", "CSV file is empty.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def draw_graph(self):
        self.ax.clear()
        nx.draw_networkx_edges(self.G, self.pos, ax=self.ax) #draw edges
        nx.draw_networkx_labels(self.G, self.pos, ax=self.ax) #draw labels
        labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(self.G, self.pos, edge_labels=labels, ax=self.ax)

        # Store the path collection object in self.scatter
        self.scatter = nx.draw_networkx_nodes(self.G, self.pos, node_size=1300, node_color=list(self.node_colors.values()), ax=self.ax)

    def on_node_click(self, event):     
        if event.inaxes != self.ax:
            return

        # Check for clicks on the nodes using the scatter plot (which holds the nodes)
        contains, ind = self.scatter.contains(event)  # Use self.scatter for nodes
        print(f"Contains: {contains}")
        print(f"Ind: {ind}") # Add this line

        if contains:
            if 'ind' in ind and len(ind['ind']) > 0: # Check if 'ind' key exists and is not empty
                node_index = ind['ind'][0]
                node = list(self.G.nodes())[node_index]

                if node == self.start_node:
                    self.start_node = None
                    self.node_colors[node] = 'skyblue'
                elif node == self.end_node:
                    self.end_node = None
                    self.node_colors[node] = 'skyblue'
                elif self.start_node is None:
                    self.start_node = node
                    self.node_colors[node] = 'lightgreen'
                elif self.end_node is None:
                    self.end_node = node
                    self.node_colors[node] = 'salmon'
        
                # Old Approach
                # self.draw_graph()  # Redraw the graph with updated node colors
                # self.canvas.draw()  # Update the canvas

                # Update node colors directly
                self.scatter.set_facecolor(list(self.node_colors.values()))
                self.canvas.draw()
            
            else:  # click was within the axes, but not on a node.
                pass  # or add some other behavior here, if needed.
        else:  # click was outside of the axes.
            pass  # or add some other behavior here, if needed.

    def calculate_shortest_path(self):
        if self.start_node is None:
            messagebox.showerror("Error", "Please select both starting and ending nodes.")
            return
        elif self.end_node is None:
            messagebox.showerror("Error", "Please select an ending node.")
            return

        try:
            shortest_path = nx.shortest_path(self.G, self.start_node, self.end_node, weight='weight')
            edge_colors = ['red' if (shortest_path[i], shortest_path[i + 1]) in self.G.edges() or (shortest_path[i + 1], shortest_path[i]) in self.G.edges() else 'black' for i in range(len(shortest_path) - 1)]

            edge_list = [(shortest_path[i], shortest_path[i + 1]) for i in range(len(shortest_path)-1)]

            self.draw_graph()
            nx.draw_networkx_edges(self.G, self.pos, edgelist=edge_list, edge_color='red', width=2, ax=self.ax)
            self.canvas.draw()
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", "No path found between the selected nodes.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def clear_highlights(self):
        self.start_node = None
        self.end_node = None
        self.node_colors = {node: 'skyblue' for node in self.G.nodes()}
        self.draw_graph()
        self.canvas.draw()

    def exit_app(self):
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphVisualizer(root)
    root.mainloop()