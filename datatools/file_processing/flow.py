# get sample metadata
keys = ['uri', 'fil', 'groupname', 'creator', "inst", 'cyt', 'cytsn', 'cytnum', 'tube name', 'src', 'experiment name'] # NOT ALL ARE USED EVERY TIME, 

reagent_cols = [
    "Reagent Name", 
    "Description", 
    "Manufacturer", 
    "Catalog Number", 
    "Lot Number", 
    "Weblink", 
    "Contact", 
    "Analyte Reported", 
    "Antibody Register ID", 
    "Clone Name", 
    "Reporter Name"
]

# files_information = {}
#     doc_id = row['id']
#     name = row['name']

#     data = {
#         'token': config['redcapapi_prod'],
#         'content': 'fileRepository',
#         'action': 'export',
#         'doc_id': doc_id,
#         'returnFormat': 'json'
#     }

#     r = requests.post('https://redcap.seattlechildrens.org/api/',data=data)
#     print('HTTP Status: ' + str(r.status_code))
    
#     temp_file_path = f"./flow_AD94/temp/{name}"
#     utils.utils.check_file(temp_file_path)
    
#     with open(temp_file_path, 'wb') as file: 
#         file.write(r.content)
        
#     temp = r.content.decode()
#     temp = xml_helpers.parse_xml(temp)
#     print('Number of samples: ', len(temp['Workspace']['SampleList']['Sample']))

#     for s in temp['Workspace']['SampleList']['Sample']: 
#         sample_information = {}
#         keywords_df = pd.DataFrame(s['Keywords']['Keyword'])
#         keywords_df = keywords_df.replace('', None).dropna(subset=['value'])
#         keywords_df['value'] = keywords_df['value'].str.strip()
#         keywords_df['name'] = keywords_df['name'].str.strip('$').str.lower()

#         main_kw_df = keywords_df[keywords_df['name'].isin(keys)]
#         main_kw_df = main_kw_df.set_index('name')
#         sample_information['main'] = main_kw_df.T
        
#         reagents_df = keywords_df[keywords_df['name'].str.contains(r"p[0-9]{1,}N", regex=True, flags=re.IGNORECASE)].copy()

#         anti_pattern = "^(?!SS|FS|Time).*" # remove basic channels
#         reagents_df = reagents_df[reagents_df['value'].str.contains(anti_pattern)]
#         reagents_df = reagents_df.sort_values(by = ['name'])

#         # display(reagents_df)

#         reagents_df = pd.DataFrame({'Reagent Name':reagents_df['value']}).reset_index(drop=True)
#         for c in reagent_cols: 
#             if c not in reagents_df.columns: 
#                 reagents_df[c] = ''

#         reagents_df = reagents_df[reagent_cols]
#         reagents_df['File Name'] = main_kw_df.loc['fil'].value
#         reagents_df['File Path'] = row['file_path']
        
#         if len(reagents_df) > 0: 
#             sample_information['reagents'] = reagents_df
        
#         files_information[main_kw_df.loc['fil'].value] = sample_information
        
#     reagents_list = []
#     flow_exp_list = []
    
#     for k,v in files_information.items():
#         try: 
#             reagents_list.append(v['reagents'])
#         except Exception as e:
#             # print(name)
#             pass
            
#         try: 
#             flow_exp_list.append(v['main'])
#         except Exception as e: 
#             print(e)
#             pass
    
#     if len(reagents_list) == 0: 
#         reagents_df_final = pd.DataFrame()
#         reagent_mapper = pd.DataFrame()
#     else:     
#         reagents_df_final = pd.concat(reagents_list)
#         # reagents_df_final = reagents_df_final.drop(columns=['File Name'])
#         reagents_df_final = reagents_df_final.drop_duplicates().sort_values(by = 'Reagent Name')
#         reagent_mapper = reagents_df_final.groupby('File Name').agg(unique_list)

#     flow_experiment_df = pd.concat(flow_exp_list)
#     flow_experiment_df = flow_experiment_df.rename(columns={'fil': 'File Name'})
