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



model = LogisticRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
# print(classification_report(y_test, y_pred))


text = 'transfer 500 rupees to Rahul'
vec = vectorizer.transform([text])
    
probs = model.predict_proba(vec)
max_prob = probs.max()
   

if max_prob < 0.2:
    print('please give correct input')

else:
    pred = probs[0].argmax()
    print(encoder.inverse_transform([pred])[0])