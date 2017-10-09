import MySQLdb, csv, sys, re, pprint, os
from dotenv import load_dotenv, find_dotenv

'''

NAME
    SquareImport -- Reads in a list of products to receive new shipments

SYNOPSIS
    python SquareImport.py FILENAME

DESCRIPTION
    Reads in a list of products in csv format of a single column of EAN13 SKUs
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
# output csv file
    file_out = open('up2sqr.csv', 'w')
    writer = csv.writer(file_out)
    header = [
        'Token',
        'Item Name',
        'Description',
        'Category',
        'SKU',
        'Variation Name',
        'Price',
        'Enabled Chinatsu Komori',
        'Current Quantity Chinatsu Komori',
        'New Quantity Chinatsu Komori',
        'Stock Alert Enabled Chinatsu Komori',
        'Stock Alert Count Chinatsu Komori',
        'Price Chinatsu Komori',
        'Enabled Fort Mason Center',
        'Current Quantity Fort Mason Center',
        'New Quantity Fort Mason Center',
        'Stock Alert Enabled Fort Mason Center',
        'Stock Alert Count Fort Mason Center',
        'Price Fort Mason Center',
        'Tax - CA 8.75% (8.75%)',
        'Tax - CA 8.5% (8.5%)'
    ]
    writer.writerow(header)
# parse input csv file
    input_filename = sys.argv[1]
    with open(input_filename, 'r') as file_in:
        reader = csv.reader(file_in)
        productMap = dict() # sku -> count
        for row in reader:
            sku = row[0]
            if sku in productMap:
                productMap[sku] = productMap[sku] + 1
            else:
                productMap[sku] = 1
# the loop
    line_num = 0
    for sku13, qty in productMap.items():
        line_num += 1
        prefix_num = sku13[0:1]
        prod_code = sku13[1:8]
        color_code = sku13[8:10]
        size_code = sku13[10:12]
        checksum = sku13[12:13]
        sku11 = sku13[1:12]

        # find post_id; potential error
        post_id = getPostID(cnx,sku13)
        if len(post_id) == 0:
            post_id = getPostID(cnx,sku11)
        if len(post_id) == 0:
            post_id = getPostID(cnx,prod_code)
        if len(post_id) == 0:
            print(f"Error: No matching sku for '{sku13}'")
            continue

        # get product name
        post_type = getPostType(cnx,post_id)
        if post_type == "product_variation":
            post_id = getPostParent(cnx,post_id)
        post_title = getPostTitle(cnx,post_id)

        # get price
        price = getPrice(cnx,post_id)
        if len(price) == 0:
            print(f"Error: price not found for post_id {post_id}, sku {sku13}")

# Updates to WordPress Database
# Need to update the stock, sku#
# TODO mark products(simple/variable) as instock
        # Update Stock
        addStockToWordPress(cnx,post_id,qty)
        # Update SKU number on WordPress
        updateSKUNumberOnWordPress(cnx,sku13,post_id)
        # Update Stock Status
        updateStockStatus(cnx,post_id)


        # csv row
        row = [
            '',                 # Token
            post_title,         # Item Name
            '',                 # Description
            '',                 # Category
            sku13,              # SKU
            size_code,          # Variation Name
            price,              # Price
            'Y',                # Enabled Chinatsu Komori
            '',                 # Current Quantity Chinatsu Komori
            '',                 # New Quantity Chinatsu Komori
            '',                 # Stock Alert Enabled Chinatsu Komori
            '',                 # Stock Alert Count Chinatsu Komori
            '',                 # Price Chinatsu Komori
            'N',                # Enabled Fort Mason Center
            '',                 # Current Quantity Fort Mason Center
            '',                 # New Quantity Fort Mason Center
            '',                 # Stock Alert Enabled Fort Mason Center
            '',                 # Stock Alert Count Fort Mason Center
            '',                 # Price Fort Mason Center
            '',                 # Tax - CA 8.75% (8.75%)
            'Y'                 # Tax - CA 8.5% (8.5%)
        ] # row list
        print(row)

        writer.writerow(row)

# display productMap
    #pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(productMap)
# exit procedures
    file_out.close()
    db.close()


def addStockToWordPress(cnx,post_id,qty):
    cnx.execute(f'''
SELECT meta_value
FROM wp_postmeta
WHERE meta_key = '_stock'
    AND post_id = '{post_id}'
LIMIT 1;
''')
    wp_stock = cnx.fetchall()[0][0] # assume str type
    if len(wp_stock) == 0:
        wp_stock = 0
    elif int(wp_stock) < 0:
        print(f"Error: negative stock count for post_id {post_id}: stock {wp_stock}")
        wp_stock = 0
    new_qty = int(wp_stock) + qty
    cnx.execute(f'''
UPDATE wp_postmeta
SET meta_value = '{new_qty}'
WHERE meta_key = '_stock'
    AND post_id = '{post_id}';
''')


def updateSKUNumberOnWordPress(cnx,sku13,post_id):
    cnx.execute(f'''
UPDATE wp_postmeta
SET meta_value = '{sku13}'
WHERE meta_key = '_sku'
    AND post_id = '{post_id}';
''')


def updateStockStatus(cnx,post_id):
    cnx.execute(f'''
UPDATE wp_postmeta
SET meta_value = 'instock'
WHERE meta_key = '_stock_status'
    AND post_id = '{post_id}';
''')


def getPrice(cnx,post_id):
    query = f'''
SELECT meta_value
FROM wp_postmeta
WHERE meta_key = '_price'
    AND post_id = '{post_id}'
LIMIT 1;
'''
    cnx.execute(query)
    price = cnx.fetchall()[0][0]
    return str(price)


def getPostParent(cnx,post_id):
    query = f'''
SELECT post_parent
FROM wp_posts
WHERE ID = '{post_id}'
LIMIT 1;
'''
    cnx.execute(query)
    post_parent = cnx.fetchall()[0][0]
    return post_parent


def getPostTitle(cnx,post_id):
    query = f'''
SELECT post_title
FROM wp_posts
WHERE ID = '{post_id}'
LIMIT 1;
'''
    cnx.execute(query)
    post_title = cnx.fetchall()[0][0]
    return post_title


def getPostType(cnx,post_id):
    query = f'''
SELECT post_type
FROM wp_posts
WHERE ID = '{post_id}'
LIMIT 1;
'''
    cnx.execute(query)
    post_type = cnx.fetchall()[0][0]
    return post_type

def getPostID(cnx, value):
    query = f'''
SELECT post_id
FROM wp_postmeta
WHERE meta_key = '_sku'
    AND meta_value = '{value}'
LIMIT 1;
'''
    cnx.execute(query)
    post_id = cnx.fetchall()[0][0]
    return str(post_id)


if __name__ == "__main__" : main()
