# This module contains functions used for evaluation

import numpy as np
import GPy
from matplotlib import pyplot as plt
from sklearn.metrics import confusion_matrix, roc_curve, auc, accuracy_score


# Compute kernel matrix
def compute_kernel_matrix(data, enable):
    if enable is True:
        data_attr = data[:, 4:].astype(float)
        kernel = GPy.kern.PjkRbf(data_attr.shape[1])
        kernel.variance = 3.1
        kernel.lengthscale = 4

        kernel_matrix = kernel._RbfBase_K(data_attr)
        imgplot = plt.imshow(kernel_matrix)
        imgplot.set_interpolation('none')
        plt.text(10, 80, "lengthscale: " + str(kernel.lengthscale[0]), bbox=dict(facecolor='white', alpha=0.5))
        plt.show()


def pair_preference_prediction(testPairs, p_ystar_xstar):
    dec = np.hstack((testPairs, p_ystar_xstar))
    print "\nMatrix holding a Pair of songs and associated p(y=1|x)"
    print dec


def compute_confusion_matrix(Ytest, p_ystar_xstar):
    Ypred = p_ystar_xstar > 0.5
    print "\nConfusion matrix:"
    print confusion_matrix(Ytest, Ypred)


def compute_accuracy_score(Ytest, p_ystar_xstar):
    Ypred = np.rint(p_ystar_xstar)
    return accuracy_score(Ytest, Ypred)


def compute_ROC_curve(Ytest, p_ystar_xstar):
    Ypred = p_ystar_xstar

    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for i in range(2):
        fpr[i], tpr[i], _ = roc_curve(Ytest, Ypred)
        roc_auc[i] = auc(fpr[i], tpr[i])

    plt.plot(fpr[1], tpr[1], color='darkorange',
             lw=2, label='ROC curve (area = %0.2f)' % roc_auc[1])
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([-0.05, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver operating characteristic example')
    plt.legend(loc="lower right")
    plt.show()
