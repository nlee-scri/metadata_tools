import time
import pandas as pd
from tqdm import tqdm
import re
import requests
from bs4 import BeautifulSoup
from datatools.pubmed import esummary

biosample_fields = [
    "biosample_id",
    "biosample_subject_id",
    "biosample_type",
    "biosample_subtype",
    "biosample_species",
    "biosample_description",
    "biosample_study_time_collected",
    "biosample_study_time_collected_unit",
    "biosample_study_time_t0_event",
    "biosample_study_time_t0_event_specify",
    "biosample_2_treatment_treatment_ids",
    "biosample_comments",
]


def find_value_in_table(html, target_value: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        for cell in cells:
            if cell.text.strip() == target_value:
                # print(f'Found value: {target_value}')
                return str(cell.parent.parent)
    return None


def get_table_values(html_text: str):
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find_all("tr")
    full_table = {}
    for i, _ in enumerate(table):
        try:
            temp = [str(t) for t in table[i].find_all("td")]
            if temp[1] != "":
                full_table[temp[0]] = temp[1]
        except Exception as e:
            pass
    return full_table


def get_sample_page(gsm_id: str):
    response = requests.get(
        url=f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={gsm_id}",  # using GSM - samples
    )
    html_text = response.text
    target_value = "Title"
    found_value = find_value_in_table(html_text, target_value)

    full_table = get_table_values(found_value)
    full_table = {
        BeautifulSoup(k, "html.parser").get_text(): v for k, v in full_table.items()
    }

    main_keys_samples = [
        "Title",
        "Sample type",
        "tissue",
        "Organism",
        "Description",
        "cell type",
        "genotype",
        "treatment" "Description",
        "BioSample" "Characteristics",
    ]

    main_keys_protocols = [
        "Status",
        "Extracted molecule",
        "Extraction protocol",
        "Library strategy",
        "Library source",
        "Library selection",
        "Instrument model",
        "Data processing",
    ]

    main_keys = main_keys_samples + main_keys_protocols
    reduced = {
        k: v
        for k, v in full_table.items()
        if k.lower() in [m.lower() for m in main_keys]
    }
    characteristics = reduced.pop("Characteristics", None)
    reduced = {
        k: BeautifulSoup(v, "html.parser").get_text() for k, v in reduced.items()
    }  # remove html tags

    if characteristics is not None:
        try:  # get characteristics
            test = [
                BeautifulSoup(k, "html.parser").get_text().split(":")
                for k in characteristics.split("<br/>")
            ]
            test = [[t2.strip() for t2 in t] for t in test if len(t) > 1]
            reduced = reduced | dict(test)
            reduced["Accession"] = gsm_id
            return reduced
        except Exception as e:
            print(e)
            raise Exception
        finally:
            return reduced
    else:
        return reduced


def get_samples(gds_id: str) -> pd.DataFrame:
    """Get the summary for a GEO dataset"""
    dataset_summary = esummary("gds", gds_id)[
        0
    ]  # using the ID gives more useful information
    # json.loads(json.dumps(dataset_summary)) # just for view

    samples = dataset_summary["Samples"]
    samples_df = pd.DataFrame(samples)

    print(f"Number of samples in {gds_id}: {len(samples_df)}")

    return samples_df


def get_sample_pages(samples_df: str):
    sample_pages = []
    for acc_id in tqdm(
        samples_df["Accession"], desc="Getting sample pages...", leave=False
    ):
        try:
            sample_pages.append(get_sample_page(gsm_id=acc_id))
            time.sleep(3)
        except Exception as e:
            print(acc_id, e)

    sample_pages_df = pd.DataFrame(sample_pages)
    print(sample_pages_df.head())
    return sample_pages_df, sample_pages


def process_sample_pages(sample_pages_df):
    mapper = {
        "Title": "biosample_id",
        "tissue": "biosample_type",
        "Organism": "biosample_species",
        "Description": "biosample_description",
        "treatment": "biosample_2_treatment_treatment_ids",
        # 'Accession': 'biosample_comments',
    }

    main_keys_protocols = [
        "Extraction molecule",
        "Extraction protocol",
        "Library strategy",
        "Library source",
        "Library selection",
        "Instrument model",
        "Data processing",
    ]
    sample_pages_df = sample_pages_df.rename(columns=mapper, errors="ignore")

    # protocol_cols = list(set(sample_pages_df.columns) & set(main_keys_protocols))
    sample_pages_df = sample_pages_df.drop(columns=main_keys_protocols, errors="ignore")
    # keep extra information as comments
    sample_pages_df["biosample_comments"] = sample_pages_df[
        [c for c in sample_pages_df.columns if c not in biosample_fields]
    ].to_dict("records")
    sample_pages_df["biosample_comments"] = (
        sample_pages_df["biosample_comments"]
        .astype("str")
        .apply(lambda x: re.sub(r"{|}", "", x))
    )
    sample_pages_df = sample_pages_df.drop(
        columns=[c for c in sample_pages_df.columns if c not in biosample_fields],
        errors="ignore",
    )

    return sample_pages_df


def get_bioproject(bid: str):
    """To get metadata from bioproject"""
    new_record = {}
    proj_sum = esummary("bioproject", bid)["DocumentSummarySet"]["DocumentSummary"][0]

    mapping = {
        "Project_Name": "study_brief_title",
        "Project_Title": "study_official_title",
        "Project_Description": "study_description",
        "Project_Description": "study_brief_description",
        "Organism_Name": "biosample_species",
        "Organism_Strain": "Species_strain",
        "Submitter_Organization": "study_sponsoring_organization",
        "Project_Acc": "public_repository_accession_id",
    }

    for k, v in mapping.items():
        if proj_sum[k] != "" and v != "":
            new_record[v] = proj_sum[k]
            # print(k, proj_sum[k])

    comments = []

    for k, v in proj_sum.items():
        if v != "" and v is not None and k not in list(mapping.keys()):
            comments.append(f"{k}:{v}")

    new_record["study_comments"] = ",".join(comments)

    print(new_record)

    return new_record, proj_sum


def get_protocols(sample_pages):
    # protocols
    main_keys_protocols = [
        "Extraction molecule",
        "Extraction protocol",
        "Library strategy",
        "Library source",
        "Library selection",
        "Instrument model",
        "Data processing",
    ]

    sample_pages_df = pd.DataFrame(sample_pages)
    # protocol_cols = list(set(sample_pages_df.columns) & set(main_keys_protocols))
    protocols_df = sample_pages_df[
        list(set(sample_pages_df.columns) & set(main_keys_protocols))
    ].drop_duplicates()

    print("Sample pages df shape: ", sample_pages_df.shape)
    protocols = []
    for x in protocols_df.to_dict("records"):
        for k, v in x.items():
            protocols.append({"protocol_name": k, "protocol_description": v})

    return protocols
