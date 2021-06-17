import numpy as np
import pandas as pd
import subprocess

from utils.transport import transport_to_groups
from utils.health_status import injury_to_severity_driver, \
        injury_to_severity_pedestrian
from utils.violations import violation_encoding_driver, \
        violation_encoding_pedestrian
from utils.nearby import property2cat


def cat2binary(df):
    """
    Applies one-hot-encoding for selected column.

    df: pd.DataFrame
    return:
          matrix -- encoding
          cat2idx.keys() -- keys of dict
    """

    df_size = df.shape[0]

    unique = set()
    for i in range(df_size):
        row = df.iloc[i]
        for item in row:
            unique.add(item)

    unique_size = len(unique)
    cat2idx = {key: idx for idx, key in enumerate(unique)}
    matrix = np.zeros((df_size, unique_size), dtype=np.int8)

    for i in range(df_size):
        arr = df.iloc[i]
        for word in arr:
            idx = cat2idx[word]
            matrix[i, idx] = 1
    return matrix, cat2idx.keys()


def get_gender_of_driver(x):
    hs = []
    for car in x:
        driver_g = car['participants'][0]['gender']
        hs.append(driver_g)
    return hs


def get_p(x):
    x = np.array(x)
    if len(x):
        p = len(x[x == 'Женский']) / len(x)
        return np.float32(p)
    return np.NAN


def apply_transformations(data_moscow):
    data_moscow['vehicles'] = data_moscow['properties.vehicles'] \
        .apply(
            lambda x: [transport_to_groups[car['category']] for car in x]
        )  # list of vehicles which were involved in an accident

    data_moscow['vehicle_violations'] = data_moscow['properties.vehicles'] \
        .apply(
            lambda x: [violation_encoding_driver[v]
                       for car in x
                       for person in car['participants']
                       for v in person['violations']
                       if person['violations']]
        )  # list of violations made by participants

    data_moscow['health_status_drivers'] = data_moscow['properties.vehicles'] \
        .apply(
            lambda x: [injury_to_severity_driver[person['health_status']]
                       for car in x for person in car['participants']
                       if person['health_status']]
        )  # list of injuries/health issues in an accident

    data_moscow['experience'] = data_moscow['properties.vehicles'] \
        .apply(
            lambda x: [participant['years_of_driving_experience']
                       if participant['years_of_driving_experience']
                       else 0 for car in x
                       for participant in car['participants']
                       if participant['role'] == 'Водитель']
        )  # all driver participants driving experience

    data_moscow['nearby_objects'] = data_moscow['properties.nearby'] \
        .apply(lambda x: [property2cat[obj] for obj in x])

    data_moscow['pedestrian_violations'] = data_moscow['properties.participants'] \
        .apply(
            lambda x: [violation_encoding_pedestrian[v]
                       for person in x
                       for v in person['violations']]
        )

    data_moscow['health_status_pedestrians'] = data_moscow['properties.participants'] \
        .apply(
            lambda x: [injury_to_severity_pedestrian[person['health_status']]
                       for person in x
                       if person['health_status']]
        )

    data_moscow['Driver_gender'] = data_moscow['properties.vehicles'] \
        .apply(lambda x: get_gender_of_driver(x))

    data_moscow['w_percent'] = data_moscow['Driver_gender'] \
        .apply(lambda x: get_p(x))

    return data_moscow


def encode_and_merge_columns(data_moscow):
    columns2encode = ['properties.weather',
                      'properties.road_conditions',
                      'vehicles', 'vehicle_violations',
                      'health_status_drivers',
                      'nearby_objects', 'pedestrian_violations',
                      'health_status_pedestrians']
    data2merge = [data_moscow]  # list of dataframes
    for c in columns2encode:
        tmp_m, tmp_d = cat2binary(data_moscow[c])
        tmp_df = pd.DataFrame(tmp_m, columns=tmp_d)
        data2merge.append(tmp_df)

    clean_data = pd.concat(data2merge, axis=1)
    clean_data.drop(columns2encode, axis=1, inplace=True)

    return clean_data


def delete_columns(data_moscow):
    del data_moscow['Driver_gender']
    del data_moscow['type']
    del data_moscow['geometry.type']
    del data_moscow['properties.id']
    del data_moscow['properties.tags']
    del data_moscow['geometry.coordinates']
    del data_moscow['properties.address']
    del data_moscow['properties.parent_region']
    del data_moscow['properties.participant_categories']
    del data_moscow['properties.vehicles']
    del data_moscow['properties.participants']
    del data_moscow['properties.nearby']
    return data_moscow


def download_and_preprocess_data():
    subprocess.run(['sh', './check_if_data_is_downloaded.sh'])

    path_moscow = "./data/moskva.geojson"
    data_moscow = pd.read_json(path_moscow)
    data_moscow = pd.json_normalize(data_moscow.features)
    data_moscow = apply_transformations(data_moscow)
    data_moscow = delete_columns(data_moscow)
    clean_data = encode_and_merge_columns(data_moscow)

    clean_data.rename(
        columns={
            "properties.light": 'lighting',
            "properties.point.lat": 'lat',
            "properties.point.long": 'long',
            "properties.region": 'region',
            'properties.severity': 'severity',
            'properties.dead_count': 'dead',
            'properties.injured_count': 'injured',
            'properties.participants_count': 'n_participants',
            'experience': 'dr_exp',
            'w_percent': 'w_percent',
            'properties.category': 'category',
            'properties.datetime': 'date'},
        inplace=True
    )

    clean_data = clean_data[
        (clean_data['long'] < 37.9545100)
        & (clean_data['long'] > 37.1813900)
        & (clean_data['lat'] < 55.9825000)
        & (clean_data['lat'] > 55.1339600)
    ]
    
    filename = "clean_data_MSK.csv"
    clean_data.to_csv(filename, sep=':', index=False)
    print("Done! Preprocessed data is saved in {name}".format(name=filename))

if __name__ == "__main__":
    download_and_preprocess_data()
