import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
import keras
from keras import layers
import matplotlib.pyplot as plt


load_dotenv()

conn = mysql.connector.connect(
    host="localhost",      
    user="root",          
    password=os.getenv("DB_PASSWORD"),
    database="computer_database"
)
cursor = conn.cursor()

query = "SELECT * FROM laptops"
data = pd.read_sql(query, con=conn)

data.drop('id', axis=1, inplace=True)
label = data['price']
data.drop('price', axis=1, inplace=True)

data['storage'] = data['storage'].str[:-9].astype(int)
data[['width', 'height']] = data['screen_resolution'].str.split('x', expand=True).astype('int64')
data['total_screen_pixels'] = data['width'] * data['height']

data.drop(['width', 'height', 'screen_resolution'], axis=1, inplace=True)

data['storage'] = data['storage'].astype('int64')
data['ram'] = data['ram'].astype('int64')

numerical_columns = data.select_dtypes(include=['int64', 'float64']).columns
scaler = MinMaxScaler()

data[numerical_columns] = scaler.fit_transform(data[numerical_columns])

columns_to_encode = ['cpu', 'storage_type', 'graphics', 'operating_system', 'company']

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

encoded_data = encoder.fit_transform(data[columns_to_encode])
encoded_df = pd.DataFrame(encoded_data, columns=encoder.get_feature_names_out(columns_to_encode))
data = pd.concat([data, encoded_df], axis=1).drop(columns=columns_to_encode)

print(data.head())

model = keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=(data.shape[1],)),
    layers.Dense(32, activation='relu'),
    layers.Dense(1)
])

model.compile(optimizer='adam', loss='mean_squared_error')

history = model.fit(data, label, epochs=10, batch_size=2)

plt.plot(history.history['loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()