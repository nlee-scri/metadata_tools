from dotenv import dotenv_values
import requests
import zipfile
import pandas as pd
import json
from pathlib import Path
import re
from datatools.repositories import redcap
from glob import glob

config = dotenv_values(".env.secrets")

API_ENDPOINT_BASE_URL = "https://www.immport.org"
DATA_QUERY_URL = API_ENDPOINT_BASE_URL + "/data/query"
ASPERA_TOKEN_URL = API_ENDPOINT_BASE_URL + "/data/download/token"
IMMPORT_TOKEN_URL = "https://www.immport.org/auth/token"


def get_json_templates(immport_temp_dir: str, term:str): 
    # Load templates
    templates = glob(f"{immport_temp_dir}\\json-templates\\{term}")
    temp_names = [Path(t).stem for t in templates]
    # print(temp_names)

    temp_templates = []
    for t in templates:
        with open(t) as file:
            temp = json.load(file)
            temp['template'] = Path(t).stem
            temp_templates.append(temp)

    template_df = pd.DataFrame(temp_templates)
    
    try: 
        mappings = []
        term = term.strip('*')
        for r in template_df[template_df['template'].str.contains(term)].to_dict('records'): 
            mappings.append(redcap.template_col_mapper(r))

        template_df['mappings']=mappings
    except: 
        pass
    
    template_df['templateName'] = template_df['template'].str.split('.').apply(lambda x: '.'.join(x[1:]) if len(x) > 1 else x[0])
    
    template_df = template_df.set_index('templateName')
    template_df = template_df.drop(columns = ['$schema', 'title', 'type'])
    template_df.head()
    
    return template_df

def setup_json_file(templates_df: pd.DataFrame, template_name: str): 
    
    json_template = {}
    properties = templates_df.loc[template_name, 'properties']
    for k,v in properties.items(): 
        if isinstance(v, dict): 
            if 'enum' in v.keys(): 
                # print(k,v['enum'][0])
                json_template[k] = v['enum'][0]
            elif 'type' in v.keys(): 
                if v['type'] == 'array': 
                    if '$ref' in v['items']: 
                        ref_temp_name = v['items']['$ref'].split('.')[1] # assuming reference template name is the second value
                        # print(ref_temp_name)
                        # ref_temp = templates_df.loc[ref_temp_name, 'properties']
                        json_template[k] =[{k2:"" for k2 in templates_df.loc[ref_temp_name]['properties'].keys()}]
                    else: 
                        json_template[k] = [{k2:"" for k2 in templates_df.loc[template_name]['properties'].keys()}]
            else: 
                json_template[k] = ""
    print(json.dumps(json_template, indent=2))
    return json_template

class immport_queries():
    """
    A class to interact with the ImmPort API for querying and managing biological datasets.

    Attributes:
        base_url (str): The base URL for the ImmPort API.
        config (dict): Configuration dictionary containing API credentials.
        endpoints (dict): Dictionary of API endpoints.
        auth (str): Authentication token.
    """

    def __init__(self, config: dict):
        """
        Initializes the immport_queries class with the given configuration.

        Args:
            config (dict): Configuration dictionary containing API credentials.
        """
        self.base_url = "https://immport-upload.niaid.nih.gov:8443"
        self.config = config
        self.endpoints = {
            'base': "https://immport-upload.niaid.nih.gov:8443",
            'auth': "https://www.immport.org/auth/token",
        }
        self.workspace_id = '7349' # change if needed
        self.request_history = []
        self.upload_history = []
        self.ticket_report_history = {}
        self.get_auth()
        self.headers = {
            "Authorization": f"bearer {self.auth}"
        }

    def get_auth(self):
        """
        Authenticates with the ImmPort API and retrieves an access token.
        """
        url = "https://www.immport.org/auth/token"

        payload = {
            "username": self.config["username"],
            "password": self.config["password"]
        }

        response = requests.post(url, data=payload)

        if response.status_code == 200:
            print('Authentication successful')
            self.auth = response.json()['access_token']
        else:
            print('Authentication failed')
            raise Exception

    def get_request(self, endpoint: str):
        """
        Makes a GET request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint to send the request to.

        Returns:
            response: The response object from the GET request.
        """
        url = '/'.join([self.base_url, endpoint])
        headers = {
            "Authorization": f"bearer {self.auth}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            self.request_history.append(response)
            return response
        else:
            print('Error in getting response')
            raise Exception

    def get_workspaces(self) -> pd.DataFrame:
        """
        Retrieves the list of workspaces from the ImmPort API.

        Returns:
            pd.DataFrame: A DataFrame containing the workspace information.
        """
        endpoint = 'workspaces'

        response = self.get_request(endpoint)
        workspaces = pd.DataFrame(response.json()['workspaces'])
        print(workspaces.head())
        return workspaces

    def get_templates(self, workspace_id):
        """
        Downloads and extracts templates for the specified workspace.

        Args:
            workspace_id: The ID of the workspace to get templates for.
        """
        endpoint = f'data/upload/documentation/templates/{workspace_id}'

        response = self.get_request(endpoint)

        if response.status_code == 200:
            print('SUCCESS: Downloading workspace templates ...')
            with open("immport_templates.zip", "wb") as f:
                f.write(response.content)

            with zipfile.ZipFile("immport_templates.zip", "r") as zip_ref:
                zip_ref.extractall("immport_templates")
        else:
            print('FAIL: Could not get templates')
            
    def upload_file(self, file_path: str, package_name: str, upload_propose: str):
        """
        Uploads an Excel template file to the ImmPort server for validation or other purposes.

        Args:
            excel_template_path (str): The file path to the Excel template to be uploaded.
            package_name (str): The name of the package to be uploaded.
            uploadPurpose (str): The purpose of the upload (e.g., "validateData").

        Raises:
            Exception: If the upload request fails.

        Returns:
            str: ticket_id number for checking
        """
        if upload_propose not in ['validateData', 'uploadData']:
            raise ValueError('Upload purpose not valid')
        
        if package_name is None: 
            raise ValueError('Package name must be present')
        
        endpoint = "data/upload/type/online"
        url = f"{self.base_url}/{endpoint}"
        file_path = Path(file_path).resolve()
        
        if bool(re.search(r'.txt', file_path.suffix)): 
            output_path = file_path
        
        elif bool(re.search(r'.xl', file_path.suffix)): # excel files
            print('Converting file to txt file...')
            output_path = file_path.with_suffix('.txt')
            
            # Convert xlsx file to txt file for upload
            pd.read_excel(file_path).to_string(output_path, index=False)
        
        else: 
            output_path = file_path

        # Define the payload (multipart form data)
        payload = {
            "workspaceId": self.workspace_id,
            "packageName": package_name,
            "uploadNotes": "",
            "uploadPurpose": upload_propose,
            "serverName": "ai-biscdatamgtprd1.niaid.nih.gov",
            "file": "@\\"+str(Path(file_path))
        }

        # Define the file to upload
        with open(output_path, "rb") as file:
            files = {"file": file}
            
            # Make a POST request with multipart form data
            print(f"Uploading file: {file_path.name}")
            response = requests.post(url, headers=self.headers, data=payload, files=files)
            self.request_history.append(response)
        
        if response.status_code == 200:
            ticket = response.json()['uploadTicketNumber']
            print(response.content.decode("utf-8"))
            self.upload_history.append({'purpose': 'File Upload', 'response': response.json()})
            # self.validate_ticket(ticket)
            return ticket
        else:
            print('Upload failed')
            raise Exception

    def validate_ticket(self, ticket):
        print(f'Validating ticket: {ticket} ')
        endpoint = "data/upload/validation"
        url = f"{self.base_url}/{endpoint}"
        # print(url)

        # Define the payload (multipart form data)
        payload = {
            "workspaceId": self.workspace_id,
            "uploadTicketNumber": ticket
        }

        # Make a POST request with multipart form data
        response = requests.post(url, headers=self.headers, data=payload)
        self.request_history.append(response)
        return response

    def ticket_status(self, ticket):
        """
        Retrieves the status of a specified ticket.

        Args:
            ticket: The ticket ID to check the status for.

        Returns:
            dict: A dictionary containing the ticket status information.
        """
        endpoint = f"/data/upload/registration/{ticket}/status"
        response = self.get_request(endpoint)
        result = response.json()
        print(result)
        
        if result['status'] == 'Rejected_Validation': 
            print('Getting Report ...')
            ticket_report = self.ticket_database_report(ticket)
            print(ticket_report)
            return ticket_report
            
        return result
    
    def ticket_summary(self, ticket):
        """
        Retrieves the summary report for a specified ticket.

        Args:
            ticket: The ticket ID to get the summary for.

        Returns:
            list: A list of errors found in the ticket summary.
        """
        endpoint = f"/data/upload/registration/{ticket}/reports/summary"
        response = self.get_request(endpoint)
        result = json.loads(response.content.decode('utf-8'))
        
        errors = []
        for i in result['summary']['uploadRegistrationResults']: 
            if i['errorMessage'] is not None: 
                errors.append(i)
        if len(errors) == 0: 
            return result
        else: 
            return errors

    def ticket_database_report(self, ticket):
        """
        Retrieves the database report for a specified ticket.

        Args:
            ticket: The ticket ID to get the database report for.

        Returns:
            dict: A dictionary containing the database report information.
        """
        endpoint = f"/data/upload/registration/{ticket}/reports/database"
        response = self.get_request(endpoint)
        result = response.json()
        self.ticket_report_history[ticket] = result
        
        try: 
            result_df = pd.DataFrame([r.split('\t') for r in result['database'].split('\n')[4:-2]])
            result_df.columns = list(result_df.loc[0,:])
            result_df = result_df.loc[1:, :]
            result['database_report_df'] = result_df
            report = result['database_report_df']
            with pd.option_context('display.max_colwidth', None): 
                print(report[report['Status'] == 'Error'][['Error Message', 'Description']])
        except: 
            print('Error')
        finally: 
            return result

    def validate_file(self, file_path, package_name): 
        ## Validate the template
        ticket = self.upload_file(file_path = file_path, package_name=package_name, upload_propose='validateData')
        validation = self.validate_ticket(ticket)
        
        print(validation.json()['status'])

        if validation.json()['status'] == 'Rejected_Validation': 
            print('Error in File. Getting Report ...')
            ticket_report = self.ticket_database_report(ticket)
            report = ticket_report["database_report_df"]
            md = report[report["Status"] == "Error"].to_markdown(index=False)
            report_path = Path(f'./validation_report_{Path(file_path).stem}.txt')
            print(f"Writing file to {report_path.resolve()}")
            with open(report_path, 'w') as file: 
                file.write(md)
        if validation.json()['status'] == 'Completed_Validation':
            return 'Completed Validation'
        else: 
            return validation.json()
        
        
# Work in progress -----------
# # url = '/'.join([base_url, endpoint])
# auth = immport_worker.auth
# study_id = "SDY2833"
# endpoint = "summary"
# url = f"https://www.immport.org/data/query/api/study/{endpoint}/{study_id}"

# headers = {
#     "Authorization": f"bearer {auth}", 
#     'Content-Type': 'application/json'
# }

# params = {
#     "format": "json"
# }

# response = requests.get(url, headers=headers, params=params)

# if response.status_code == 200:
#     # self.request_history.append(response)
#     # print(response.json())
#     print(json.dumps(response.json(), indent=4))
# else:
#     print('Error in getting response')
#     print(response.status_code)
#     print(response.json())