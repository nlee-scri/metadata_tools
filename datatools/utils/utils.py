from pathlib import Path
import re
import logging
import zipfile
import os
import pandas as pd
import numpy as np
import hashlib

def apply_to_list(func):
    def wrapper(*args, **kwargs):
        # Check if the first argument is a list
        if isinstance(args[0], list):
            return [func(item, *args[1:], **kwargs) for item in args[0]]
        else:
            return func(*args, **kwargs)
    return wrapper

def clean_str_cols(df):
    """ Assuming convert_dtypes gets it right """
    df = df.convert_dtypes()
    string_cols = df.select_dtypes(include='string')
    df.loc[:, string_cols.columns] = string_cols.map(lambda x: x.strip(" "))
    return df

def remove_special_characters(input_string):
    # Remove any non-alphanumeric characters (including underscore)
    return re.sub(r"[^a-zA-Z0-9\s]", "", input_string)


def clean_field_names(x: str) -> str:
    new_name = re.sub(" ", "_", re.sub("\\*|\\(|\\)|-|/|,", "_", x)).strip()
    new_name = re.sub('_{2}', "_", new_name)
    return new_name

@apply_to_list
def col_renamer(word:str, case: str):
    """ Transform columns to desired case """
    if case not in ['human_readable', 'snake_case']:
        raise ValueError("Case must be either 'human_readable' or 'snake_case'")
    
    word = utils.remove_special_characters(word)
    
    if case == 'human_readable':
        if not bool(re.search(' ', word)): 
            for i, letter in enumerate(word): 
                if i == 0: 
                    new_word = letter.upper()
                else: 
                    if letter.isupper(): 
                        new_word += " " + letter 
                    else: 
                        new_word += letter
        else:           
            new_word = word.replace('_', ' ')
            new_word = re.sub(r' {2,}', ' ', new_word)
        # new_word = new_word.title()
        # return new_word
    
    elif case == 'snake_case': 
        word = word.replace(' ', "_")
        new_word = word.lower()
        # return new_word
        
    else: 
        word = word.replace(' ', "")
        new_word = ""
        for i, letter in enumerate(word): 
            if i == 0: 
                new_word += letter.lower()
            else: 
                if letter.isupper(): 
                    new_word += "" + letter 
                else: 
                    new_word += letter
            
    if bool(re.search('id', word, flags=re.IGNORECASE)): 
        new_word = re.sub('id', 'Id', new_word, flags=re.IGNORECASE)

    return new_word


def rename_duplicates(df):
    # Rename duplicate columns
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    return df

def drop_duplicate_cols(df: pd.DataFrame) -> pd.DataFrame: 
    return df.loc[:, ~df.T.duplicated()]

class MyLogger:
    def __init__(self, log_file="my_log.log", level=logging.INFO):
        # Create a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

        # Create a file handler and set the log level
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        # Create a formatter and set it for the file handler
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


def create_path(file_path):
    if Path(file_path).suffix is not None:
        if file_path.parent.exists(): 
            print('Directory exists')
        else: 
            print(f"Making parent directories for file: {file_path}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Making directories for folder: {file_path}")
        file_path.mkdir(parents=True, exist_ok=True)


def check_file(file_path, overwrite='y'):
    file_path = Path(file_path)
    if file_path.exists():
        print("Output file already exists")
        if overwrite is None:
            overwrite = input("Overwrite file? y/[n]")
            if overwrite.lower() == "n":
                return None
            elif overwrite.lower() == "y":
                create_path(file_path)
                return True
            else:
                print("Error")
                return None
    else:
        create_path(file_path)
        return True


def zip_files(file_paths, output_zip):
    checker = check_file(output_zip)
    if checker == True:
        with zipfile.ZipFile(output_zip, "w") as zipf:
            for file in file_paths:
                if os.path.isfile(file):
                    zipf.write(file, os.path.basename(file))
                else:
                    print(f"File not found: {file}")
        print(f"Created file: {str(output_zip)}")
    else:
        print(f"Did not create zipped file: {output_zip}")

def transform_dict(input_dict):
    """
    Transforms a dictionary with nested 'text' keys into a simplified dictionary.

    Args:
        input_dict (dict): The input dictionary to transform.

    Returns:
        dict: A simplified dictionary with the 'Key' value as the new key and the 'Value' value as the new value.
    """
    key = input_dict.get('Key', {}).get('text')
    value = input_dict.get('Value', {}).get('text')
    if key is not None and value is not None:
        return {key: value}
    return {}

def unique_list_keep_order(l: list): 
    new_list = []
    for x in l: 
        if x not in new_list: 
            new_list.append(x)
    
    if len(new_list) > 0: 
        return '_'.join(new_list)
    else: 
        return None

def unique_list_sorted(l:list, delimiter: str = ","): 
    """ Join together a list of items during an aggregation function and return unique sorted values
    
    Returns: str
    """
    try: 
        result = f'{delimiter}'.join(sorted(list(np.unique(l))))
        return result
    except: 
        return ''

def value_counts_by_col(df: pd.DataFrame) -> pd.DataFrame: 
    # Split DataFrame by column

    columns = df.columns
    split_dfs = {col: df[[col]].dropna() for col in columns}

    # Get value counts for each column
    value_counts = {col: split_df[col].value_counts() for col, split_df in split_dfs.items()}

    # Inspect value counts for each column
    for col, counts in value_counts.items():
        print(f"Value counts for column {col}:")
        print(counts)
        print("\n")

def generate_md5(file_path):
    """
    Generate MD5 checksum for a given file.

    Parameters:
    file_path (str): The path to the file for which the MD5 checksum is to be generated.

    Returns:
    str: The MD5 checksum of the file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()