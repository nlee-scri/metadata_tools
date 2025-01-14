""" Functions for procesing metadata from microscopy files"""


from readlif.reader import LifFile
import os
from glob import glob
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from imaris_ims_file_reader.ims import ims
from datatools.utils import xml_helpers
from datatools.utils.utils import transform_dict

md_keys = {
    "general": ["path", "name", "channels"],
    "settings": ["MicroscopeModel", "Magnification", "ObjectiveName"],
}

class lif_file_processor: 
    def __init__(self, file_path): 
        self.file_path = file_path
        self.lif = LifFile(file_path)
        self.md_df = self.get_overall_md()
        self.md_keys = {
            "general": ["path", "name", "channels"],
            "settings": ["MicroscopeModel", "Magnification", "ObjectiveName"],
        }
        

    def get_overall_md(self): 
        md_temp = []

        for image in self.lif.image_list: 
            temp = {'general.'+k:image[k] for k in md_keys['general']}
            temp_settings = {"setting."+k:image['settings'][k] for k in md_keys['settings']}
            temp_hardware = {"hardware." + k: v for k,v in self.get_software_md().items()}
            temp_final = temp | temp_settings | temp_hardware
            md_temp.append(temp_final)
        
        md_df = pd.DataFrame(md_temp)
        md_df = md_df.assign(
            file_name = Path(self.lif.filename).name,
            Files = self.file_path
        )
        
        return md_df
    
    def get_software_md(self):
        try: 
            result = xml_helpers.recursive_search_for_tag_with_attribute(self.lif.xml_header, 'Attachment', 'Name', 'HardwareSetting')
            software_md = result.attrib
            return software_md
        except Exception as e: 
            print(e)
            return None
        
    
# def process_file(file_name):
#     """ For .lif files, extract metadata and channels.

#     Args:
#         file_name (str): path to the file

#     Returns:
#         (pd.DataFrame,pd.DataFrame): Dataframes of metadata and channels
#     """
#     lfil = LifFile(file_name)
    
#     # metadata to pull out
#     # md_df = get_overall_md(lfil)
    
#     channels = get_channels(lfil)
    
#     return md_df, channels
    

def get_channels(lfil):
    """
    Extracts channel information from the XML header of a given file.
    Args:
        lfil: An object containing an XML header attribute.
    Returns:
        A list of pandas DataFrames, each containing channel information for sub-images.
        Each DataFrame includes the following columns:
            - 'file_name': The name of the top-level element.
            - 'element_name': The name of the sub-image element.
            - 'path': The path to the channel property.
            - 'DyeName': The name of the dye used in the channel.
            - Additional columns transformed from the channel property elements.
    """
    
    root = ET.fromstring(lfil.xml_header)
    top_name = root.find('Element').attrib['Name']
    sub_image_elements = root.findall('Element/Children/Element')
    full_results = []
    for e in sub_image_elements: 
        results = []
        possible_tags = ['ChannelProperty', 'ChannelDescription']
        for tag in possible_tags: 
            elements = xml_helpers.recursive_find_with_path(e, tag)
            if len(elements) > 0: 
                break
            
        for t in elements: 
            temp = {'path': t[0]} | transform_dict(xml_helpers.parse_element(t[1]))
            results.append(temp)

        results_df = pd.DataFrame(results)

        df_filled = results_df.groupby('path').ffill().bfill()
        df_filled['path'] = results_df['path']

        df_collapsed = df_filled.drop_duplicates(subset=['path', 'DyeName']).reset_index(drop = True)
        df_collapsed
        sub_image_elements[0].attrib['Name']
        df_collapsed.insert(0, 'file_name', top_name)
        df_collapsed.insert(1, 'element_name', e.attrib['Name'])
        full_results.append(df_collapsed)
    
    return full_results


class ims_file_processor:
    def __init__(self, file_name, sub_dir, exp_name, output_file_name):
        """
        Initialize the FileProcessor with the given file name.
        
        :param file_name: The name of the file to process.
        :param sub_dir: Directory to write out files for data submission.
        :param exp_name: Name of the experiment, will be subfolder of sub_dir.
        :param output_file_name: Name to export the file as.
        """
        self.file_name = file_name
        # self.lfil = LifFile(file_name)
        # self.sub_dir = sub_dir
        # self.study_id = Path(sub_dir).name # assuming this will be the same as in ImmPort
        # self.exp_name = exp_name
        # self.output_file_name = output_file_name
        self.md_keys = {
            "general": ["path", "name", "channels"],
            "settings": ["MicroscopeModel", "Magnification", "ObjectiveName"],
        }
        
        # self.process_file()
        
    def ims_metadata_extract(file_path): 
        keys = [
            "ElementName",
            "LensPower",
            "MicroscopeModality",
            "NumericalAperture",
            "OriginalFormat",
            "OriginalFormatFileIOVersion",
            'Unit',
        ]
        
        a = ims(file_path)

        metadata = {k: a.read_attribute("DataSetInfo/Image", k) for k in keys}
        metadata['dimensions'] = 'x'.join([a.read_attribute("DataSetInfo/Image", 'X'), a.read_attribute("DataSetInfo/Image", 'Y'), a.read_attribute("DataSetInfo/Image", 'Z')]) 
        metadata['file_name'] = Path(file_path).name
        return metadata

    def get_overall_md(self): 
        md_temp = []

        for image in self.lif.image_list: 
            temp = {'general.'+k:image[k] for k in md_keys['general']}
            temp_settings = {"setting."+k:image['settings'][k] for k in md_keys['settings']}
            temp_hardware = {"hardware." + k: v for k,v in self.get_software_md().items()}
            temp_final = temp | temp_settings | temp_hardware
            md_temp.append(temp_final)
        
        md_df = pd.DataFrame(md_temp)
        md_df = md_df.assign(
            file_name = Path(self.lif.filename).name,
            Files = self.file_path
        )
        md_df = md_df.loc[:,~md_df.columns.duplicated()]
        
        return md_df
        
    def get_channels(self):
        """
        Extract channel information from the file.
        
        :return: A list of DataFrames containing the channel information.
        """
        root = ET.fromstring(self.lfil.xml_header)
        top_name = root.find('Element').attrib['Name']
        sub_image_elements = root.findall('Element/Children/Element')
        full_results = []

        for e in sub_image_elements:
            results = []
            for t in xml_helpers.recursive_find_with_path(e, 'ChannelProperty'):
                temp = {'path': t[0]} | transform_dict(xml_helpers.parse_element(t[1]))
                results.append(temp)

            results_df = pd.DataFrame(results)

            df_filled = results_df.groupby('path').ffill().bfill()
            df_filled['path'] = results_df['path']

            df_collapsed = df_filled.drop_duplicates(subset=['path', 'DyeName']).reset_index(drop=True)
            df_collapsed.insert(0, 'file_name', top_name)
            df_collapsed.insert(1, 'element_name', e.attrib['Name'])
            full_results.append(df_collapsed)

        return full_results

    def cleanup(self):
        """
        Clean up the final results by concatenating, dropping duplicates, and renaming columns.
        
        :return: A DataFrame containing the cleaned-up results.
        """
        channels = self.get_channels()
        final_results = pd.concat(channels)
        final_results = final_results.drop_duplicates(subset=['DyeName']).reset_index(drop=True)
        final_results.info()
        main_cols = [
            "User Defined ID",
            "Name",
            "Description",
            "Manufacturer",
            "Catalog Number",
            "Lot Number",
            "Weblink",
            "Contact",
        ]
        final_results['File Name'] = Path(self.file_name).name
        final_results = final_results.rename(columns={'DyeName': 'Name'})
        for m in main_cols:
            if m not in final_results.columns:
                final_results[m] = None
                
        final_results = final_results[main_cols + ['File Name']]
        
        final_results = final_results.loc[:,~final_results.columns.duplicated()]
        
        return final_results

    def process_file(self):
        """
        Process the file to extract metadata and channels.
        
        :return: A tuple containing the metadata DataFrame and the channels list.
        """
        self.md_df = self.get_overall_md()
        self.channels = self.cleanup()
        
        # final cleanup 
        if 'Study ID' in self.md_df.columns: 
            self.md_df['Study ID'] = self.study_id
        if 'Study ID' in self.channels.columns: 
            self.channels['Study ID'] = self.study_id
        
        # self.write_out_results(exp = self.md_df, exp_reagents = self.channels)
    
def write_out_results(sub_dir, exp_name, output_file_name, exp: pd.DataFrame, exp_md: pd.DataFrame = None, exp_reagents: pd.DataFrame = None):
    """
    Write out the results to an Excel file.
    
    :param exp: The experiment DataFrame.
    :param exp_md: The metadata DataFrame (optional).
    :param exp_reagents: The reagents DataFrame (optional).
    """
    output_dir = Path(os.path.join(sub_dir, exp_name))
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    output_path = os.path.join(output_dir, "exp_" + output_file_name + '.xlsx')
    
    print(f'Writing results to: {output_path}')

    with pd.ExcelWriter(output_path) as writer:
        exp.to_excel(writer, sheet_name='experiment', index=False)
        if exp_md is not None:
            exp_md.to_excel(writer, sheet_name='samples', index=False)
        if exp_reagents is not None:
            exp_reagents.to_excel(writer, sheet_name='reagents', index=False)
            
def ims_metadata_extract(file_path): 
    keys = [
        "ElementName",
        "LensPower",
        "MicroscopeModality",
        "NumericalAperture",
        "OriginalFormat",
        "OriginalFormatFileIOVersion",
        'Unit',
    ]
    
    a = ims(file_path)

    metadata = {k: a.read_attribute("DataSetInfo/Image", k) for k in keys}
    metadata['dimensions'] = 'x'.join([a.read_attribute("DataSetInfo/Image", 'X'), a.read_attribute("DataSetInfo/Image", 'Y'), a.read_attribute("DataSetInfo/Image", 'Z')]) 
    metadata['file_name'] = Path(file_path).name
    metadata['Files'] = file_path
    return metadata