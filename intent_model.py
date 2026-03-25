import numpy as np  
import pandas as pd 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle



df = pd.read_csv('intent_data.csv')
df.info()


text = df['text']
labels = df['intent']


encoder = LabelEncoder()
y = encoder.fit_transform(labels)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(text)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)



lg_model = LogisticRegression()
lg_model.fit(X_train, y_train)
y_pred = lg_model.predict(X_test)
# print(classification_report(y_test, y_pred))
# 


text = 'transfer 500 rupees to Rahul'
vec = vectorizer.transform([text])
    
pred = lg_model.predict(vec)
print(encoder.inverse_transform(pred)[0])
   




#saving the vectorizer model
with open('vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

#saving the lg model
with open('intent_model.pkl', 'wb') as f:
    pickle.dump(lg_model, f)