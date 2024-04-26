import csv
import requests
from datetime import datetime

def oczysc_nip(nip):
    return nip.replace('-', '').zfill(10)

def pobierz_dane_firmy(nip):
    cleaned_nip = oczysc_nip(nip)
    data = datetime.now().strftime('%Y-%m-%d')
    url = f"https://wl-api.mf.gov.pl/api/search/nip/{cleaned_nip}?date={data}"
    response = requests.get(url)
    
    if response.status_code == 200 and response.json().get('result'):
        response_data = response.json()['result'].get('subject')
        if not response_data:
            return 'skip_row'
        
        registration_legal_date = response_data.get('registrationLegalDate', "Brak")
        if registration_legal_date != "Brak":
            try:
                formatted_registration_date = datetime.strptime(registration_legal_date, '%Y-%m-%d').strftime('%Y-%m-%d')
                registration_legal_date = formatted_registration_date
            except ValueError:
                pass  # Keep the original date if it's in an unexpected format

        krs_number = response_data.get('krs')
        if krs_number and krs_number.isdigit():  # Ensure it's a string of digits
            krs_number = krs_number.zfill(10)  # Pad with zeros to ensure length is 10
        else:
            krs_number = "Brak informacji"

        output = {
            'Nazwa': response_data.get('name', "Brak informacji"),
            'Adres': response_data.get('residenceAddress') or response_data.get('workingAddress', "Brak informacji"),
            'KRS': krs_number,
            'REGON': response_data.get('regon', "Brak informacji"),
            'Data utworzenia': registration_legal_date,
        }
        return output
    else:
        return 'skip_row'

# Specify the file path for your CSV file
input_file_path = 'file.csv'
output_file_path = 'u_file.csv'

with open(input_file_path, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    companies_data = list(reader)

nip_seen = set()
updated_companies_data = []

for company in companies_data:
    nip = company['NIP']
    if nip not in nip_seen:
        api_response = pobierz_dane_firmy(nip)
        nip_seen.add(nip)
        if api_response != 'skip_row':
            company.update(api_response)
            updated_companies_data.append(company)
    # Jeśli NIP jest już w zbiorze, pomijamy ten wiersz (duplikat)

with open(output_file_path, mode='w', newline='', encoding='utf-8') as file:
    fieldnames = reader.fieldnames + ['Właściciel2']  # Add the new column name to the fieldnames
    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    for company in updated_companies_data:
        company['Właściciel2'] = company['Właściciel']  # Duplicate the value from "Właściciel"
        writer.writerow(company)

print(f"Updated CSV file with duplicated column 'Właściciel2' has been saved to {output_file_path}.")
