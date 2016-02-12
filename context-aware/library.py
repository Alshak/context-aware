from math import floor

def ca_set_binary_threshold_from_skew(input_dict):
    cost_false_pos = input_dict['cost_false_pos']
    cost_false_neg = input_dict['cost_false_neg']
    ratio_pos_neg = input_dict['ratio_pos_neg']
    output_dict = {}
    output_dict['bin_thres'] =  float(ratio_pos_neg) * (float(cost_false_neg) / float(cost_false_pos))
    return output_dict

def ca_estimate_pos_neg_from_prd_fct(input_dict):
    import re
    output_dict = {}
    deploy_data = input_dict['deploy_data']
    target_att = input_dict['target_att']
    pos_col = input_dict['pos_col']
    neg_col = input_dict['neg_col']

    
    with open(deploy_data) as f:
        deploy_file = f.read()
        
    pos_arr = re.findall(target_att+"\(.*," +pos_col+"\)\.", deploy_file)
    print len(pos_arr)

    neg_arr = re.findall(target_att+"\(.*," +neg_col+"\)\.", deploy_file)
    print len(neg_arr)
    
    output_dict['ratio_pos_neg'] = len(pos_arr)/float(len(neg_arr))  
    return output_dict

def ca_apply_binary_threshold(input_dict):
    performance = input_dict['score']
    thres = input_dict['bin_thres']
    
    n = len(performance['predicted'])
    for i in range(n):
        if performance['predicted'][i] >= thres:
            performance['predicted'][i] = 1
        else:
            performance['predicted'][i] = 0
                
    output_dict = {}
    output_dict['classes'] = performance
    return output_dict

def ca_rank_driven_binary_threshold_selection(input_dict):
    from collections import Counter

    performance = input_dict['score']
    rate = input_dict['rate']
    list_score = []
    labels = ''
    n = len(performance['actual'])
    for i in range(n):
        list_score.append((performance['actual'][i],performance['predicted'][i]))
    output_dict = {}
    sorted_score = sorted(list_score, key=lambda scr: scr[1],reverse=True)

    rank = floor(n * (float(rate) / float(100)))
    current_rank = 0
    previous = float('inf')
    current = previous
    for i in range(n):
        current = sorted_score[i][1]
        current_rank = current_rank + 1        
        if current_rank > rank:
            output_dict['bin_thres'] = (previous + current) / float(2)                     
            break
        previous = sorted_score[i][1]
    return output_dict

def ca_optimal_binary_threshold_selection(input_dict):
    from collections import Counter

    performance = input_dict['score']
    method = input_dict['method']
    list_score = []
    labels = ''
    n = len(performance['actual'])
    for i in range(n):
        list_score.append((performance['actual'][i],performance['predicted'][i]))
    output_dict = {}
    sorted_score = sorted(list_score, key=lambda scr: scr[1],reverse=True)
    counter_neg = len([score for score in list_score if score[0] == 0])
    counter_pos = len([score for score in list_score if score[0] == 1])
    output_dict['bin_thres'] = find_best_roc_weight(method,sorted_score,counter_pos,counter_neg)        
    return output_dict

def find_best_roc_weight(method,a_list,a_num_positives,a_num_negatives):
    previous = float('inf')
    xpos = 0
    xneg = a_num_negatives
    the_best_value = get_value(method,xpos,xneg,a_num_positives,a_num_negatives)
    best = previous
    for the_elt in a_list:
        the_roc = the_elt
        current = the_roc[1]
        if current != previous:
            possible_best_value = get_value(method,xpos,xneg,a_num_positives,a_num_negatives)
            print '%f > %f' %(possible_best_value,the_best_value)
            if  possible_best_value > the_best_value:
                the_best_value = possible_best_value
                print '%f -> %f' %(best,(previous + current) / float(2))
                best = (previous + current) / float(2)
        if the_roc[0] == 1:
            xpos += 1
        else:
            xneg -= 1
        previous = current;        

    possible_best_value = get_value(method,xpos,xneg,a_num_positives,a_num_negatives)
    if  possible_best_value > the_best_value:
        the_best_value = possible_best_value
        best = (previous + float('-inf')) / float(2)   
    return best

def get_value(method, TP, TN, P, N):
    if method == 'accuracy':
        accuracy = (TP + TN) / float(P+N)
        return accuracy
    elif method == 'balanced':
        balanced = ( TP / float(P) + TN / float(N)) / 2
        return balanced
    FN = P - TP
    FP = N - TN
    recall = TP / float(P)
    if method == 'recall':
        return recall
    if TP + FP > 0:
        precision = TP / float(TP + FP)
        if method == 'precision':
            return precision
        if precision + recall > 0:
            F_measure = 2 * precision * recall / (precision + recall)
        else:
            F_measure = 0
    else:
        F_measure = 0
    return F_measure