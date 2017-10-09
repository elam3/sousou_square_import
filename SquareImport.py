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
# parse input csv file
    with open('up10.5.csv', 'r') as file_in:
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
        print(f"{line_num}: {sku13} -> {prefix_num} {prod_code} {color_code} {size_code} {checksum}. {sku11}")

        post_id = getPostID(cnx,sku13)
        if len(post_id) == 0:
            post_id = getPostID(cnx,sku11)
        if len(post_id) == 0:
            post_id = getPostID(cnx,prod_code)
        if len(post_id) == 0:
            print(f"Error: No matching sku for '{sku13}'")
            continue

        post_type = getPostType(cnx,post_id)
        if post_type == "product_variation":
            post_id = getPostParent(cnx,post_id)
        post_title = getPostTitle(cnx,post_id)
        print(f"\tPostTitle: {post_title}")

# display productMap
    pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(productMap)
# exit procedures
    db.close()


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
