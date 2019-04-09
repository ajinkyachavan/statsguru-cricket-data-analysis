"""
Read the test match results from the statsguru site and save them in a SQLite database.
"""

from bs4 import BeautifulSoup
import requests
import sqlite3
import time

#  constants
DB_NAME = "statsguru.db"

URLS = [
    "http://stats.espncricinfo.com/ci/engine/stats/index.html?class=1;page=%s;template=results;type=team;view=results",
    "http://stats.espncricinfo.com/ci/engine/player/219889.html?class=1;page=%s;spanval1=span;template=results;type=batting;view=innings"
]

INDEX = 0
BASE_URL = URLS[INDEX]

TABLE_NAMES = ['results', 'batting']
TABLE_NAME = TABLE_NAMES[INDEX];

# Filter = keyword of table in the html data from BASE_URL
FILTERS = ["Match results", "Innings by innings list"]
FILTER = FILTERS[INDEX];


class Scraper:
    """
    Do all the scraping and writing to the database using a scraper object.
    """
    def __init__(self):
        """
        Form the database connection and get ready to do the downloading
        """
        self.con = sqlite3.connect(DB_NAME)
        self.cur = self.con.cursor()

        self.baseUrl = BASE_URL

        self.create_database()
        self.scrape_pages()
        self.parse_page()

    def create_database(self):
        """
        Create the results table (if it doesn't exist), then make sure it is clean and empty
        """
        self.createTableIfNotExists()
        self.con.commit()

    def createTableIfNotExists(self):
        if (INDEX == 0):
            createQuery = "create table if not exists %s (%s VARCHAR , %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR)"
            self.cur.execute(
                createQuery %
                (TABLE_NAME, "team", "result", "margin", "toss", "bat", "blank", "opposition", "ground", "start_date",
                 "blank2")
            )
        elif (INDEX == 1):
            createQuery = "create table if not exists %s (%s VARCHAR , %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR, %s VARCHAR)"
            self.cur.execute(
                createQuery %
                (TABLE_NAME, "runs", "mins", "bf", "four", "six", "sr", "pos", "dismissal", "inns", "blank",
                 "opposition", "ground", "start_date", "blank2")
            )

    def scrape_pages(self):
        """
        Loops through all the pages and grabs the results from them.
        """
        # Get the first page - there will always be a first page.
        index = 1
        self.getpage(index)
        # more_results returns True if that page contained results, false if it didn't.
        # This lets us know if we should continue to loop
        more_results = self.parse_page()
        while more_results:
            print("Scraping page %s" % index)
            index += 1
            self.getpage(index)
            more_results = self.parse_page()
            # put a sleep in there so we don't hammer the cricinfo site too much
            time.sleep(1)

    def getpage(self, index):
        """
        Returns the HTML of a page of results, given the index.
        """
        page = requests.get(self.baseUrl % index).text
        self.soup = BeautifulSoup(page, features="html.parser")
        print(self.soup)

    def parse_page(self):
        """
        Writes the contents of the page to the sqlite database.
        """
        for table in self.soup.findAll("table", class_="engineTable"):
            # There are a few table.engineTable in the page. We want the one that has the match
            # results caption
            if table.find("caption", text=FILTER) is not None:
                rows = table.findAll("tr", class_="data1")
                for row in rows:
                    values = [i.text
                              for i in row.findAll("td")]
                    # if the only result in the table says "No records...", this means that we're
                    # at a table with no results. We've queried too many tables, so just return
                    # False
                    if values[0] == u'No records available to match this query':
                        return False

                    self.insertValuesInTable(values)

                # Return true to say that this page was parsed correctly
                return True

    def insertValuesInTable(self, values):
        if (INDEX == 0):
            insertQuery = "INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(TABLE_NAME)
            self.cur.execute(insertQuery, values)
        elif (INDEX == 1):
            insertQuery = "INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?)".format(TABLE_NAME)
            self.cur.execute(insertQuery, values)
        self.con.commit()
        return True


if __name__ == "__main__":
    scraper = Scraper()
