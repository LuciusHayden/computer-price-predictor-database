import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PowerTransformer, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import BayesianRidge
import joblib

def create_model():
    data = pd.read_csv('laptop_price.csv', encoding='iso-8859-15')

    data.drop('Product', axis=1, inplace=True)
    data.drop('TypeName', axis=1, inplace=True)
    data.drop('laptop_ID', axis=1, inplace=True)

    data['Resolution'] = data['ScreenResolution'].apply(lambda x : x[-10:])
    data.drop('ScreenResolution', axis=1, inplace=True)

    data['Ram']= data['Ram'].str.replace('GB', '')
    data['Ram']= data['Ram'].astype(int)

    data['Weight']= data['Weight'].str.replace('kg', '')
    data['Weight']= data['Weight'].astype(float)

    X= data.drop('Price_euros', axis=1)
    Y= data['Price_euros']

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
    print(X_test[:5])
    print(data.head(10))

    numeric_features = X.select_dtypes(exclude='object').columns
    categorical_features = X.select_dtypes(include='object').columns

    numeric_transformer = Pipeline([
        ('power_transformer', PowerTransformer()),
    ])

    string_transformer = Pipeline([
        ('one_hot_encoder', OneHotEncoder(handle_unknown='ignore', drop='first', sparse_output=False))
    ])

    preproccesor = ColumnTransformer([
        ("numeric_transformer", numeric_transformer, numeric_features),
        ("string_transformer", string_transformer, categorical_features)
    ])

    model = BayesianRidge()

    pipe = Pipeline([
        ('preproccesor', preproccesor),
        ('model', model)
    ])

    pipe.fit(X_train, Y_train)

    Y_pred = pipe.predict(X_test)

    print('Mean Absolute Error:', mean_absolute_error(Y_test, Y_pred))
    print('Mean Squared Error:', mean_squared_error(Y_test, Y_pred))
    print('R^2:', r2_score(Y_test, Y_pred))
    
    for col in categorical_features:
        print(f"Unique categories in {col}:", X_train[col].unique())


    joblib.dump(pipe, 'model.joblib')

    return pipe
