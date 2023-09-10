# -*- coding: utf-8 -*-
"""ADE_Corpus_V2_revise_eval_matrics_plot_result (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RIw7yYmKFTMigZil7Lm4DXvJtRPh_EY5
"""

# !pip install transformers accelerate datasets tokenizers seqeval -q

from datasets import Dataset, ClassLabel, Sequence, load_dataset, load_metric
import numpy as np
import pandas as pd
from spacy import displacy
import transformers
from transformers import (AutoModelForTokenClassification,
                          AutoTokenizer,
                          DataCollatorForTokenClassification,
                          pipeline,
                          TrainingArguments,
                          Trainer)

# confirm version > 4.11.0
print(transformers.__version__)

#dataset ADE-corpus-v2
#https://huggingface.co/datasets/ade_corpus_v2
datasets = load_dataset("ade_corpus_v2", "Ade_corpus_v2_drug_ade_relation")

consolidated_dataset = {}

for row in datasets["train"]:
    if row["text"] in consolidated_dataset:
        # consolidated_dataset[row["text"]]["drug_indices_start"].update(row["indexes"]["drug"]["start_char"])
        # consolidated_dataset[row["text"]]["drug_indices_end"].update(row["indexes"]["drug"]["end_char"])
        consolidated_dataset[row["text"]]["effect_indices_start"].update(row["indexes"]["effect"]["start_char"])
        consolidated_dataset[row["text"]]["effect_indices_end"].update(row["indexes"]["effect"]["end_char"])
        # consolidated_dataset[row["text"]]["drug"].append(row["drug"])
        consolidated_dataset[row["text"]]["effect"].append(row["effect"])

    else:
        consolidated_dataset[row["text"]] = {
            "text": row["text"],
            # "drug": [row["drug"]],
            "effect": [row["effect"]],
            # use sets because the indices can repeat for various reasons
            # "drug_indices_start": set(row["indexes"]["drug"]["start_char"]),
            # "drug_indices_end": set(row["indexes"]["drug"]["end_char"]),
            "effect_indices_start": set(row["indexes"]["effect"]["start_char"]),
            "effect_indices_end": set(row["indexes"]["effect"]["end_char"])
        }

df = pd.DataFrame(list(consolidated_dataset.values()))

# df.shape

# df.head()
# #

# #after merge the repreated sentences, plot each sentences word length distribution.
# #draw the distribution of the text length
# import matplotlib.pyplot as plt

# # Assuming you have a list of texts like this:
# texts = df['text']

# # Calculate lengths of each text
# text_lengths = [len(text) for text in texts]

# # Compute statistical measures
# mean_length = np.mean(text_lengths)
# std_length = np.std(text_lengths)

# # Plotting the histogram
# plt.figure(figsize=(12, 6))
# plt.hist(text_lengths, bins=30, color='blue', alpha=0.7, edgecolor='black')  # You can adjust the number of bins as needed

# # Adding vertical lines for mean and standard deviation
# plt.axvline(mean_length, color='r', linestyle='dashed', linewidth=2, label=f'Mean = {mean_length:.2f}')
# plt.axvline(mean_length + std_length, color='g', linestyle='dashed', linewidth=2, label=f'Mean + 1 Std = {mean_length + std_length:.2f}')
# plt.axvline(mean_length - std_length, color='g', linestyle='dashed', linewidth=2, label=f'Mean - 1 Std = {mean_length - std_length:.2f}')

# plt.title('Distribution of Text Lengths with Mean and Std Dev')
# plt.xlabel('Text Length')
# plt.ylabel('Number of Texts')
# plt.legend()
# plt.grid(axis='y', linestyle='--')
# plt.tight_layout()
# plt.show()
# # # Plotting the histogram
# # plt.figure(figsize=(12, 6))
# # plt.hist(text_lengths, bins=50, color='blue', alpha=0.7)  # You can adjust the number of bins as needed
# # plt.title('Distribution of Text Lengths in ADE_Corpus_V2')
# # plt.xlabel('Text Length')
# # plt.ylabel('Number of Texts')
# # plt.grid(axis='y', linestyle='--')
# # plt.show()

## since no spans overlap, we can sort to get 1:1 matched index spans
# note that sets don't preserve insertion order

# df["drug_indices_start"] = df["drug_indices_start"].apply(list).apply(sorted)
# df["drug_indices_end"] = df["drug_indices_end"].apply(list).apply(sorted)
df["effect_indices_start"] = df["effect_indices_start"].apply(list).apply(sorted)
df["effect_indices_end"] = df["effect_indices_end"].apply(list).apply(sorted)

print(len(df['effect']))
print(df.shape)
# print(df['text'][5],df['effect'][5], df['effect_indices_start'][5], df['effect_indices_end'][5])

import pandas as pd
from itertools import chain

# Flatten the lists in the 'effect' column
flattened_effects = list(chain.from_iterable(df['effect']))

# Count the distinct values
distinct_count = len(set(flattened_effects))
all_ae_count = len(flattened_effects)

print("Number of distinct count in 'Adverse Event' terms:", distinct_count)
print("Number of count in 'Adverse Event' terms:", all_ae_count)


# Count the number of terms in each list within 'effect' column
# df['num_terms'] = df['effect'].apply(lambda x: len(x))

# print("total number of Adverse Event Lables:",df['num_terms'].sum())

# save to JSON to then import into Dataset object
df.to_json("dataset.jsonl", orient="records", lines=True)

cons_dataset = load_dataset("json", data_files="dataset.jsonl")

# no train-test provided, so we create our own
# cons_dataset = cons_dataset["train"].train_test_split(test_size=0.2, seed=42)

cons_dataset = cons_dataset["train"].train_test_split(test_size=0.2, seed=42)

import pandas as pd
from itertools import chain

# Flatten the lists in the 'effect' column
flattened_effects = list(chain.from_iterable(cons_dataset['train']['effect']))

# Count the distinct values
distinct_count = len(set(flattened_effects))
total_count = len(flattened_effects)
print("Number of distinct count in 'Adverse Event' terms in training:", distinct_count)
print("Number of count in 'Adverse Event' terms in training:", total_count)

flattened_effects = list(chain.from_iterable(cons_dataset['test']['effect']))

# Count the distinct values
distinct_count = len(set(flattened_effects))
total_count = len(flattened_effects)
print("Number of distinct count in 'Adverse Event' terms in training:", distinct_count)
print("Number of count in 'Adverse Event' terms in training:", total_count)

label_list = ['O', 'B-AE', 'I-AE']



custom_seq = Sequence(feature=ClassLabel(num_classes=3,
                                         names=label_list,
                                         names_file=None, id=None), length=-1, id=None)

cons_dataset["train"].features["ner_tags"] = custom_seq
cons_dataset["test"].features["ner_tags"] = custom_seq

#fine-tuning
from transformers import AutoTokenizer

task = "ner" # Should be one of "ner", "pos" or "chunk"
model_checkpoint = "bert-base-uncased"
batch_size = 16

# model_checkpoint = "biomednlp/pubmedbert-base-uncased-abstract"
model_checkpoint = "bert-base-uncased"
# model_checkpoint = "allenai/scibert_scivocab_uncased"
model = AutoModelForTokenClassification.from_pretrained(model_checkpoint, num_labels=len(label_list))
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

#function to generate BIO tags for effect
def generate_row_labels(row, verbose=False):
    """ Given a row from the consolidated `Ade_corpus_v2_drug_ade_relation` dataset,
    generates BIO tags for drug and effect entities.

    """

    text = row["text"]

    labels = []
    label = "O"
    prefix = ""

    # while iterating through tokens, increment to traverse all drug and effect spans
    # drug_index = 0
    effect_index = 0

    tokens = tokenizer(text, return_offsets_mapping=True)

    for n in range(len(tokens["input_ids"])):
        offset_start, offset_end = tokens["offset_mapping"][n]

        # should only happen for [CLS] and [SEP]
        if offset_end - offset_start == 0:
            labels.append(-100)
            continue

        # if drug_index < len(row["drug_indices_start"]) and offset_start == row["drug_indices_start"][drug_index]:
        #     label = "DRUG"
        #     prefix = "B-"

        if effect_index < len(row["effect_indices_start"]) and offset_start == row["effect_indices_start"][effect_index]:
            label = "AE"
            prefix = "B-"

        labels.append(label_list.index(f"{prefix}{label}"))

        # if drug_index < len(row["drug_indices_end"]) and offset_end == row["drug_indices_end"][drug_index]:
        #     label = "O"
        #     prefix = ""
        #     drug_index += 1

        if effect_index < len(row["effect_indices_end"]) and offset_end == row["effect_indices_end"][effect_index]:
            label = "O"
            prefix = ""
            effect_index += 1

        # need to transition "inside" if we just entered an entity
        if prefix == "B-":
            prefix = "I-"

    if verbose:
        print(f"{row}\n")
        orig = tokenizer.convert_ids_to_tokens(tokens["input_ids"])
        for n in range(len(labels)):
            print(orig[n], labels[n])
    tokens["labels"] = labels

    return tokens

#labeled_dataset
labeled_dataset = cons_dataset.map(generate_row_labels)

labeled_dataset['train']

# word will be splitted into subwords
#test the generate_row_labels function
generate_row_labels(cons_dataset["train"][0], verbose=True)

# !pip install accelerate -U
# !pip install transformers[torch]

model_name = model_checkpoint.split("/")[-1]
from transformers import TrainingArguments, Trainer

args = TrainingArguments(
    f"{model_name}-finetuned-{task}",
    evaluation_strategy = "epoch",
    learning_rate=1e-5,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    num_train_epochs=5,
    weight_decay=0.05,
    logging_steps=1
)

data_collator = DataCollatorForTokenClassification(tokenizer)
metric = load_metric("seqeval")

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Remove ignored index (special tokens)
    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    # results = metric.compute(predictions=true_predictions, references=true_labels)
    #flat the prediction result
    flat_y_true = [item for sublist in true_labels for item in sublist]
    flat_y_pred = [item for sublist in true_predictions for item in sublist]

    #use the macro average precision, recall, f1 for training
    precision = precision_score(flat_y_true, flat_y_pred, average='macro')
    recall = recall_score(flat_y_true, flat_y_pred, average='macro')
    f1 = f1_score(flat_y_true, flat_y_pred, average='macro')
    accuracy = accuracy_score(flat_y_true, flat_y_pred)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        # "precision": results["overall_precision"],
        # "recall": results["overall_recall"],
        # "f1": results["overall_f1"],
        # "accuracy": results["overall_accuracy"],
    }

# cons_dataset = cons_dataset["train"].train_test_split(test_size=0.2, seed=42)

lltraindata = labeled_dataset['train'].train_test_split(test_size=0.2,seed=42)
print(lltraindata)

from sklearn.metrics import precision_score, recall_score, f1_score,accuracy_score, classification_report

# trainer = Trainer(
#     model,
#     args,
#     train_dataset=lltraindata["train"],
#     eval_dataset=lltraindata["test"],
#     data_collator=data_collator,
#     tokenizer=tokenizer,
#     compute_metrics=compute_metrics,

# )
trainer = Trainer(
    model,
    args,
    train_dataset=labeled_dataset["train"],
    eval_dataset=labeled_dataset["test"],
    data_collator=data_collator,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,

)

trainer.train()

train_result = trainer.state.log_history
# print(train_result)

# Define a filename for the log file
log_file = "training_log.json"

# Save the log history to a JSON file
with open(log_file, "w") as f:
    json.dump(train_result, f)

print(f"Training log saved to {log_file}")

train_loss = []
epoches = []
# numbers_list = [round(x, 1) for x in list(float(i)/10 for i in range(10, 51))]

for elem in trainer.state.log_history:
    # if elem['epoch'] in numbers_list and 'loss' in elem.keys():
    if 'loss' in elem.keys():
      train_loss.append(elem['loss'])
      epoches.append(elem['epoch'])
      # break
# print(train_result['loss'], train_result['epochs]'])
print(len(train_loss))
print(epoches)

macroF1 = []
macroPrecision = []
macroRecall = []
epochF1 = []
# numbers_list = [round(x, 1) for x in list(float(i)/10 for i in range(10, 51))]

for elem in trainer.state.log_history:
    # if elem['epoch'] in numbers_list and 'loss' in elem.keys():
    if 'eval_f1' in elem.keys():
      macroF1.append(elem['eval_f1'])
      macroPrecision.append(elem['eval_precision'])
      macroRecall.append(elem['eval_recall'])
      epochF1.append(elem['epoch'])
      # break
# print(train_result['loss'], train_result['epochs]'])
print(len(macroF1),len(macroPrecision),len(macroRecall))
print(epochF1)

numbers_list = [round(x, 1) for x in list(float(i)/10 for i in range(10, 21))]
# numbers_list

#plot the macro f1 over epoches
import matplotlib.pyplot as plt
from transformers import Trainer, TrainingArguments

# Define your Trainer and TrainingArguments
# Start training
# Extract training and validation loss from the log history

# train_losses = [0.0162, 0.0111, 0.0547, 0.0033, 0.0024]
# eval_losses = [item['eval_loss'] for item in trainer.state.log_history]
# Plot training and validation loss
# print(epoches)
plt.plot(epochF1, macroF1, label='macro F1 score')
# plt.plot(eval_losses, label='Testing loss')
#plt.title('Training and Testing Loss vs. Steps')
plt.title('macro F1 score vs. Steps')

plt.xlabel('Steps')
plt.ylabel('macro F1')
plt.legend()
plt.show()

# Save the plot to a file (e.g., PNG, PDF, or SVG)
plt.savefig('macrof1 vs steps.png')  # Save as PNG
# Close the plot
plt.close()

#plot the macro f1, precision, recall over epoches
import matplotlib.pyplot as plt
from transformers import Trainer, TrainingArguments

# Define your Trainer and TrainingArguments
# Start training
# Extract training and validation loss from the log history

# train_losses = [0.0162, 0.0111, 0.0547, 0.0033, 0.0024]
# eval_losses = [item['eval_loss'] for item in trainer.state.log_history]
# Plot training and validation loss
# print(epoches)
plt.plot(epochF1, macroF1, label='macro F1 score')
plt.plot(epochF1, macroPrecision, label='macro Precision score')
plt.plot(epochF1, macroRecall, label='macro Recall score')

# plt.plot(eval_losses, label='Testing loss')
#plt.title('Training and Testing Loss vs. Steps')
plt.title('macro F1 score vs. Steps')

plt.xlabel('Steps')
plt.ylabel('macro F1, Precision, Recall')
plt.legend()
plt.show()

# Save the plot to a file (e.g., PNG, PDF, or SVG)
plt.savefig('macrof1 precision recall vs steps.png')  # Save as PNG
# Close the plot
plt.close()

#plot the training loss
import matplotlib.pyplot as plt
from transformers import Trainer, TrainingArguments

# Define your Trainer and TrainingArguments
# Start training
# Extract training and validation loss from the log history

# train_losses = [0.0162, 0.0111, 0.0547, 0.0033, 0.0024]
# eval_losses = [item['eval_loss'] for item in trainer.state.log_history]
x = [1,2,3,4,5]
# Plot training and validation loss
print(epoches)
plt.plot(epoches, train_loss, label='Training loss')
# plt.plot(eval_losses, label='Testing loss')
#plt.title('Training and Testing Loss vs. Steps')
plt.title('Training Loss vs. Steps')

plt.xlabel('Steps')
plt.ylabel('Loss')
plt.legend()
plt.show()

# Save the plot to a file (e.g., PNG, PDF, or SVG)
plt.savefig('loss vs steps.png')  # Save as PNG
# Close the plot
plt.close()

#plot the training loss in moving average
import matplotlib.pyplot as plt
from transformers import Trainer, TrainingArguments

# Define your Trainer and TrainingArguments
# Start training
# Extract training and validation loss from the log history
#plot epoches, train_loss
window_size = 5
moving_average = np.convolve(train_loss, np.ones(window_size)/window_size, mode='valid')

# Plot original loss and moving average
plt.figure(figsize=(10, 6))
plt.plot(epoches[window_size - 1:], moving_average, label=f'Moving Average (Window = {window_size})',color = 'blue')
plt.plot(epoches, train_loss, alpha=0.3, label='Original Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss with Moving Average')
plt.legend()
plt.grid(True)
plt.show()
# Save the plot to a file (e.g., PNG, PDF, or SVG)
plt.savefig('average loss vs steps.png')  # Save as PNG
# Close the plot
plt.close()

from sklearn.metrics import precision_score, recall_score, f1_score,accuracy_score, classification_report

predictions, labels, _ = trainer.predict(labeled_dataset["test"])
# print(predictions)
#neural network output classification
predictions = np.argmax(predictions, axis=2)
# print(predictions)

# Remove ignored index (special tokens)
true_predictions = [
    [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
    for prediction, label in zip(predictions, labels)
]
# print(true_predictions)

true_labels = [
    [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
    for prediction, label in zip(predictions, labels)
]
print("number of text in prediction:",len(true_predictions))
# print(len(true_labels))
print("predict labels",true_predictions)
print("true labels",true_labels)
# results = metric.compute(predictions=true_predictions, references=true_labels)
# print(results)

flat_y_true = [item for sublist in true_labels for item in sublist]
flat_y_pred = [item for sublist in true_predictions for item in sublist]
print("totoal number of labels in prediction:",len(flat_y_true))


precision = precision_score(flat_y_true, flat_y_pred, average='macro')
recall = recall_score(flat_y_true, flat_y_pred, average='macro')
f1 = f1_score(flat_y_true, flat_y_pred, average='macro')
accuracy = accuracy_score(flat_y_true, flat_y_pred)

print("Macro Precision:", precision)
print("Macro Recall:", recall)
print("Macro F1 Score:", f1)
print("Accuracy:", accuracy)

report = classification_report(flat_y_true, flat_y_pred, output_dict=True)

# report

#use the table to show the evaluation result
eval_test_result = pd.DataFrame(report).transpose()

# eval_test_result
x
#show dimensions
num_rows = len(true_predictions)
# Assuming each inner list can have a different length
num_cols_per_row = [len(row) for row in true_predictions]

print("Number of rows for predictions:", num_rows)
print("Number of columns in each row:", num_cols_per_row)
