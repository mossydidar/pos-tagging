import pickle
import time
import gzip
import zlib
import _pickle as cPickle
import json

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix
from sklearn.externals import joblib


class pos_tagger():

    def __init__(self):
        self.sentences  = list()
        self.features   = list()
        self.pos_labels = list()
        self.vectorizer = DictVectorizer()
        self.model      = LogisticRegressionCV(n_jobs=-1,
                                               verbose=1,
                                               random_state=123)

    def read_data(self, train_datapath):
        self.sentences  = []
        with open(train_datapath, 'r') as infile:
            sent = []
            for line in infile:
                line = str.split(str.strip(line), '\t')
                if len(line) == 3:
                    token, tag_label = line[0], line[2]
                    sent.append((token, tag_label))
                    continue
                self.sentences.append(sent)
                sent = []
        print("-> %d sentences are read from '%s'." % (len(self.sentences), train_datapath))
        return

    def get_feature(self, token, token_index, sent):
        token_feature = {
                        'token'             : token,
                        'is_first'          : token_index == 0,
                        'is_last'           : token_index == len(sent)-1,

                        'is_capitalized'    : token[0].upper() == token[0],
                        'is_all_capitalized': token.upper() == token,
                        'is_capitals_inside': token[1:].lower() != token[1:],
                        'is_numeric'        : token.isdigit(),

                        'prefix-1'          : token[0],
                        'prefix-2'          : '' if len(token) < 2  else token[:1],

                        'suffix-1'          : token[-1],
                        'suffix-2'          : '' if len(token) < 2  else token[-2:],

                        'prev-token'        : '' if token_index == 0     else sent[token_index - 1][0],
                        '2-prev-token'      : '' if token_index <= 1     else sent[token_index - 2][0],

                        'next-token'        : '' if token_index == len(sent) - 1     else sent[token_index + 1][0],
                        '2-next-token'      : '' if token_index >= len(sent) - 2     else sent[token_index + 2][0]
                        }
        return  token_feature

    def form_data(self):
        self.features   = []
        self.pos_labels = []
        for sent in self.sentences:
            for token_index, token_pair in enumerate(sent):
                token       = token_pair[0]
                self.features.append(self.get_feature(token, token_index, sent))
                try:
                    pos_label = token_pair[1]
                    self.pos_labels.append(pos_label)
                except:
                    pass
        return

    def train(self, train_datapath):
        self.read_data(train_datapath)
        self.form_data()
        print("-> Training phase is started.")
        t0 = time.time()
        self.model.fit(self.vectorizer.fit_transform(self.features), self.pos_labels)
        print("-> Training is completed in %s secs." % (str(round(time.time() - t0, 3))))
        preds = self.model.predict(self.vectorizer.transform(self.features))
        acc_score = accuracy_score(self.pos_labels, preds)
        print("## Evaluation accuracy is %.2f on '%s'" % (acc_score, train_datapath))
        print()
        return

    def evaluate(self, datapath):
        self.read_data(datapath)
        self.form_data()
        preds       = self.model.predict(self.vectorizer.transform(self.features))
        acc_score   = accuracy_score(self.pos_labels, preds)
        print("## Evaluation accuracy is %.2f on '%s'" % (acc_score, datapath))
        print()
        return acc_score

    def test(self, datapath):
        self.read_data(datapath)
        self.form_data()
        preds       = self.model.predict(self.vectorizer.transform(self.features))
        precision   = precision_score(self.pos_labels, preds, average='micro')
        recall      = recall_score(self.pos_labels, preds, average='micro')
        f1          = f1_score(self.pos_labels, preds, average='micro')
        accuracy    = accuracy_score(self.pos_labels, preds)
        conf_matrix = confusion_matrix(self.pos_labels, preds)
        return precision, recall, f1, accuracy, conf_matrix

    def tag(self, sentence):
        self.sentences = list([sentence])
        self.form_data()
        preds       = (self.model.predict(self.vectorizer.transform(self.features)))
        tagged_sent = list(zip(sentence, preds))
        return tagged_sent

    def tag_sents(self, sentences):
        tagged_sents = list()
        for sent in sentences:
            tagged_sents.append(self.tag(sent))
        return tagged_sents

    def save(self, save_path):
        with gzip.GzipFile(save_path, 'wb') as outfile:
            joblib.dump((self.vectorizer, self.model), outfile, compress=('gzip', 9))
        print("-> POS tagger is saved to '%s'" % save_path)
        return

    def load(self, load_path):
        with gzip.GzipFile(load_path, 'rb') as infile:
            self.vectorizer, self.model = joblib.load(infile)
        print("-> POS tagger is loaded from '%s'" % load_path)
        return


def main():

    TRAIN_DATAPATH          = '../data/en-ud-train.conllu'
    DEV_DATAPATH            = '../data/en-ud-dev.conllu'

    tagger = pos_tagger()

    tagger.train(TRAIN_DATAPATH)
    tagger.evaluate(DEV_DATAPATH)

    precision, recall, f1, accuracy, confusion = tagger.test(DEV_DATAPATH)
    print('test pre:', precision)
    print('test rec:', recall)
    print('test f1: ', f1)
    print('test acc:', accuracy)
    print('test con:', confusion)

    SAVE_PATH = '../model/pos_tagger.gz'
    tagger.save(SAVE_PATH)

    SAVE_PATH = '../model/pos_tagger.gz'
    tagger = pos_tagger()
    tagger.load(SAVE_PATH)

    print(tagger.tag(['I', 'do', 'n\'t', 'think', 'it', 'matters']))
    print(tagger.tag_sents([['I', 'do', 'n\'t', 'think', 'it', 'matters'], ['Gets', 'the', 'Job', 'Done']]))
    return

if __name__ == '__main__':
    main()