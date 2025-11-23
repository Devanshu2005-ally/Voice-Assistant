def token2features(sent, i):
    token = sent[i][0]  # token text
    features = {
        'word.lower()': token.lower(),
        'word.isupper()': token.isupper(),
        'word.istitle()': token.istitle(),
        'word.isdigit()': token.isdigit(),
    }
    # Previous token
    if i > 0:
        token1 = sent[i-1][0]
        features.update({
            '-1:word.lower()': token1.lower(),
            '-1:word.istitle()': token1.istitle(),
            '-1:word.isupper()': token1.isupper()
        })
    else:
        features['BOS'] = True  # beginning of sentence

    # Next token
    if i < len(sent)-1:
        token1 = sent[i+1][0]
        features.update({
            '+1:word.lower()': token1.lower(),
            '+1:word.istitle()': token1.istitle(),
            '+1:word.isupper()': token1.isupper()
        })
    else:
        features['EOS'] = True  # end of sentence

    return features

def sent2features(sent):
    return [token2features(sent, i) for i in range(len(sent))]