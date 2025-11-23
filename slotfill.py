from sklearn.model_selection import train_test_split
import sklearn_crfsuite
from sklearn_crfsuite import metrics
from token_feature import sent2features
import pickle


def load_custom_conll(file_path):
    sentences = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # skip empty lines

            splits = line.split()  # split by spaces
            sentence = []

            # Each token has a word and a label, so step=2
            for i in range(0, len(splits), 2):
                token = splits[i]
                label = splits[i + 1]
                sentence.append((token, label))

            sentences.append(sentence)

    return sentences


file_path = r"slot_filling_train.conll"  # your file
sentences = load_custom_conll(file_path)

# Check first sentence
# print(sentences[0])



train_sents, test_sents = train_test_split(sentences, test_size=0.3, random_state=42)

# print(len(train_sents))
# print(len(test_sents))


    
# Prepare features and labels
X_train = [sent2features(s) for s in train_sents]
y_train = [[label for token, label in s] for s in train_sents]

X_test = [sent2features(s) for s in test_sents]
y_test = [[label for token, label in s] for s in test_sents]



# Create and train CRF model
crf = sklearn_crfsuite.CRF(
    algorithm='lbfgs',
    c1=0.1,
    c2=0.1,
    max_iterations=100,
    all_possible_transitions=True
)

crf.fit(X_train, y_train)


# Evaluate the model
y_pred = crf.predict(X_test)

print(metrics.flat_classification_report(
    y_test, y_pred, labels=crf.classes_, digits=2
))




# tokens = ["Remind", "me", "to", "pay", "my", "electricity", "bill", "tomorrow"]
# features = sent2features([(t, 'O') for t in tokens])
# pred = crf.predict([features])[0]
# result = list(zip(tokens, pred))
# print(result)

#saving the model
with open("slot_filling_crf_model.pkl", "wb") as f:
    pickle.dump(crf, f)
