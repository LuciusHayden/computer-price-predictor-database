import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
import keras
from keras import layers
import matplotlib.pyplot as plt
from sklearn.preprocessing import RobustScaler
import numpy as np
import random

load_dotenv()

def create_model():
    conn = mysql.connector.connect(
        host="localhost",      
        user="root",          
        password=os.getenv("DB_PASSWORD"),
        database="computer_database"
    )

    np.random.seed(42)
    random.seed(42)
    tf.random.set_seed(42)

    query = "SELECT * FROM laptops"
    data = pd.read_sql(query, con=conn)

    data.drop('id', axis=1, inplace=True)
    data.drop('company', axis=1, inplace=True)

    data['storage'] = data['storage'].str[:-9].astype(int)
    data[['width', 'height']] = data['screen_resolution'].str.split('x', expand=True).astype('int64')
    data['total_screen_pixels'] = data['width'] * data['height']

    data.drop(['width', 'height', 'screen_resolution'], axis=1, inplace=True)

    data['storage'] = data['storage'].astype('int64')
    data['ram'] = data['ram'].astype('int64')

    # plt.figure(figsize=(8, 5))
    # plt.hist(data['price'], bins=30, color='skyblue', edgecolor='black')
    # plt.title('Price Distribution')
    # plt.xlabel('Price')
    # plt.ylabel('Frequency')
    # plt.show()

    label = data['price']
    data.drop('price', axis=1, inplace=True)
   
    numerical_columns = data.select_dtypes(include=['int64', 'float64']).columns
    scaler = MinMaxScaler()
    # scaler = RobustScaler()

    data[numerical_columns] = scaler.fit_transform(data[numerical_columns])

    label = label.values.reshape(-1, 1)
    scaler_target = MinMaxScaler(feature_range=(0, 100))
    label = scaler_target.fit_transform(label)

    columns_to_encode = ['cpu', 'storage_type', 'graphics', 'operating_system']

    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    
    encoded_data = encoder.fit_transform(data[columns_to_encode])
    encoded_df = pd.DataFrame(encoded_data, columns=encoder.get_feature_names_out(columns_to_encode))
    data = pd.concat([data, encoded_df], axis=1).drop(columns=columns_to_encode)
    
    print(data.head())
    print(label[:5])
    x_train, x_test, y_train, y_test = train_test_split(data, label, test_size=0.05, random_state=42)

    model = keras.Sequential([
        layers.Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001), input_shape=(data.shape[1],)),
        layers.Dense(128, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(32, activation='relu'),
        layers.Dense(1)
    ])  

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mean_squared_error', metrics=['mse'])

    history = model.fit(x_train, y_train, epochs=10, batch_size=20, validation_split=0.3)

    predictions = model.predict(x_test[:5])
    print(scaler_target.inverse_transform(y_test[:5]))
    print(scaler_target.inverse_transform(predictions))

    # uncomment to graph
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['mse'], label='Training MSE')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.plot(history.history['val_mse'], label='Validation MSE')
    plt.title('Model Performance')
    plt.ylabel('Value')
    plt.xlabel('Epoch')
    plt.legend(['Train loss', 'Train MSE', 'Validation loss', 'Validation MSE'], loc='upper left')
    plt.show()

    return model

create_model()