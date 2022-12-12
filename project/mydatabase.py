import pandas as pd
import sqlite3
import os

# A module to retrieve/save data from/to the dabatase into/from Pandas dataframes

def connect_to_db():
    '''Connect with SQLite carpool database'''

    conn = sqlite3.connect("db.sqlite3")
    print('Connected to the carpool database')
    return conn


def read_table_to_df(table_name):
    '''Import table into dataframe'''
    
    query = 'SELECT * from ' + table_name

    conn = connect_to_db()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def read_zips_on_route_from(zip_origin):
    '''Read zips_on_route from zip_origin into a dataframe'''

    query = 'SELECT zips_on_route FROM carpool_routes WHERE origin_id = '
    query += str(zip_origin)

    conn = connect_to_db()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def read_coordinates_from(zip_code):
    '''Read coordinates latitude and longitude from zip_code into a dataframe'''

    query = 'SELECT latitude, longitude FROM carpool_ca_zip WHERE zip_code = '
    query += str(zip_code)

    conn = connect_to_db()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def save_carpool_df_into_db(carpool_df):
    '''Save carpool dataframe into database.
    Drop previous table, then insert new values'''

    conn = connect_to_db()
    carpool_df.to_sql('carpool_carpools', conn, if_exists='replace')
    conn.close()
    return

def save_file_into_candidates_db(file_name):
    '''Save file into a database table replacing existing data'''
    file_df = pd.DataFrame()
    print(file_name)

    # First, save csv or excel file into a pandas dataframe
    split_tup = os.path.splitext(file_name)
    if split_tup[1] == '.csv':
        file_df = pd.read_csv(file_name)
        print('csv saved into df with %d records' % file_df.shape[0] )
    if split_tup[1] == '.xls' or split_tup[1] == '.xlsx':
        file_df = pd.read_excel(file_name)

    if (file_df):
        conn = connect_to_db()
        try:
            print('try')
            file_df.to_sql('carpool_candidates', conn, if_exists='replace')
        except:
            print("It was not possible to save file into database")
        conn.close() 
    return 


def save_new_route_into_db(route_df):
    '''Save new route dataframe into database'''

    conn = connect_to_db()
    route_df.to_sql('carpool_routes', conn, if_exists='append')
    conn.close()
    return


