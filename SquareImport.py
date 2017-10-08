import MySQLdb, csv, sys, re, pprint, os
from dotenv import load_dotenv, find_dotenv

'''

NAME
    SquareImport -- Reads in a list of products to receive new shipments

SYNOPSIS
    python SquareImport.py FILENAME

DESCRIPTION
    Reads in a list of products in the format of a single column of EAN13 SKUs
    to tally each product and push the data to WordPress. Then finally produce
    a CSV file used to upload to squareup.com.

'''

def main():
    ''' Main Function '''
# read .env credentials
    load_dotenv(find_dotenv())
    DB_USER = os.environ.get('DB_USER')
    DB_PW = os.environ.get('DB_PW')
    DB_NAME = os.environ.get('DB_NAME')
# open mysql connection
    db = MySQLdb.connect(user=DB_USER, passwd=DB_PW, db=DB_NAME)
    cnx = db.cursor()
# exit procedures
    db.close()

if __name__ == "__main__" : main()
