from collections import defaultdict
import pickle
import time, math

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
        if i%50000 == 0:
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
        if i%50000 == 0:
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
        if i % 50000 == 0:
            print ('line no.(ro)',i)
        i += 1
        line = line.split(' ||| ')
        f = line[0]
        e = line[1]
        probs = [float(p) for p in line[2].split()]
        # todo: no use of alignments?
        reordering[(f, e)] = probs

    return reordering
# todo: calculate cost from language model recursive?
def lm_cost(phrase_lm, lm, min_lm_prob):
    return

def word_cost():
    # for back-off
    return

def reor_model_cost(phrase, trace, reorder_file, f_line):

    # index of the phrase in the trace sentence
    phrase_index = ''.join([str(phrase[0]), ':', str(phrase[1])])

    phrase_pos = trace.index(phrase_index)
    prev_ph_align = trace[phrase_pos - 1].split(':')[0]
    if (phrase_pos != len(trace) - 1):
        next_ph_align = trace[phrase_pos + 1].split(':')[0]
    else:
        next_ph_align = 'end-end'
    next_ph_align_begin, next_ph_align_end = next_ph_align.split('-')
    prev_ph_align_start, prev_ph_align_end = prev_ph_align.split('-')

    reor_cost = 0
    e = phrase[1].rstrip()
    f_align_start = int(phrase[0].split('-')[0])
    f_align_end = int(phrase[0].split('-')[1])

    # list of words from the f_line
    f = f_line[f_align_start:f_align_end + 1]
    f = ' '.join(f).rstrip()
    try:
        probs = reorder_file[(f, e)]
        rl_m, rl_s, rl_d, lr_m, lr_s, lr_d = probs
        RL_cost = 0
        LR_cost = 0

        # if phrase is first in line
        if phrase_pos == 0:
            RL_cost = rl_m
        else:
            if (int(prev_ph_align_end) == f_align_start - 1):
                RL_cost = rl_m
            elif (int(prev_ph_align_start) == f_align_end + 1):
                RL_cost = rl_s
            else:
                RL_cost = rl_d

        # if phrase is last in line
        if phrase_pos == len(trace) - 1:
            LR_cost = lr_m
        else:
            if int(next_ph_align_begin) == f_align_end + 1:
                LR_cost = lr_m
            elif int(next_ph_align_end) == f_align_start - 1:
                LR_cost = lr_s
            else:
                LR_cost = lr_d

        # probabs of both direction multiplied
        phrase_cost = LR_cost * RL_cost

        # log probabs
        phrase_cost = math.log10(phrase_cost)
        phrase_cost *= 1
    except KeyError:
        # untranslated phrase
        phrase_cost = -1
    reor_cost += phrase_cost
    return reor_cost


def transl_model_cost(phrase,p_table,f_line):
    # phrases in the trace assign 4 translation model weights
    e = phrase[1].rstrip()

    f_al_start = int(phrase[0].split('-')[0])
    f_al_stop = int(phrase[0].split('-')[1])

    # Get list of words from the f_line
    f = f_line[f_al_start:f_al_stop + 1]
    f = ' '.join(f).rstrip()

    try:
        p_fe, lex_fe, p_ef, lex_ef, word_pen = p_table[(f, e)]
        # For now assumed to be the sum of all the probs (weighted by 1)
        phrase_cost = 1 * math.log10(p_fe) + 1 * math.log10(lex_fe) + 1 * math.log10(p_ef) + 1 * math.log10(
            lex_ef) + 1 * word_pen
        phrase_cost = phrase_cost * 1  # -1
    except KeyError:
        if f != e:
            print 'key not found: ', (f, e)

        phrase_cost = -1
    return phrase_cost


def overall_trans_cost(p_table,lm,min_lm_prob, reorder_file):

    print ('overall cost function')
    with open('testresults.trans.txt.trace', 'r') as traces:
        with open('file.test.de', 'r') as f_file:
            # dump the cost in the file
            with open('cost_output.txt', 'w') as output_file:
                sentence_cost_list = []
                for f_line, trace in zip(f_file, traces):
                    trace = trace.split(' ||| ')
                    f_line = f_line.split()
                    phrases = [tuple(p.split(':', 1)) for p in trace]
                    cost_per_phrase = []
                    for i in range(0, len(phrases)):
                        phrase = phrases[i]
                        phrase_translation_model_cost = transl_model_cost(phrase, p_table, f_line)
                        phrase_reordering_model_cost = reor_model_cost(phrase, trace, reorder_file, f_line)

                        # language model-> start and end symbols need to be added to the phrase

                        phrase_lm = phrase[1]
                        if i == 0:
                            phrase_lm = "<s> " + phrase[1]
                        if i == len(phrases):
                            phrase_lm = phrase[1] + " </s>"
                        phrase_language_model_cost = lm_cost(phrase_lm, lm, min_lm_prob)
                        phrase_penalty = -1
                        phrase_cost = 1 * phrase_reordering_model_cost + 1 * phrase_translation_model_cost + 1 * phrase_language_model_cost + 1 * phrase_penalty
                        cost_per_phrase.append(phrase_cost)

    return


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


    reordering_file = open(data_path+'dm_fe_0.75', 'r')
    reordering = read_ro(ro_file=reordering_file)

    # test_results_trace = open(data_path+'testresults.trans.txt.trace', 'r')

    overall_trans_cost(phrases,lm,minlm_p,reordering)



    print('time:', time.time() - start)