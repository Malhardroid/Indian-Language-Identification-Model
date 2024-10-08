!pip3 install fasttext
!pip3 install transformers

import zipfile
import os
import re
import pandas as pd
import fasttext
from collections import defaultdict
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report

"""#dataset"""

zip_file_path = '/content/native_script_train_valid_data.zip'
extract_to = 'extracted_data/'

os.makedirs(extract_to, exist_ok=True)

with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(extract_to)

data_file_path = os.path.join('/content/extracted_data/Native_script_data', 'train_combine.txt')

data = pd.read_csv(data_file_path, sep='\t', header=None, usecols=[0], names=['labels'])

print(data.head())

formatted_data_path = '/content/extracted_data/Native_script_data/train_combine.txt'

print("Using formatted data for FastText training from:", formatted_data_path)

def count_sentences_per_language(file_path):
    language_count = defaultdict(int)

    with open(file_path, 'r') as f:
        for line in f:
            language_label, _ = line.strip().split(' ', 1)
            language = language_label.replace('__label__', '')
            language_count[language] += 1

    return language_count

train_data_path = '/content/extracted_data/Native_script_data/train_combine.txt'
valid_data_path = '/content/extracted_data/Native_script_data/valid_combine.txt'

train_language_counts = count_sentences_per_language(train_data_path)
valid_language_counts = count_sentences_per_language(valid_data_path)


print("Sentence counts in training data:")
for language, count in train_language_counts.items():
    print(f"{language}: {count}")

print("\nSentence counts in validation data:")
for language, count in valid_language_counts.items():
    print(f"{language}: {count}")

"""#model training"""

model = fasttext.train_supervised(
    input=formatted_data_path,
    label_prefix='__label__',
    epoch=50,
    lr=0.1,
)

model.save_model('/content/extracted_data/Native_script_data/language_id_model.ftz')

print("model trained")

"""#prediction"""

new_text = "এইটো এটা উদাহৰণ বিবৃতি"

predicted_label = model.predict(new_text)

print(f"Predicted Language: {predicted_label[0][0].replace('__label__', '')}")

"""#evaluation"""

test_data_path = '/content/extracted_data/Native_script_data/valid_combine.txt'

test_results = model.test(test_data_path)

n_examples, precision, recall = test_results

print(f"Number of examples: {n_examples}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")

model = fasttext.load_model('/content/extracted_data/Native_script_data/language_id_model.ftz')


test_data_path = '/content/extracted_data/Native_script_data/valid_combine.txt'


with open(test_data_path, 'r') as f:
    test_data = [line.strip().split(' ', 1) for line in f]


test_df = pd.DataFrame(test_data, columns=['language', 'text'])


test_df['language'] = test_df['language'].str.replace('__label__', '')


test_df['predicted_language'] = test_df['text'].apply(lambda x: model.predict(x)[0][0])
test_df['predicted_language'] = test_df['predicted_language'].str.replace('__label__', '')


language_accuracy = {}


for language in test_df['language'].unique():

    total_instances = test_df[test_df['language'] == language].shape[0]

    correct_predictions = test_df[(test_df['language'] == language) & (test_df['predicted_language'] == language)].shape[0]

    accuracy = correct_predictions / total_instances if total_instances > 0 else 0
    language_accuracy[language] = accuracy

for language, accuracy in language_accuracy.items():
    print(f"Accuracy for {language}: {accuracy:.4f}")
