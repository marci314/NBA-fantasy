# Cilj je, da dobi basketball reference CSV tabelo in vrne vrstice, pripravljene za vstavit v sql.
import numpy as np
from datetime import datetime

def uvozi_iz_csv(dat):
    #df = pd.read_csv(dat)
    df = np.loadtxt(dat,
                 delimiter=",", dtype='str')
    return df

def ohrani_relevantno(df):
    #df1 = df[:, 'Starters', 'MP', 'FG%', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PTS', '-9999']
    df1 = df[1:, [1, 4, 13, 14, 15, 16, 17, 19, 21]]
    return df1

def pretvori_v_sql(dat, id_tekme=0, id_ekipa=0, izid=0):
    '''Vrne podatke o tekmah, pripravljene za INSERT v SQL.'''
    df = np.loadtxt(dat,
            delimiter=",", dtype='str')
    df = df[1:, [1, 4, 13, 14, 15, 16, 17, 19, 21]]
    for i in range(1, len(df[0])):
        str = df[i, 0]
        interval = f"{str[0:2]} minutes {str[3:]} seconds"
        print(f"('{df[i, -1]}', {id_tekme}, {id_ekipa}, {df[i, 1]}, {df[i, 4]}, {df[i, 5]}, {df[i, 6]}, {df[i, 2]}, {df[i, 3]}, INTERVAL '{interval}', {df[i, 7]}, {izid}),")



def transform_date_to_postgresql_format(date_str):
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_str, '%B %d %Y')
    # Format the datetime object into the desired PostgreSQL date format
    postgres_date_str = date_obj.strftime('%Y-%m-%d')
    return postgres_date_str

def height_to_cm(height_str):
    # Split the height string into feet and inches
    feet, inches = map(int, height_str.split('-'))
    
    # Convert feet to inches and add the remaining inches
    total_inches = feet * 12 + inches
    
    # Convert inches to centimeters (1 inch = 2.54 cm)
    cm = total_inches * 2.54
    
    return round(cm)

def igralci_v_sql(data):
    '''Vrne podatke o igralcih, pripravljene za INSERT v SQL.'''
    df = np.loadtxt(data,
        delimiter=",", dtype='str')
    ime = df[:, 1]
    poz = df[:, 2]
    visina = df[:, 3]
    rojstvo = df[:, 5]
    for i in range(1, len(df[0])):
        visinacm = height_to_cm(str(visina[i]))
        rojstvo1 = transform_date_to_postgresql_format(rojstvo[i])
        print(f"(, '{ime[i]}', '{poz[i]}', {visinacm}, {rojstvo1})")
    return

