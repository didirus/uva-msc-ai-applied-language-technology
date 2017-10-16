from collections import defaultdict
import pickle
import time

def checkif_float(N):
    '''
    check if the value if float
    :param N:
    :return:T/F
    '''
    try:
        float(N)
        return True
    except ValueError:
        return False


def read_pt(pt_file=None):
    """
    Function to read phrase table
    :param pt_file: file object for phrase table
    :return: Dictionary of phrases. key: (f,e) and value:list of probability
    """
    phrases = {}
    i = 0
    for line in pt_file:
        if i%10000 == 0:
            print('line no.(PT) ', i)
        i += 1

        line = line.split(' ||| ')
        f = line[0]
        e = line[1]
        probab = [float(p) for p in line[2].split()]
        phrases[(f, e)] = probab
    return phrases


def read_lm(lm_file=None):
    """
    Function to read Language modelprobs
    :param lm_file: file object for lang. Model
    :return: Dictionary with key: 'ngram text' and value (ngram prob, backoff)
    """
    gram = 0
    lm = {}
    min_p = 0.0

    i=0
    for line in lm_file:
        if i%10000 == 0:
            print ('line no.(lm): ',i)
        i+=1

        if line[0] =='\\':
            if line[-7:-1]=='grams:':
                print (line)
                gram = line[1]
                # print (gram)
            continue
        line = line.split()

        if gram!=0 and len(line)>0:
            prob = float(line[0])
            if prob < min_p:
                min_p = prob

            if checkif_float(line[-1]):
                backoff_prob = float(line[-1])
                words = line[1:-1]
            else:
                backoff_prob = 0
                words = line[1:]

            ph = ' '.join(words)
            lm[ph] = (prob, backoff_prob)

    # print ("min prob: " ,str(min_p))
    return lm, min_p

def read_ro(ro_file=None):
    """
    Function(same as read_pt()) to read phrase table
    :param ro_file: file object for reorderings
    :return: Dictionary of phrases. key: (f,e) and value:list of probability
    """
    i = 0
    reordering = {}
    for line in ro_file:
        if i % 10000 == 0:
            print ('line no.(ro)',i)
        i += 1
        line = line.split(' ||| ')
        f = line[0]
        e = line[1]
        probs = [float(p) for p in line[2].split()]
        # todo: no use of alignments?
        reordering[(f, e)] = probs

    return reordering

if __name__ == '__main__':

    start = time.time()

    data_path = '../data/ALT/'
    # need data file?
    # f_en = open(data_path +'file.test.en', 'r')
    # f_de = open(data_path+'file.test.de', 'r')


    # Read  phrases and probabs from phrase table
    phrase_table = open(data_path + 'phrase-table', 'r')
    phrases = read_pt(pt_file=phrase_table)
    
    # Read Language model and probabilities
    language_model = open(data_path+'file.en.lm', 'r')
    lm,minlm_p = read_lm(lm_file=language_model)


    reordering_file = open(data_path+'dm.fe.0.75', 'r')
    reordering = read_ro(ro_file=reordering_file)

    # test_results = open(data_path+'testresults.trans.txt.trace', 'r')
    print('time:', time.time() - start)
