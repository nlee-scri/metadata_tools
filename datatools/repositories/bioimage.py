from datatools.utils import apply_to_list
import pandas as pd

def dict_to_pagetab_string(d: dict, section_header=None) -> None:
    """
    Converts a dictionary to a string formatted with tab-separated values, 
    optionally including a section header.
    Args:
        d (dict): The dictionary to convert to a string.
        section_header (str, optional): An optional header to include at the 
            beginning of the output string. Defaults to None.
    Returns:
        str: A string representation of the dictionary with each key-value 
        pair separated by a tab and each pair on a new line. If a section 
        header is provided, it will be included at the beginning of the 
        string.
    """
    
    output_string = ""
    if section_header is not None:
        output_string += f"\n{section_header}\n"

    for k, v in d.items():
        output_string += f"{k}\t{v}\n"

    return output_string


def df_to_pagetab_string(df: pd.DataFrame, section_title: str = None) -> None:
    """
    Converts a pandas DataFrame into a string formatted with tab-separated values, 
    optionally including a section title at the beginning of each row.
    Args:
        df (pd.DataFrame): The DataFrame to be converted into a string.
        section_title (str, optional): A title to be included at the beginning of each row. Defaults to None.
    Returns:
        str: A string representation of the DataFrame with tab-separated values.
    """
    
    output_string = ""
    for _, row in df.iterrows():
        if section_title:
            output_string += f"\n{section_title}"
        output_string += '\n'
        for k, v in row.items():
            output_string += f"{k}\t{v}\n"
                
    return output_string


def write_to_pagetab(output_file: str, output_string: str, mode='a') -> None:
    """
    Writes a given string to a specified file.
    Args:
        output_file (str): The path to the file where the string will be written.
        output_string (str): The string content to write to the file.
        mode (str, optional): The mode in which to open the file. Defaults to 'a' (append mode).
    Returns:
        None
    """
    
    print('Writing to pagetab: ', output_file)
    with open(output_file, mode) as file:
        file.write(output_string)

class bioimage_pagetab(): 
    def __init__(self, file_path):
        self.sections = {}
        self.section_order = []
        self.file_path = file_path
        self.sections['base_block'] = {
            "Submission": "", 
            "Title": "",
            "RootPath": "",
            'ReleaseDate': "",
            "AttachTo": "BioImages",
        }
    
    def add_section(self, section_title, section_data):
        self.sections[section_title] = section_data
        self.section_order.append(section_title)
    
    # add publication section