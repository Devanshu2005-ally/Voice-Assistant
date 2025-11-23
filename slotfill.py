from sklearn.model_selection import train_test_split
import sklearn_crfsuite
from sklearn_crfsuite import metrics
from feature import sent2features
import pickle
import os
import nltk
from nltk.tokenize import word_tokenize # Added for explicit tokenization if needed later
import sys

# Ensure necessary NLTK data is downloaded for POS tagging
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("⏳ Downloading NLTK resources for POS tagging...")
    try:
        nltk.download('averaged_perceptron_tagger')
        nltk.download('punkt')
        print("✅ NLTK resources downloaded.")
    except Exception as e:
        print(f"❌ ERROR downloading NLTK resources: {e}")
        sys.exit(1)


def load_custom_conll(file_path):
    sentences = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            current_sentence = []
            for line in f:
                line = line.strip()
                if not line:
                    if current_sentence:
                        sentences.append(current_sentence)
                        current_sentence = []
                    continue  # skip empty lines

                splits = line.split()  # split by spaces
                
                # Each token is expected to have a word and a label (two items)
                if len(splits) % 2 != 0:
                     print(f"Warning: Skipping malformed line in CONLL file: {line}")
                     continue
                
                sentence = []
                for i in range(0, len(splits), 2):
                    token = splits[i]
                    label = splits[i + 1]
                    # We store (token, label) here. POS tagging happens next.
                    sentence.append((token, label))

                sentences.append(sentence)
                
            # Handle the last sentence if file doesn't end with a newline
            if current_sentence:
                sentences.append(current_sentence)

    except FileNotFoundError:
        print(f"❌ ERROR: File '{file_path}' not found. Please ensure it is in the same directory.")
        exit()
    
    return sentences

# NEW: Function to add POS tags to the (token, label) sentence data
def transform_sentence(sents_with_labels):
    # 1. Extract tokens
    tokens = [token for token, label in sents_with_labels]
    
    # 2. Get POS tags (nltk.pos_tag returns a list of (token, postag))
    tagged_tokens = nltk.pos_tag(tokens)

    # 3. Combine (token, postag, label)
    transformed = []
    for (token, label), (tagged_token, postag) in zip(sents_with_labels, tagged_tokens):
        # We use the token/label from the raw data and the postag from NLTK
        transformed.append((token, postag, label))
    return transformed


file_path = r"slot_filling_train.conll"  # your file
raw_sentences = load_custom_conll(file_path)
print(f"Loaded {len(raw_sentences)} sentences for slot filling.")

if not raw_sentences:
    print("❌ ERROR: No sentences loaded. Cannot train Slot Filling model.")
    exit()

# NEW: Transform all raw sentences to include POS tags
sentences = [transform_sentence(s) for s in raw_sentences]
print("✅ POS tags generated for training data.")


train_sents, test_sents = train_test_split(sentences, test_size=0.3, random_state=42)

# Prepare features and labels
# CRITICAL FIX: sent2features expects a list of (word, postag), which is indices 0 and 1.
X_train = [sent2features([(w, p) for w, p, l in s]) for s in train_sents]
y_train = [[label for w, p, label in s] for s in train_sents]

X_test = [sent2features([(w, p) for w, p, l in s]) for s in test_sents]
y_test = [[label for w, p, label in s] for s in test_sents]


# Create and train CRF model
crf = sklearn_crfsuite.CRF(
    algorithm='lbfgs',
    c1=0.1,
    c2=0.1,
    max_iterations=100,
    all_possible_transitions=True
)

print("\n⏳ Training CRF model...")
crf.fit(X_train, y_train)
print("✅ CRF model training complete.")

# Evaluate
y_pred = crf.predict(X_test)
# The evaluation metrics may show a warning if some classes are not in the test set
print("\nEvaluation (F1 Score):\n", metrics.flat_classification_report(y_test, y_pred, zero_division=0))


# Save the model
if not os.path.exists('models'):
    os.makedirs('models')
with open("slot_filling_crf_model.pkl", "wb") as f:
    pickle.dump(crf, f)
    
print("\n✅ Slot Filling Model saved successfully.")