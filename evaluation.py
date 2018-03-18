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

        # red lines
        plt.plot([0, 20], [0, 0], color='red', lw=1)
        plt.plot([0, 0], [20, 0], color='red', lw=1)
        plt.plot([20, 20], [0, 40], color='red', lw=1)
        plt.plot([0, 40], [20, 20], color='red', lw=1)
        plt.plot([40, 40], [20, 60], color='red', lw=1)
        plt.plot([20, 60], [40, 40], color='red', lw=1)
        plt.plot([60, 60], [40, 80], color='red', lw=1)
        plt.plot([40, 80], [60, 60], color='red', lw=1)
        plt.plot([80, 80], [60, 99], color='red', lw=1)
        plt.plot([60, 99], [80, 80], color='red', lw=1)
        plt.plot([80, 99], [99, 99], color='red', lw=1)
        plt.plot([99, 99], [80, 99], color='red', lw=1)

        # cluster text
        plt.text(22, 5, "rap", color='red')
        plt.text(2, 37, "classical", color='red')
        plt.text(28, 57, "blues", color='red')
        plt.text(48, 77, "metal", color='red')
        plt.text(68, 97, "disco", color='red')

        plt.show()


def pair_preference_prediction(testPairs, p_ystar_xstar):
    dec = np.hstack((testPairs, p_ystar_xstar))
    print "\nMatrix holding a Pair of songs and associated p(y=1|x)"
    print dec


def compute_confusion_matrix(Ytest, p_ystar_xstar):
    Ypred = p_ystar_xstar > 0.5
    print "\nConfusion matrix:"
    return confusion_matrix(Ytest, Ypred)


def compute_accuracy_score(Ytest, p_ystar_xstar):
    Ypred = np.rint(p_ystar_xstar)
    return accuracy_score(Ytest, Ypred)


def compute_ROC_curve(Ytest, p_ystar_xstar):
    Ypred = p_ystar_xstar

    fpr, tpr, thresholds = roc_curve(Ytest, Ypred)
    print thresholds
    roc_auc = auc(fpr, tpr)

    plt.plot(fpr, tpr, color='darkorange',
             lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([-0.05, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver operating characteristic example')
    plt.legend(loc="lower right")
    plt.show()

    return fpr, tpr, roc_auc
