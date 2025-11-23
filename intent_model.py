import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
from sklearn.utils import shuffle
import os

# Load CSV
try:
    df = pd.read_csv("intent_data.csv")
except FileNotFoundError:
    print("❌ ERROR: 'intent_data.csv' not found. Please ensure it is in the same directory.")
    exit()

print("Initial Intent Counts:")
label_counts = df['intent'].value_counts()
print(label_counts)


# Handle missing values (if any)
df['intent'] = df['intent'].fillna("check_balance")

df1 = shuffle(df, random_state=42)
X = df1["text"]
y = df1["intent"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,random_state=42)

print(f"\nTraining on {len(X_train)} samples...")

# TF-IDF Vectorizer
tfidf = TfidfVectorizer(ngram_range=(1,2))  # unigrams + bigrams
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)


# Model Training
model = LogisticRegression(max_iter=200)
model.fit(X_train_tfidf, y_train)

y_pred = model.predict(X_test_tfidf)
print(f"\nModel Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print("Classification Report:\n", classification_report(y_test, y_pred, zero_division=0))


# Save the model and vectorizer
if not os.path.exists('models'):
    os.makedirs('models')
joblib.dump(model, "intent_model.pkl")
joblib.dump(tfidf, "tfidf_vectorizer.pkl")

print("\n✅ Intent Model and TFIDF Vectorizer saved successfully.")