# Automate screenshot capture

## File format

|client_name|farm_name|field_name|org_id|field_id|cycle_id|
|---|---|---|---|---|---|
|client 1|farm 1|field2|1234|34222322|23323287|

## Usage
1. Create a `.env` file as follows:
```
USERNAME=email@farm.ag
PASSWORD="******"
```

2. Run the login script:
```
$ python login.py
```
Produces `storage_state.json`

3. Run the script:
```
$ python screenshot --input data/fields.csv
```
Produces screenshots for each row in the CSV file.