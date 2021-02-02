import pandas as pd
import numpy as np
import xlrd
import re

def get_sheet_names(excel_file_location):
    """
    Inputs:
        excel_file_location (str) - location of excel files 
    This function gets the excel sheet names that contain the rental "Summary"

    Returns:
        open_file_sheet_names (list of strings) - the sheet names we are going to want to open 
    """
    open_file = xlrd.open_workbook(excel_file_location, on_demand=True)
    open_file_sheet_names = open_file.sheet_names()
    open_file_sheet_names = [x for x in open_file_sheet_names if not x.endswith('Summary')] #we want to drop summary tabs 
    return open_file_sheet_names

def make_header(df):
    """
    inputs:
        df (dataframe)
    returns:
        df (dataframe)
    do some basic cleanup of the header row 
    """
    new_header = df.iloc[4] #grab the forth row for the header
    df = df[5:] #take the data less the blank rows
    df.columns = new_header
    return df

def read_in_check_status(file,sheet):
    """
    inputs:
        file (str): filepath of excel file
        sheet (str): name of sheet in excel sheet
    returns:
        df (dataframe)
    Read in data from a given excel sheet, do some cleaning 
    """
    df = pd.read_excel(file,sheet_name = sheet)
    new_header = df.iloc[4] #grab the forth row for the header
    df = df[5:] #take the data less the blank rows
    df.columns = new_header
    df = df[:-2]#drop bottom two rows, which contain summary info
    df = df.reset_index().drop(columns=["index","Property"])
    df = df.rename(columns={"Tenant Lease Charge":"Tenant Lease Charge"+" "+df["Period"][5],
                   "Tenant Rent Collected":"Tenant Rent Charge"+" "+df["Period"][5],
                  "Percent Collected":"Tenant Percent Collected"+" "+df["Period"][5],"Property Name":"Property"})
    #lowercase, remove punction and whitespace from names, and then concat with tenant id to make a key to match on
    df.Name = df.Name.str.lower()
    p = re.compile(r'[^\w\s]+')
    df['Name'] = [p.sub('', x) for x in df['Name'].tolist()]
    df.Name = df.Name.str.replace(' ', '')
    df["key"] = df["Tenant"] + df["Name"]
    #df = df.drop(columns={"Period"})
    return df

def read_in(file,sheet):
    """
    inputs:
        file (str): filepath of excel file
        sheet (str): name of sheet in excel sheet
    returns:
        df (dataframe)
    Read in data from a given excel sheet, do some cleaning and then 
    make new column names that adds the date for financial transaction 
    and drops the rest of the data. 
    """
    df = pd.read_excel(file,sheet_name=sheet)
    new_header = df.iloc[4] #grab the forth row for the header
    df = df[5:] #take the data less the blank rows
    df.columns = new_header
    df = df[:-2]#drop bottom two rows, which contain summary info
    df = df.reset_index().drop(columns=["index"])
    df = df[['Tenant Lease Charge','Is Subsidized?', 'Fixed Income?', 'Tenant Rent Collected',
             'Percent Collected',"Period","Tenant","Name","Property Name"]]
    df = df.rename(columns={"Tenant Lease Charge":"Tenant Lease Charge"+" "+df["Period"][5],
                   "Tenant Rent Collected":"Tenant Rent Charge"+" "+df["Period"][5],
                  "Percent Collected":"Tenant Percent Collected"+" "+df["Period"][5],
                   'Is Subsidized?':"Is Subsidized?"+" "+df["Period"][5], 
                    'Fixed Income?':"Fixed Income?"+" "+df["Period"][5]}) 
    df = df.drop(columns={"Period"})
    #lowercase, remove punction and whitespace from names, and then concat with tenant id to make a key to match on
    df.Name = df.Name.str.lower()
    p = re.compile(r'[^\w\s]+')
    df['Name'] = [p.sub('', x) for x in df['Name'].tolist()]
    df.Name = df.Name.str.replace(' ', '')
    df["key"] = df["Tenant"] + df["Name"]
    df = df.drop(["Tenant","Name","Property Name"], axis = 1)
    return df

def filter_eden_rent_roll(df):
    """
    inputs:
        df - eden rent roll data 
    This function removes employee units as well as units that were not completed for the entirity of 2019-2020 
    (found by looking at Eden's website for properties with high vacencies in the data)
    """
    df = df.drop(columns=["Period"]) #drop col we dont need anymore
    searchfor = ["employee","manager"]
    df = df[~df.key.str.lower().str.contains('|'.join(searchfor))]
    all_hands_on_the_bad_ones = ['Stone Pine Meadows','Quail Run Apartments','Lincoln Corner Apartments',
    'Vacaville Meadows Drive','Orchard/Maples Apartments','Willows Apartments',
    'Highlands Apartments', 'Hillside Senior Apartments']
    df = df[~df["Property"].isin(all_hands_on_the_bad_ones)]
    return df 

def clean_names(df,col,col2,eden_tenants=True):
    """
    inputs:
        df - eden rent roll data or eden demographic data
        col (str) - Name of col with Eden resident's name 
        col2 (str) - Tenant code for eden resident
        eden_tenent (boolean) - If dataset is payment data (eden_tenant=True), if demogarphic data (eden_tenant=False) 
    This function cleans up the name column and the properties list for better matching. Then this function 
    creates a key to match on based on a combination of the name, tenant ID and property ID. 
    """
    if eden_tenants == False:
         
        #df["Flipped_Name"] = df["Name"].str.replace(r'(.+),\s+(.+)', r'\2 \1')
        df.Member_Name  = df.Member_Name.str.split().apply(lambda x: ''.join(x[::-1]))
        df = df.rename(columns={"Property_Name":"Property","Unit_Code":"Unit"})


    df[col] = df[col].str.lower()
    p = re.compile(r'[^\w\s]+')
    df['Name_Clean'] = [p.sub('', x) for x in df[col].tolist()]
    df.Name_Clean = df.Name_Clean.str.replace(' ', '')
    
    df.Property = df.Property.str.lower()
    df.Property = [p.sub('', x) for x in df.Property.tolist()]
    df.Property = df.Property.str.replace(' ', '')

    if eden_tenants == True:
        df = df.replace({
    'Property':{"paulineweaverseniorapartmentsfour": "paulineweaverseniorapart", 
            "paulineweaverseniorapartmentsnine": "paulineweaverseniorapart",
                                 "altenheimseniorhousingphaseii":"altenheimseniorhousing",
                                  "vistapointatpacificgrove":"pacificgrove",
                                  "warnercreekseniorhousinglp":"warnercreekseniorhousing"}})
        df["Match"] = df.Name_Clean + df.Tenant + df.Property

    else:
        df = df.replace({
    'Property':{"altenheimseniorhousingp":"altenheimseniorhousing",
                            "seacliffhighlandsapartmen":"seacliffhighlandsapartments",
                            "universityvillageapartmen":"universityvillageapartments",
                              "belleterreseniorapartmen":"belleterreseniorapartments",
                              "mirafloresseniorapartment":"mirafloresseniorapartments",
                              "monteverdevilla":"monteverde"}})
        df["Match"] = df.Name_Clean + df["Tenant_Code"] + df.Property
 
    return df

def filter_eden_resident(df):
    """
    Inputs:
        df (dataframe) -  demographic data about eden residents 
    This function filteres the eden demograpic data for heads of household as well as for 2019 data, 
    as the rent payment data we are matching on is 2019-2020 and the demographic data is for 2018-2019
    """
    #keep only heads and co-heads of households
    head_household = ['HoH']
    #note, not including Co-Head, any household with a co-head will have a head still, and they share a tenant ID
    df = df[df["Member_Relation"].isin(head_household)]
    #keep only 2019 data for Tenants 
    df = df[df.year == 2019]
    #drop true duplicates (those who share both exact name and tenant code match)
    #df = df[~df.duplicated(['Tenant_Code',"Name_Clean"],keep=False)].sort_values("Tenant_Code")
    #currently there are 24 pairs of duplicates where a house shares a head of house, remove them 
    #df = df[df.duplicated(['Tenant_Code'],keep=False)].sort_values("Tenant_Code")
    return df 

def match_name(name, list_names, min_score=0):
    
    """
    This function, called by the below function, calc_matches, goes through all possible combinations of two 
    keys (which are building name, tenant name, tenant ID, concats) and assigns the max possible levenshtein distance score 
    """  
    # -1 score if no match
    max_score = -1
    max_name = ""
    for name2 in list_names:
        score = fuzz.ratio(name, name2)
        if (score > min_score) & (score > max_score):
            max_name = name2
            max_score = score
    return (max_name, max_score)


def calc_matches(df_tenants_clean,eden_residents_clean):
    """
    Inputs:
        df_tenants_clean (dataframe) - eden tenant payment info, row is a tenant
        eden_residents_clean (dataframe) - eden tenant demographic info, row is a tenant
    This function is called by the function keep_high_scores_and_merge. It compares combinations of 
    match keys from df_tenants_clean & eden_residents_clean and finds the highest combined levenshtein distance
    Returns:
        merge_table_big (dataframe) - dataframe with matches from df_tenants_clean & eden_residents_clean
                                        scored with levenstein distance 
    """

    #NOTE, this is going to take like 5 minutes to run 
    dict_list_big = []
    for name in df_tenants_clean.Match:
        match = match_name(name, eden_residents_clean.Match, 50)

        dict_ = {}
        dict_.update({"player_name" : name})
        dict_.update({"match_name" : match[0]})
        dict_.update({"score" : match[1]})
        dict_list_big.append(dict_)

    merge_table_big = pd.DataFrame(dict_list_big)
    return merge_table_big

def keep_high_scores_and_merge(df_tenants_clean,eden_residents_clean,merge_table_big):
    """
    Inputs:
        df_tenants_clean (dataframe) - eden payment data
        eden_residents_clean (dataframe) - eden demographic data
        merge_table_big (dataframe) - dataframe with matches from df_tenants_clean & eden_residents_clean
                                        scored with levenstein distance 
    This function takes in the eden payment data and the eden demographic data and merges it together 
    It takes scores over 89 from the merge_table_big table (this cutoff was determined by manually examining the matches)
    and merges them together into eden_merged_fuzzy
    """
    #make matches above threshold  we want to keep into a dictonary 
    high_score_merge = merge_table_big[(merge_table_big["score"]>=89)&(merge_table_big["score"]<100)]
    merge_dict_eden = dict(zip(high_score_merge.player_name, high_score_merge.match_name))
    #Use dictionary to update values in Rent Roll Data to be ones that match tenant data 
    df_tenants_clean['Match'] = df_tenants_clean['Match'].replace(merge_dict_eden)
    #same thing but with eden residents data 
    high_score_merge = merge_table_big[(merge_table_big["score"]>=89)&(merge_table_big["score"]<100)]
    merge_dict_eden = dict(zip(high_score_merge.match_name,high_score_merge.player_name))
    #Use dictionary to update values in  to be ones that match tenant data 
    eden_residents_clean['Match'] = eden_residents_clean['Match'].replace(merge_dict_eden)
    #merge data now using fuzzy matching 
    eden_merged_fuzzy = df_tenants_clean.merge(eden_residents_clean,on="Match",how="inner")
    return eden_merged_fuzzy

def drop_cols_post_merge(df):
    """
    Inputs:
        df (dataframe) - dataframe of eden residents full merged data
    This small function just drops columns we don't need after the merge and does some renaming for cleanliness. 
    """
    df = df.drop(columns={'Property_y', 'Tenant',"year",'Unit_y',"key","Name_Clean_y","Flipped_Name",
                                                        "Name_Clean_x","Tenant Lease Charge 02/01/20 - 02/29/20_y",
                                                        "Fixed Income? 02/01/20 - 02/29/20_y","Tenant Rent Charge 02/01/20 - 02/29/20_y",
                                                        "Tenant Percent Collected 02/01/20 - 02/29/20_y"})
    df = df.rename(columns={'Property_x':"Property", 'Unit_x':"Unit"})
    df = df[df.columns.drop(list(df.filter(regex='Fixed Income?')))]
    df = df[df.columns.drop(list(df.filter(regex='Is Subsidized?')))]
    return df

def melt_rows(df):
    """
    Inputs:
        df (dataframe) - dataframe of eden residents full merged data 
    This function creates a unique indentifier for each eden resident and the melts the dataset so that we have each row as a person - month paring. 
    It also drops all months where no rent was charged, indicating that the person was not yet in the dataset.
    """
    #rename some columns so we can easily collect the rest of the columns with "tenant" in their name 
    df = df.rename(columns={"Tenant_Code":"ID_Code","Tenant_Status":"Status"})
    df['person_id'] = np.arange(df.shape[0])
    tmp = eden_merged_fuzzy.melt(id_vars=[x for x in df.columns if 'Tenant' not in x])
    tmp['date'] = tmp.variable.apply(lambda x: x.split()[3])
    tmp['info'] = tmp.variable.apply(lambda x: ' '.join(x.split()[:3]))
    tmp['value'] = tmp.value.astype(int)
    tmp = tmp.pivot(index=['person_id', 'date'], columns='info', values='value').reset_index()
    tmp = tmp.loc[tmp['Tenant Lease Charge']!=0] #want to drop months where person was not yet in dataset, meaning they were charged zero 
    merged = pd.merge(df[[x for x in df.columns if 'Tenant' not in x]], tmp, on='person_id')
    return merged

