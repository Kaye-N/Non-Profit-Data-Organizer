#Program will find the financial data for a non profit organization
#Jamie Nazareno
#Warren Cox
#Date Created: 11/26/2022
#Date Finished: 12/4/2022

import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
currentDate = datetime.date.today()
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import sys

import mainGUI as gui
from webscraper import DataFinder
from webscraper import DataFrameModel

import os 

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pyg

# Creates variables that iwll be used later
org_name = ''
data = 0
ein = ''
graphic_select = ''
headers_in = []
 
# Create pathname popup
class fileSavepopup(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = gui.Ui_fileSave_popup()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.okClicked)
    def okClicked(self):
        self.close()
        
#Create graph window
class GraphWindow(QMainWindow):
    def __init__ (self):
        global data
        global graphic_select
        graph_w= pyg.plot()
        graph_w.setGeometry(200, 200, 1200, 1000)
       
        #Take info as columns from data
        years= data['Year']
        graphic_y = data[graphic_select]
 
        new_years=[]
        for i in years:
            a =i.split(" ")
            new_years.append(int (a[0]))
       
        new_y=[]
        for x in graphic_y:
            b = x.replace(",", "")
            c = b.replace("$", "")
            new_y.append(int(c))


        #plot years and revenue as x and y axis
        bargraph= pyg.BarGraphItem(x= new_years, height= new_y, width= 0.6, brush= 'b')
        graph_w.setWindowTitle(graphic_select + " In Given Years")
        graph_w.addItem(bargraph)

# Creates the results window Gui        
class ResultsWindow(QMainWindow):
    def __init__(self, parent=None):
        global headers_in
        super(ResultsWindow, self).__init__(parent=parent)
        self.ui = gui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.csv_yes_btn.clicked.connect(self.yesClicked)
        self.ui.csv_no_button.clicked.connect(self.noClicked)
        self.ui.go_btn.clicked.connect(self.go_click)
        
        for item in headers_in:
            self.ui.graphic_dd.addItem(item)

    def yesClicked(self):
        if not os.path.exists('C:\\Financial_DataFinder_Results'):
            os.makedirs('C:\\Financial_DataFinder_Results')
        path = 'C:\\Financial_DataFinder_Results\\' + org_name.replace(' ', '_') + 'FINANCIALDATA'
        data.to_csv('C:\\Financial_DataFinder_Results\\' + org_name.replace(' ', '_') + 'FINANCIALDATA')
        self.w = fileSavepopup()
        self.w.ui.path_lable.setText(path)
        self.w.show()

    def noClicked(self):
        self.close()
    def go_click(self):
        global graphic_select
        graphic_select = self.ui.graphic_dd.currentText()
        self.graph= GraphWindow()
        self.graph.show()

# Creates the Error window GUI
class IntervalError(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = gui.Ui_EIN_error_popup()
        self.ui.setupUi(self)
        self.ui.ok_btn.clicked.connect(self.okClicked)

    # If the button on this window is clicked it opens the input window Gui 
    def okClicked(self):
        self.close()
        self.w = InputWindow()
        self.w.show()
    
# Creates the secondary window Gui
class IntervalWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = gui.Ui_Interval_Screen()
        self.ui.setupUi(self)
        self.ui.run_btn2.clicked.connect(self.run_click_2)
    # If the Gui's button is clicked it opens the results window 
    def run_click_2(self):
            ein = self.ui.ein_val.text()
            self.close()
            self.w = ResultsWindow()
            # Turns the data frame into a model that can be displayed in PyQt Gui
            model = DataFrameModel(data)
            self.w.ui.tableView.setModel(model)
            self.w.ui.ein_val.setText(ein)
            self.w.ui.name_val.setText(org_name)
            self.w.show()
            
# Creates the Input window Gui
class InputWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = gui.Ui_Input_Screen()
        self.ui.setupUi(self)
        self.ui.find_btn.clicked.connect(self.find_click)
    def find_click(self):
        # When clicked records the ein that the user has typed in the input and checks if it is valid using the DataFind function
        global ein
        ein_with_dash = self.ui.ein_input.text()
        ein = ein = ein_with_dash.replace('-', '')
        if DataFinder(ein) == 'EIN Not Valid':
            self.close()
            self.w = IntervalError()
            self.w.show()
        else:
            # If the ein was valid it opens the Secondary Window
            global org_name
            global data
            global headers_in
            results = DataFinder(ein)
            org_name = results[0]
            data = results[1]
            headers_in = results[2]
            self.close()
            self.w = IntervalWindow()
            self.w.ui.ein_val.setText(ein)
            self.w.ui.name_val.setText(org_name)
            self.w.show()
        
# Opens the Input window if the file is the main file
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = InputWindow()
    w.show()
    sys.exit(app.exec())
