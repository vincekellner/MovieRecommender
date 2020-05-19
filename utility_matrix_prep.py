'''
This module contains a couple of functions to create the utility matrix based on the MovieLens datasets
'''

import numpy as np
import pandas as pd


def get_merged_ratings_df(ratings_df, movies_df):
    
    ratings_and_movies = pd.merge(ratings_df , movies_df[['movie_title','movieId']], on='movieId', how='left')
        
    return ratings_and_movies[['userId', 'movie_title', 'rating']]



def create_initial_util_matrix(movies_df):

    '''creates initial utility matrix '''
    
    #get all unique movies:
    all_titles = movies_df['movie_title'].unique()

    #create initial row of utility_matrix based on unique movie titles:
    init_util_matrix = pd.DataFrame(np.zeros((1, len(all_titles)))) #needed to add the user ratings correctly; later the row is deleted
    init_util_matrix.columns = all_titles
    init_util_matrix.index = ['a']
    
    return init_util_matrix
    
    
def utility_matrix_preprocessing(df, util_matrix):
    
    '''
    based on ratings of each user creates utility matrix: rows = user ratings, cols = Movie titles, row_index = userID
    '''
    #eliminate duplicated columns (some users might have rated a movie twice --> this code only keeps the first rating)
    df = df[~df[['userId','movie_title']].duplicated()]
       
    #create rows for each user rating: each row contains the movies as columns with the corresponding rating and userID as index
    help_piv_df = df.pivot(values='rating', index='userId', columns='movie_title')
    
    #adjust axis:
    help_piv_df = help_piv_df.rename_axis(None, axis=1).reset_index().set_index('userId') #removes MultiIndex
    #rename index axis:
    help_piv_df = help_piv_df.rename(index=lambda idx: 'User_' + str(idx))
        
    #concat user_ratings with pre-defined utility matrix
    util_matrix = pd.concat([util_matrix,help_piv_df])


    return util_matrix



def handle_duplicated_entries(util_matrix):
    
    '''combines duplicated entries (which might occur due to non-overlapping chunks)
        e.g.: in chunk1 user_100 has given a rating to some movies
               in chunk2 user_100 has given a rating to addtional movies
    '''
    
    
    #get indices of duplicated entries:
    dup_idx = util_matrix[util_matrix.index.duplicated(keep=False)].index.unique()  
    
    print('No. of duplicated entries: ', len(dup_idx))
    
    #create two dfs: one which stores the last row of duplicates, one that stores the first row of duplicates
    help_dups_first = util_matrix[util_matrix.index.duplicated(keep='last')]
    
    help_dups_last = util_matrix[util_matrix.index.duplicated(keep='first')] #returns last duplicates (keeps first duplicates)

    #combine duplicates:
    dups_combined_df = help_dups_first.combine_first(help_dups_last)

    #drop all duplicated rows in util_matrix:
    util_matrix.drop(dup_idx, inplace=True)
        
    #add updated rows:
    util_matrix = pd.concat([util_matrix,dups_combined_df])
        
        
    return util_matrix



def create_utility_matrix(ratings_path: str ='/...', ratings_file_name: str= '/...', 
                          ratings_df = None, movies_df = None, chunk_size= 100000):
    '''
    calls several functions to obatin utility matrix for given data
    '''
    
    #get initial utility_matrix:
    utility_matrix = create_initial_util_matrix(movies_df)
    
    try:
        size = ratings_df.shape[0]
    except:
        size = None
    
    
    if size == None:
    
        #load ratings_data:
        path = ratings_path
        file_name = ratings_file_name

        df_ratings_chunk = pd.read_csv(
            path + file_name,
            encoding = "ISO-8859-1", 
            header=0,
            chunksize = chunk_size
            )
        
        count = 0
        # Each chunk is in df format
        for ratings_chunk in df_ratings_chunk:  

            count += 1 
            print('processing chunk {} : '.format(count))

            #perform merge to get correct movie titles:
            chunk_merge = get_merged_ratings_df(ratings_chunk, movies_df)

            # perform data filtering 
            utility_matrix = utility_matrix_preprocessing(chunk_merge, utility_matrix)

            #free memory
            del chunk_merge
     
    elif size > 0:
        #perform merge to get correct movie titles:
        merged_df = get_merged_ratings_df(ratings_df, movies_df)
        
        # perform data filtering 
        utility_matrix = utility_matrix_preprocessing(merged_df, utility_matrix)
    
    else:
        print('No correct df given as input')
    
    #handle duplicates in utility_matrix:
    final_utility_matrix = handle_duplicated_entries(utility_matrix)

    #del initial_row:
    final_utility_matrix.drop(['a'], inplace=True)

    return final_utility_matrix



