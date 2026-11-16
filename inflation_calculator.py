'''
inflation_calculator.py

FINE 3300 (Fall 2026) - Assignment #2
Part B: Consumer Price Index (CPI)

This program replicates (and enhances) the Bank of Canada's Inflation Calculator:
    https://www.bankofcanada.ca/rates/related/inflation-calculator/

What the program does:
    1. Reads the Bank of Canada's monthly CPI data file (STATIC_INFLATIONCALC.csv)
       into a Pandas data frame and cleans it.
    2. Uses NumPy to compute the annual (year-over-year) percentage change in CPI.
    3. Uses Matplotlib to graph the CPI time series (left axis) and the annual
       percentage change (right axis), with a dotted line through the base
       level (2002 = 100). The graph is saved as cpi_graph.png.
    4. Runs an enhanced inflation calculator: the Bank of Canada's calculator only
       accepts a YEAR, but our data is MONTHLY, so this calculator accepts a full
       date (year and month). All user input is validated.

Data source: Statistics Canada, Consumer Price Indexes for Canada, Monthly
             (V41690973 series), as published by the Bank of Canada (2002 CPI = 100).
'''

import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Constants (settings used throughout the program)
# ---------------------------------------------------------------------------
DATA_FILE = 'STATIC_INFLATIONCALC.csv'   # downloaded from the Bank of Canada (CSV format)
GRAPH_FILE = 'cpi_graph.png'             # the graph is saved under this name
BASE_YEAR = 2002                         # Statistics Canada base period: 2002 CPI = 100
BASE_LEVEL = 100.0
CURRENCY = 'CAD'                         # currency identifier shown with every dollar amount

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


# ---------------------------------------------------------------------------
# CPIData class: loads the data, draws the graph, and performs calculations
# (same style as the Bond / Lottery / Index classes from Lectures 4 and 5)
# ---------------------------------------------------------------------------
class CPIData:

    def __init__(self, filename=DATA_FILE):
        # Private data member (double underscore) - holds the cleaned data frame
        self.__data = self.__read_data(filename)

    def __read_data(self, filename):
        '''
        Read the Bank of Canada CSV file into a Pandas data frame.

        The file does NOT start with the data. It begins with a "TERMS AND CONDITIONS"
        block and a "SERIES" block; the actual data comes after the line "OBSERVATIONS".
        We first read the file as text (Lecture 5) to find that line, then let
        Pandas read everything after it (Lecture 6).
        '''
        file = open(filename, 'r')
        lines = file.readlines()
        file.close()

        # Find the line number where the observations begin
        header_row = None
        for i, line in enumerate(lines):
            if line.strip().strip('"') == 'OBSERVATIONS':
                header_row = i + 1      # the next line holds the column names: date, STATIC_INFLATIONCALC
                break

        if header_row is None:
            raise ValueError('Could not find the OBSERVATIONS section in {}'.format(filename))

        # Skip everything above the column-name line and read the data into a data frame
        df = pd.read_csv(filename, skiprows=header_row)

        # Give the columns friendlier names
        df = df.rename(columns={'date': 'Date', 'STATIC_INFLATIONCALC': 'CPI'})

        # Extract the year and the month from each date string (format YYYY-MM-DD)
        df['Year'] = [int(d[0:4]) for d in df['Date']]
        df['Month'] = [int(d[5:7]) for d in df['Date']]

        # DATA CLEANING: the file contains two duplicated months (April 1927 and April 1932
        # appear twice, dated YYYY-04-01 and YYYY-04-30). The Bank of Canada's calculator keeps
        # the LAST value it reads for a month, so we do the same to match its results.
        df = df.drop_duplicates(subset=['Year', 'Month'], keep='last')
        df = df.reset_index(drop=True)

        # Build a proper datetime column (first day of each month) for plotting
        df['Date'] = [dt.datetime(year, month, 1) for year, month in zip(df['Year'], df['Month'])]

        # Annual (year-over-year) percentage change, computed with NumPy array slicing (Lecture 8):
        #   change in month t = (CPI[t] / CPI[t - 12] - 1) * 100
        # The first 12 months have no value from a year earlier, so they are left as NaN (not a number).
        cpi = df['CPI'].to_numpy()
        annual_change = np.full(cpi.shape[0], np.nan)
        annual_change[12:] = (cpi[12:] / cpi[:-12] - 1.0) * 100.0
        df['Annual % Change'] = annual_change

        return df

    # ----- Information about the data set ---------------------------------

    def first_date(self):
        '''Return (year, month) of the first observation.'''
        return (int(self.__data['Year'].iloc[0]), int(self.__data['Month'].iloc[0]))

    def last_date(self):
        '''Return (year, month) of the most recent observation.'''
        return (int(self.__data['Year'].iloc[-1]), int(self.__data['Month'].iloc[-1]))

    def __len__(self):
        return len(self.__data)

    def base_year_average(self):
        '''Average CPI over the base year (should be 100.0 since 2002 = 100).'''
        return self.__data[self.__data['Year'] == BASE_YEAR]['CPI'].mean()

    def is_in_range(self, year, month):
        '''True if the (year, month) exists in our data set.'''
        match = self.__data[(self.__data['Year'] == year) & (self.__data['Month'] == month)]
        return len(match) > 0

    def get_cpi(self, year, month):
        '''Return the CPI level for a given year and month.'''
        match = self.__data[(self.__data['Year'] == year) & (self.__data['Month'] == month)]
        return float(match['CPI'].iloc[0])

    # ----- Graph ------------------------------------------------------------

    def plot(self, filename=GRAPH_FILE, show=True):
        '''
        Graph the CPI (left axis) and the annual percentage change (right axis),
        with a dotted line through the base level (2002 = 100). Save it as a PNG.
        '''
        df = self.__data
        first_year, first_month = self.first_date()
        last_year, last_month = self.last_date()

        # Explicit interface (Lecture 7): create the Figure and the left-hand Axes
        fig, ax1 = plt.subplots(figsize=(14, 7), layout='constrained')

        # 1) CPI time series on the LEFT axis
        cpi_line = ax1.plot(df['Date'], df['CPI'], color='#2a78d6', linewidth=2.0,
                            label='Consumer Price Index (left axis)')

        # 2) Dotted line passing through the base level (CPI = 100 in 2002)
        base_line = ax1.axhline(BASE_LEVEL, color='#52514e', linestyle=':', linewidth=1.8,
                                label='Base level: {} CPI = {:.0f}'.format(BASE_YEAR, BASE_LEVEL))
        # Mark the base point itself (mid-2002, where the CPI crosses 100) and label it
        ax1.plot(dt.datetime(BASE_YEAR, 7, 1), BASE_LEVEL, marker='o', markersize=8,
                 color='#52514e', markeredgecolor='white')
        ax1.annotate('Base year {}: CPI = 100'.format(BASE_YEAR),
                     xy=(dt.datetime(BASE_YEAR, 7, 1), BASE_LEVEL),
                     xytext=(dt.datetime(2004, 1, 1), 55),
                     arrowprops=dict(arrowstyle='->', color='#52514e'),
                     fontsize=10, color='#52514e')

        ax1.set_xlabel('Date (monthly observations)', fontsize=12)
        ax1.set_ylabel('CPI level ({} = 100)'.format(BASE_YEAR), fontsize=12)
        ax1.set_ylim(0, 200)
        ax1.grid(True, color='#e2e1dc', linewidth=0.6)

        # 3) Annual percentage change on the RIGHT axis: twinx() creates a second y-axis
        #    that shares the same x-axis (dates)
        ax2 = ax1.twinx()
        change_line = ax2.plot(df['Date'], df['Annual % Change'], color='#eb6834', linewidth=1.0,
                               label='Annual % change, year over year (right axis)')
        ax2.axhline(0.0, color='#eb6834', linewidth=0.6, alpha=0.6)   # reference line at 0% change
        ax2.set_ylabel('Annual percentage change [%]', fontsize=12)
        ax2.set_ylim(-20, 30)

        # Title
        ax1.set_title('Canada Consumer Price Index and Annual Inflation Rate, {} {} to {} {}'.format(
                      MONTH_NAMES[first_month - 1], first_year, MONTH_NAMES[last_month - 1], last_year),
                      fontsize=16)

        # One legend for both axes: combine the line handles from ax1 and ax2
        handles = cpi_line + [base_line] + change_line
        labels = [h.get_label() for h in handles]
        ax1.legend(handles, labels, loc='upper left', fontsize=10, framealpha=0.95)

        # Source note at the bottom
        fig.text(0.01, 0.005, 'Source: Statistics Canada, Consumer Price Indexes for Canada, Monthly '
                 '(V41690973), via Bank of Canada.', fontsize=8, color='#52514e')

        fig.savefig(filename, dpi=150)
        if show:
            plt.show()
        plt.close(fig)

    # ----- Calculator -------------------------------------------------------

    def calculate(self, price, year1, month1, year2, month2):
        '''
        Replicates the Bank of Canada calculator formulas, using monthly CPI values:
            Cost2            = Cost1 * (CPI2 / CPI1)
            % change         = (Cost2 - Cost1) / Cost1 * 100
            Avg. annual rate = 100 * exp( (ln CPI2 - ln CPI1) / |years| ) - 100
        Returns the results in a dictionary.
        '''
        cpi1 = self.get_cpi(year1, month1)
        cpi2 = self.get_cpi(year2, month2)

        new_price = price * (cpi2 / cpi1)
        percent_change = (new_price - price) / price * 100.0

        # Number of months (and years) between the two dates; negative if date 2 is earlier
        months = (year2 - year1) * 12 + (month2 - month1)
        years = months / 12.0

        # Average annual (compound) rate of change - same formula as the Bank of Canada.
        # Not defined if both dates are the same (we cannot divide by zero years).
        if months == 0:
            annual_rate = None
        else:
            annual_rate = 100.0 * np.exp((np.log(cpi2) - np.log(cpi1)) / abs(years)) - 100.0

        return {'price': price, 'new price': new_price,
                'date 1': (year1, month1), 'date 2': (year2, month2),
                'cpi 1': cpi1, 'cpi 2': cpi2,
                'percent change': percent_change,
                'months': months, 'years': years,
                'annual rate': annual_rate}


# ---------------------------------------------------------------------------
# Helper functions: formatting, input parsing and validation
# ---------------------------------------------------------------------------
def format_money(amount):
    '''Format a dollar amount, e.g. 1234.5 -> $1,234.50 CAD (rounded to the nearest penny).'''
    return '${:,.2f} {}'.format(amount, CURRENCY)


def format_date(year, month):
    '''Format (2000, 9) as "Sep 2000".'''
    return '{} {}'.format(MONTH_NAMES[month - 1], year)


def parse_price(text):
    '''
    Convert the user's text into a price. Like the Bank of Canada calculator, commas and
    spaces are allowed (and a $ sign or "CAD" is ignored). Returns None if the text is invalid.
    '''
    cleaned = text.upper().replace('CAD', '').replace('$', '').replace(',', '').replace(' ', '')
    try:
        price = float(cleaned)
    except ValueError:
        return None

    # The price must be a real, positive number (rejects 0, negatives, "nan" and "inf")
    if not np.isfinite(price) or price <= 0:
        return None
    return price


def parse_date(text):
    '''
    Extract the year and month from the user's date.
    Accepted formats: YYYY-MM  or  YYYY-MM-DD  ("/" can be used instead of "-").
    Returns (year, month, error_message). If the date is valid, error_message is None.
    '''
    parts = text.strip().replace('/', '-').split('-')

    if len(parts) not in (2, 3):
        return (None, None, 'Please use the format YYYY-MM (e.g. 2000-09) or YYYY-MM-DD.')

    for part in parts:
        if not part.isdigit():
            return (None, None, 'The date may only contain numbers and "-" or "/".')

    if len(parts[0]) != 4:
        return (None, None, 'The year must have 4 digits and come first (YYYY-MM).')

    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2]) if len(parts) == 3 else 1

    if month < 1 or month > 12:
        return (None, None, 'The month must be between 1 and 12.')

    # Use the datetime module to make sure the date really exists (e.g. rejects 2023-02-30)
    try:
        dt.datetime(year, month, day)
    except ValueError:
        return (None, None, '{} is not a valid calendar date.'.format(text.strip()))

    return (year, month, None)


def ask_price():
    '''Prompt until the user enters a valid price.'''
    while True:
        price = parse_price(input('Enter the price of the goods or services (e.g. 100 or 1,250.50): $'))
        if price is not None:
            return price
        print('  Invalid amount. Please enter a positive number (commas and spaces are allowed).')


def ask_date(prompt, cpi_data):
    '''Prompt until the user enters a valid date that is inside the data set.'''
    first_year, first_month = cpi_data.first_date()
    last_year, last_month = cpi_data.last_date()

    while True:
        year, month, error = parse_date(input(prompt))

        if error is not None:
            print('  Invalid date. ' + error)
        elif not cpi_data.is_in_range(year, month):
            print('  {} is outside the data set. Please enter a date between {} and {}.'.format(
                  format_date(year, month), format_date(first_year, first_month),
                  format_date(last_year, last_month)))
        else:
            return (year, month)


def ask_yes_no(prompt):
    '''Prompt until the user answers y or n.'''
    while True:
        answer = input(prompt).strip().lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        print('  Please answer y or n.')


def print_results(results):
    '''Print the results in the same layout as the Bank of Canada calculator.'''
    year1, month1 = results['date 1']
    year2, month2 = results['date 2']

    # Number of years between the two dates (negative when the second date is earlier,
    # just like the Bank of Canada calculator), plus a plain-English years/months breakdown
    total_months = abs(results['months'])
    whole_years = total_months // 12
    extra_months = total_months % 12
    breakdown = '{} year{}, {} month{}'.format(whole_years, '' if whole_years == 1 else 's',
                                               extra_months, '' if extra_months == 1 else 's')
    if results['months'] < 0:
        breakdown = breakdown + ' back'
    period = '{:.2f} ({})'.format(results['years'], breakdown)

    if results['annual rate'] is None:
        annual_rate = 'N/A (same date)'
    else:
        annual_rate = '{:.2f}%'.format(results['annual rate'])

    print()
    print(70 * '=')
    print('INFLATION CALCULATOR RESULTS'.center(70))
    print(70 * '=')
    print('A "basket" of goods and services that cost:')
    print('    {:>20}  in {}'.format(format_money(results['price']), format_date(year1, month1)))
    print('...would cost:')
    print('    {:>20}  in {}'.format(format_money(results['new price']), format_date(year2, month2)))
    print(70 * '-')
    print('{:<52}{:>18}'.format('Percent change:', '{:,.2f}%'.format(results['percent change'])))
    print('{:<36}{:>34}'.format('Number of years:', period))
    print('Average annual rate of inflation (%) /')
    print('{:<52}{:>18}'.format('  Decline in the value of money:', annual_rate))
    print('{:<52}{:>18}'.format('CPI for first date ({}):'.format(format_date(year1, month1)),
                                '{:.1f}'.format(results['cpi 1'])))
    print('{:<52}{:>18}'.format('CPI for second date ({}):'.format(format_date(year2, month2)),
                                '{:.1f}'.format(results['cpi 2'])))
    print(70 * '=')
    print('{} CPI = 100.0'.format(BASE_YEAR))
    print()


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------
if __name__ == '__main__':

    # 1. Read and clean the data
    cpi_data = CPIData(DATA_FILE)
    first_year, first_month = cpi_data.first_date()
    last_year, last_month = cpi_data.last_date()

    print(70 * '=')
    print('BANK OF CANADA INFLATION CALCULATOR (MONTHLY EDITION)'.center(70))
    print(70 * '=')
    print('Data loaded: {} monthly CPI observations from {} to {}.'.format(
          len(cpi_data), format_date(first_year, first_month), format_date(last_year, last_month)))
    print('Check: average CPI in {} = {:.1f} (base level should be 100.0)'.format(
          BASE_YEAR, cpi_data.base_year_average()))

    # 2. Graph the CPI and the annual percentage change
    print('Saving the graph to {} ... close the graph window to continue.'.format(GRAPH_FILE))
    cpi_data.plot(GRAPH_FILE)

    # 3. Run the calculator (repeat until the user is done)
    print()
    print('Enter dates as YYYY-MM (e.g. 2000-09) or YYYY-MM-DD, between {} and {}.'.format(
          format_date(first_year, first_month), format_date(last_year, last_month)))

    again = True
    while again:
        print()
        price = ask_price()
        year1, month1 = ask_date('Enter the date of the FIRST period  (YYYY-MM): ', cpi_data)
        year2, month2 = ask_date('Enter the date of the SECOND period (YYYY-MM): ', cpi_data)

        results = cpi_data.calculate(price, year1, month1, year2, month2)
        print_results(results)

        again = ask_yes_no('Would you like to do another calculation? (y/n): ')

    print('Thank you for using the inflation calculator!')
