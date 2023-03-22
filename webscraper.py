import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
from PyQt5 import QtCore
currentDate = datetime.date.today()

# Class that creates a model from a dataframe that can be used in PyQt's table view
class DataFrameModel(QtCore.QAbstractTableModel):
    DtypeRole = QtCore.Qt.UserRole + 1000
    ValueRole = QtCore.Qt.UserRole + 1001

    def __init__(self, df=pd.DataFrame(), parent=None):
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._dataframe.columns[section]
            else:
                return str(self._dataframe.index[section])
        return QtCore.QVariant()
    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount() \
            and 0 <= index.column() < self.columnCount()):
            return QtCore.QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype

        val = self._dataframe.iloc[row][col]
        if role == QtCore.Qt.DisplayRole:
            return str(val)
        elif role == DataFrameModel.ValueRole:
            return val
        if role == DataFrameModel.DtypeRole:
            return dt
        return QtCore.QVariant()

    def roleNames(self):
        roles = {
            QtCore.Qt.DisplayRole: b'display',
            DataFrameModel.DtypeRole: b'dtype',
            DataFrameModel.ValueRole: b'value'
        }
        return roles

# Creates a function that takes an ein, scrapes and cleans data and returns a name and data frame
def DataFinder(ein):
    # finds the page and compiles all the text from the page into one string
    req= requests.get(f"https://projects.propublica.org/nonprofits/organizations/{ein}").text
    soup= BeautifulSoup(req, 'html.parser')
    soup.select("class")
    s = ""
    name= soup.find("h1")
    for name in soup:
        s = s + str(name.get_text())
    # sets a variable to be the current year
    start_year = currentDate.year
    # if the ein is not found return an error
    if s.find('Not Found') != -1:
        return ('EIN Not Valid')
    # if it is not an error it cleans the data
    else:
        # first it finds the organiations name
        # splits the text into a list of lines
        r = s.split('\n')
        name = ''
        counter = 0
        # loops through the lines of text until it gets to the first non blank line, this is the name line
        while name == '':
            name = r[counter]
            counter += 1
        
        # the name is formatted with other information after a dash, we split of the name only and return it
        name_split = name.split('-')
        org_name = name_split[0]
        
        # initializes a list of months and reverses it to start with december
        month_found = False
        months = ['Jan. ', 'Feb. ', 'March ', 'April ', 'May ', 'June ', 'July ', 'Aug. ', 'Sept. ', 'Oct. ', 'Nov. ', 'Dec. ']
        months.reverse()
        
        # while loop to find the first year of data available on the page regardless of the filing month
        while month_found is False:
            for name in months:
                if s.find(name + str(start_year)) != -1:
                    month_found=True
                else:
                    pass
            start_year = start_year - 1
        year = start_year + 1
        
        # Creates a list of indices for where we want to seperate the text from the web page
        indices = []
        # the earliest year of data is from 2011 so this finds the areas for indicing until 2011 
        while year-2011 >= 0:
            for name in months:
                if s.find(name + str(year)) != -1:
                    indices.append(s.find(name + str(year)))
                    break
            year = year - 1
        indices.append(None)
        
        # Creates a list of data by year filed by finding data between two set indice points
        years_data = [s[indices[i]:indices[i+1]] for i in range(len(indices)-1)]
        
        # Initializes the list of headers we will search for each year
        headers = ['Total Revenue', 'Total Functional Expenses', 'Net income', 'Contributions', 'Program services', 'Investment income', 'Bond proceeds', 'Royalties', 'Rental property income', 'Net fundraising', 'Sales of assets', 'Net inventory sales', 'Other revenue', 'Executive compensation', 'Professional fundraising fees', 'Other salaries and wages', 'Total Assets', 'Total Liabilities', 'Net Assets']
        # Initalizes the list of headers that are actually in the web page
        headers_in = ['Year']
        
        #Searches through each year and finds all unique headers that data can begin with
        for year in years_data:
            token = year.split('\n')
            for header in headers:
                if header not in headers_in and header in token:
                    headers_in.append(header)
        # Creates a data frame where the columns are all the unique headers from the data          
        data = pd.DataFrame(columns=headers_in)
        
        # sets a variable to keep track of what year was last added to the dataframe
        year_on = currentDate.year + 1
        # Loops through each year to find data
        for year in years_data:
            token = year.split('\n')
            # This loop finds the year and month that it was filed
            for name in months:
                edit_name = name.strip(' ')
                try:
                    year_prefix = token.index('Fiscal year ending ' + edit_name)
                    time_year = token[year_prefix + 1]
                    break
                except ValueError:
                    pass
            # If there is associated data this loop finds all that data and adds it to a list that begins with its year and month filed
            if "Total Revenue" in token and int(time_year) <= int(year_on):
                temp_list = [str(time_year) + ' ' + edit_name]
                for header in headers:
                    try: temp_list.append(token[token.index(header) + 1])
                    except ValueError:  
                        None
                year_on = time_year
                # The list is then added as a row on a data frame
                data.loc[len(data)] = temp_list
        # Returns the orginzations name and data frame of the data
        return [org_name, data, headers_in]
