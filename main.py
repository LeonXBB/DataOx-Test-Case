from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions

import psycopg2
from psycopg2 import sql

import os

from logger import Logger


class Driver(webdriver.Chrome):

    """
    A custom WebDriver class for running Chrome with the necessary options
    """

    def __init__(self):

        """
        Initializes the Chrome WebDriver with the required options for this app and logs successful result
        """

        self.options = Options()
        self.options.add_argument("--headless") # no need to open actual browser
        self.options.add_argument("--log-level=1") # suppress weird tensorflow log message inside of selenium
        self.options.add_argument("--disable-dev-shm-usage") # selenium doesn't work inside docker without...
        self.options.add_argument("--no-sandbox") # ...these two args

        super().__init__(self.options)
        logger.info("Acquired headless driver")


class Item:

    """
    Represents an item extracted from a webpage, fetches item data, checks database existence,
    and saves relevant fields to the database.
    """


    # A dictionary that stores data about fields we want to extract. It's to be used by class methods. Contains the
    # following keys:
    #   by (selenium.webdriver.common.by) - how to find the given attribute in the html.
    #   value (str) - value for "by" to match.
    #   edit_function (None | callable) - optional function to run to retrieve the element's value after being located
    #       with "by". If none, the element's "text" attribute is called.
    #   joiner (None | str) - optional str to be used to call "join" method on itself in case "by" returns multiple
    #       elements. If by does return multiple instances and no joiner is given, the results will be stored as a list.
    #   db_table (str) - name of the db table to associate field with.
    #   db_col (str) - name of the column in the db table to associate field with.

    # Allows for customization, easy fields editing, addition and removal.

    FIELD_DATA = {
        "image_url": {
            "by": By.CLASS_NAME,
            "value": "css-1bmvjcs",
            "edit_function": lambda x: x.get_property("src"),
            "joiner": None,
            "db_table": "_Pictures_",
            "db_col": "pictureUrl"
        },
        "publication_date": {
            "by": By.XPATH,
            "value": "//span[@data-cy='ad-posted-at']",
            "edit_function": None,
            "joiner": None,
            "db_table": "Items",
            "db_col": "publicationDate"
        },
        "title": {
            "by": By.XPATH,
            "value": "//div[@data-cy='ad_title']/h4",
            "edit_function": None,
            "joiner": "\n",
            "db_table": "Items",
            "db_col": "title"
        },
        "price":
            {"by": By.XPATH,
             "value": "//div[@data-testid='ad-price-container']/h3",
             "edit_function": None,
             "joiner": None,
             "db_table": "Items",
             "db_col": "price"
        },
        "options": {
            "by": By.CLASS_NAME,
            "value": "css-rn93um",
            "edit_function": None,
            "joiner": "\n",
            "db_table": "Items",
            "db_col": "options"
        },
        "description":
            {"by": By.XPATH,
             "value": "//div[@data-cy='ad_description']/div",
             "edit_function": None,
            "joiner": "\n",
            "db_table": "Items",
            "db_col": "description"},
        "id": {
            "by": By.CLASS_NAME,
            "value": "css-1i121pa",
            "edit_function": lambda x: x.text.split(" ")[-1],
            "joiner": None,
            "db_table": "Items",
            "db_col": "olxId"
        },
        "views": {
            "by": By.XPATH,
            "value": "//span[@data-testid='page-view-counter']",
            "edit_function": lambda x: x.text.split(" ")[-1],
            "joiner": None,
            "db_table": "Items",
            "db_col": "views"
        },
        "user_phone_number": {
            "by": By.CLASS_NAME,
            "value": "css-v1ndtc",
            "edit_function": None,
            "joiner": None,
            "db_table": "Users",
            "db_col": "phoneNumber"
        },
        "user_name": {
            "by": By.CLASS_NAME,
            "value": "css-lyp0yk",
            "edit_function": None,
            "joiner": None,
            "db_table": "Users",
            "db_col": "Name"
        },
        "user_rating": {
            "by": By.CLASS_NAME,
            "value": "css-450u1d",
            "edit_function": None,
            "joiner": None,
            "db_table": "Users",
            "db_col": "rating"
        },
        "user_registration_date": {
            "by": By.CLASS_NAME,
            "value": "css-1h2xv7i",
            "edit_function": None,
            "joiner": None,
            "db_table": "Users",
            "db_col": "registrationDate"
        },
        "user_last_online": {
            "by": By.XPATH,
            "value": "//p[@data-testid='lastSeenBox']/span",
            "edit_function": None,
            "joiner": None,
            "db_table": "Users",
            "db_col": "lastOnline"
        },
        "user_location": {
            "by": By.CLASS_NAME,
            "value": "css-13l8eec",
            "edit_function": None,
            "joiner": None,
            "db_table": "Users",
            "db_col": "location"
        }
    }

    TIMEOUT = 5 # how long to wait until the element appears on the webpage.

    def __init__(self, url :str):

        """
        Initializes an Item object with the given URL.
        If the item is not found in the database, retrieves and saves its fields.

        :param url: The webpage URL of the item.
        """

        self.page_url = url
        if not self.is_in_db():  # don't update

            driver.get(self.page_url) #move to the item url
            logger.info(f"Located item with url {self.page_url}, getting fields values..")

            self.fields = {"page_url": self.page_url}
            self.get_fields()
            self.save_fields()

    def is_in_db(self) -> bool:

        """
        Checks whether the item URL exists in the database.

        :return: True if the item exists, otherwise False.
        """
        result = None
        connection = None
        cursor = None

        try:

            logger.info(f"Checking whether the url {self.page_url} is in the db already...")

            connection = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                host="postgres_db",
                port="5432"
            )

            cursor = connection.cursor()

            query = sql.SQL("SELECT 1 FROM Items WHERE pageUrl  = %s LIMIT 1")
            cursor.execute(query, (self.page_url,))

            result = cursor.fetchone()

        except Exception as e:
            logger.warning(f"Exception occurred: {e}")
            return False

        finally:
            if connection:
                cursor.close()
                connection.close()

        logger.info(f"Results for the url {self.page_url}: {result}")
        return result is not None

    def save_table_fields(self, table :str, extension_cols :list, extension_vals :list, return_id=False) -> int | None:

        """
        Inserts item fields into the specified database table.

        :param table: Name of the database table.
        :param extension_cols: Additional columns to insert.
        :param extension_vals: Values for the additional columns.
        :param return_id: Whether to return the inserted record ID.
        :return: Inserted record ID if requested, otherwise None.
        """

        connection = None
        cursor = None
        rv = 0

        fields = {field for field in self.fields if
                  (field in self.FIELD_DATA and self.FIELD_DATA[field]["db_table"] == table)}
        columns = [self.FIELD_DATA[field]["db_col"] for field in fields]
        values = [self.fields[field] for field in fields]

        columns.extend(extension_cols)
        values.extend(extension_vals)

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))}) {'RETURNING id' if return_id else ''}"

        try:
            logger.info(f"Trying to insert {table} fields in the database...")

            connection = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                host="postgres_db",
                port="5432"
            )

            cursor = connection.cursor()
            cursor.execute(query, values)
            if return_id: rv = cursor.fetchone()[0]
            connection.commit()

        except psycopg2.Error as e:
            logger.warning(f"An error occurred: {e}")
            return
        else:
            logger.info("Inserted successfully!")
        finally:
            if connection:
                cursor.close()
                connection.close()

        return rv

    def save_fields(self) -> None:

        """
        Saves extracted item fields into their respective database tables.
        """
        logger.info("Saving item fields into the database...")

        user_id = self.save_table_fields("Users", (), (), True)
        item_id = self.save_table_fields("Items", ("userId", "pageUrl"), (user_id, self.page_url), True)
        for imageUrl in self.fields["image_url"]:
            self.save_table_fields("ItemPictures", ("itemId", "pictureUrl"), (item_id, imageUrl))

        logger.info("Saved!")

    def get_fields(self) -> None:

        """
        Retrieves all field values based on the defined field_data.
        """

        for field in self.FIELD_DATA:
            self.get_field(field)

    def get_field_params(self, field :str) -> list:

        """
        Retrieves parameters required to locate and extract a field.

        :param field: Field name to retrieve parameters for.
        :return: List of field parameters.
        """

        return list(self.FIELD_DATA[field].values())

    def get_field(self, field :str) -> None:

        """
        Extracts the value of a single field from the webpage and saves it to the self.fields.

        :param field: The field name to extract.
        """

        logger.info(f"Getting field value for field {field}")
        by, value, edit_function, joiner, _, _ = self.get_field_params(field)

        if (by is not None) and (value is not None):
            try:
                field_els = WebDriverWait(driver, self.TIMEOUT).until(EC.presence_of_all_elements_located((by, value)))
            except selenium.common.exceptions.TimeoutException:
                logger.warning(f"Selenium couldn't find the html element for field {field}, skipping...")
                return

            field_vals = set()

            for el in field_els:

                if edit_function is not None:
                    field_vals.add(edit_function(el))

                elif el.text:
                    field_vals.add(el.text)

            if len(field_vals) == 1:
                self.fields[field] = list(field_vals)[0]
            elif len(field_vals) > 1:
                if joiner is None:
                    self.fields[field] = field_vals
                else:
                    self.fields[field] = joiner.join(field_vals)

            if len(field_vals) > 0: #sometimes the code doesn't trigger the selenium exception but also field_els are
                # empty
                logger.info(f'Got value "{self.fields[field]}" for field {field}')


class ItemFactory:

    """
    A factory class to fetch item URLs from a predefined OLX listing page,
    log the retrieved URLs up to a given limit, and create Item instances from them.
    """

    DEFAULT_URL = "https://www.olx.ua/uk/list/"
    LOCATOR = {"by": By.XPATH, "value": "//div[@data-cy='ad-card-title']/a"} # how to find item elements
    LIMIT = 5

    def __init__(self):

        """
        Initializes the ItemFactory by loading the webpage, extracting item URLs,
        logging them, and instantiating an Item object for the first URL found.
        """

        driver.get(self.DEFAULT_URL) # load list page

        items_urls = []

        for located_item in driver.find_elements(**self.LOCATOR)[:self.LIMIT]: #fetch item urls
            items_urls.append(located_item.get_property("href"))

        url_string = "\n".join(items_urls) #can't have '\' inside F-strings for some reason
        logger.info(f"Got the following urls:\n{url_string}")

        for item_url in items_urls:
            Item(item_url)


if __name__ == "__main__":
    logger = Logger().get_logger()

    driver = Driver()
    ItemFactory()
