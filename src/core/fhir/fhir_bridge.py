#import requests
from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.observation import Observation
from fhirclient.models.encounter import Encounter
import json


fhir_server_url = 'https://server.fire.ly/'
settings = {
        'app_id': 'ampere_app',
        'api_base': fhir_server_url
    }
smart = client.FHIRClient(settings=settings)

def get_patient_entries(patient_name):
    # Search for the patient by name
    search = Patient.where(struct={'name': patient_name})
    patients = search.perform_resources(smart.server)
    
    # List to store all entries
    all_entries = []

    for patient in patients:
        # Assuming each patient has an id
        patient_id = patient.id

        # You can add logic here to query different types of resources
        # related to the patient using patient_id. For example, to get
        # Observations, Medications, etc. You'll need to use appropriate
        # models like Observation, MedicationRequest etc.

        all_entries.append(patient.as_json())

    return all_entries


def list_patients_by_birth_year(birth_year):
    # Search for patients by birth year
    # The birthDate format is "YYYY", "YYYY-MM", or "YYYY-MM-DD"
    search = Patient.where(struct={'birthdate': birth_year})
    patients = search.perform_resources(smart.server)

    # List to store patient information
    patient_list = []

    for patient in patients:
        # Extract patient details, modify as needed
        if patient.name and len(patient.name) > 0:
            first_name = patient.name[0]
            full_name = ' '.join(first_name.given) + ' ' + first_name.family if first_name.given and first_name.family else 'Unknown'
        else:
            full_name = 'Unknown'

        patient_info = {
            'id': patient.id,
            'name': full_name,
            'birthDate': patient.birthDate.isostring if patient.birthDate else 'Unknown'
        }
        patient_list.append(patient_info)

    return patient_list

def get_patient_observations(patient_id):
    # Query for Observations related to the patient
    search = Observation.where(struct={'subject': f"Patient/{patient_id}"})
    observations = search.perform_resources(smart.server)

    observation_list = [obs.as_json() for obs in observations]
    return observation_list


def get_patient_encounters(patient_id):
    # Query for Encounters related to the patient
    search = Encounter.where(struct={'subject': f"Patient/{patient_id}"})
    encounters = search.perform_resources(smart.server)

    encounter_list = [enc.as_json() for enc in encounters]
    return encounter_list



def test_patient_encounters():
    # Example usage
    patient_id = '22e112d1-261d-4fb4-b680-32d21ea9c334'
    encounter_list = get_patient_encounters(patient_id)
    print(encounter_list)
    with open('./encounter_list.txt', 'w') as f:
        json.dump(encounter_list, f, indent=4)

def test_get_patient_observations():
    # Example usage
    patient_id = '22e112d1-261d-4fb4-b680-32d21ea9c334'
    observation_list = get_patient_observations(patient_id)
    print(observation_list)
    with open('./observation_list.txt', 'w') as f:
        json.dump(observation_list, f, indent=4)

def test_find_patient_entries():
    # Example usage
    patient_name = 'Doe, John'
    patient_entries = get_patient_entries(patient_name)
    print(patient_entries)
    with open('./patient_entries.txt', 'w') as f:
        json.dump(patient_entries, f, indent=4)

def test_list_patients_by_birth_year():
    # Example usage
    birth_year = '1994'
    patient_list = list_patients_by_birth_year(birth_year)
    print(patient_list)
    with open('./patient_list.txt', 'w') as f:
        json.dump(patient_list, f, indent=4)

def test_patients_observations_encounters_by_birth_year():
    birth_year = '1994'
    patients = list_patients_by_birth_year(birth_year)

    # Dictionary to hold patient ID and their observations & encounters
    patient_data = {}

    for patient in patients:
        patient_id = patient['id']
        observations = get_patient_observations(patient_id)
        encounters = get_patient_encounters(patient_id)

        patient_data[patient_id] = {
            'observations': observations,
            'encounters': encounters
        }

    # Write to JSON file
    with open('./patients_observations_encounters.json', 'w') as f:
        json.dump(patient_data, f, indent=4)

    print(f"Data saved for patients born in {birth_year}.")


if __name__ == '__main__':
    #test_find_patient_entries()
    test_list_patients_by_birth_year()
    #test_get_patient_observations()
    #test_patient_encounters()
    #test_patients_observations_encounters_by_birth_year()