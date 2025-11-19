import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
from sklearn.utils import shuffle

# Load CSV
df = pd.read_csv("intent_data.csv")
# print(df.head())

label_counts = df['intent'].value_counts()
print(label_counts)


# print(df.isnull().sum())

df['intent'] = df['intent'].fillna("check_balance")
# print(df.isnull().sum())

df1 = shuffle(df, random_state=42)
X = df1["text"]
y = df1["intent"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,random_state=42)

# print(X_train.shape, X_test.shape)

tfidf = TfidfVectorizer(ngram_range=(1,2))  # unigrams + bigrams
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)


model = LogisticRegression(max_iter=200)
model.fit(X_train_tfidf, y_train)

y_pred = model.predict(X_test_tfidf)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))




input_text = "tell me my current credit score"
input_tfidf = tfidf.transform([input_text])
predicted_intent = model.predict(input_tfidf)[0]
print(f"Predicted Intent: {predicted_intent}")



# Save the model and vectorizer
joblib.dump(model, "intent_model.pkl")
joblib.dump(tfidf, "tfidf_vectorizer.pkl")